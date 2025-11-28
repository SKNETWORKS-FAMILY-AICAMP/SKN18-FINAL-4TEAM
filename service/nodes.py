from dotenv import load_dotenv
load_dotenv()
import json

from service.state import InterviewState
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage
from service.prompt import (
    PROBLEM_INTRO_PROMPT, QUESTION_GEN_PROMPT, PROBLEM_SOLVING_PROMPT,
    SUPERVISOR_PROMPT, CODE_QUALITY_PROMPT, COLLAB_PROMPT
)

def _parse_res_content(res, state, error_key: str):
    """Helper to parse JSON from model response and set state error on failure."""
    try:
        return json.loads(res.content)
    except json.JSONDecodeError:
        state[error_key] = res.content
        return None

#################################
# 문제 설명 및 전략 질문 노드 
#################################
def problem_intro_and_strategy(state: InterviewState) -> InterviewState:
    llm_input = {
        "user_name": state["user_name"],
        "problem_description": state["problem_description"],
    }
    model = init_chat_model("gpt-5-nano")
    res = model.invoke([
        SystemMessage(content=PROBLEM_INTRO_PROMPT),
        HumanMessage(content=json.dumps(llm_input, ensure_ascii=False)),
    ])

    data = _parse_res_content(res, state, "problem_intro_error")
    if not data:
        return state

    smalltalk = data.get("smalltalk", "")
    intro = data.get("intro", "")
    strategy_question = data.get("strategy_question", "")

    # TTS로 읽어줄 전체 인트로 텍스트
    state["problem_intro_text"] = (smalltalk + "\n" + intro).strip()
    # 첫 번째 질문: 전략 질문
    state["current_question_text"] = strategy_question
    
    # 이제 "문제 설명 + 전략 질문까지 한 상태"
    state["phase"] = "strategy_intro"
    
    # human-in-the-loop: 이후 1분 동안 생각 시간 + 전략 답변은 사람(유저)이 채울 것
    state["await_human"] = {
        "type": "candidate_strategy_answer",
        "question": strategy_question
    }
    return state
###############################################


#################################
# Agent 호출 supervisor
#################################
def supervisor(state: InterviewState) -> InterviewState:
    mode = state.get("supervisor_mode", "none")
    if mode not in ("classify", "judge"):
        # 아무것도 안 할 턴                                                                          
        return state
    
    human_message_input = {
        "mode": mode,
        "problem_description": state["problem_description"],
        "latest_code": state.get("latest_code", ""),
        "qa_history_brief": state.get("qa_history_brief", ""),
        "initial_strategy_eval": state.get("initial_strategy_eval"),
        "step_num": state.get("step_num", 0),
        "question_text": state.get("current_question_text"),
        "user_answer": state.get("last_user_answer", None),
        "raw_eval": state.get("last_raw_eval", None),
    }
    
    model = init_chat_model("gpt-4.1")
    res = model.invoke([
        SystemMessage(content=SUPERVISOR_PROMPT),
        HumanMessage(content=json.dumps(human_message_input, ensure_ascii=False)),
    ])
    data = _parse_res_content(res, state, "supervisor_error")
    if not data:
        return state

    if mode == "classify":
        # eval_target -> current_focus에 저장
        eval_target = data.get("eval_target", "none")
        state["current_focus"] = eval_target if eval_target != "none" else None
        state["supervisor_reason"] = data.get("reason", "")
        state["supervisor_mode"] = "none"
        state["next_node"] = "generator_question" if state.get("current_focus") else None
    elif mode == "judge":
        state["last_judge_meta"] = {
            "is_consistent": data.get("is_consistent"),
            "adjusted": data.get("adjusted"),
            "adjust_reason": data.get("adjust_reason"),
        }
        state["last_final_eval"] = data.get("final_eval")
        state["supervisor_mode"] = "none"
        state["next_node"] = "qa_summary"

    return state

