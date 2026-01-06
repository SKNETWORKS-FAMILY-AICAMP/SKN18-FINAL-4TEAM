import math
from collections import Counter
from typing import Dict, Iterable, List, Tuple

from django.core.cache import cache

from .neo4j_client import post_cypher


_AUTO_SOURCE = "auto"


def update_algo_similarity(
    min_cooccurrence: int = 5,
    pmi_threshold: float = 0.0,
    sigmoid_scale: float = 1.0,
    include_reports: bool = True,
) -> int:
    docs = list(_iter_algorithm_sets(include_reports=include_reports))
    total_docs = len(docs)
    if total_docs == 0:
        return 0

    algo_doc_counts = Counter()
    pair_counts = Counter()
    for algos in docs:
        unique_algos = sorted(set(algos))
        if not unique_algos:
            continue
        for algo in unique_algos:
            algo_doc_counts[algo] += 1
        if len(unique_algos) < 2:
            continue
        for i in range(len(unique_algos)):
            for j in range(i + 1, len(unique_algos)):
                pair_counts[(unique_algos[i], unique_algos[j])] += 1

    rows = []
    for (a, b), co in pair_counts.items():
        if co < min_cooccurrence:
            continue
        p_a = algo_doc_counts[a] / total_docs
        p_b = algo_doc_counts[b] / total_docs
        p_ab = co / total_docs
        if p_a == 0 or p_b == 0 or p_ab == 0:
            continue
        pmi = math.log(p_ab / (p_a * p_b))
        if pmi < pmi_threshold:
            continue
        score = _sigmoid(pmi, sigmoid_scale) * math.log1p(co)
        rows.append(
            {
                "a": a,
                "b": b,
                "score": round(score, 4),
                "co": int(co),
                "pmi": round(pmi, 4),
            }
        )

    _replace_auto_related(rows)
    cache.set("graph_sync:algo_similarity:last_run", _now_iso(), timeout=None)
    return len(rows)


def _iter_algorithm_sets(include_reports: bool) -> Iterable[List[str]]:
    from api.models import CodingProblem, LivecodingReport

    for raw in (
        CodingProblem.objects.values_list("algorithm", flat=True)
        .iterator(chunk_size=500)
    ):
        algos = _coerce_algorithms(raw)
        if algos:
            yield algos

    if not include_reports:
        return

    for payload in (
        LivecodingReport.objects.values_list("graph_output", flat=True)
        .iterator(chunk_size=500)
    ):
        if not isinstance(payload, dict):
            continue
        algos = payload.get("problem_algorithms") or payload.get("strategy_algorithms") or []
        algos = _coerce_algorithms(algos)
        if algos:
            yield algos


def _coerce_algorithms(value) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return []
        if value.startswith("["):
            try:
                import json

                parsed = json.loads(value)
                if isinstance(parsed, list):
                    value = parsed
                else:
                    value = [value]
            except Exception:
                value = [value]
        else:
            value = [v.strip() for v in value.split(",") if v.strip()]
    if not isinstance(value, list):
        return []
    cleaned = []
    for item in value:
        text = str(item).strip()
        if text:
            cleaned.append(text)
    return cleaned


def _replace_auto_related(rows: List[Dict[str, object]]) -> None:
    delete_query = "MATCH ()-[r:RELATED {source: $source}]->() DELETE r"
    post_cypher(delete_query, {"source": _AUTO_SOURCE})

    if not rows:
        return

    query = (
        "UNWIND $rows AS row "
        "MERGE (a:AlgoSkill {name: row.a}) "
        "MERGE (b:AlgoSkill {name: row.b}) "
        "MERGE (a)-[r:RELATED]->(b) "
        "SET r.score = row.score, r.co = row.co, r.pmi = row.pmi, "
        "r.source = $source, r.updated_at = timestamp() "
        "MERGE (b)-[r2:RELATED]->(a) "
        "SET r2.score = row.score, r2.co = row.co, r2.pmi = row.pmi, "
        "r2.source = $source, r2.updated_at = timestamp() "
    )
    post_cypher(query, {"rows": rows, "source": _AUTO_SOURCE})


def _sigmoid(value: float, scale: float) -> float:
    scaled = value * scale
    if scaled >= 50:
        return 1.0
    if scaled <= -50:
        return 0.0
    return 1.0 / (1.0 + math.exp(-scaled))


def _now_iso() -> str:
    from django.utils import timezone

    return timezone.localtime(timezone.now()).isoformat()
