import logging
import os
from dotenv import load_dotenv
from langgraph.checkpoint.redis import RedisSaver
from tts_client import generate_interview_audio_batch
from interview_engine import llm
from interview_engine.graph import (
    create_chapter1_graph_flow,
    create_chapter2_graph_flow,
)
from interview_engine import llm
from langgraph.checkpoint.redis import RedisSaver
from .stt_buffer import append_conversation_event
load_dotenv()
REDIS_URL = os.getenv("REDIS_URL")
logger = logging.getLogger(__name__)

# 모듈 전역
_checkpointer = None
_graph_cache = {}  # {"chapter1": compiled_graph, ...}
_llm_instance = None


def get_checkpointer():
    """RedisSaver를 우선 사용하되, 실패 시 인메모리로 폴백.

    - cp.setup()을 호출해 애플리케이션 시작 시점에 연결 풀을 미리 올려
      첫 호출 지연을 줄인다.
    - Redis 설정이 없거나 실패하면 MemorySaver로 전환해 가용성을 보장한다.
    """

    global _checkpointer
    if _checkpointer is not None:
        return _checkpointer

    if REDIS_URL:
        try:
            cp = RedisSaver(REDIS_URL)
            cp.setup()  # 연결 풀 및 키스페이스 준비
            _checkpointer = cp
            return _checkpointer
        except Exception as exc:  # noqa: BLE001
            logger.warning("RedisSaver 초기화 실패: %s", exc)

    return _checkpointer

def get_cached_graph(name: str):
    if name not in _graph_cache:
        cp = get_checkpointer()
        if name == "chapter1":
            _graph_cache[name] = create_chapter1_graph_flow(checkpointer=cp)
        elif name == "chapter2":
            _graph_cache[name] = create_chapter2_graph_flow(checkpointer=cp)
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

def _generate_tts_payload(text: str, session_id: str | None = None, max_sentences=None):
    """
    LangGraph thread_id와 문장 수 제한을 반영해 배치 TTS를 수행하고
    프론트로 내려줄 청크 페이로드를 생성합니다.
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

    # 생성된 TTS 텍스트를 공용 대화 버퍼에도 기록
    if session_id and text:
        append_conversation_event(
            session_id,
            role="system",
            channel="tts",
            text=text,
            stage=None,
            meta={"source": "tts"},
        )
    return sentences_payload