##########################
# 
#############################
def qa_summary(state: InterviewState) -> InterviewState:
    """
    한 턴의 평가가 끝난 후:
    - qa_history에 현재 턴 기록 추가
    - qa_history_brief 업데이트 (지금은 간단히 누적)
    - 다음 턴을 위해 state 초기화
    """
    final_eval = state.get("last_final_eval")
    focus = state.get("current_focus")
    question_text = state.get("current_question_text")
    user_answer = state.get("last_user_answer", "")
    finishing = state.get("event_payload", {}).get("finalizing", False)

    if final_eval and focus and question_text:
        turn_id = len(state.get("qa_history", []))

        record = {
            "turn_id": turn_id,
            "focus": focus,
            "question_text": question_text,
            "user_answer": user_answer,
            "final_eval": final_eval,
        }

        state.setdefault("qa_history", []).append(record)

        # 간단한 텍스트 누적 방식
        brief = state.get("qa_history_brief", "")
        state["qa_history_brief"] = brief + f"\n[{focus}] {question_text}"

    # 턴 마무리 초기화
    state["current_question_text"] = None
    state["current_focus"] = None
    state["waiting_for_answer"] = False
    state["last_raw_eval"] = None
    state["last_final_eval"] = None
    state["phase"] = "live_loop"
    state["event_type"] = "none"
    state["event_payload"] = {}
    state["next_node"] = None

    # 다음 질문이 필요하면 supervisor를 다시 호출
    state["supervisor_mode"] = "classify" if not finishing else "none"

    return state

##############################################

################################################
#
######################################################
def _run_eval_node(state: InterviewState, system_prompt: str, error_key: str) -> InterviewState:
    """Common body for eval_* nodes."""
    model = init_chat_model("gpt-4.1")

    user_answer = state.get("event_payload", {}).get("answer_text", "")
    state["last_user_answer"] = user_answer

    payload = {
        "problem_description": state["problem_description"],
        "question_text": state.get("current_question_text"),
        "user_answer": user_answer,
        "latest_code": state.get("latest_code", ""),
        "qa_history_brief": state.get("qa_history_brief", ""),
        "step_num": state.get("step_num", 0),
    }

    res = model.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=json.dumps(payload, ensure_ascii=False)),
    ])
    raw_eval = _parse_res_content(res, state, error_key)
    if not raw_eval:
        return state

    state["last_raw_eval"] = raw_eval
    state["supervisor_mode"] = "judge"
    return state

def eval_code_quality(state: InterviewState) -> InterviewState:
    return _run_eval_node(state, CODE_QUALITY_PROMPT, "eval_code_quality_error")

def eval_collaboration(state: InterviewState) -> InterviewState:
    return _run_eval_node(state, COLLAB_PROMPT, "eval_collaboration_error")

def eval_problem_solving(state: InterviewState) -> InterviewState:
    return _run_eval_node(state, PROBLEM_SOLVING_PROMPT, "eval_problem_solving_error")

def generator_question(state: InterviewState) -> InterviewState:
    """
    QuestionGenerator 프롬프트 기반으로 질문을 생성하고
    그 질문을 state["current_question_text"]에 저장한다.
    """
    model = init_chat_model("gpt-4.1")

    payload = {
        "problem_description": state["problem_description"],
        "latest_code": state.get("latest_code", ""),
        "qa_history_brief": state.get("qa_history_brief", ""),
        "initial_strategy_eval": state.get("initial_strategy_eval"),
        "step_num": state.get("step_num", 0),
        "focus": state.get("current_focus"),
        "language": "ko",
    }

    res = model.invoke([
        SystemMessage(content=QUESTION_GEN_PROMPT),
        HumanMessage(content=json.dumps(payload, ensure_ascii=False)),
    ])

    data = _parse_res_content(res, state, "generator_error")
    if not data:
        return state

    # 프롬프트 규칙:
    # {
    #   "question_text": "...",
    #   "reason": "..."
    # }

    question_text = data.get("question_text")
    if question_text:
        state["current_question_text"] = question_text
        state["waiting_for_answer"] = True
        state["step_num"] += 1
        state["phase"] = "live_loop"
        state["await_human"] = {
            "type": "candidate_answer",
            "question": question_text,
            "focus": state.get("current_focus"),
        }

    state["question_gen_reason"] = data.get("reason", "")

    return state