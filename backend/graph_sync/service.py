from typing import Any, Dict, List


def _resolve_problem_algorithms(graph_output: Dict[str, Any]) -> List[str]:
    algos = graph_output.get("problem_algorithms") or []
    if isinstance(algos, str):
        algos = [a.strip() for a in algos.split(",") if a.strip()]
    if algos:
        return [str(a) for a in algos if a]

    problem_id = graph_output.get("problem_id")
    if not problem_id:
        return []

    try:
        from api.models import CodingProblem

        problem = CodingProblem.objects.filter(problem_id=problem_id).first()
        if not problem:
            return []
        algo_value = problem.algorithm
        if isinstance(algo_value, str):
            try:
                import json

                parsed = json.loads(algo_value)
                if isinstance(parsed, list):
                    algo_value = parsed
                else:
                    algo_value = [algo_value]
            except Exception:
                algo_value = [algo_value]
        if isinstance(algo_value, list):
            return [str(a) for a in algo_value if a]
    except Exception:
        return []
    return []


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

    problem_algorithms = _resolve_problem_algorithms(graph_output)
    problem_id = graph_output.get("problem_id")
    if not problem_id and isinstance(getattr(report, "problem", None), dict):
        problem_id = report.problem.get("problem_id")
    if problem_id is not None:
        try:
            problem_id = int(problem_id)
        except (TypeError, ValueError):
            problem_id = None
    sync_report(
        user_id=str(user.user_id),
        session_id=str(report.session_id),
        created_at=report.created_at or report.updated_at,
        problem_algorithms=problem_algorithms,
        strategy_algorithms=graph_output.get("strategy_algorithms") or [],
        consistency_status=consistency_status,
        problem_id=problem_id,
        solved_score=report.final_score,
    )
