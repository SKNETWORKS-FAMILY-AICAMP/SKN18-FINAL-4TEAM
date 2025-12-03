from __future__ import annotations

import json
from typing import List, Tuple

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

from interview_engine.state import InterviewState

DEFAULT_RUBRIC = (
    "가독성, 정확성, 안정성, 성능을 중심으로 요약·피드백하고, 실무적으로 바로 적용할 수 있는 개선안을 제시합니다."
)


def _parse_json_content(content: str) -> Tuple[str, List[str], float]:
    """LLM이 돌려준 JSON 문자열을 안전하게 파싱."""
    summary = ""
    feedback: List[str] = []
    score = 0.0
    try:
        payload = json.loads(content)
        summary = str(payload.get("summary", "")).strip()
        fb = payload.get("feedback", [])
        if isinstance(fb, list):
            feedback = [str(item).strip() for item in fb if str(item).strip()]
        score_val = payload.get("score", 0)
        try:
            score = float(score_val)
        except (TypeError, ValueError):
            score = 0.0
    except json.JSONDecodeError:
        # JSON 실패 시 상위 로직이 폴백 처리
        pass
    return summary, feedback, score


def code_quality_agent(state: InterviewState) -> InterviewState:
    """
    Step: 코드 품질 평가 Agent.

    기대 입력(state):
      - submitted_code / code: 평가할 코드 문자열
      - language: 언어명 (기본값 python)
      - code_quality_rubric: 사용자 정의 평가 기준 (옵션)

    설정 출력(state):
      - code_quality_summary: 1~2문장 요약
      - code_quality_feedback: 실행 가능한 짧은 피드백 리스트
      - code_quality_score: 0~1 스코어 (1이 최고)
      - code_quality_error: 실패 시 에러 메시지
    """
    source_code = (state.get("submitted_code") or state.get("code") or "").strip()
    language = (state.get("language") or "python").strip() or "python"
    rubric = (state.get("code_quality_rubric") or DEFAULT_RUBRIC).strip()

    if not source_code:
        state["code_quality_error"] = "평가할 코드가 없습니다."
        return state

    system_prompt = (
        "당신은 시니어 코드 리뷰어입니다. 결과는 반드시 JSON 한 덩어리로만 답변하세요. "
        "키는 summary(1~2문장), feedback(짧고 실행 가능한 항목 리스트), score(0~1, 1이 최고)입니다. "
        "장황한 말은 피하고 핵심 개선점을 제시하세요."
    )

    human_prompt = (
        f"Language: {language}\n"
        f"Rubric: {rubric}\n"
        "Code:\n"
        f"```{language}\n{source_code}\n```"
    )

    model = init_chat_model("gpt-5-nano")
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]

    try:
        response = model.invoke(messages)
        content = (getattr(response, "content", "") or "").strip()
        summary, feedback, score = _parse_json_content(content)

        # JSON 파싱 실패 시 전체 텍스트를 요약으로 사용
        if not summary and content:
            summary = content[:500]
        if not feedback and summary:
            feedback = [summary]

        state["code_quality_summary"] = summary
        state["code_quality_feedback"] = feedback
        state["code_quality_score"] = max(0.0, min(1.0, score))
        state.pop("code_quality_error", None)
        state["last_action"] = "code_quality_evaluated"
    except Exception as exc:  # noqa: BLE001
        state["code_quality_error"] = str(exc)

    return state
