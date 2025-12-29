import json
import ast
import difflib
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage

from interview_engine.llm import get_llm
from interview_engine.state import CodingState


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


def _compute_change_metrics(prev_code: str, current_code: str, language: str) -> dict:
    """
    이전 코드와 현재 코드의 변화량을 추정하기 위한 간단한 휴리스틱.
    - 라인 단위 diff (difflib.SequenceMatcher)
    - 문자 단위 유사도 기반 편집 거리 근사
    - (python 한정) AST 구조 변화량

    반환값 예:
      {
        "line_change": 0.0~1.0,
        "char_change": 0.0~1.0,
        "ast_change":  0.0~1.0,
        "score":       0.0~1.0,   # 가중 평균
      }
    """
    prev_norm = _normalize_code_for_compare(prev_code)
    curr_norm = _normalize_code_for_compare(current_code)

    # 1) 라인 단위 변화량 (1 - similarity)
    prev_lines = prev_norm.splitlines()
    curr_lines = curr_norm.splitlines()
    if prev_lines or curr_lines:
        line_sim = difflib.SequenceMatcher(None, prev_lines, curr_lines).ratio()
        line_change = 1.0 - line_sim
    else:
        line_change = 0.0

    # 2) 문자 단위 변화량 (1 - similarity)
    if prev_norm or curr_norm:
        char_sim = difflib.SequenceMatcher(None, prev_norm, curr_norm).ratio()
        char_change = 1.0 - char_sim
    else:
        char_change = 0.0

    # 3) AST 구조 변화량 (python 계열 언어에 대해서만)
    ast_change = 0.0
    lang_lower = (language or "").lower()
    is_python = any(k in lang_lower for k in ("python", "py"))
    if is_python:
        try:
            prev_ast = ast.parse(prev_norm)
            curr_ast = ast.parse(curr_norm)
            prev_dump = ast.dump(prev_ast)
            curr_dump = ast.dump(curr_ast)
            if prev_dump or curr_dump:
                ast_sim = difflib.SequenceMatcher(None, prev_dump, curr_dump).ratio()
                ast_change = 1.0 - ast_sim
        except Exception:
            # 파싱 실패 시 AST 변화량은 사용하지 않음
            ast_change = 0.0

    # 가중 평균 스코어 (라인 0.4, 문자 0.3, AST 0.3)
    score = (
        0.4 * line_change +
        0.3 * char_change +
        0.3 * ast_change
    )

    return {
        "line_change": line_change,
        "char_change": char_change,
        "ast_change": ast_change,
        "score": score,
    }


