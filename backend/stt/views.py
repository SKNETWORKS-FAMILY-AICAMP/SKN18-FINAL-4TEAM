# backend/stt/views.py
import os
import asyncio
import subprocess
import tempfile
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .stt_client import STTClient

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

        if not pcm_bytes:
            return JsonResponse({"error": "Empty PCM data"}, status=500)

        # 4) WhisperLiveKit STT 실행 (async → sync)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            lines = loop.run_until_complete(stt_client.transcribe_pcm(pcm_bytes))
        finally:
            loop.close()

        return JsonResponse({"lines": lines}, status=200)

    finally:
        # 5) 임시 파일 정리
        for p in (webm_path, pcm_path):
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
