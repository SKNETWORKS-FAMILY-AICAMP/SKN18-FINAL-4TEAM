import json
from pathlib import Path

from django.core.cache import cache

from .es_client import es_request, es_request_raw
from .embeddings import embed_texts


def ensure_problem_index():
    cache_key = "graph_sync:es_index_ready"
    if cache.get(cache_key):
        return
    index_name = "coding_problem"
    status, _ = es_request("HEAD", index_name)
    if status == 404:
        mapping_path = Path(__file__).resolve().parents[2] / "docker" / "elasticsearch" / "coding_problem_mapping.json"
        mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
        status, body = es_request("PUT", index_name, mapping)
        if status >= 300:
            raise RuntimeError(f"ES index create failed: {body}")
    cache.set(cache_key, True, timeout=None)


def _bulk_index(payload: str) -> None:
    status, body = es_request_raw("POST", "_bulk", payload, content_type="application/x-ndjson")
    if status >= 300:
        raise RuntimeError(f"ES bulk index failed: {body}")


def _bulk_payload(items: list) -> str:
    lines = []
    for doc in items:
        pid = doc.get("problem_id")
        lines.append(json.dumps({"index": {"_index": "coding_problem", "_id": str(pid)}}))
        lines.append(json.dumps(doc))
    return "\n".join(lines) + "\n"


def ensure_problem_documents():
    cache_key = "graph_sync:es_problem_docs_ready"
    if cache.get(cache_key):
        return
    ensure_problem_index()
    status, body = es_request("GET", "coding_problem/_count")
    if status == 200 and int(body.get("count", 0)) > 0:
        missing = _count_missing_embeddings()
        if missing == 0:
            cache.set(cache_key, True, timeout=None)
            return
        _backfill_missing_embeddings()
        cache.set(cache_key, True, timeout=None)
        return

    from api.models import CodingProblem

    batch = []
    texts = []
    for problem in CodingProblem.objects.all().iterator(chunk_size=200):
        algorithms = problem.algorithm or []
        if isinstance(algorithms, str):
            try:
                algorithms = json.loads(algorithms)
            except Exception:
                algorithms = []
        if not isinstance(algorithms, list):
            algorithms = []
        item = {
            "problem_id": str(problem.problem_id),
            "problem": problem.problem or "",
            "category": problem.category or "",
            "algorithm": algorithms,
            "difficulty": problem.difficulty or "",
        }
        text = _embedding_text(item)
        batch.append(item)
        texts.append(text)
        if len(batch) >= 100:
            embeddings = embed_texts(texts)
            _attach_embeddings(batch, embeddings)
            _bulk_index(_bulk_payload(batch))
            batch = []
            texts = []
    if batch:
        embeddings = embed_texts(texts)
        _attach_embeddings(batch, embeddings)
        _bulk_index(_bulk_payload(batch))
    cache.set(cache_key, True, timeout=None)


def _embedding_text(item: dict) -> str:
    algos = item.get("algorithm") or []
    if isinstance(algos, list):
        algo_text = ", ".join([str(a) for a in algos if a])
    else:
        algo_text = str(algos)
    return (
        f"{item.get('problem', '')}\n\n"
        f"카테고리: {item.get('category', '')}\n"
        f"난이도: {item.get('difficulty', '')}\n"
        f"알고리즘: {algo_text}"
    )


def _attach_embeddings(items: list, embeddings: list) -> None:
    for item, emb in zip(items, embeddings):
        item["embedding"] = emb


def _count_missing_embeddings() -> int:
    query = {"query": {"bool": {"must_not": [{"exists": {"field": "embedding"}}]}}}
    status, body = es_request("POST", "coding_problem/_count", query)
    if status != 200:
        return 0
    return int(body.get("count", 0))


def _backfill_missing_embeddings() -> None:
    from api.models import CodingProblem

    search_after = None
    while True:
        query = {
            "query": {"bool": {"must_not": [{"exists": {"field": "embedding"}}]}},
            "_source": ["problem_id"],
            "size": 200,
            "sort": [{"_id": "asc"}],
        }
        if search_after is not None:
            query["search_after"] = search_after
        status, body = es_request("POST", "coding_problem/_search", query)
        if status != 200:
            return
        hits = body.get("hits", {}).get("hits", [])
        if not hits:
            return
        problem_ids = [h.get("_source", {}).get("problem_id") for h in hits if h.get("_source")]
        problem_ids = [pid for pid in problem_ids if pid is not None]
        problems = list(CodingProblem.objects.filter(problem_id__in=problem_ids))
        batch = []
        texts = []
        for problem in problems:
            algorithms = problem.algorithm or []
            if isinstance(algorithms, str):
                try:
                    algorithms = json.loads(algorithms)
                except Exception:
                    algorithms = []
            if not isinstance(algorithms, list):
                algorithms = []
            item = {
                "problem_id": str(problem.problem_id),
                "problem": problem.problem or "",
                "category": problem.category or "",
                "algorithm": algorithms,
                "difficulty": problem.difficulty or "",
            }
            batch.append(item)
            texts.append(_embedding_text(item))
        if batch:
            embeddings = embed_texts(texts)
            _attach_embeddings(batch, embeddings)
            _bulk_index(_bulk_payload(batch))
        search_after = hits[-1].get("sort")
