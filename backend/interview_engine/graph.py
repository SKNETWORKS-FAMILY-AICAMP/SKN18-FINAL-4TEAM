from langgraph.graph import StateGraph, END
from interview_engine.state import IntroState
from interview_engine.nodes.problem_intro_node import problem_intro_agent
from interview_engine.nodes.problem_answer_node import problem_answer_agent
from interview_engine.nodes.answer_classify import answer_classify_agent
from interview_engine.conditional_edges import chap1_main_condition, chap1_answer_route



def create_chapter1_graph_flow(checkpointer=None):
    graph = StateGraph(IntroState)

    # chapter 1: Intro
    graph.add_node("problem_intro_agent",problem_intro_agent)
    graph.add_node("problem_answer_agent",problem_answer_agent)
    graph.add_node("answer_classify_agent",answer_classify_agent)

    graph.set_conditional_entry_point(chap1_main_condition)
    graph.add_edge("problem_intro_agent", END)
    graph.add_conditional_edges(
        "answer_classify_agent",
        chap1_answer_route,
        {
            "finish": END,
            "problem_answer_agent": "problem_answer_agent",
        })
    graph.add_edge("problem_answer_agent", END)
    
    return graph.compile(checkpointer=checkpointer)
