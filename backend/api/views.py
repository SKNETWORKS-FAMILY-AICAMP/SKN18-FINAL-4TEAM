import json
import sys
from pathlib import Path
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from interview_engine.graph import create_graph_flow

# Ensure project root (where stt_client.py lives) is on sys.path
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from backend.tts_client import generate_interview_audio


def health(request):
    return JsonResponse({"status": "ok"})


def roadmap(request):
    data = {
        "phases": [
            {
                "name": "pre_interview",
                "steps": [
                    "문항/자기소개서 기반 분석",
                    "JD 기반 질문 생성",
                    "세션 시작 및 환경 확인",
                ],
            },
            {
                "name": "behavioral_interview",
                "steps": [
                    "상황 질문 4~5개",
                    "STT/TTS, 시선/표정 추적",
                    "평가 리포트 생성",
                ],
            },
            {
                "name": "coding_test",
                "steps": [
                    "문제 1~4 세트",
                    "코드 자동 채점 및 리포트",
                ],
            },
        ]
    }
    return JsonResponse(data)


@csrf_exempt
def start_livecoding(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        payload = {}

    user_name = payload.get("user_name") or "지원자"
    problem_description = payload.get("problem_description") or ""

    initial_state = {
        "user_name": user_name,
        "problem_description": problem_description,
        "event_type": "init",
    }

    graph = create_graph_flow()
    final_state = graph.invoke(initial_state)

    question_text = final_state.get("current_question_text", "")

    # Run TTS after graph execution
    tts_chunks = []
    tts_first_audio_base64 = None
    tts_error = None
    if question_text:
        try:
            for chunk in generate_interview_audio(question_text):
                tts_chunks.append(chunk)
            first_with_audio = next((c for c in tts_chunks if c.get("audio_base64")), None)
            if first_with_audio:
                tts_first_audio_base64 = first_with_audio["audio_base64"]
        except Exception as e:
            tts_error = str(e)

    response = {
        "question_text": question_text,
        "tts_first_audio_base64": tts_first_audio_base64,
        "tts_audio_chunks": tts_chunks,
        "await_human": final_state.get("await_human", False),
        "error": final_state.get("problem_intro_error") or tts_error,
    }

    return JsonResponse(response)
