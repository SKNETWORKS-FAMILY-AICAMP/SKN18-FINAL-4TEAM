import json
import os
import urllib.error
import urllib.request
from base64 import b64encode


def _basic_auth_header(username: str, password: str) -> str:
    token = b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
    return f"Basic {token}"


def _parse_neo4j_auth():
    raw = os.getenv("NEO4J_AUTH", "")
    if "/" in raw:
        user, pwd = raw.split("/", 1)
        return user, pwd
    return None, None


def post_cypher(query: str, params=None) -> dict:
    url = os.getenv("NEO4J_HTTP_URL")
    if not url:
        raise RuntimeError("NEO4J_HTTP_URL is required")
    user = os.getenv("NEO4J_USER")
    pwd = os.getenv("NEO4J_PASSWORD")
    if not user or not pwd:
        user, pwd = _parse_neo4j_auth()
    if not user or not pwd:
        raise RuntimeError("NEO4J_AUTH is required (format: neo4j/<password>)")

    payload = {
        "statements": [
            {
                "statement": query,
                "parameters": params or {},
            }
        ]
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", _basic_auth_header(user, pwd))
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Neo4j HTTP {exc.code}: {body}") from exc
