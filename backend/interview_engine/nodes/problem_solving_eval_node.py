import json
from typing import Any, Dict, List

from interview_engine.state import InterviewState
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage


def _format_problem_context(problem_data: Any, problem_description: str = "") -> str:
    """
    문제 정보를 문자열로 정리한다. state에는 문자열/딕셔너리 둘 다 올 수 있으므로 유연하게 처리.
    """
    if problem_description:
        return f"문제 설명: {problem_description}"

    if isinstance(problem_data, dict):
        title = problem_data.get("title") or problem_data.get("problem") or "제목 없음"
        desc = problem_data.get("description") or problem_data.get("problem") or "설명 없음"
        constraints = problem_data.get("constraints") or problem_data.get("category") or "제약조건 정보 없음"
        examples = problem_data.get("io_examples")
        if not examples and isinstance(problem_data.get("test_cases"), list):
            # test_case 포맷을 간단히 요약
            tc_list: List[Dict[str, Any]] = problem_data["test_cases"]
            preview = tc_list[:2]
            examples = "\n".join(
                f"- input: {tc.get('input') or tc.get('input_data')}, output: {tc.get('output') or tc.get('output_data')}"
                for tc in preview
            )
        return (
            f"제목: {title}\n"
            f"설명: {desc}\n"
            f"제약조건/카테고리: {constraints}\n"
            f"예시: {examples or '예시 정보 없음'}"
        )

    if isinstance(problem_data, str) and problem_data.strip():
        return f"문제 설명: {problem_data}"

    return "문제 정보 없음"


def _stringify_history(history: Any) -> str:
    """
    대화 기록을 사람이 읽기 좋은 문자열로 변환.
    """
    if isinstance(history, str):
        return history

    if isinstance(history, list):
        lines: List[str] = []
        for item in history:
            role = ""
            content = ""
            if isinstance(item, dict):
                role = item.get("role") or item.get("sender") or item.get("type") or "unknown"
                content = item.get("content") or item.get("message") or ""
            else:
                role = getattr(item, "role", "unknown")
                content = getattr(item, "content", str(item))
            line = f"{role}: {content}".strip()
            if line:
                lines.append(line)
        return "\n".join(lines)

    return ""


def problem_solving_eval_agent(state: InterviewState) -> InterviewState:
    """
    Step 3: 문제 해결력 평가 에이전트

    사용 state 필드 (프로젝트 기준):
      - problem_description 또는 problem_data: 문제 설명/정보
      - current_user_code (fallback: final_user_code): 사용자가 작성한 코드
      - conversation_history: (선택) 인터뷰 대화 기록

    결과:
      - problem_solving_result: JSON 평가 결과
      - last_action: "problem_solving_evaluated"
    """

    problem_data = state.get("problem_data") or {}
    problem_description = state.get("problem_description", "")
    user_code = state.get("current_user_code") or state.get("final_user_code", "")
    history = state.get("conversation_history", [])

    problem_context = _format_problem_context(problem_data, problem_description)
    conversation_text = _stringify_history(history)

    system_prompt = (
        "당신은 시니어 테크니컬 인터뷰어이자 알고리즘 평가 전문가입니다.\n"
        "지원자의 코드와 대화 기록을 바탕으로 문제 해결 역량을 평가하고, 아래 JSON 형식으로만 응답하세요.\n\n"
        "[채점 기준표]\n"
        "- 90~100점: 완벽한 솔루션 (최적의 효율성 + 깔끔한 코드 + 논리적 설명)\n"
        "- 70~89점: 정답이지만 개선 여지(효율성 등)가 있거나, 설명이 다소 부족함\n"
        "- 40~69점: 정답은 맞췄으나 비효율적이거나, 힌트 의존도가 높음\n"
        "- 0~39점: 미완성 코드, 실행 불가, 또는 문제 이해 실패\n"
        "위 기준에 맞춰 냉정하게 점수를 매기세요.\n\n"
        "{\n"
        '  \"score\": 0~100 사이의 정수 점수,\n'
        '  \"algorithm_analysis\": \"시간/공간 복잡도 분석 및 선택한 알고리즘 설명\",\n'
        '  \"process_evaluation\": \"대화 흐름과 접근 방식을 바탕으로 한 평가\",\n'
        '  \"strengths\": [\"잘한 점 1\", \"잘한 점 2\"],\n'
        '  \"weaknesses\": [\"아쉬운 점 1\", \"아쉬운 점 2\"]\n'
        "}"
    )

    human_prompt = (
        f"[문제 정보]\n{problem_context}\n\n"
        f"[사용자 코드]\n{user_code or '코드가 비어 있습니다.'}\n\n"
        f"[대화 기록]\n{conversation_text or '대화 기록이 없습니다.'}\n\n"
        "위 정보를 바탕으로 JSON만 응답해 주세요."
    )

    model = init_chat_model("gpt-4o")
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ]

    try:
        response = model.invoke(messages)
        content = (getattr(response, "content", "") or "").strip()

        # 코드 펜스 제거
        if content.startswith("```json"):
            content = content.removeprefix("```json").removesuffix("```").strip()
        elif content.startswith("```"):
            content = content.removeprefix("```").removesuffix("```").strip()

        eval_data = json.loads(content)
        state["problem_solving_result"] = eval_data
        state["last_action"] = "problem_solving_evaluated"
    except json.JSONDecodeError:
        state["problem_solving_result"] = {
            "score": 0,
            "algorithm_analysis": "평가 결과를 JSON으로 파싱하는 데 실패했습니다.",
            "process_evaluation": "",
            "strengths": [],
            "weaknesses": [],
            "error": "JSON_PARSE_ERROR",
        }
    except Exception as e:
        state["problem_solving_result"] = {
            "score": 0,
            "algorithm_analysis": f"시스템 오류: {e}",
            "process_evaluation": "",
            "strengths": [],
            "weaknesses": [],
        }

    return state
