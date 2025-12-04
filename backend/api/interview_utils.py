from interview_engine.graph import create_graph_flow
from interview_engine import llm 


# langgraph/LLM 재사용을 위한 캐시
_graph_instance = None
_llm_instance = None


def get_cached_graph():
    """create_graph_flow() 결과를 캐싱해 재사용."""
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = create_graph_flow()
    return _graph_instance


def get_cached_llm():
    """interview_engine.llm.LLM 인스턴스를 캐싱해 재사용."""
    global _llm_instance
    if _llm_instance is None:
        # llm 모듈 import 시 생성된 LLM을 활용
        _llm_instance = getattr(llm, "LLM", None)
    return _llm_instance