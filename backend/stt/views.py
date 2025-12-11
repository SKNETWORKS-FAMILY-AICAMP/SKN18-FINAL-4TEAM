# backend/stt/views.py
import os
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache

from api.stt_buffer import append_conversation_event
from .stt_client import STTClient

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

        # STT 텍스트를 공용 대화 버퍼에 기록 (가능한 경우)
        session_id = request.GET.get("session_id") or request.headers.get("X-Session-Id")
        if session_id and text:
            meta_key = f"livecoding:{session_id}:meta"
            meta = cache.get(meta_key) or {}
            stage = (meta.get("stage") or "").strip() or None
            append_conversation_event(
                session_id,
                role="user",
                channel="stt",
                text=text,
                stage=stage,
                meta={"source": "stt.transcribe_only"},
            )

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
