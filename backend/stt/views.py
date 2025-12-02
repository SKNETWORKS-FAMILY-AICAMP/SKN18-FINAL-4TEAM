from django.shortcuts import render

# Create your views here.
# backend/stt/views.py
import asyncio
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .stt_client import STTClient


@csrf_exempt
def run_stt(request):
    """
    POST /api/stt/run/
    body: raw PCM bytes (녹음한 bytes 그대로)
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    pcm_bytes = request.body
    if not pcm_bytes:
        return JsonResponse({"error": "No audio data"}, status=400)

    client = STTClient(model_size="base")

    # asyncio.run() 은 Django에서 직접 못쓰니 loop 생성
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    lines = loop.run_until_complete(client.transcribe_pcm(pcm_bytes))

    return JsonResponse({"lines": lines}, status=200)
