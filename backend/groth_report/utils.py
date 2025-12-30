import json
from django.db import transaction
from django.db.models import Max
from django.utils.timezone import now
from api.models import UserGrowthInsight
from django.db.utils import ProgrammingError


def append_growth_state(user_id: str, new_state: dict):
    """
    누적 성장 리포트 append-only 저장
    (user_id 기준 version 증가)
    new_state에는 strengths/weaknesses/improvements/changes/report_ids 포함
    extra_fields로 추가 저장할 필드를 덮어쓸 수 있음.
    """
    report_content = new_state.get("report_content")
    if report_content is None:
        try:
            report_content = json.dumps(new_state, ensure_ascii=False)
        except Exception:
            report_content = str(new_state)

    report_ids = new_state.get("report_ids") or []
    if not isinstance(report_ids, list):
        report_ids = [report_ids]

    try:
        with transaction.atomic():
            last_version = (
                UserGrowthInsight.objects
                .select_for_update()
                .filter(user_id=user_id)
                .aggregate(v=Max("version"))
                .get("v")
            )
            next_version = (last_version or 0) + 1

            base = {
                "user_id": user_id,
                "version": next_version,
                "window_size": new_state.get("window_size") or len(report_ids) or 3,
                "report_ids": report_ids,
                "report_content": report_content,
                "created_at": now(),
            }

            obj = UserGrowthInsight.objects.create(
                **base
            )
            return obj
    except ProgrammingError as e:
        # 테이블이 없을 때는 호출자 레벨에서 처리하도록 예외 전달
        print(f"[append_growth_state] table missing: {e}", flush=True)
        raise
