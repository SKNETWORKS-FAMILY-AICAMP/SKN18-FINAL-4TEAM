import os
from langchain.chat_models import init_chat_model


API_KEY = os.environ.get("OPENAI_API_KEY")

# 역할별 기본 모델 설정 (환경변수로 오버라이드 가능)
MODEL_CONFIG = {
    "default": os.getenv("LLM_MODEL_DEFAULT", "gpt-5-nano"),
    "intro": os.getenv("LLM_MODEL_INTRO", "gpt-5-nano"),
    "classify": os.getenv("LLM_MODEL_classify", "gpt-5-nano"),
    "hint": os.getenv("LLM_MODEL_HINT", "gpt-4o"),
    "question": os.getenv("LLM_MODEL_QUESTION", "gpt-5-nano"),
    "report": os.getenv("LLM_MODEL_REPORT", "gpt-5.1"),
}

_llm_cache = {}


def get_llm(role: str = "default"):
    """
    역할별로 다른 모델을 선택하되, 인스턴스는 캐싱해 재사용한다.
    role:
        - "default": 기본 대화/노드용
        - "intro": 문제 인트로/오리엔테이션용
        - "hint": 힌트 전용
        - "question": 후속 질문 생성용
        - "report": 최종 리포트/평가용
    """
    key = (role or "default").strip() or "default"
    if key not in _llm_cache:
        model_name = MODEL_CONFIG.get(key, MODEL_CONFIG["default"])
        _llm_cache[key] = init_chat_model(model_name, api_key=API_KEY)
    return _llm_cache[key]


