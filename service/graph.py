from langgraph.graph import StateGraph, END
from service.state import InterviewState
from service.conditional_edges import route_main_loop, route_from_supervisor
from service.nodes import (
    problem_intro_and_strategy,
    generator_question,
    eval_problem_solving,
    eval_collaboration,
    eval_code_quality,
    supervisor,
    qa_summary,
)

def main_loop(state: InterviewState) -> InterviewState:
    # 그냥 state 그대로 리턴, 라우팅은 route_main_loop가 결정
    return state

def create_graph_flow():
    graph = StateGraph(InterviewState)

    graph.add_node("main_loop", main_loop)
    graph.add_node("problem_intro", problem_intro_and_strategy)
    graph.add_node("generator_question", generator_question)
    graph.add_node("problem_solving", eval_problem_solving)
    graph.add_node("collaboration", eval_collaboration)
    graph.add_node("code_quality", eval_code_quality)
    graph.add_node("supervisor", supervisor)
    graph.add_node("qa_summary", qa_summary)

    graph.set_entry_point("main_loop")

    # main_loop -> (어떤 노드를 탈지) 조건부 라우팅
    graph.add_conditional_edges(
        "main_loop",
        route_main_loop,
        {
            "problem_intro": "problem_intro",
            "supervisor": "supervisor",
            "problem_solving": "problem_solving",
            "collaboration": "collaboration",
            "code_quality": "code_quality",
            "generator_question": "generator_question",
            "qa_summary": "qa_summary",
            "idle": END,
        },
    )

    # 워커 노드들은 일을 끝내고 항상 main_loop로 돌아온다
    graph.add_edge("problem_intro", "main_loop")
    graph.add_edge("generator_question", "main_loop")
    graph.add_edge("problem_solving", "main_loop")
    graph.add_edge("collaboration", "main_loop")
    graph.add_edge("code_quality", "main_loop")
    graph.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "to_generator": "generator_question",
            "to_summary": "qa_summary",
            "idle": "main_loop",
        },
    )
    graph.add_edge("qa_summary", "main_loop")

    return  graph.compile()



graph = create_graph_flow()