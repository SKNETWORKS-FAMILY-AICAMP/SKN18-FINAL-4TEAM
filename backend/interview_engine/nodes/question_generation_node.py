from __future__ import annotations

from typing import List, Tuple

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

from interview_engine.state import InterviewState


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


def question_generation_agent(state: InterviewState) -> InterviewState:
    """
    Step: 코드 품질 평가 결과 기반 후속 질문 생성 Agent.

    기대 입력(state):
      - code_quality_summary: str         # 코드 품질 요약 (1~2문장)
      - code_quality_feedback: List[str]  # 개선 피드백 리스트
      - code_quality_score: float         # 0~1 (선택)
      - language: str                     # 코드 언어 (예: python)

    설정 출력(state):
      - code_quality_questions: List[str] # 면접관이 물어볼 후속 질문 리스트
      - tts_text: str                     # TTS로 바로 읽을 대표 질문(일단 첫 번째 질문)
      - question_generation_error: str    # 실패 시 에러 메시지
      - last_action: str                  # "code_quality_questions_generated"
    """

    summary: str = (state.get("code_quality_summary") or "").strip()
    feedback: List[str] = state.get("code_quality_feedback") or []
    score = float(state.get("code_quality_score") or 0.0)
    language = (state.get("language") or "python").strip() or "python"

    # 코드가 없어서 품질 평가도 안 된 경우
    if not feedback and not summary:
        state["question_generation_error"] = "코드 품질 평가 결과가 없어서 질문을 생성할 수 없습니다."
        # 그래도 완전 빈 상태로 두기보다는, 아주 일반적인 질문 하나 넣어준다.
        generic_q = "현재 작성하신 코드에서 본인이 가장 개선하고 싶은 부분은 어디인가요?"
        state["code_quality_questions"] = [generic_q]
        state["tts_text"] = generic_q
        return state

    # 시스템 프롬프트: 반드시 JSON으로만 답하게 강하게 명시
    system_prompt = (
        "당신은 실무 경험이 풍부한 시니어 개발자이자 면접관입니다. "
        "입력으로 주어지는 코드 품질 요약과 피드백을 바탕으로, "
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

    # 사람 프롬프트: 코드 품질 결과를 그대로 넘겨줌
    feedback_block = "\n".join(f"- {line}" for line in feedback)

    human_prompt = (
        f"코드 언어: {language}\n"
        f"품질 점수(0~1): {score:.2f}\n\n"
        f"[코드 품질 요약]\n{summary or '(요약 없음)'}\n\n"
        f"[세부 피드백]\n{feedback_block or '(피드백 없음)'}\n\n"
        "위 정보를 바탕으로, 지원자의 코드에 대해 후속 질문 1~3개를 생성하세요.\n"
        "- 질문은 개선이 필요한 부분(가독성, 구조, 성능, 안정성 등)을 자연스럽게 짚어야 합니다.\n"
        "- 예를 들어, '이 부분의 변수 이름을 이렇게 정한 이유가 있나요?' 와 같이 맥락이 드러나야 합니다.\n"
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
            # 전체 텍스트에서 한 줄짜리 질문으로 폴백
            fallback_q = (
                "현재 코드에서 가장 크게 개선이 필요하다고 생각되는 부분은 무엇이며, "
                "어떻게 리팩터링할 수 있을지 설명해 주시겠어요?"
            )
            questions = [fallback_q]

        # state 업데이트
        state["code_quality_questions"] = questions
        # TTS로 읽을 대표 질문은 첫 번째로 지정
        state["tts_text"] = questions[0]
        state.pop("question_generation_error", None)
        state["last_action"] = "code_quality_questions_generated"

    except Exception as exc:  # noqa: BLE001
        err_msg = f"질문 생성 중 오류가 발생했습니다: {exc}"
        state["question_generation_error"] = err_msg
        # 그래도 완전히 비우지 말고 generic 질문 하나 넣어줌
        fallback_q = "현재 작성하신 코드에서 본인이 가장 개선하고 싶은 부분은 어디인가요?"
        state["code_quality_questions"] = [fallback_q]
        state["tts_text"] = fallback_q

    return state