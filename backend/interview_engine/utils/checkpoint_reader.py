# backend/interview_engine/utils/checkpoint_reader.py
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from django.conf import settings
from langgraph.checkpoint.redis import RedisSaver


def _redis_url() -> str:
    return (
        os.getenv("REDIS_URL")
        or getattr(settings, "REDIS_URL", None)
        or "redis://127.0.0.1:6379/0"
    )


def load_chapter_channel_values(session_id: str, chapter: str) -> Dict[str, Any]:
    """
    너희 Redis 저장 규칙 기준:
      thread_id = "{session_id}:{chapter}"
      checkpoint_ns = "__empty__"
      checkpoint["channel_values"] 를 반환
    chapter 예: "chapter1", "chapter2", "chapter2_hint"
    """
    if not session_id:
        return {}

    thread_id = f"{session_id}:{chapter}"
    checkpoint_ns = "__empty__"

    try:
        saver = RedisSaver.from_conn_string(_redis_url())

        # LangGraph 버전별 대응: get_tuple 우선
        if hasattr(saver, "get_tuple"):
            tup = saver.get_tuple(thread_id=thread_id, checkpoint_ns=checkpoint_ns)
            if not tup or not getattr(tup, "checkpoint", None):
                return {}
            ckpt = tup.checkpoint or {}
            return (ckpt.get("channel_values") or {}) if isinstance(ckpt, dict) else {}

        # 일부 버전에서는 get_state
        if hasattr(saver, "get_state"):
            st = saver.get_state(thread_id=thread_id, checkpoint_ns=checkpoint_ns) or {}
            return (st.get("channel_values") or {}) if isinstance(st, dict) else {}

        return {}
    except Exception:
        return {}
