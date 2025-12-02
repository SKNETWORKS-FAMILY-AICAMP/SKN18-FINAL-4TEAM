"""
stt_client.py

WhisperLiveKit를 직접 Python 코드에서 호출해서
- PCM 음성 바이트를 넣으면
- 마지막 FrontData 기준의 `lines` (list[Line]) 까지만 만들어서
  그대로 반환해 주는 간단 래퍼 + (선택) 가벼운 NLP 보정.
"""

import asyncio
import os
from typing import Any, Dict, List, Optional

from whisperlivekit import AudioProcessor, TranscriptionEngine  # basic_server와 동일한 import

#from openai import OpenAI  # 매우 약한 의미 보정에 사용 (선택)


class STTClient:
    """
    WhisperLiveKit 기반 STT 클라이언트.

    - 최초 호출 시 TranscriptionEngine을 한 번만 띄워서 재사용
    - audio_bytes(PCM)를 넣으면 마지막 FrontData.lines 를 그대로 돌려줌
    - (옵션) 각 line["text"]에 대해 약한 의미 보정(NLP) 수행
    """

    def __init__(
        self,
        *,
        model_size: str = "base",
        language: str = "auto",
        backend: str = "auto",
        device: Optional[str] = None,
        enable_diarization: bool = False,
        enable_translation: bool = False,
        enable_repair: bool = False,    # ✅ NLP 보정 켜기/끄기
        **extra_engine_kwargs: Any,
    ) -> None:
        """
        STTClient 초기화.

        필요하면 TranscriptionEngine에 넘길 옵션들을 여기서 조정하면 됨.
        """
        self.enable_repair = enable_repair

        # TranscriptionEngine 에 넘길 옵션 모음 (core.py 참고, 일부만 사용)
        self._engine_kwargs: Dict[str, Any] = {
            "backend": backend,
            "model_size": model_size,
            "lan": language,
            "direct_english_translation": False,
            "pcm_input": True,          # ✅ 우리는 PCM 바이트를 직접 넣을 것이므로 항상 True
            "transcription": True,
            "diarization": enable_diarization,
        }

        if enable_translation:
            self._engine_kwargs["translation"] = True

        self._engine_kwargs.update(extra_engine_kwargs)

        self._engine: Optional[TranscriptionEngine] = None
        self._lock = asyncio.Lock()

        # NLP 보정을 쓸 경우에만 OpenAI 클라이언트 준비
        

    async def _get_engine(self) -> TranscriptionEngine:
        """
        TranscriptionEngine을 lazy init 해서 재사용.
        """
        async with self._lock:
            if self._engine is None:
                self._engine = TranscriptionEngine(**self._engine_kwargs)
            return self._engine

    # -------------------------
    #  NLP 보정 관련 내부 함수들
    # -------------------------

    

    def _repair_lines(self, lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return lines

    # -------------------------
    #  STT 메인 로직
    # -------------------------

    async def _run_once_pcm(self, pcm_bytes: bytes) -> List[Dict[str, Any]]:
        """
        한 번의 STT 세션:
        - AudioProcessor 생성
        - create_tasks()로 내부 작업(task) 시작
        - pcm_bytes를 chunk 단위로 process_audio()로 흘려보냄
        - 마지막에 빈 바이트를 보내 stop
        - 동시에 results_formatter() (create_tasks의 반환값)을 소비하면서
          가장 마지막 FrontData의 lines 를 기억했다가 반환
        """
        engine = await self._get_engine()
        audio_processor = AudioProcessor(transcription_engine=engine)

        results_generator = await audio_processor.create_tasks()

        bytes_per_sec = getattr(audio_processor, "bytes_per_sec", 32000)
        chunk_size = max(bytes_per_sec // 4, 1)  # 대략 0.25초 단위

        last_lines: List[Dict[str, Any]] = []

        async def _feed_audio() -> None:
            for i in range(0, len(pcm_bytes), chunk_size):
                chunk = pcm_bytes[i : i + chunk_size]
                await audio_processor.process_audio(chunk)
            # 빈 바이트를 보내서 "이제 끝났다" 신호 보내기
            await audio_processor.process_audio(b"")

        async def _consume_results() -> None:
            nonlocal last_lines
            async for front_data in results_generator:
                data = front_data.to_dict()
                if "lines" in data:
                    last_lines = data["lines"]

        try:
            await asyncio.gather(_feed_audio(), _consume_results())
        finally:
            await audio_processor.cleanup()

        # 🔧 여기에서 NLP 보정 한 번 태운다
        
        return last_lines

    async def transcribe_pcm(self, pcm_bytes: bytes) -> List[Dict[str, Any]]:
        """
        16kHz mono s16le PCM 바이트를 입력하면
        WhisperLiveKit가 구성한 마지막 FrontData 기준의
        list[Line] (dict 형태) 를 그대로 반환한다.
        (옵션) text는 약한 의미 보정을 거친 최종 버전일 수 있다.
        """
        return await self._run_once_pcm(pcm_bytes)

    def transcribe_pcm_sync(self, pcm_bytes: bytes) -> List[Dict[str, Any]]:
        return asyncio.run(self.transcribe_pcm(pcm_bytes))
