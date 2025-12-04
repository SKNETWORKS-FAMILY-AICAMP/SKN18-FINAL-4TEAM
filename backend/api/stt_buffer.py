from __future__ import annotations

import json
from typing import Any, Dict, List

from django_redis import get_redis_connection


def _key(session_id: str) -> str:
    return f"stt:{session_id}"


def append_utterance(session_id: str, utterance: Dict[str, Any], ttl_seconds: int = 60 * 60) -> None:
    """
    STT/TTS로부터 받은 단일 발화 조각을 Redis 리스트에 추가합니다.
    utterance는 JSON 직렬화 가능한 dict 형태여야 합니다.
    """
    conn = get_redis_connection("default")
    key = _key(session_id)
    conn.rpush(key, json.dumps(utterance, ensure_ascii=False))
    # 세션마다 TTL을 갱신해 일정 시간 후 자동 만료되도록 합니다.
    conn.expire(key, ttl_seconds)


def get_utterances(session_id: str) -> List[Dict[str, Any]]:
    """
    해당 세션의 모든 발화 조각을 시간 순서대로 가져옵니다.
    """
    conn = get_redis_connection("default")
    key = _key(session_id)
    raw_items = conn.lrange(key, 0, -1)
    utterances: List[Dict[str, Any]] = []
    for raw in raw_items:
        try:
            utterances.append(json.loads(raw))
        except Exception:
            # 파싱 실패 항목은 건너뜁니다.
            continue
    return utterances


def clear_utterances(session_id: str) -> None:
    """
    평가가 끝난 후 세션별 STT 버퍼를 제거합니다.
    """
    conn = get_redis_connection("default")
    conn.delete(_key(session_id))

