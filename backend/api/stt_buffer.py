from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from django.utils import timezone
from django_redis import get_redis_connection


def _key(session_id: str) -> str:
    # STT/TTS를 모두 포함하는 공용 대화 버퍼 키
    return f"conv:{session_id}"


def append_conversation_event(
    session_id: str,
    *,
    role: str,
    channel: str,
    text: str,
    stage: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
    ttl_seconds: int = 60 * 60,
) -> None:
    """
    STT/TTS를 포함한 단일 대화 이벤트를 Redis 리스트에 추가합니다.

    role:   "user" | "system"
    channel:"stt"  | "tts"
    text:   실제 텍스트
    stage:  "intro" | "coding" 등 (옵션)
    meta:   question_id 등 부가 정보 (옵션)
    """
    if not session_id or not text:
        return

    event: Dict[str, Any] = {
        "ts": timezone.now().isoformat(),
        "role": role,
        "channel": channel,
        "text": text,
    }
    if stage:
        event["stage"] = stage
    if meta:
        event["meta"] = meta

    conn = get_redis_connection("default")
    key = _key(session_id)
    conn.rpush(key, json.dumps(event, ensure_ascii=False))
    conn.expire(key, ttl_seconds)


def append_utterance(session_id: str, utterance: Dict[str, Any], ttl_seconds: int = 60 * 60) -> None:
    """
    [하위 호환용] 단일 발화 조각을 Redis 리스트에 추가합니다.
    utterance는 JSON 직렬화 가능한 dict 형태여야 합니다.
    """
    if not session_id:
        return
    conn = get_redis_connection("default")
    key = _key(session_id)
    conn.rpush(key, json.dumps(utterance, ensure_ascii=False))
    conn.expire(key, ttl_seconds)


def get_utterances(session_id: str) -> List[Dict[str, Any]]:
    """
    해당 세션의 모든 대화 이벤트를 시간 순서대로 가져옵니다.
    (STT/TTS 공용 버퍼)
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
    평가가 끝난 후 세션별 대화 버퍼를 제거합니다.
    """
    conn = get_redis_connection("default")
    conn.delete(_key(session_id))
