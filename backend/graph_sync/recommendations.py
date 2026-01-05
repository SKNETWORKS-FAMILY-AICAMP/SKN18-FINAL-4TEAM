from typing import Any, Dict, List
import os

from api.models import CodingProblemLanguage
from .neo4j_client import post_cypher
from .es_client import es_request
from .embeddings import embed_texts


def _difficulties_from_grade(grade: str) -> list:
    grade = (grade or "").strip().upper()
    if grade in {"A+", "A"}:
        return ["hard"]
    if grade in {"B+", "B"}:
        return ["normal", "hard"]
    if grade in {"C+", "C"}:
        return ["normal"]
    return ["normal", "hard"]


def _neo4j_recommend_problem_ids(user_id: str, limit: int, difficulties: list) -> list:
    query = (
        "MATCH (u:User {user_id:$user_id}) "
        "WITH u, CASE coalesce(u.activity_level, 'light') "
        "  WHEN 'heavy_growth' THEN 1.3 "
        "  WHEN 'heavy_rand' THEN 0.6 "
        "  ELSE 0.0 "
        "END AS sim_factor "
        "CALL { "
        "  WITH u, sim_factor "
        "  MATCH (u)-[:HAS_EVIDENCE]->(e:Evidence)-[sup:SUPPORTS]->(s:AlgoSkill) "
        "  RETURN s AS skill, coalesce(sup.weight, e.weight, 1.0) AS weight "
        "  UNION "
        "  WITH u, sim_factor "
        "  MATCH (u)-[g:SHOWED_GAP]->(s2:AlgoSkill) "
        "  RETURN s2 AS skill, coalesce(g.weight, 1.0) AS weight "
        "  UNION "
        "  WITH u, sim_factor "
        "  MATCH (u)-[sim:SIMILAR]->(u2:User)-[g2:SHOWED_GAP]->(s3:AlgoSkill) "
        "  RETURN s3 AS skill, coalesce(g2.weight, 1.0) * coalesce(sim.score, 1.0) * sim_factor AS weight "
        "  UNION "
        "  WITH u, sim_factor "
        "  MATCH (u)-[g3:SHOWED_GAP]->(s4:AlgoSkill)-[rel:RELATED]->(s5:AlgoSkill) "
        "  RETURN s5 AS skill, coalesce(g3.weight, 1.0) * coalesce(rel.score, 0.5) AS weight "
        "} "
        "MATCH (skill)<-[:USES_ALGO]-(p:Problem)-[:HAS_DIFFICULTY]->(d:Difficulty) "
        "WHERE d.level IN $difficulties "
        "WITH p, sum(weight) AS score "
        "RETURN p.problem_id AS problem_id "
        "ORDER BY score DESC "
        "LIMIT $limit"
    )
    payload = {
        "statements": [
            {
                "statement": query,
                "parameters": {
                    "user_id": user_id,
                    "limit": limit,
                    "difficulties": difficulties,
                },
            }
        ]
    }
    data = post_cypher(query, {"user_id": user_id, "limit": limit, "difficulties": difficulties})
    errors = data.get("errors") or []
    if errors:
        return []
    rows = data.get("results", [{}])[0].get("data", [])
    problem_ids = []
    for r in rows:
        row = r.get("row") or []
        if not row:
            continue
        problem_ids.append(row[0])
    return problem_ids


def _es_hybrid_rerank(
    query_text: str,
    problem_ids: list,
    difficulties: list,
    top_k: int,
):
    if not query_text:
        return []
    if not problem_ids:
        return []
    if not os.getenv("OPENAI_API_KEY"):
        return []

    index_name = os.getenv("ES_INDEX", "coding_problem")
    embedding = embed_texts([query_text])[0]
    problem_ids = [str(pid) for pid in problem_ids]
    difficulties = difficulties or []

    body = {
        "size": top_k,
        "query": {
            "bool": {
                "should": [
                    {"match": {"problem": query_text}},
                    {"terms": {"problem_id": problem_ids}},
                ],
                "filter": [
                    {"terms": {"problem_id": problem_ids}},
                    {"terms": {"difficulty": difficulties}},
                ],
            }
        },
        "knn": {
            "field": "embedding",
            "query_vector": embedding,
            "k": max(10, top_k),
            "num_candidates": max(50, len(problem_ids)),
            "filter": {
                "bool": {
                    "filter": [
                        {"terms": {"problem_id": problem_ids}},
                        {"terms": {"difficulty": difficulties}},
                    ]
                }
            },
        },
        "rank": {"rrf": {"window_size": max(50, len(problem_ids)), "rank_constant": 60}},
    }

    status, body_resp = es_request("POST", f"{index_name}/_search", body)
    if status >= 300:
        body.pop("rank", None)
        status, body_resp = es_request("POST", f"{index_name}/_search", body)
        if status >= 300:
            return []
    hits = body_resp.get("hits", {}).get("hits", [])
    ranked = []
    for hit in hits:
        source = hit.get("_source") or {}
        pid = source.get("problem_id")
        if pid is not None:
            ranked.append(pid)
    return ranked


def _problem_payloads(problem_ids: list, language: str, limit: int) -> list:
    payloads = []
    seen = set()
    for pid in problem_ids:
        if pid in seen:
            continue
        seen.add(pid)
        problem_lang = (
            CodingProblemLanguage.objects.select_related("problem")
            .prefetch_related("problem__test_cases")
            .filter(problem_id=pid, language__iexact=language)
            .first()
        )
        if not problem_lang:
            continue
        problem = problem_lang.problem
        test_cases = [
            {"id": tc.id, "input": tc.input_data, "output": tc.output_data}
            for tc in (problem.test_cases.all() if hasattr(problem, "test_cases") else [])
        ]
        payloads.append(
            {
                "problem_id": problem.problem_id,
                "problem": problem.problem,
                "difficulty": problem.difficulty,
                "category": problem.category,
                "algorithm": problem.algorithm,
                "language": problem_lang.language,
                "function_name": problem_lang.function_name,
                "starter_code": problem_lang.starter_code,
                "test_cases": test_cases,
                "source": "neo4j",
            }
        )
        if len(payloads) >= limit:
            break
    return payloads


def build_recommended_problems(
    user_id: str,
    graph_output: Dict[str, Any],
    limit: int,
    language: str,
) -> List[Dict[str, Any]]:
    existing = graph_output.get("recommended_problems")
    if isinstance(existing, list) and existing:
        return existing
    difficulties = _difficulties_from_grade(graph_output.get("final_grade") or "")
    neo4j_ids = _neo4j_recommend_problem_ids(user_id, max(limit * 10, 50), difficulties)
    query_text = (graph_output.get("recommendation_query") or "").strip()
    reranked = _es_hybrid_rerank(query_text, neo4j_ids, difficulties, limit)
    problem_ids = reranked or neo4j_ids[:limit]
    return _problem_payloads(problem_ids, language, limit)
