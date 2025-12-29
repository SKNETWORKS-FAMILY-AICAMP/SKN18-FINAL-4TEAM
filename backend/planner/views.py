from datetime import date, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db import transaction
from django.contrib.auth import get_user_model
from .agents.graph import agent_app
from .models import StudyPlan, DailyTask

class GeneratePlanView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_weakness = request.data.get('weakness')
        duration = int(request.data.get('duration', 7))

        # 임시 유저 처리
        User = get_user_model()
        user = request.user if request.user.is_authenticated else User.objects.first()
        if not user:
            return Response({"error": "superuser를 먼저 생성해주세요."}, status=500)

        # 1. Agent 실행
        try:
            inputs = {"user_weakness": user_weakness, "duration": duration}
            result = agent_app.invoke(inputs)
            # 최종 결과 가져오기 (비어있는 날짜는 curriculum 정보로 메꿈)
            final_schedule = result.get('final_schedule', [])
            curriculum = result.get('curriculum', [])
        except Exception as e:
            return Response({"error": str(e)}, status=500)

        # 2. DB 저장 및 응답 데이터 생성
        start_date = date.today()
        calendar_events = []
        
        with transaction.atomic():
            plan = StudyPlan.objects.create(user=user, topic=user_weakness, duration=duration)
            tasks_to_create = []

            for i in range(duration):
                day_num = i + 1
                
                # 결과가 있으면 쓰고, 없으면(최종 실패) Fallback 링크 생성
                item = final_schedule[i] if i < len(final_schedule) and final_schedule[i] else None
                
                if item:
                    topic = item['topic']
                    url = item['video_url']
                    title = item['video_title']
                else:
                    # Fallback Logic
                    topic = curriculum[i]['topic']
                    title = f"'{topic}' 검색 결과 보기 (영상 못 찾음)"
                    url = f"https://www.youtube.com/results?search_query={topic}"

                actual_date = start_date + timedelta(days=i)

                tasks_to_create.append(DailyTask(
                    plan=plan, day=day_num, topic=topic,
                    video_title=title, video_url=url
                ))

                calendar_events.append({
                    "title": topic,
                    "start": actual_date.strftime("%Y-%m-%d"),
                    "url": url,
                    "extendedProps": {"day_number": day_num}
                })

            DailyTask.objects.bulk_create(tasks_to_create)

        return Response({"message": "OK", "events": calendar_events}, status=201)