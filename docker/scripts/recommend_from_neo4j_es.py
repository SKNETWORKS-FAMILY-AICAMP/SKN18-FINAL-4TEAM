import argparse
import json
import os
import urllib.request
import urllib.error
from base64 import b64encode
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None


def _basic_auth_header(username: str, password: str) -> str:
    token = b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
    return f"Basic {token}"


def _post_json(url, payload, auth_header=None):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if auth_header:
        req.add_header("Authorization", auth_header)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} from {url}: {body}") from exc


def _parse_neo4j_auth():
    raw = os.getenv("NEO4J_AUTH", "")
    if "/" in raw:
        user, pwd = raw.split("/", 1)
        return user, pwd
    return None, None


def _normalize_difficulties(raw: str) -> list:
    return [d.strip() for d in (raw or "").split(",") if d.strip()]


def _neo4j_candidates(neo4j_url, auth_header, user_id, limit, difficulties):
    query = (
        "MATCH (u:User {user_id:$user_id})-[:TOOK]->(i:Interview) "
        "WITH i ORDER BY i.created_at DESC LIMIT 1 "
        "OPTIONAL MATCH (i)-[:HAS_EVIDENCE]->(e:Evidence)-[sup:SUPPORTS]->(s:AlgoSkill) "
        "WITH i, collect({skill: s, weight: coalesce(sup.weight, e.weight, 1.0)}) AS ev "
        "CALL { "
        "  WITH i, ev "
        "  WITH i, ev "
        "  WHERE size(ev) > 0 "
        "  UNWIND ev AS item "
        "  RETURN item.skill AS skill, item.weight AS weight "
        "  UNION "
        "  WITH i, ev "
        "  WHERE size(ev) = 0 "
        "  MATCH (i)-[g:SHOWED_GAP]->(s2:AlgoSkill) "
        "  RETURN s2 AS skill, coalesce(g.weight, 1.0) AS weight "
        "} "
        "MATCH (skill)<-[:USES_ALGO]-(p:Problem) "
        "MATCH (p)-[:HAS_DIFFICULTY]->(d:Difficulty) "
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
                "parameters": {"user_id": user_id, "limit": limit, "difficulties": difficulties},
            }
        ]
    }
    data = _post_json(neo4j_url, payload, auth_header)
    rows = data.get("results", [{}])[0].get("data", [])
    return [int(r["row"][0]) for r in rows if r.get("row")]  # list of problem_id


