from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User, LivecodingReport
from rest_framework.permissions import IsAuthenticated
from .authentication import JWTAuthentication
from .models import UserGrowthInsight
from django.db.utils import ProgrammingError
from groth_report.graph import run_growth_report
from groth_report.utils import append_growth_state


class UserReportsPayloadView(APIView):
    """
    로그인 사용자의 모든 리포트를 DB에서 조회해 에이전트 입력용 JSON으로 반환.
    GET /api/livecoding/reports/payload/
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = getattr(request, "user", None)
        if not isinstance(user, User):
            return Response({"detail": "로그인이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            reports = (
                LivecodingReport.objects.filter(user=user)
                .order_by("-id")
            )
            report_count = reports.count()
        except ProgrammingError as e:
            return Response(
                {
                    "detail": "livecoding_reports 테이블 조회 중 오류가 발생했습니다. 마이그레이션을 확인해주세요.",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
            
        try:
            latest_growth = (
                UserGrowthInsight.objects.filter(user_id=user)
                .order_by("-version")
                .first()
            )
            has_previous_growth = True if latest_growth else False
        except ProgrammingError as e:
            return Response(
                {
                    "detail": "user_growth_insight 테이블 조회 중 오류가 발생했습니다. 마이그레이션을 확인해주세요.",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
                
        # 1. 리포트가 3개 미만이면 바로 차단 응답
        if report_count < 3:
            return Response(
                {
                    "report_count": report_count,
                    "run_mode": "blocked",
                },
                status=status.HTTP_200_OK,
            )
        
        # 2. UserGrowthInsight 의 report_ids 와 LivecodingReport 에 저장된 report_ids 차이 보기
        report_ids = []
        payload = []
        for r in reports:
                report_ids.append(r.session_id)
                payload.append(
                    {
                        "session_id": r.session_id,
                        "report_md": r.report_md or "",
                    }
                )
        if not has_previous_growth: # 처음 성장 리포트 실행
            return Response(
            {
                "run_mode": "initial",
                "user_id": getattr(user, "user_id", None) or getattr(user, "id", None) or str(user),
                "reports": payload,
                "report_ids": report_ids,
            },
            status=status.HTTP_200_OK,
        )
        else: # 성장 리포트 갱신
            insight_ids = latest_growth.report_ids
            pending = [r for r in report_ids if r not in insight_ids]
            prev_agent_result = latest_growth.report_content
            if not pending:
                run_mode = "cached"
                return Response(
                {
                    "user_id": getattr(user, "user_id", None) or getattr(user, "id", None) or str(user),
                    "report_ids":report_ids,
                    "run_mode": run_mode,
                    "prev_agent_result": prev_agent_result,

                },
                status=status.HTTP_200_OK,)
                
            else:
                latest_by_id = reports.first()
                selected_report = [
                        {"session_id": latest_by_id.session_id, "report_md": latest_by_id.report_md or ""}
                ]

                return Response(
                    {
                        "user_id": getattr(user, "user_id", None) or getattr(user, "id", None) or str(user),
                        "run_mode": "incremental",
                        "report_ids":report_ids,
                        "selected_report": selected_report,
                        "prev_agent_result": prev_agent_result,
                    },
                    status=status.HTTP_200_OK,
                )

class DeepAgentReportView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = getattr(request, "user", None)
        if not isinstance(user, User):
            return Response({"detail": "로그인이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)

        # UserReportsPayloadView에서 결정한 실행 입력 사용 (없으면 서버가 재계산)
        selected_reports = request.data.get("selected_reports") or request.data.get("selected_report") or []
        report_ids = request.data.get("report_ids") or []
        run_mode = request.data.get("run_mode")
        prev_agent_result = request.data.get("prev_agent_result") or ""
        reports = request.data.get("reports") or []
        result_text = ""
        
        if run_mode == "blocked":
            return Response(
                    {"detail": "최소 3개의 리포트가 쌓여야 에이전트를 실행합니다.", "run_mode": run_mode},
                    status=status.HTTP_400_BAD_REQUEST,
            )
        
        elif run_mode == "initial":
            try:
                response = run_growth_report(reports)
                result_text = response.get("final_report") if isinstance(response, dict) else str(response)
                append_growth_state(
                    user_id=str(user),
                    new_state={
                        "report_content": result_text,
                        "report_ids": report_ids or [r.get("session_id") for r in reports if isinstance(r, dict)],
                        "window_size": len(report_ids or reports) or 3,
                    },
                )
            except Exception as e:
                print(f"[DeepAgentReportView] append_growth_state failed: {e}", flush=True)
                return Response({"detail": "에이전트 실행에 실패했습니다.", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif run_mode== "cached":
            try:
                # 캐시 결과 그대로 반환
                result_text = prev_agent_result or ""
            except Exception as e:
                print(f"[DeepAgentReportView] cached branch failed: {e}", flush=True)
                return Response({"detail": "에이전트 실행에 실패했습니다.", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        elif run_mode=="incremental":
            try:
                response = run_growth_report(selected_reports, prev_agent_result)
                result_text = response.get("final_report") if isinstance(response, dict) else str(response)
                append_growth_state(
                    user_id=str(user),
                    new_state={
                        "report_content": result_text,
                        "report_ids": report_ids,
                        "window_size": len(report_ids) or 3,
                    },
                )


            except Exception as e:
                print(f"[DeepAgentReportView] append_growth_state failed: {e}", flush=True)

        return Response(
                {
                    "agent_result": result_text,
                    "run_mode": run_mode,
                },
                status=status.HTTP_200_OK,
        )
