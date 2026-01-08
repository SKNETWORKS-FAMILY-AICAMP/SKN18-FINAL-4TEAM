from datetime import date, timedelta
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .deep_recommend.graph import create_recommend_graph
from .deep_coach.graph import create_evidence_coach_graph
from .models import StudyPlan, DailyTask, RecommendedVideo
from api.models import UserGrowthInsight, UserProfile

# video recommendation graph 호출
class GeneratePlanView(APIView):
    permission_classes = [IsAuthenticated]
    agent_app = create_recommend_graph()

    def post(self, request):
        try:
            user = request.user
            if not user or not user.is_authenticated:
                return Response({"error": "로그인이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)

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

            profile = UserProfile.objects.filter(user_id=user_id).first()
            user_profile = {
                "tech_stack": profile.tech_stack if profile else [],
                "desired_role": profile.desired_role if profile else [],
                "detailed_role": profile.detailed_role if profile else [],
            }

            # 1. planner langgraph 실행
            inputs = {
                "user_id": user_id,
                "growth_report": growth_content,
                "user_profile": user_profile,
            }
            result = self.agent_app.invoke(inputs)

            # 최종 결과 가져오기
            final_schedule = result.get("final_plan", []) or []
            duration = 7

            # 2. DB 저장 및 응답 데이터 생성
            start_date = date.today()
            calendar_events = []

            with transaction.atomic():
                plan_topic = "라이브코딩 성장 리포트 기반 커리큘럼"
                plan = StudyPlan.objects.create(user=user, topic=plan_topic, duration=duration)

                for i in range(duration):
                    day_num = i + 1

                    item = final_schedule[i] if i < len(final_schedule) and final_schedule[i] else None

                    topic = (item or {}).get("day_plan_topic") or f"Day {day_num} 학습"
                    video_id = (item or {}).get("video_id")
                    url = (item or {}).get("video_url") or ""
                    why_selected = (item or {}).get("why_selected") or ""
                    is_completed = "미진행"

                    actual_date = start_date + timedelta(days=i)

                    task = DailyTask(
                        plan=plan,
                        day=day_num,
                        topic=topic,
                        video_id=video_id,
                        video_url=url,
                        why_selected=why_selected,
                        is_completed=is_completed,
                    )
                    task.save()  # DB 저장 및 ID 생성

                    calendar_events.append(
                        {
                            "title": topic,
                            "start": actual_date.strftime("%Y-%m-%d"),
                            "url": url,
                            "extendedProps": {
                                "day_number": day_num,
                                "task_id": task.id,
                                "is_completed": is_completed,
                                "why_selected": why_selected,
                                "lecture_note": "",
                            },
                            "backgroundColor": "#e7f5ff",
                            "borderColor": "#42b883",
                        }
                    )

            return Response({"message": "OK", "events": calendar_events}, status=201)

        except Exception as exc:  # noqa: BLE001
            print(f"[GeneratePlanView] error: {exc}", flush=True)
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 기존 plan 불러오기
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
                        "why_selected": task.why_selected,
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

# 사용자 글 입력 
class StudyTaskReflectionView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return Response({"error": "로그인이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)

        task_id = request.data.get("task_id")
        lecture_note = request.data.get("lecture_note", "")

        if task_id is None:
            return Response({"error": "task_id는 필수입니다."}, status=status.HTTP_400_BAD_REQUEST)

        lecture_note = (lecture_note or "").strip()
        if len(lecture_note) < 30:
            return Response({"error": "올바른 내용을 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)

        task = DailyTask.objects.filter(id=task_id, plan__user=user).first()
        if not task:
            return Response({"error": "작업을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        # deep_coach 호출: 사용자 글 + 영상 요약 기반 completion_level/feedback
        video_summary = ""
        if task.video_id:
            rv = RecommendedVideo.objects.filter(id=task.video_id).first()
            video_summary = rv.summary if rv else ""

        coach_input = {
            "user_id": getattr(user, "user_id", None) or getattr(user, "id", None) or str(user),
            "video_id": str(task.video_id) if task.video_id is not None else "",
            "video_summary": video_summary,
            "draft": lecture_note,
        }
        coach_result = {}
        try:
            coach_app = create_evidence_coach_graph()
            coach_result = coach_app.invoke(coach_input)
            print(f"[coach] input={coach_input} output={coach_result}", flush=True)
        except Exception as exc:
            print(f"[StudyTaskReflectionView] coach error: {exc}", flush=True)

        completion_level = coach_result.get("completion_level") or "완료"
        coach_output = coach_result.get("coach_output") or ""

        # completion_level이 COMPLETE이면 사용자가 입력한 lecture_note 그대로 저장,
        # 그 외에는 coach_output이 있으면 coach_output을 저장(없으면 사용자가 입력한 내용을 저장)
        note_to_save = lecture_note if completion_level == "COMPLETE" else coach_output

        task.lecture_note = note_to_save
        task.is_completed = completion_level or "완료"
        task.save(update_fields=["lecture_note", "is_completed"])

        return Response(
            {
                "task_id": task.id,
                "lecture_note": task.lecture_note,
                "is_completed": task.is_completed,
                "coach_output": coach_output,
            },
            status=status.HTTP_200_OK,
        )
