# backend/stt/views.py
import os
import asyncio
import subprocess
import tempfile
import logging
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response

from .stt_client import STTClient
from api.interview_utils import get_cached_graph

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
            subprocess.run(
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

        if not pcm_bytes:
            return JsonResponse({"error": "Empty PCM data"}, status=500)

        # 4) WhisperLiveKit STT 실행 (async → sync)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            lines = loop.run_until_complete(stt_client.transcribe_pcm(pcm_bytes))
        finally:
            loop.close()

        # 5) langgraph 연동: STT 텍스트를 latest_user_text로 전달
        user_question = None
        answer_class = None
        intro_text = None
        text = " ".join((ln.get("text") or "").strip() for ln in (lines or []) if isinstance(ln, dict)).strip()
        if text:
            update_state = {
                "event_type": "strategy_submit",  # answer_classify_agent 경로
                "stt_text": text,
                "await_human": False,
            }
            try:
                graph = get_cached_graph()
                result_state = graph.invoke(update_state)
                if isinstance(result_state, dict):
                    intro_text = result_state.get("tts_text") 
                    user_question = result_state.get("user_question")
                    answer_class = result_state.get("answer_class")
                    
                    
            except Exception as exc:  # noqa: BLE001
                return JsonResponse({"error": f"{str(exc)} 오류 발생"}, status=500)

        return JsonResponse(
            {
                "answer_class":answer_class,
                "tts_text": intro_text,
                "user_question":user_question
            },
            status=200,
        )
    finally:
        # 임시 파일 정리
        for path in (pcm_path, webm_path):
            try:
                if path and os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass
