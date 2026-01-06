import math
from collections import defaultdict
from datetime import datetime
from typing import Optional

from django.utils import timezone

from .neo4j_client import post_cypher


def _cosine(a: dict, b: dict) -> float:
    if not a or not b:
        return 0.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for key, val in a.items():
        na += val * val
        if key in b:
            dot += val * b[key]
    for val in b.values():
        nb += val * val
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / math.sqrt(na * nb)


def _recency_weight(ts: Optional[datetime]) -> float:
    if not ts:
        return 1.0
    now = timezone.now()
    if timezone.is_naive(ts):
        ts = timezone.make_aware(ts, timezone.get_current_timezone())
    days = max(0.0, (now - ts).days)
    return math.exp(-days / 30.0)


def _user_reports():
    from api.models import LivecodingReport

    return LivecodingReport.objects.values(
        "user_id",
        "final_score",
        "graph_output",
        "created_at",
    )


def build_user_profiles():
    profiles = defaultdict(lambda: defaultdict(float))
    stats = {}
    score_series = defaultdict(list)
    last_report_at = {}

    for row in _user_reports().iterator(chunk_size=500):
        user_id = str(row.get("user_id"))
        created_at = row.get("created_at")
        graph_output = row.get("graph_output") or {}

        algos = graph_output.get("problem_algorithms") or graph_output.get("strategy_algorithms") or []
        if isinstance(algos, str):
            algos = [a.strip() for a in algos.split(",") if a.strip()]
        weight = _recency_weight(created_at)
        for algo in algos:
            profiles[user_id][str(algo)] += weight

        score = row.get("final_score")
        if score is not None:
            score_series[user_id].append((created_at, float(score)))
        if created_at:
            last_report_at[user_id] = max(last_report_at.get(user_id, created_at), created_at)

    for user_id, series in score_series.items():
        series.sort(key=lambda x: x[0] or timezone.now())
        count = len(series)
        first_score = series[0][1] if count else 0.0
        last_score = series[-1][1] if count else 0.0
        slope = (last_score - first_score) / max(1, count - 1)
        variance = 0.0
        if count > 1:
            mean = sum(s for _, s in series) / count
            variance = sum((s - mean) ** 2 for _, s in series) / (count - 1)
        activity_score = math.log1p(count) * _recency_weight(last_report_at.get(user_id))
        growth_score = slope
        activity_level = "light"
        if count >= 5:
            activity_level = "heavy_growth" if slope > 0.0 else "heavy_rand"

        stats[user_id] = {
            "report_count": count,
            "growth_score": growth_score,
            "variance": variance,
            "activity_score": activity_score,
            "activity_level": activity_level,
            "last_report_at": last_report_at.get(user_id),
        }
    return profiles, stats


def update_user_similarity(user_id: str, top_k: int = 20):
    profiles, stats = build_user_profiles()
    _update_similarity_for_user(user_id, profiles, stats, top_k)


def _update_similarity_for_user(user_id: str, profiles: dict, stats: dict, top_k: int):
    target_profile = profiles.get(user_id) or {}
    if not target_profile:
        return

    rows = []
    for other_id, profile in profiles.items():
        if other_id == user_id:
            continue
        cos = _cosine(target_profile, profile)
        if cos <= 0:
            continue
        overlap = len(set(target_profile.keys()) & set(profile.keys()))
        activity_weight = math.sqrt(
            max(stats.get(user_id, {}).get("activity_score", 1.0), 0.0)
            * max(stats.get(other_id, {}).get("activity_score", 1.0), 0.0)
        )
        score = cos * (1.0 + activity_weight)
        rows.append(
            {
                "other_id": other_id,
                "score": float(score),
                "overlap": overlap,
                "activity_weight": float(activity_weight),
            }
        )

    rows.sort(key=lambda x: x["score"], reverse=True)
    rows = rows[:top_k]
    now_iso = timezone.now().isoformat()

    query = (
        "MERGE (u:User {user_id:$user_id}) "
        "SET u.report_count = $report_count, "
        "u.growth_score = $growth_score, "
        "u.activity_score = $activity_score, "
        "u.activity_level = $activity_level, "
        "u.last_report_at = $last_report_at "
        "WITH u "
        "OPTIONAL MATCH (u)-[r:SIMILAR]->(:User) DELETE r "
        "WITH u "
        "UNWIND $rows AS row "
        "MATCH (v:User {user_id: row.other_id}) "
        "MERGE (u)-[s:SIMILAR]->(v) "
        "SET s.score = row.score, s.overlap = row.overlap, s.activity_weight = row.activity_weight, s.ts = $ts"
    )
    stat = stats.get(user_id) or {}
    params = {
        "user_id": user_id,
        "rows": rows,
        "ts": now_iso,
        "report_count": stat.get("report_count", 0),
        "growth_score": stat.get("growth_score", 0.0),
        "activity_score": stat.get("activity_score", 0.0),
        "activity_level": stat.get("activity_level", "light"),
        "last_report_at": stat.get("last_report_at").isoformat() if stat.get("last_report_at") else None,
    }
    post_cypher(query, params)


def update_all_user_similarity(top_k: int = 20):
    profiles, stats = build_user_profiles()
    for user_id in profiles.keys():
        _update_similarity_for_user(user_id, profiles, stats, top_k)
