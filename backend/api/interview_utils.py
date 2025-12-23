import os
from dotenv import load_dotenv
from langgraph.checkpoint.redis import RedisSaver
from tts_client import generate_interview_audio_batch

from interview_engine.graph import (
    create_chapter1_graph_flow,
    create_chapter2_graph_flow,
    create_chapter2_hint_graph,
    create_chapter3_graph_flow,
)
from interview_engine import llm
from .stt_buffer import append_conversation_event  # noqa: F401  # kept for side effects

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL")

# 캐시
_checkpointer = None
_graph_cache = {}  # {"chapter1": compiled_graph, ...}
_llm_instance = None


def get_checkpointer():
    global _checkpointer
    if _checkpointer is not None:
        return _checkpointer

    if REDIS_URL:
        try:
            cp = RedisSaver(REDIS_URL)
            cp.setup()
            _checkpointer = cp
            return _checkpointer
        except Exception:
            pass

    return _checkpointer


def get_cached_graph(name: str):
    if name not in _graph_cache:
        cp = get_checkpointer()
        if name == "chapter1":
            _graph_cache[name] = create_chapter1_graph_flow(checkpointer=cp)
        elif name == "chapter2":
            _graph_cache[name] = create_chapter2_graph_flow(checkpointer=cp)
        elif name == "chapter2_hint":
            _graph_cache[name] = create_chapter2_hint_graph(checkpointer=cp)
        elif name == "chapter3":
            _graph_cache[name] = create_chapter3_graph_flow(checkpointer=cp)
        else:
            raise ValueError(f"unknown graph {name}")
    return _graph_cache[name]


def get_cached_llm():
    """interview_engine.llm.LLM 클래스만 캐싱해서 반환합니다"""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = getattr(llm, "LLM", None)
    return _llm_instance


def _generate_tts_payload(text: str, session_id: str | None = None, max_sentences=None):
    """
    LangGraph thread_id를 문장 단위로 반영해 배치 TTS를 실행하고
    클라이언트로 전달할 base64 오디오 리스트를 리턴합니다.
    """
    config = {"configurable": {}}
    if session_id:
        config["configurable"]["thread_id"] = session_id
    if isinstance(max_sentences, int) and max_sentences > 0:
        config["configurable"]["max_sentences"] = max_sentences
    if not config["configurable"]:
        config = None

    sentences_payload = []
    tts_result = generate_interview_audio_batch(text, config=config)
    for chunk in tts_result.get("audio_chunks", []):
        audio_b64 = chunk.get("audio_base64")
        if not audio_b64:
            continue
        sentences_payload.append({"text": chunk.get("text", ""), "audio": audio_b64})

    return sentences_payload
