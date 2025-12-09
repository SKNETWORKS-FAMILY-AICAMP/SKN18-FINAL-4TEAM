import os
from pathlib import Path

from dotenv import load_dotenv
from backend.interview_engine.graph import (
    create_chapter1_graph_flow,
    create_chapter2_graph_flow,
    create_chapter3_graph_flow
)
from interview_engine import llm
from langgraph.checkpoint.redis import RedisSaver
load_dotenv()
REDIS_URL = os.getenv("REDIS_URL")

# 모듈 전역
_checkpointer = None
_graph_cache = {}  # {"chapter1": compiled_graph, ...}
_llm_instance = None


def get_checkpointer():
    global _checkpointer
    if _checkpointer is None:
        cp = RedisSaver(REDIS_URL)
        cp.setup()
        _checkpointer = cp
    return _checkpointer

def get_cached_graph(session_id, name: str):
    if name not in _graph_cache:
        cp = get_checkpointer()
        if name == "chapter1":
            _graph_cache[name] = create_chapter1_graph_flow(checkpointer=cp)
        elif name == "chapter2":
            _graph_cache[name] = create_chapter2_graph_flow(checkpointer=cp)
        elif name == "chapter3":
            _graph_cache[name] = create_chapter3_graph_flow(checkpointer=cp)
        else:
            raise ValueError(f"unknown graph {name}")
    return _graph_cache[name]


def get_cached_llm():
    """interview_engine.llm.LLM 인스턴스를 캐싱해 재사용."""
    global _llm_instance
    if _llm_instance is None:
        # llm 모듈 import 시 생성된 LLM을 활용
        _llm_instance = getattr(llm, "LLM", None)
    return _llm_instance
