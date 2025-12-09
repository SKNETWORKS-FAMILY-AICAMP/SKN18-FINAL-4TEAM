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
def transcribe_only(request):
    """
    POST /api/stt/transcribe/
    body: 브라우저에서 보낸 audio/webm 바이트
    → OpenAI Whisper STT만 수행하고 바로 텍스트/segments를 반환합니다.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    webm_bytes = request.body
    if not webm_bytes:
        return JsonResponse({"error": "No audio data"}, status=400)
    logger.info("webm(len)=%s", len(webm_bytes))

    max_bytes = int(os.getenv("STT_MAX_WEBM_BYTES", "2000000"))  # 약 2MB
    if len(webm_bytes) > max_bytes > 0:
        webm_bytes = webm_bytes[-max_bytes:]
        logger.info("trimmed webm to %s bytes", len(webm_bytes))

    try:
        lines = stt_client.transcribe_pcm_sync(webm_bytes)
        logger.info("stt lines=%s", lines)
        text = " ".join(
            (ln.get("text") or "").strip()
            for ln in (lines or [])
            if isinstance(ln, dict)
        ).strip()
        return JsonResponse(
            {
                "lines": lines,
                "stt_text": text,
            },
            status=200,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("STT transcribe_only failed: %s", exc)
        return JsonResponse(
            {"error": "stt_failed", "detail": str(exc)},
            status=500,
        )


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

    # 너무 긴 녹음은 STT 지연을 줄이기 위해 최대 바이트를 잘라냅니다.
    # 대략 수~십 초 수준으로 제한 (환경변수로 조정 가능).
    max_bytes = int(os.getenv("STT_MAX_WEBM_BYTES", "2000000"))  # 약 2MB
    if len(webm_bytes) > max_bytes > 0:
        # 최근 구간이 더 중요하다고 보고, 마지막 max_bytes만 사용
        webm_bytes = webm_bytes[-max_bytes:]
        logger.info("trimmed webm to %s bytes", len(webm_bytes))

    try:
        # 1) OpenAI Whisper STT 실행
        # STTClient는 webm 바이트를 그대로 받아 내부에서 tempfile(.webm)로 저장 후
        # OpenAI API에 전달합니다.
        lines = stt_client.transcribe_pcm_sync(webm_bytes)
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

        # fast=1 이면 STT 결과까지만 반환 (LangGraph/TTS는 생략)
        fast_mode = request.GET.get("fast") == "1"
        if fast_mode:
            return JsonResponse(
                {
                    "lines": lines,
                    "stt_text": text,
                    "tts_text": "",
                    "tts_audio": [],
                    "await_human": False,
                    "user_question": None,
                    "problem_answer": None,
                    "user_answer_class": None,
                    "stage": stage,
                    "intro_flow_done": None,
                    "event_type": None,
                },
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
        # 현재는 run_stt에서 생성한 임시 파일이 없으므로 정리할 항목 없음
        pass
