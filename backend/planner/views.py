from datetime import date, timedelta
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
#from .deep_recommandation.graph import agent_app
from .models import StudyPlan, DailyTask
from api.models import UserGrowthInsight

class GeneratePlanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user
            if not user or not user.is_authenticated:
                return Response({"error": "로그인이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                duration = int(request.data.get("duration", 7))
            except (TypeError, ValueError):
                return Response({"error": "duration은 숫자여야 합니다."}, status=status.HTTP_400_BAD_REQUEST)

            user_id = getattr(user, "user_id", None) or getattr(user, "id", None) or str(user)
            latest_growth = (
                UserGrowthInsight.objects.filter(user_id=user_id)
                .order_by("-version")
                .first()
            )
            if not latest_growth:
                return Response(
                    {
                        "detail": "라이브 코딩 테스트를 최소 3회 완료해야 학습 계획을 생성할 수 있습니다.",
                        "code": "need_min_livecoding",
                        "redirect_to": "home",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            growth_content = latest_growth.report_content or ""

            # 1. planner langgraph 실행
            inputs = {
                "growth_report_content": growth_content,
                "duration": duration,
            }
            result = agent_app.invoke(inputs)
            
            # 최종 결과 가져오기 (비어있는 날짜는 curriculum 정보로 메꿈)
            final_schedule = result.get("final_schedule", [])
            curriculum = result.get("curriculum", [])

            # 2. DB 저장 및 응답 데이터 생성
            start_date = date.today()
            calendar_events = []

            with transaction.atomic():
                plan_topic = "라이브코딩 성장 리포트 기반 커리큘럼"
                plan = StudyPlan.objects.create(user=user, topic=plan_topic, duration=duration)
                
                # tasks_to_create 리스트 삭제 (반복문 안에서 바로 저장하기 위해)

                for i in range(duration):
                    day_num = i + 1

                    # 결과가 있으면 쓰고, 없으면(최종 실패) Fallback 링크 생성
                    item = final_schedule[i] if i < len(final_schedule) and final_schedule[i] else None

                    if item:
                        topic = item["topic"]
                        url = item["video_url"]
                        title = item["video_title"]
                    else:
                        # Fallback Logic
                        topic = curriculum[i]["topic"]
                        title = f"'{topic}' 검색 결과 보기 (영상 못 찾음)"
                        url = f"https://www.youtube.com/results?search_query={topic}"

                    actual_date = start_date + timedelta(days=i)

                    # [수정] 객체를 만들고 바로 save() 해야 task.id가 생성됨
                    task = DailyTask(
                        plan=plan,
                        day=day_num,
                        topic=topic,
                        video_title=title,
                        video_url=url,
                        is_completed=False
                    )
                    task.save() # DB 저장 및 ID 생성

                    calendar_events.append(
                        {
                            "title": topic,
                            "start": actual_date.strftime("%Y-%m-%d"),
                            "url": url,
                            "extendedProps": {
                                "day_number": day_num,
                                "task_id": task.id, # [중요] 프론트엔드 체크박스 기능용 ID
                                "is_completed": False,
                                "reflection_difficulty": None,
                                "lecture_note": ""
                            },
                            "backgroundColor": '#e7f5ff',
                            "borderColor": '#42b883'
                        }
                    )

            # bulk_create 삭제됨 (위에서 이미 저장함)

            return Response({"message": "OK", "events": calendar_events}, status=201)
            
        except Exception as exc:  # noqa: BLE001
            print(f"[GeneratePlanView] error: {exc}", flush=True)
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LatestStudyPlanView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return Response({"error": "로그인이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)

        plan = (
            StudyPlan.objects.filter(user=user)
            .order_by("-created_at", "-id")
            .first()
        )
        if not plan:
            return Response({"error": "저장된 커리큘럼이 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        tasks = DailyTask.objects.filter(plan=plan).order_by("day")
        base_date = timezone.localdate(plan.created_at) if plan.created_at else date.today()

        events = []
        for task in tasks:
            actual_date = base_date + timedelta(days=task.day - 1)
            events.append(
                {
                    "title": task.topic,
                    "start": actual_date.strftime("%Y-%m-%d"),
                    "url": task.video_url,
                    "extendedProps": {
                        "day_number": task.day,
                        "task_id": task.id,
                        "is_completed": task.is_completed,
                        "reflection_difficulty": task.reflection_difficulty,
                        "lecture_note": task.lecture_note,
                    },
                }
            )

        return Response(
            {
                "plan": {
                    "id": plan.id,
                    "topic": plan.topic,
                    "duration": plan.duration,
                    "created_at": plan.created_at.isoformat() if plan.created_at else None,
                },
                "events": events,
            },
            status=status.HTTP_200_OK,
        )


class StudyTaskCompletionView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return Response({"error": "로그인이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)

        task_id = request.data.get("task_id")
        is_completed = request.data.get("is_completed")

        if task_id is None or is_completed is None:
            return Response({"error": "task_id와 is_completed는 필수입니다."}, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(is_completed, str):
            is_completed = is_completed.strip().lower() in ("true", "1", "yes", "y", "t")
        elif not isinstance(is_completed, bool):
            return Response({"error": "is_completed는 boolean이어야 합니다."}, status=status.HTTP_400_BAD_REQUEST)

        task = DailyTask.objects.filter(id=task_id, plan__user=user).first()
        if not task:
            return Response({"error": "작업을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        task.is_completed = is_completed
        task.save(update_fields=["is_completed"])

        return Response(
            {"task_id": task.id, "is_completed": task.is_completed},
            status=status.HTTP_200_OK,
        )


class StudyTaskReflectionView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return Response({"error": "로그인이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)

        task_id = request.data.get("task_id")
        difficulty = request.data.get("difficulty")
        lecture_note = request.data.get("lecture_note", "")

        if task_id is None:
            return Response({"error": "task_id는 필수입니다."}, status=status.HTTP_400_BAD_REQUEST)

        if difficulty is None:
            return Response({"error": "difficulty는 필수입니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            difficulty = int(difficulty)
        except (TypeError, ValueError):
            return Response({"error": "difficulty는 숫자여야 합니다."}, status=status.HTTP_400_BAD_REQUEST)

        if difficulty < 1 or difficulty > 5:
            return Response({"error": "difficulty는 1~5 사이여야 합니다."}, status=status.HTTP_400_BAD_REQUEST)

        lecture_note = (lecture_note or "").strip()
        if len(lecture_note) > 200:
            return Response({"error": "lecture_note는 200자 이하여야 합니다."}, status=status.HTTP_400_BAD_REQUEST)

        task = DailyTask.objects.filter(id=task_id, plan__user=user).first()
        if not task:
            return Response({"error": "작업을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        task.reflection_difficulty = difficulty
        task.lecture_note = lecture_note
        task.is_completed = True
        task.save(update_fields=["reflection_difficulty", "lecture_note", "is_completed"])

        return Response(
            {
                "task_id": task.id,
                "difficulty": task.reflection_difficulty,
                "lecture_note": task.lecture_note,
                "is_completed": task.is_completed,
            },
            status=status.HTTP_200_OK,
        )
