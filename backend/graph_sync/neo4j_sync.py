import json
from datetime import datetime
from typing import Optional

from django.core.cache import cache

from .neo4j_client import post_cypher


SCHEMA_STATEMENTS = [
    "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE;",
    "CREATE CONSTRAINT problem_id_unique IF NOT EXISTS FOR (p:Problem) REQUIRE p.problem_id IS UNIQUE;",
    "CREATE CONSTRAINT role_name_unique IF NOT EXISTS FOR (r:Role) REQUIRE r.name IS UNIQUE;",
    "CREATE CONSTRAINT algoskill_name_unique IF NOT EXISTS FOR (s:AlgoSkill) REQUIRE s.name IS UNIQUE;",
    "CREATE CONSTRAINT difficulty_level_unique IF NOT EXISTS FOR (d:Difficulty) REQUIRE d.level IS UNIQUE;",
    "CREATE CONSTRAINT evidence_id_unique IF NOT EXISTS FOR (e:Evidence) REQUIRE e.evidence_id IS UNIQUE;",
    "CREATE INDEX user_id_idx IF NOT EXISTS FOR (u:User) ON (u.user_id);",
    "CREATE INDEX problem_id_idx IF NOT EXISTS FOR (p:Problem) ON (p.problem_id);",
    "CREATE INDEX evidence_type_idx IF NOT EXISTS FOR (e:Evidence) ON (e.type);",
]


def ensure_schema():
    cache_key = "graph_sync:neo4j_schema_ready"
    if cache.get(cache_key):
        return
    for stmt in SCHEMA_STATEMENTS:
        post_cypher(stmt)
    _cleanup_user_role_edges()
    _cleanup_role_nodes()
    cache.set(cache_key, True, timeout=None)


def _cleanup_user_role_edges():
    query = "MATCH (:User)-[r:WANTS_ROLE]->(:Role) DELETE r"
    post_cypher(query)


def _cleanup_role_nodes():
    query = "MATCH (:Problem)-[r:IN_ROLE]->(role:Role) DELETE r WITH role OPTIONAL MATCH (role)<-[x]-() WITH role, count(x) AS rels WHERE rels = 0 DETACH DELETE role"
    post_cypher(query)


def _count_nodes(label: str) -> int:
    query = f"MATCH (n:{label}) RETURN count(n) AS cnt"
    data = post_cypher(query)
    rows = data.get("results", [{}])[0].get("data", [])
    if not rows:
        return 0
    row = rows[0].get("row") or []
    return int(row[0]) if row else 0


def ensure_problem_graph():
    cache_key = "graph_sync:neo4j_problem_graph_ready"
    if cache.get(cache_key):
        if _count_nodes("Problem") > 0:
            return
        cache.delete(cache_key)
    if _count_nodes("Problem") > 0:
        cache.set(cache_key, True, timeout=None)
        return

    from api.models import CodingProblem  # local import to avoid app loading issues

    batch = []
    for problem in CodingProblem.objects.all().iterator(chunk_size=500):
        algorithms = problem.algorithm
        if isinstance(algorithms, str):
            try:
                algorithms = json.loads(algorithms)
            except Exception:
                algorithms = []
        if not isinstance(algorithms, list):
            algorithms = []
        batch.append(
            {
                "problem_id": int(problem.problem_id),
                "problem": problem.problem or "",
                "difficulty": problem.difficulty or "",
                "category": problem.category or "",
                "algorithms": [str(a) for a in algorithms if a],
            }
        )
        if len(batch) >= 500:
            _upsert_problem_batch(batch)
            batch = []
    if batch:
        _upsert_problem_batch(batch)

    cache.set(cache_key, True, timeout=None)