def _openai_embedding(text, api_key, model):
    url = "https://api.openai.com/v1/embeddings"
    payload = json.dumps({"model": model, "input": [text]}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {api_key}")
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["data"][0]["embedding"]


def _latest_grade_from_postgres(user_id: str) -> str:
    db_user = os.getenv("DB_USER")
    db_name = os.getenv("DB_NAME")
    db_password = os.getenv("DB_PASSWORD")
    if not db_user or not db_name:
        return ""

    safe_user_id = user_id.replace("'", "''")
    sql = (
        "SELECT final_grade "
        "FROM livecoding_reports "
        f"WHERE user_id = '{safe_user_id}' "
        "ORDER BY created_at DESC "
        "LIMIT 1;"
    )

    cmd = [
        "docker",
        "compose",
        "-f",
        "docker/docker-compose.yml",
        "--env-file",
        ".env",
        "exec",
        "-T",
        "postgres",
        "psql",
        "-U",
        db_user,
        "-d",
        db_name,
        "-t",
        "-A",
        "-c",
        sql,
        "--set",
        "ON_ERROR_STOP=1",
    ]
    env = os.environ.copy()
    if db_password:
        env["PGPASSWORD"] = db_password
    try:
        import subprocess

        result = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
    except Exception as exc:
        print(f"warning: failed to fetch grade from postgres: {exc}", flush=True)
        return ""

    if result.returncode != 0:
        print(
            "warning: failed to fetch grade from postgres "
            f"(code={result.returncode}, stdout={result.stdout!r}, stderr={result.stderr!r})",
            flush=True,
        )
        return ""

    grade = (result.stdout or "").strip()
    if not grade:
        print(f"warning: no grade found (stdout={result.stdout!r}, stderr={result.stderr!r})", flush=True)
    return grade


def _es_hybrid_search(es_url, auth_header, index_name, query_text, problem_ids, top_k, difficulties):
    body = {
        "size": top_k,
        "query": {
            "bool": {
                "should": [
                    {"match": {"problem": query_text}},
                    {"terms": {"problem_id": [str(pid) for pid in problem_ids]}},
                ],
                "filter": [
                    {"terms": {"difficulty": difficulties}},
                ],
            }
        },
        "knn": {
            "field": "embedding",
            "query_vector": _openai_embedding(query_text, os.environ.get("OPENAI_API_KEY", ""),
                                              os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")),
            "k": max(10, top_k),
            "num_candidates": max(50, len(problem_ids)),
            "filter": {
                "bool": {
                    "filter": [
                        {"terms": {"problem_id": [str(pid) for pid in problem_ids]}},
                        {"terms": {"difficulty": difficulties}},
                    ]
                }
            },
        },
        "rank": {"rrf": {"window_size": max(50, len(problem_ids)), "rank_constant": 60}},
    }
    try:
        return _post_json(f"{es_url}/{index_name}/_search", body, auth_header)
    except SystemExit as exc:
        msg = str(exc)
        if "Reciprocal Rank Fusion" not in msg:
            raise
    # Fallback without RRF for basic license
    body.pop("rank", None)
    return _post_json(f"{es_url}/{index_name}/_search", body, auth_header)


def main():
    if load_dotenv:
        repo_root = Path(__file__).resolve().parents[2]
        load_dotenv(repo_root / ".env")

    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--neo4j-url", default=os.getenv("NEO4J_HTTP_URL", "http://localhost:7474/db/neo4j/tx/commit"))
    parser.add_argument("--neo4j-user", default=os.getenv("NEO4J_USER"))
    parser.add_argument("--neo4j-password", default=os.getenv("NEO4J_PASSWORD"))
    parser.add_argument("--es-url", default=os.getenv("ES_URL", "http://localhost:9200"))
    parser.add_argument("--es-index", default=os.getenv("ES_INDEX", "coding_problem"))
    parser.add_argument("--es-user", default=os.getenv("ES_USER", "elastic"))
    parser.add_argument("--es-password", default=os.getenv("ELASTIC_PASSWORD"))
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--grade", default=os.getenv("RECOMMEND_GRADE", ""))
    parser.add_argument("--difficulty", default=os.getenv("RECOMMEND_DIFFICULTIES", ""))
    parser.add_argument("--auto-grade", action="store_true")
    args = parser.parse_args()

    if not args.neo4j_user or not args.neo4j_password:
        user, pwd = _parse_neo4j_auth()
        if not args.neo4j_user:
            args.neo4j_user = user or "neo4j"
        if not args.neo4j_password:
            args.neo4j_password = pwd

    if not args.neo4j_password:
        raise SystemExit("NEO4J_AUTH is required (set in .env, format: neo4j/<password>)")
    if not args.es_password:
        raise SystemExit("ELASTIC_PASSWORD is required (set in .env)")
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is required for embeddings")

    if args.auto_grade and not args.grade:
        args.grade = _latest_grade_from_postgres(args.user_id)

    if args.difficulty:
        difficulties = _normalize_difficulties(args.difficulty)
    elif args.grade:
        grade = args.grade.strip().upper()
        if grade in {"A+", "A"}:
            difficulties = ["hard"]
        elif grade in {"B+", "B"}:
            difficulties = ["normal", "hard"]
        elif grade in {"C+", "C"}:
            difficulties = ["normal"]
        else:
            difficulties = ["normal"]
    else:
        difficulties = ["normal", "hard"]

    if args.auto_grade and not args.grade:
        print("warning: auto-grade enabled but no grade found; using default difficulties", flush=True)

    print(f"grade={args.grade or ''} difficulties={difficulties}", flush=True)

    neo4j_auth = _basic_auth_header(args.neo4j_user, args.neo4j_password)
    es_auth = _basic_auth_header(args.es_user, args.es_password)

    candidates = _neo4j_candidates(args.neo4j_url, neo4j_auth, args.user_id, args.limit, difficulties)
    if not candidates:
        raise SystemExit("No candidate problem_id found from Neo4j")

    result = _es_hybrid_search(args.es_url, es_auth, args.es_index, args.query, candidates, args.top_k, difficulties)
    hits = result.get("hits", {}).get("hits", [])
    hits = [
        h for h in hits
        if (h.get("_source", {}) or {}).get("difficulty") in difficulties
    ]
    output = [
        {
            "problem_id": h.get("_source", {}).get("problem_id"),
            "score": h.get("_score"),
            "problem": h.get("_source", {}).get("problem", "")[:120],
            "difficulty": h.get("_source", {}).get("difficulty"),
        }
        for h in hits
    ]
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
