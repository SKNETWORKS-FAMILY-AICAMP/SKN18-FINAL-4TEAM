from langgraph.graph import StateGraph, END
from interview_engine.state import IntroState, InterviewState, CodingState
from interview_engine.nodes.problem_intro_node import problem_intro_agent
from interview_engine.nodes.problem_answer_node import problem_answer_agent
from interview_engine.nodes.answer_classify import answer_classify_agent
from interview_engine.conditional_edges import chap1_main_condition, chap1_answer_route
from interview_engine.nodes.hint_node import hint_agent
from interview_engine.nodes.code_quality_collabo_node import code_quality_collabo_agent
from interview_engine.nodes.question_generate_node import question_generation_agent
from interview_engine.nodes.coding_intro_node import coding_stage_intro_agent
from interview_engine.nodes.coding_answer_feedback_node import (
    coding_answer_feedback_agent,
)


def create_chapter1_graph_flow(checkpointer=None):
    graph = StateGraph(IntroState)

    # chapter 1: Intro
    graph.add_node("problem_intro_agent", problem_intro_agent)
    graph.add_node("problem_answer_agent", problem_answer_agent)
    graph.add_node("answer_classify_agent", answer_classify_agent)

    graph.set_conditional_entry_point(chap1_main_condition)
    graph.add_edge("problem_intro_agent", END)
    graph.add_conditional_edges(
        "answer_classify_agent",
        chap1_answer_route,
        {
            "finish": END,
            "problem_answer_agent": "problem_answer_agent",
        },
    )
    graph.add_edge("problem_answer_agent", END)

    return graph.compile(checkpointer=checkpointer)


def create_chapter2_graph_flow(checkpointer=None):
    """
    coding stage 전용 그래프.
    - coding_stage_intro_agent: 코딩 스테이지 진입 안내 멘트(TTS용)
    - code_quality_collabo_agent: Ruff 실행 → 코드 품질/협업 피드백 채움
    - question_generation_agent: 피드백/코드/진행상황을 보고 질문 생성 (또는 스킵)
    - coding_answer_feedback_agent: 질문에 대한 사용자의 답변에 짧게 반응하는 멘트 생성

    event_type에 따라 엔트리 노드가 달라진다.
      - event_type == "coding_intro"    → coding_intro → END
      - event_type == "question_answer" → coding_answer_feedback → END
      - 그 외                            → code_quality_collabo → question_generate → END
    """
    graph = StateGraph(CodingState)

    # entry 분기 함수
    def chap2_entry_condition(state: CodingState) -> str:
        event_type = (state.get("event_type") or "").strip()
        if event_type == "coding_intro":
            return "coding_intro"
        if event_type == "question_answer":
            return "coding_answer_feedback"
        return "code_quality_collabo"

    graph.add_node("coding_intro", coding_stage_intro_agent)
    graph.add_node("coding_answer_feedback", coding_answer_feedback_agent)
    graph.add_node("code_quality_collabo", code_quality_collabo_agent)
    graph.add_node("question_generate", question_generation_agent)

    graph.set_conditional_entry_point(chap2_entry_condition)

    graph.add_edge("coding_intro", END)
    graph.add_edge("coding_answer_feedback", END)
    graph.add_edge("code_quality_collabo", "question_generate")
    graph.add_edge("question_generate", END)

    return graph.compile(checkpointer=checkpointer)

def create_chapter2_graph_flow(checkpointer=None):
    graph = StateGraph(InterviewState)

    # chapter 2: Hint
    graph.add_node("hint_agent",hint_agent)
    graph.set_entry_point("hint_agent")
    
    return graph.compile(checkpointer=checkpointer)
