from __future__ import annotations

from typing import List

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

from interview_engine.state import CodingState


def _parse_questions_content(content: str) -> List[str]:
    """
    LLM이 돌려준 JSON 문자열에서 questions 리스트만 안전하게 파싱.
    기대 포맷:
      {
        "questions": ["...", "..."]
      }
    """
    import json

    questions: List[str] = []
    try:
        payload = json.loads(content)
        q = payload.get("questions", [])
        if isinstance(q, list):
            questions = [str(item).strip() for item in q if str(item).strip()]
    except json.JSONDecodeError:
        # JSON 파싱 실패 시 상위 로직에서 폴백
        pass
    return questions


def _normalize_code_for_compare(code: str) -> str:
    """
    코드 비교용 정규화:
    - 앞뒤 공백 제거
    - 각 줄의 우측 공백 제거
    """
    if not code:
        return ""
    lines = [line.rstrip() for line in str(code).splitlines()]
    return "\n".join(lines).strip()


def question_generation_agent(state: CodingState) -> CodingState:
    """
    Step: 현재 코드 + Ruff 피드백을 기반으로
    코딩 단계에서 후속 질문을 생성하는 Agent.

    CodingState 기준 기대 입력(state):
      - code: str                         # 현재 코드 스냅샷
      - starter_code: str                 # 초기 starter code (있다면)
      - prev_code: str                    # 이전 질문 시점의 코드 (없을 수도 있음)
      - snapshot_index: int               # 현재 코드 스냅샷 인덱스(1부터)
      - last_snapshot_index: int          # 마지막 질문이었던 스냅샷 인덱스(0이면 없음)
      - language: str                     # 코드 언어 (예: python)
      - code_quality_feedback: List[str]  # Ruff 기반 코드 품질 피드백
      - collaboration_feedback: List[str] # 협업 관점 피드백
      - question_cnt: int                 # 지금까지 물어본 질문 수 (0~3)

    설정 출력(state):
      - question: str                     # 대표 질문 한 줄 (TTS용, 없으면 빈 문자열)
      - tts_text: str                     # question과 동일하게 세팅 (호환용)
      - question_skip_reason: str         # 질문을 생성하지 않은 이유(옵션)
    """
    current_code = (state.get("code") or "").strip()
    starter_code = (state.get("starter_code") or "").strip()
    prev_code = (state.get("prev_code") or "").strip()
    snapshot_index = int(state.get("snapshot_index") or 0)
    last_snapshot_index = int(state.get("last_snapshot_index") or 0)
    question_cnt = int(state.get("question_cnt") or 0)
    last_question_text = (state.get("last_question_text") or "").strip()

    norm_current = _normalize_code_for_compare(current_code)
    norm_prev = _normalize_code_for_compare(prev_code)
    norm_starter = _normalize_code_for_compare(starter_code)

    # 1) 이전 질문 이후 코드 변화가 거의 없다면 질문 생성을 스킵
    no_progress = False
    if last_snapshot_index and snapshot_index and snapshot_index <= last_snapshot_index:
        no_progress = True
    elif norm_prev and norm_prev == norm_current:
        no_progress = True

    # 2) 아직 starter code에서 크게 벗어나지 않았다면(거의 손대지 않은 상태) 질문 스킵
    is_starter_only = bool(norm_starter) and norm_starter == norm_current

    if no_progress or is_starter_only:
        state["question"] = ""
        state["tts_text"] = ""
        reason_parts = []
        if no_progress:
            reason_parts.append("no_progress_since_last_question")
        if is_starter_only:
            reason_parts.append("starter_code_only")
        state["question_skip_reason"] = ",".join(reason_parts) or "no_progress"
        return state

    # code_quality_feedback는 리스트 또는 문자열일 수 있으므로 정규화
    raw_feedback = state.get("code_quality_feedback") or []
    feedback: List[str]
    if isinstance(raw_feedback, str):
        feedback = [raw_feedback] if raw_feedback.strip() else []
    elif isinstance(raw_feedback, list):
        feedback = [str(x).strip() for x in raw_feedback if str(x).strip()]
    else:
        feedback = []

    # 협업 피드백도 있으면 함께 프롬프트에 포함
    raw_collab = state.get("collaboration_feedback") or []
    collab_lines: List[str]
    if isinstance(raw_collab, str):
        collab_lines = [raw_collab] if raw_collab.strip() else []
    elif isinstance(raw_collab, list):
        collab_lines = [str(x).strip() for x in raw_collab if str(x).strip()]
    else:
        collab_lines = []

    language = (state.get("language") or "python").strip() or "python"

    # 시스템 프롬프트: 반드시 JSON으로만 답하게 강하게 명시
    system_prompt = (
        "당신은 실무 경험이 풍부한 시니어 개발자이자 면접관입니다. "
        "입력으로 주어지는 현재 코드와 Ruff 기반 코드 품질/협업 피드백을 바탕으로, "
        "지원자에게 던질 후속 질문들을 만듭니다.\n\n"
        "규칙:\n"
        "1) 반드시 JSON 한 덩어리로만 답변하세요.\n"
        "2) 최상위 키는 questions 이어야 합니다.\n"
        "3) questions 값은 문자열 리스트(List[str])여야 합니다.\n"
        '   예: {\"questions\": [\"첫 번째 질문\", \"두 번째 질문\"]}\n'
        "4) 질문은 한국어로 작성하고, 구체적이고 실행 가능한 대화를 유도해야 합니다.\n"
        "5) 답변(solution)을 주지 말고, '왜 그렇게 작성했는지', '어떻게 개선할 수 있는지'를 묻는 형식으로 만드세요.\n"
        "6) 각 질문은 한두 문장 이내로 짧게 유지하세요."
    )

    # 사람 프롬프트: 코드 + 코드 품질 결과를 함께 넘겨줌
    feedback_block = "\n".join(f"- {line}" for line in feedback) or "(피드백 없음)"
    collab_block = "\n".join(f"- {line}" for line in collab_lines) or "(피드백 없음)"

    # 코드 전체를 다 넘기면 토큰이 길어질 수 있으니 앞부분만 잘라서 제공
    MAX_CODE_CHARS = 2000
    code_snippet = norm_current[:MAX_CODE_CHARS]

    human_prompt = (
        f"코드 언어: {language}\n"
        f"현재 질문 번호(0부터 시작): {question_cnt}\n"
        f"[현재 코드 스니펫]\n{code_snippet}\n\n"
        f"[코드 품질 피드백]\n{feedback_block}\n\n"
        f"[협업/스타일 피드백]\n{collab_block}\n\n"
        "위 정보를 바탕으로, 지원자의 코드에 대해 후속 질문 1개를 생성하세요.\n"
        "- 질문은 개선이 필요한 부분(가독성, 구조, 성능, 안정성 등)을 자연스럽게 짚어야 합니다.\n"
        "- 예를 들어, '이 부분의 변수 이름을 이렇게 정한 이유가 있나요?' 와 같이 맥락이 드러나야 합니다.\n"
        "- 이전에 물어본 것과 최대한 중복되지 않도록, 코드와 피드백에서 새롭게 눈에 띄는 부분을 중심으로 질문하세요.\n"
        "- 질문은 반드시 JSON 포맷으로만 반환해야 한다는 규칙을 지켜주세요."
    )

    model = init_chat_model("gpt-5-nano")
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]

    try:
        response = model.invoke(messages)
        content = (getattr(response, "content", "") or "").strip()

        questions = _parse_questions_content(content)

        # JSON 파싱 실패 or 질문 비어 있으면 폴백
        if not questions:
            fallback_q = (
                "현재 코드에서 가장 크게 개선이 필요하다고 생각되는 부분은 무엇이며, "
                "어떻게 리팩터링할 수 있을지 설명해 주시겠어요?"
            )
            questions = [fallback_q]

        # 이전 질문과 다른 문장을 우선적으로 선택
        def _norm_q(q: str) -> str:
            return " ".join((q or "").split())

        norm_last = _norm_q(last_question_text)
        chosen = None
        for q in questions:
            if _norm_q(q) != norm_last:
                chosen = q
                break

        # 모든 후보가 이전 질문과 동일하면 질문을 스킵
        if chosen is None and norm_last:
            state["question"] = ""
            state["tts_text"] = ""
            state["question_skip_reason"] = "duplicate_with_last_question"
            return state

        main_q = chosen or questions[0]
        state["question"] = main_q
        state["tts_text"] = main_q

    except Exception:
        # 에러 시에는 질문을 생성하지 않고 스킵 처리
        state["question"] = ""
        state["tts_text"] = ""
        state["question_skip_reason"] = "llm_error"

    return state
