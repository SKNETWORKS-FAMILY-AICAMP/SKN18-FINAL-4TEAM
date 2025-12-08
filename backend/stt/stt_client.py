"""
stt_client.py

브라우저에서 올라온 audio/webm 바이트를 받아
OpenAI Whisper(whisper-1) API로 전사한 뒤,
segment 기반 lines(list[dict])를 반환하는 클라이언트.
"""

import asyncio
import io
import os
import tempfile
import wave
from typing import Any, Dict, List, Optional, Mapping

from openai import OpenAI


class STTClient:
    def __init__(
        self,
        *,
        model_size: str = "base",  # 호환성 유지용
        language: str = "auto",
        backend: str = "openai",
        device: Optional[str] = None,
        enable_diarization: bool = False,
        enable_translation: bool = False,
        enable_repair: bool = False,
        openai_model: str = "whisper-1",
        openai_api_key: Optional[str] = None,
        temperature: float = 0.0,
        prompt: Optional[str] = None,
        **extra_engine_kwargs: Any,
    ) -> None:
        self.enable_repair = enable_repair

        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY 환경변수가 설정되지 않았습니다. "
                "또는 STTClient(openai_api_key=...)로 키를 넘겨주세요."
            )

        self._client = OpenAI(api_key=api_key)

        self._language = language
        self._model = openai_model
        self._temperature = temperature
        self._prompt = (prompt or "").strip()
        self._extra_engine_kwargs: Dict[str, Any] = dict(extra_engine_kwargs)

        self._lock = asyncio.Lock()

    # --- (옵션) 정말로 raw PCM을 받을 때만 쓰는 유틸: 지금은 안 써도 됨 ----
    @staticmethod
    def _pcm16_to_wav_bytesio(
        pcm_bytes: bytes,
        sample_rate: int = 16000,
        num_channels: int = 1,
    ) -> io.BytesIO:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(num_channels)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_bytes)
        buf.seek(0)
        buf.name = "audio.wav"
        return buf

    # ----------------------------------------------------------------------
    # 핵심: webm 바이트를 안전하게 임시 .webm 파일로 만들어서 OpenAI에 넘긴다
    # ----------------------------------------------------------------------
    def _openai_transcribe_from_webm_bytes(self, webm_bytes: bytes):
        """
        webm 바이트를 tempfile에 .webm 으로 저장한 뒤,
        해당 파일 객체를 OpenAI whisper-1에 넘긴다.
        """
        # NamedTemporaryFile 래퍼(tmp) 자체를 넘기지 말고,
        # 경로를 통해 다시 열린 실제 파일 객체를 OpenAI에 전달합니다.
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(webm_bytes)
            tmp.flush()
            webm_path = tmp.name

        try:
            with open(webm_path, "rb") as f:
                kwargs: Dict[str, Any] = {
                    "model": self._model,
                    "file": f,
                    "response_format": "verbose_json",
                    "temperature": self._temperature,
                }
                if self._language != "auto":
                    kwargs["language"] = self._language
                if self._prompt:
                    kwargs["prompt"] = self._prompt

                # 실제 API 호출
                resp = self._client.audio.transcriptions.create(**kwargs)
                return resp
        finally:
            try:
                os.remove(webm_path)
            except Exception:
                # 임시 파일 삭제 실패는 치명적이지 않으므로 무시
                pass

    # -------------------------
    #  NLP 보정 훅 (현재는 패스스루)
    # -------------------------

    def _repair_lines(self, lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not self.enable_repair:
            return lines
        # TODO: LLM 기반 보정 로직 추가 가능
        return lines

    # -------------------------
    #  OpenAI Whisper 호출 (sync)
    # -------------------------

    def _transcribe_pcm_sync_impl(self, pcm_bytes: bytes) -> List[Dict[str, Any]]:
        """
        여기서의 pcm_bytes 는 실제로는 브라우저에서 온 audio/webm 바이트라고 가정.
        (뷰에서 그대로 request.body 를 넘기고 있다는 전제)
        """
        # 1) webm 바이트를 .webm 파일로 저장 → OpenAI에 전달
        resp = self._openai_transcribe_from_webm_bytes(pcm_bytes)

        # 2) segment → lines 변환
        segments = getattr(resp, "segments", None) or []

        lines: List[Dict[str, Any]] = []

        def seg_to_mapping(seg: Any) -> Mapping[str, Any]:
            if isinstance(seg, Mapping):
                return seg
            return {
                "id": getattr(seg, "id", None),
                "seek": getattr(seg, "seek", None),
                "start": getattr(seg, "start", None),
                "end": getattr(seg, "end", None),
                "text": getattr(seg, "text", None),
                "tokens": getattr(seg, "tokens", None),
                "temperature": getattr(seg, "temperature", None),
                "avg_logprob": getattr(seg, "avg_logprob", None),
                "compression_ratio": getattr(seg, "compression_ratio", None),
                "no_speech_prob": getattr(seg, "no_speech_prob", None),
            }

        for idx, seg in enumerate(segments):
            s = seg_to_mapping(seg)
            line = {
                "id": s.get("id", idx),
                "start": s.get("start"),
                "end": s.get("end"),
                "text": s.get("text", "") or "",
                "tokens": s.get("tokens"),
                "avg_logprob": s.get("avg_logprob"),
                "no_speech_prob": s.get("no_speech_prob"),
            }
            lines.append(line)

        lines = self._repair_lines(lines)
        return lines

    # -------------------------
    #  STT 메인 로직 (async)
    # -------------------------

    async def _run_once_pcm(self, pcm_bytes: bytes) -> List[Dict[str, Any]]:
        loop = asyncio.get_running_loop()
        async with self._lock:
            return await loop.run_in_executor(
                None, self._transcribe_pcm_sync_impl, pcm_bytes
            )

    async def transcribe_pcm(self, pcm_bytes: bytes) -> List[Dict[str, Any]]:
        return await self._run_once_pcm(pcm_bytes)

    def transcribe_pcm_sync(self, pcm_bytes: bytes) -> List[Dict[str, Any]]:
        return asyncio.run(self.transcribe_pcm(pcm_bytes))