def question_generation_agent(state: CodingState) -> CodingState:
    """
    Step: 현재 코드 + Ruff 피드백을 기반으로
    코딩 단계에서 후속 질문을 생성하는 Agent.

    CodingState 기준 기대 입력(state):
      - code: str                         # 현재 코드 스냅샷
      - starter_code: str                 # 초기 starter code (있다면)
      - prev_code: str                    # 이전 질문 시점의 코드 (없을 수도 있음)
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
    last_question_text = (state.get("last_question_text") or "").strip()
    language = (state.get("language") or "python").strip() or "python"
    existing_questions = state.get("question") or []
    if not isinstance(existing_questions, list):
        existing_questions = [str(existing_questions)] if str(existing_questions) else []
            
    norm_current = _normalize_code_for_compare(current_code)
    norm_prev = _normalize_code_for_compare(prev_code)
    norm_starter = _normalize_code_for_compare(starter_code)

    # 1) 아직 starter code에서 크게 벗어나지 않았다면(거의 손대지 않은 상태) 질문 스킵
    is_starter_only = norm_starter == norm_current

    # 2) 라인/문자/AST 기반으로 코드 변화량을 계산하고,
    #    변화량이 아주 작으면 "실질적인 진행 없음"으로 간주
    #    - 이전 질문이 없다면 starter_code 기준으로 비교
    baseline_code = prev_code if norm_prev else starter_code
    change_metrics = _compute_change_metrics(baseline_code, current_code, language)
    change_score = change_metrics.get("score", 0.0)

    NO_PROGRESS_THRESHOLD = 0.2  # 0~1 사이, 거의 변화가 없는 수준

    # 코드 변화량 점수가 너무 낮으면 "진행 없음"으로 간주
    baseline_norm = norm_prev if norm_prev else norm_starter
    
    no_progress = change_score < NO_PROGRESS_THRESHOLD and bool(baseline_norm)

    if no_progress or is_starter_only:
        state["tts_text"] = ""
        return state

    system_prompt = (
        "당신은 실무 경험이 풍부한 시니어 개발자이자 면접관입니다. "
        "입력으로 주어지는 현재 코드와 Ruff 기반 코드 품질/협업 피드백을 바탕으로, "
        "지원자에게 던질 후속 질문들을 만듭니다.\n\n"
        "규칙:\n"
        "1) 반드시 JSON 한 덩어리로만 답변하세요.\n"
        "2) 최상위 키는 question 이어야 합니다.\n"
        "3) question 값은 문자열 이여야 합니다.\n"
        '   예: {\"question\": "질문"}\n'
        "4) 질문은 한국어로 작성하고, 구체적이고 실행 가능한 대화를 유도해야 합니다.\n"
        "5) 답변(solution)을 주지 말고, '왜 그렇게 작성했는지', '어떻게 개선할 수 있는지'를 묻는 형식으로 만드세요.\n"
        "6) 질문은 한두 문장 이내로 짧게 유지하세요."
    )

    # 사람 프롬프트: 코드 + 코드 품질 결과를 함께 넘겨줌
    # (feedback, collab_lines는 code_quality_collabo_agent에서 채워진 값을 사용)
    raw_quality = state.get("code_quality_feedback") or []
    raw_collab = state.get("collaboration_feedback") or []

    human_prompt = (
        f"코드 언어: {language}\n"
        f"[현재 전체 코드]\n{norm_current}\n\n"
        f"[코드 품질 피드백]\n{raw_quality}\n\n"
        f"[협업/스타일 피드백]\n{raw_collab}\n\n"
        f"[이전 질문]\n{last_question_text}\n\n"
        "위 정보를 바탕으로, 지원자의 코드에 대해 후속 질문 1개를 생성하세요.\n"
        "- ruff 피드백에 대해선 언급하지 않고 참고만 합니다."
        "- 질문은 개선이 필요한 부분(가독성, 구조, 성능, 안정성 등)을 자연스럽게 짚어야 합니다.\n"
        "- 예를 들어, '이 부분의 변수 이름을 이렇게 정한 이유가 있나요?' 와 같이 맥락이 드러나야 합니다.\n"
        "- 이전에 물어본 것과 최대한 중복되지 않도록, 코드와 피드백에서 새롭게 눈에 띄는 부분을 중심으로 질문하세요.\n"
        "- 질문은 반드시 JSON 포맷으로만 반환해야 한다는 규칙을 지켜주세요."
    )

    model = get_llm("question")
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]

    existing_questions = state.get("question") or []
    if not isinstance(existing_questions, list):
        existing_questions = [str(existing_questions)] if str(existing_questions) else []
    state["question"] = existing_questions

    try:
        print("[LLM][question_generation_agent] system_prompt:", system_prompt, flush=True)
        print("[LLM][question_generation_agent] human_prompt:", human_prompt, flush=True)
        response = model.invoke(messages)
        raw_content = (getattr(response, "content", "") or "").strip()

        # LLM이 반환한 JSON 문자열 파싱
        try:
            data = json.loads(raw_content)
        except Exception:
            # 일부 모델은 앞뒤에 설명 텍스트가 붙을 수 있으므로
            # 가장 처음 나오는 '{'부터 마지막 '}'까지를 잘라 다시 시도
            start = raw_content.find("{")
            end = raw_content.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    data = json.loads(raw_content[start : end + 1])
                except Exception:
                    data = {}
            else:
                data = {}

        question_text = ""
        if isinstance(data, dict):
            question_text = (data.get("question") or "").strip()

        if not question_text:
            # JSON 파싱이 되지 않거나 question 필드가 비어 있으면 스킵 처리
            state["question"] = existing_questions
            state["tts_text"] = ""
            state["question_skip_reason"] = "llm_invalid_or_empty_json"
            return state


        existing_questions.append(question_text)
        state["question"] = existing_questions
        state["tts_text"] = question_text

    except Exception:
        # 에러 시에는 질문을 생성하지 않고 스킵 처리
        state["question"] = existing_questions
        state["tts_text"] = ""
        state["question_skip_reason"] = "llm_error"

    return state
