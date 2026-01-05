import json
import os
import urllib.error
import urllib.request
from base64 import b64encode


def _basic_auth_header(username: str, password: str) -> str:
    token = b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
    return f"Basic {token}"


def _es_request(method: str, path: str, body=None, content_type="application/json") -> tuple[int, dict]:
    es_url = os.getenv("ES_URL", "http://localhost:9200").rstrip("/")
    user = os.getenv("ES_USER", "elastic")
    pwd = os.getenv("ELASTIC_PASSWORD")
    if not pwd:
        raise RuntimeError("ELASTIC_PASSWORD is required")

    url = f"{es_url}/{path.lstrip('/')}"
    data = None
    if body is not None:
        if isinstance(body, (bytes, bytearray)):
            data = body
        elif isinstance(body, str):
            data = body.encode("utf-8")
        else:
            data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method.upper())
    req.add_header("Content-Type", content_type)
    req.add_header("Authorization", _basic_auth_header(user, pwd))
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = resp.read().decode("utf-8") or "{}"
            return resp.status, json.loads(payload)
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace") or "{}"
        try:
            return exc.code, json.loads(payload)
        except Exception:
            return exc.code, {"error": payload}


def es_request(method: str, path: str, body=None) -> tuple[int, dict]:
    return _es_request(method, path, body, content_type="application/json")


def es_request_raw(method: str, path: str, body, content_type: str) -> tuple[int, dict]:
    return _es_request(method, path, body, content_type=content_type)