def _upsert_problem_batch(rows: list):
    query = (
        "UNWIND $rows AS row "
        "MERGE (p:Problem {problem_id: row.problem_id}) "
        "SET p.problem = row.problem, p.difficulty = row.difficulty, p.category = row.category "
        "MERGE (d:Difficulty {level: row.difficulty}) "
        "MERGE (p)-[:HAS_DIFFICULTY]->(d) "
        "WITH p, row, coalesce(row.algorithms, []) AS algos "
        "UNWIND algos AS algo "
        "MERGE (a:AlgoSkill {name: algo}) "
        "MERGE (p)-[:USES_ALGO]->(a)"
    )
    post_cypher(query, {"rows": rows})



def sync_report(
    user_id: str,
    session_id: str,
    created_at: Optional[datetime],
    problem_algorithms: list,
    strategy_algorithms: list,
    consistency_status: str,
    problem_id: Optional[int],
    solved_score: Optional[float],
):
    ensure_schema()
    ensure_problem_graph()

    problem_algorithms = [str(a) for a in (problem_algorithms or []) if a]
    strategy_algorithms = [str(a) for a in (strategy_algorithms or []) if a]
    if problem_algorithms:
        gap_algos = problem_algorithms
    else:
        gap_algos = strategy_algorithms

    missing_algos = [a for a in gap_algos if a not in strategy_algorithms]
    consistency_weight = 0.0
    if consistency_status == "불일치":
        consistency_weight = 1.0
    elif consistency_status == "개선하여 구현":
        consistency_weight = 0.6

    query = (
        "MERGE (u:User {user_id:$user_id}) "
        "SET u.last_session_id = $session_id, u.last_interview_at = $created_at "
        "WITH u "
        "OPTIONAL MATCH (u)-[g:SHOWED_GAP]->(:AlgoSkill) DELETE g "
        "WITH u "
        "OPTIONAL MATCH (u)-[:HAS_EVIDENCE]->(e:Evidence) DETACH DELETE e "
        "WITH u "
        "UNWIND $gap_algos AS algo "
        "MERGE (s:AlgoSkill {name: algo}) "
        "MERGE (u)-[:SHOWED_GAP {weight: 1.0, ts: $created_at}]->(s) "
        "WITH u "
        "UNWIND $missing_algos AS algo "
        "MERGE (s2:AlgoSkill {name: algo}) "
        "MERGE (e1:Evidence {evidence_id: $user_id + ':strategy_mismatch:' + algo}) "
        "SET e1.type = 'strategy_mismatch', e1.detail = algo, e1.weight = 1.0 "
        "MERGE (u)-[:HAS_EVIDENCE {weight: 1.0, ts: $created_at}]->(e1) "
        "MERGE (e1)-[:SUPPORTS {weight: 1.0}]->(s2) "
        "WITH u "
        "FOREACH (_ IN CASE WHEN $consistency_weight > 0 THEN [1] ELSE [] END | "
        "  MERGE (e2:Evidence {evidence_id: $user_id + ':consistency'}) "
        "  SET e2.type = 'implementation_mismatch', e2.weight = $consistency_weight "
        "  MERGE (u)-[:HAS_EVIDENCE {weight: $consistency_weight, ts: $created_at}]->(e2) "
        "  FOREACH (a IN $gap_algos | "
        "    MERGE (s3:AlgoSkill {name: a}) "
        "    MERGE (e2)-[:SUPPORTS {weight: $consistency_weight}]->(s3) "
        "  ) "
        ") "
        "WITH u "
        "FOREACH (_ IN CASE WHEN $problem_id IS NULL THEN [] ELSE [1] END | "
        "  MERGE (p:Problem {problem_id: $problem_id}) "
        "  MERGE (u)-[s:SOLVED]->(p) "
        "  SET s.score = coalesce($solved_score, s.score, 1.0), "
        "      s.ts = coalesce($created_at, s.ts) "
        ")"
    )
    params = {
        "user_id": user_id,
        "session_id": session_id,
        "created_at": created_at.isoformat() if created_at else None,
        "gap_algos": gap_algos,
        "missing_algos": missing_algos,
        "consistency_weight": consistency_weight,
        "problem_id": problem_id,
        "solved_score": float(solved_score) if solved_score is not None else None,
    }
    post_cypher(query, params)
