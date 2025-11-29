from django.http import JsonResponse


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
