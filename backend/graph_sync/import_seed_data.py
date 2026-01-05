import csv
import json
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import sys
import django
from django.utils import timezone


def _setup_django():
    repo_root = Path(__file__).resolve().parents[2]
    backend_root = repo_root / "backend"
    sys.path.insert(0, str(backend_root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()


def _parse_json(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        return None


def _parse_decimal(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except Exception:
        return None


def _parse_datetime(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text)
    except Exception:
        return None
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone=timezone.get_current_timezone())
    return dt


def _load_livecoding_reports(csv_paths):
    from api.models import LivecodingReport, User, UserProfile

    user_ids = set()
    for csv_path in csv_paths:
        with csv_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                uid = (row.get("user_id") or "").strip()
                if uid:
                    user_ids.add(uid)

    users = []
    for uid in sorted(user_ids):
        users.append(
            User(
                user_id=uid,
                email=f"{uid}@seed.local",
                name=uid,
                phone_number=None,
                password_hash=None,
                birthdate=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        )
        if len(users) >= 500:
            User.objects.bulk_create(users, ignore_conflicts=True, batch_size=500)
            users = []
    if users:
        User.objects.bulk_create(users, ignore_conflicts=True, batch_size=500)

    profiles = []
    for uid in sorted(user_ids):
        profiles.append(
            UserProfile(
                user_id=uid,
            )
        )
        if len(profiles) >= 500:
            UserProfile.objects.bulk_create(profiles, ignore_conflicts=True, batch_size=500)
            profiles = []
    if profiles:
        UserProfile.objects.bulk_create(profiles, ignore_conflicts=True, batch_size=500)

    reports = []
    for csv_path in csv_paths:
        with csv_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                reports.append(
                    LivecodingReport(
                        session_id=row.get("session_id") or "",
                        user_id=row.get("user_id") or "",
                        report_md=row.get("report_md") or "",
                        final_score=_parse_decimal(row.get("final_score")),
                        final_grade=row.get("final_grade") or None,
                        graph_output=_parse_json(row.get("graph_output")) or {},
                        problem_text=row.get("problem_text") or None,
                        code_feedback=row.get("code_feedback") or None,
                        problem_solving_evaluation=_parse_json(row.get("problem_solving_evaluation")) or None,
                        initial_strategy=row.get("initial_strategy") or None,
                        approach_validity=row.get("approach_validity") or None,
                        consistency_status=row.get("consistency_status") or None,
                        consistency_feedback=row.get("consistency_feedback") or None,
                        submitted_code=row.get("submitted_code") or None,
                        annotated_code=row.get("annotated_code") or None,
                        strength=row.get("strength") or None,
                        improvement=row.get("improvement") or None,
                        comprehensive_evaluation=row.get("comprehensive_evaluation") or None,
                        anti_cheat_summary=_parse_json(row.get("anti_cheat_summary")) or None,
                        problem_eval_score=_parse_decimal(row.get("problem_eval_score")),
                        problem_eval_feedback=row.get("problem_eval_feedback") or None,
                        code_collab_score=_parse_decimal(row.get("code_collab_score")),
                        code_collab_feedback=row.get("code_collab_feedback") or None,
                        problem_evidence=_parse_json(row.get("problem_evidence")) or None,
                        code_collab_evidence=_parse_json(row.get("code_collab_evidence")) or None,
                        created_at=_parse_datetime(row.get("created_at")),
                        updated_at=_parse_datetime(row.get("updated_at")),
                    )
                )
                if len(reports) >= 500:
                    LivecodingReport.objects.bulk_create(reports, ignore_conflicts=True, batch_size=500)
                    reports = []
    if reports:
        LivecodingReport.objects.bulk_create(reports, ignore_conflicts=True, batch_size=500)


def main():
    _setup_django()

    csv_dir = Path("docker/csv_files")
    if not csv_dir.exists():
        raise SystemExit(f"csv dir not found: {csv_dir}")
    report_paths = sorted(csv_dir.glob("livecoding_reports_*.csv"))
    if not report_paths:
        raise SystemExit("no livecoding_reports_*.csv found")
    _load_livecoding_reports(report_paths)


if __name__ == "__main__":
    main()
