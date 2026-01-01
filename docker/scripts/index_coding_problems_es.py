import argparse
import csv
import json
import os
import time
import urllib.request
import urllib.error
from base64 import b64encode
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional dependency
    load_dotenv = None

DEFAULT_INDEX = "coding_problem"


def _basic_auth_header(username: str, password: str) -> str:
    token = b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
    return f"Basic {token}"


def _openai_embedding(texts, api_key, model):
    url = "https://api.openai.com/v1/embeddings"
    payload = json.dumps({"model": model, "input": texts}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {api_key}")
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    # Preserve order
    return [item["embedding"] for item in data["data"]]


def _es_bulk(items, es_url, auth_header):
    data = "".join(items).encode("utf-8")
    req = urllib.request.Request(f"{es_url}/_bulk", data=data, method="POST")
    req.add_header("Content-Type", "application/x-ndjson")
    if auth_header:
        req.add_header("Authorization", auth_header)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _build_text(problem, category, difficulty, algos):
    parts = [problem.strip()]
    if category:
        parts.append(f"Category: {category}")
    if difficulty:
        parts.append(f"Difficulty: {difficulty}")
    if algos:
        parts.append("Algorithms: " + ", ".join(algos))
    return "\n".join(parts)


def main():
    if load_dotenv:
        repo_root = Path(__file__).resolve().parents[2]
        env_path = repo_root / ".env"
        load_dotenv(env_path)

    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="docker/csv_files/coding_problems.csv")
    parser.add_argument("--es-url", default=os.getenv("ES_URL", "http://localhost:9200"))
    parser.add_argument("--es-index", default=os.getenv("ES_INDEX", DEFAULT_INDEX))
    parser.add_argument("--es-user", default=os.getenv("ES_USER", "elastic"))
    parser.add_argument("--es-password", default=os.getenv("ELASTIC_PASSWORD"))
    parser.add_argument("--openai-model", default=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large"))
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--no-embeddings", action="store_true")
    args = parser.parse_args()

    if not os.path.exists(args.csv):
        raise SystemExit(f"CSV not found: {args.csv}")

    auth_header = None
    if args.es_password:
        auth_header = _basic_auth_header(args.es_user, args.es_password)

    api_key = os.getenv("OPENAI_API_KEY")
    use_embeddings = (not args.no_embeddings) and bool(api_key)

    bulk_items = []
    batch_texts = []
    batch_docs = []

    with open(args.csv, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            problem_id = str(row.get("problem_id", "")).strip()
            if not problem_id:
                continue
            problem = row.get("problem", "")
            category = row.get("category", "")
            difficulty = row.get("difficulty", "")
            algorithm_raw = row.get("algorithm", "")
            algos = []
            if algorithm_raw:
                try:
                    algos = json.loads(algorithm_raw)
                except Exception:
                    algos = []

            doc = {
                "problem_id": problem_id,
                "problem": problem,
                "category": category,
                "difficulty": difficulty,
                "algorithm": algos,
            }

            if use_embeddings:
                text_for_embedding = _build_text(problem, category, difficulty, algos)
                batch_texts.append(text_for_embedding)
                batch_docs.append(doc)
            else:
                action = {"index": {"_index": args.es_index, "_id": problem_id}}
                bulk_items.append(json.dumps(action) + "\n")
                bulk_items.append(json.dumps(doc, ensure_ascii=False) + "\n")

            if use_embeddings and len(batch_texts) >= args.batch_size:
                embeddings = _openai_embedding(batch_texts, api_key, args.openai_model)
                for emb, doc_item in zip(embeddings, batch_docs):
                    doc_item["embedding"] = emb
                    action = {"index": {"_index": args.es_index, "_id": doc_item["problem_id"]}}
                    bulk_items.append(json.dumps(action) + "\n")
                    bulk_items.append(json.dumps(doc_item, ensure_ascii=False) + "\n")
                batch_texts.clear()
                batch_docs.clear()

            if len(bulk_items) >= args.batch_size * 2:
                resp = _es_bulk(bulk_items, args.es_url, auth_header)
                if resp.get("errors"):
                    raise SystemExit("Bulk indexing failed: errors=true")
                bulk_items.clear()
                time.sleep(0.2)

    if use_embeddings and batch_texts:
        embeddings = _openai_embedding(batch_texts, api_key, args.openai_model)
        for emb, doc_item in zip(embeddings, batch_docs):
            doc_item["embedding"] = emb
            action = {"index": {"_index": args.es_index, "_id": doc_item["problem_id"]}}
            bulk_items.append(json.dumps(action) + "\n")
            bulk_items.append(json.dumps(doc_item, ensure_ascii=False) + "\n")

    if bulk_items:
        resp = _es_bulk(bulk_items, args.es_url, auth_header)
        if resp.get("errors"):
            raise SystemExit("Bulk indexing failed: errors=true")

    print("Done")


if __name__ == "__main__":
    main()
