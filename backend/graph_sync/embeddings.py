import json
import os
import urllib.error
import urllib.request


def embed_texts(texts):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for embeddings")
    model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")

    url = "https://api.openai.com/v1/embeddings"
    payload = json.dumps({"model": model, "input": texts}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {api_key}")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI HTTP {exc.code}: {body}") from exc

    items = data.get("data") or []
    items.sort(key=lambda x: x.get("index", 0))
    return [item.get("embedding") for item in items]
