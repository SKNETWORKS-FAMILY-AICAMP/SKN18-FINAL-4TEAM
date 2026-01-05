from typing import Any, Dict, List


def ensure_graph_sources():
    from .neo4j_sync import ensure_schema, ensure_problem_graph
    from .es_sync import ensure_problem_documents

    ensure_schema()
    ensure_problem_graph()
    try:
        ensure_problem_documents()
    except Exception as exc:
        print(f"[graph_sync] ES bootstrap failed: {exc}", flush=True)


def sync_report_to_graph(report, user, graph_output: Dict[str, Any]) -> None:
    from .neo4j_sync import sync_report

    consistency_status = ""
    ps_eval = graph_output.get("problem_solving_evaluation") or {}
    if isinstance(ps_eval, dict):
        consistency_status = ps_eval.get("consistency_status") or ""

    sync_report(
        user_id=str(user.user_id),
        session_id=str(report.session_id),
        created_at=report.created_at or report.updated_at,
        problem_algorithms=graph_output.get("problem_algorithms") or [],
        strategy_algorithms=graph_output.get("strategy_algorithms") or [],
        consistency_status=consistency_status,
    )
