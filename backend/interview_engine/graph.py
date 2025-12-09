from langgraph.graph import StateGraph, END
from backend.interview_engine.state import IntroState
from interview_engine.nodes.problem_intro_node import problem_intro_agent
from interview_engine.nodes.problem_answer_node import problem_answer_agent
from interview_engine.nodes.hint_node import hint_agent
from interview_engine.nodes.question_generation_node import question_generation_agent
from interview_engine.nodes.answer_classify import answer_classify_agent
from interview_engine.nodes.problem_solving_eval_node import problem_solving_eval_agent
from backend.interview_engine.conditional_edges import chap1_main_condition, chap1_answer_route
from interview_engine.nodes.code_quality_collabo_node import collaboration_eval_agent


def create_chapter1_graph_flow(checkpointer=None):
    graph = StateGraph(IntroState)

    # chapter 1: Intro
    graph.add_node("condition",lambda s:s),
    graph.add_node("problem_intro_agent",problem_intro_agent)
    graph.add_node("problem_answer_agent",problem_answer_agent)
    graph.add_node("answer_classify_agent",answer_classify_agent)
    
    graph.set_entry_point("condition")
    graph.add_conditional_edges(
        "condition",
        chap1_main_condition,
        {
        "problem_intro_agent": "problem_intro_agent",
        "answer_classify_agent": "answer_classify_agent",
        "idle": END,  # 기본값 처리
        })
    graph.add_edge("problem_intro_agent", END)
    graph.add_conditional_edges(
        "answer_classify_agent",
        chap1_answer_route,
        {
            "finish": END,
            "problem_answer": "problem_answer_agent",
        })
    graph.add_edge("problem_answer_agent", END)
    
    return graph.compile(checkpointer=checkpointer)

def create_chapter2_graph_flow(checkpointer=None):
    pass

def create_chapter3_graph_flow(checkpointer=None):
    pass


# STT 판단
# - 3가지 경우의 수
# 1. 다시 대답해주세요
# 2. 정답
# 3. 질문인경우