# backend/stt/views.py
import os
import asyncio
import subprocess
import tempfile
import logging
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .stt_client import STTClient
from api.interview_utils import get_cached_graph
from tts_client import generate_interview_audio_batch

logger = logging.getLogger(__name__)

# 한 번만 만들어서 재사용 (매 요청마다 로딩하지 않도록)
stt_client = STTClient(model_size="base")


@csrf_exempt
def run_stt(request):
    """
    POST /api/stt/run/
    body: 브라우저에서 보낸 audio/webm 바이트
    → ffmpeg 로 16kHz mono s16le PCM 으로 변환
    → WhisperLiveKit STT 실행
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    webm_bytes = request.body
    if not webm_bytes:
        return JsonResponse({"error": "No audio data"}, status=400)
    logger.info("webm len=%s", len(webm_bytes))

    # 1) webm 임시 파일로 저장
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
        f.write(webm_bytes)
        webm_path = f.name

    pcm_path = webm_path + ".s16le"

    try:
        # 2) ffmpeg 로 16kHz mono s16le PCM 으로 변환
        cmd = [
            "ffmpeg",
            "-y",           # 덮어쓰기 허용
            "-i", webm_path,
            "-ac", "1",     # mono
            "-ar", "16000", # 16kHz
            "-f", "s16le",  # signed 16-bit little endian (raw PCM)
            pcm_path,
        ]
        try:
            proc = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as e:
            logger.error("ffmpeg 변환 실패: %s", e.stderr.decode("utf-8", "ignore"))
            return JsonResponse(
                {"error": "ffmpeg convert failed", "detail": "see server log"},
                status=500,
            )

        # 3) 변환된 PCM 바이트 읽기
        with open(pcm_path, "rb") as f:
            pcm_bytes = f.read()
        logger.info("pcm len=%s", len(pcm_bytes))

        if not pcm_bytes:
            return JsonResponse({"error": "Empty PCM data"}, status=500)

        # 4) WhisperLiveKit STT 실행 (async → sync)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            lines = loop.run_until_complete(stt_client.transcribe_pcm(pcm_bytes))
        finally:
            loop.close()
        logger.info("stt lines=%s", lines)

        # 5) langgraph 호출: 세션 상태를 thread_id로 이어서 사용
        # Django HttpRequest에는 query_params가 없으므로 GET/헤더에서만 조회
        session_id = (
            request.GET.get("session_id")
            or request.headers.get("X-Session-Id")
        )

        # 답변하기 버튼 → 항상 strategy_submit 이벤트로 처리
        graph = get_cached_graph()

        # 현재 세션 stage에 따라 event_type 자동 결정 (기본: strategy_submit)
        stage = ""
        try:
            state_snapshot = graph.get_state(
                config={
                    "configurable": {
                        "thread_id": session_id
                    }
                }
            )
            values = state_snapshot
            if hasattr(state_snapshot, "values"):
                values = getattr(state_snapshot, "values", {})
            if isinstance(values, dict):
                stage = (
                    ((values.get("meta") or {}).get("stage") or "")
                    .strip()
                    .lower()
                )
        except Exception:
            stage = ""

        # stage 기반으로 event_type 매핑
        event_type = "strategy_submit"
        if stage == "coding":
            event_type = "code_init"
        elif stage == "intro":
            event_type = "strategy_submit"

        text = " ".join(
            (ln.get("text") or "").strip()
            for ln in (lines or [])
            if isinstance(ln, dict)
        ).strip()

        if not session_id:
            return JsonResponse(
                {"error": "session_id is required (query param or X-Session-Id)"},
                status=400,
            )

        if not text:
            # 음성이 없더라도 흐름이 끊기지 않도록 200으로 반환
            return JsonResponse(
                {"error": "Empty STT text", "lines": lines},
                status=200,
            )

        update_state = {
            "event_type": event_type,
            "stt_text": text,
            "await_human": False,
        }

        try:
            result_state = graph.invoke(
                update_state,
                config={
                    "configurable": {
                        "thread_id": session_id
                    }
                },
            )
        except Exception as exc:  # noqa: BLE001
            return JsonResponse(
                {"error": "langgraph invoke failed", "detail": str(exc)},
                status=500,
            )

        # 응답에 필요한 필드만 노출
        response_payload = {
            "lines": lines,
            "stt_text": text,
            "tts_text": "",
            "tts_audio": [],
            "await_human": False,
            "user_question": None,
            "problem_answer":None,
            "user_answer_class": None,
            "stage": stage,
            "intro_flow_done":(values.get("meta") or {}).get("intro_flow_done")
        }

        if isinstance(result_state, dict):
            
            meta = result_state.get("meta") or {}
            response_payload["stage"] = meta.get("stage") or stage
            response_payload["intro_flow_done"] = meta.get("intro_flow_done")
    
            tts_text_val = result_state.get("tts_text") or ""
            response_payload["tts_text"] = tts_text_val
            response_payload["event_type"] = result_state.get("event_type")
            response_payload["await_human"] = bool(result_state.get("await_human"))
            intro = result_state.get("intro") or {}
            response_payload["user_question"] = (
                intro.get("user_question") or result_state.get("user_question")
            )
            response_payload["user_answer_class"] = intro.get("user_answer_class") or result_state.get("answer_class")
            response_payload["problem_answer"]= intro.get("problem_answer")
            # 텍스트 응답이 있으면 서버에서 바로 TTS 생성해 전달
            if isinstance(tts_text_val, str) and tts_text_val.strip():
                try:
                    tts_res = generate_interview_audio_batch(tts_text_val)
                    audio_chunks = tts_res.get("audio_chunks") or []
                    response_payload["tts_audio"] = audio_chunks
                except Exception:
                    # TTS 실패 시에도 나머지 응답은 전달
                    pass

        return JsonResponse(response_payload, status=200)

    finally:
        # 6) 임시 파일 정리
        for p in (webm_path, pcm_path):
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
