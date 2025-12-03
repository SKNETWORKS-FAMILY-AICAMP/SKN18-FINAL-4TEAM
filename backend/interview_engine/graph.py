from langgraph.graph import StateGraph, END
from interview_engine.state import InterviewState
from interview_engine.nodes.problem_intro_node import problem_intro_agent
from interview_engine.nodes.problem_solving_eval_node import problem_solving_eval_agent
from interview_engine.nodes.hint_node import hint_agent
from interview_engine.nodes.question_generation_node import question_generation_agent
from interview_engine.nodes.final_eval_node import final_eval_agent
from interview_engine.nodes.answer_classify import answer_classify_agent
from interview_engine.nodes.code_quality_node import code_quality_agent
from interview_engine.conditional_edges import route_loop

def session_manager(state: InterviewState) -> InterviewState:
    # 그냥 state 그대로 리턴, 라우팅은 route_main_loop가 결정
    return state

def create_graph_flow():
    graph = StateGraph(InterviewState)

    # chapter 1: Intro
    graph.add_node("session_manager", session_manager)
    graph.add_node("problem_intro_agent", problem_intro_agent)
    graph.add_node("problem_solving_eval_agent", problem_solving_eval_agent)
    graph.add_node("answer_classify_agent", answer_classify_agent)
    
    # chapter 2: Coding
    graph.add_node("hint_agent", hint_agent)
    graph.add_node("code_quality_agent", code_quality_agent)
    graph.add_node("question_generation_agent", question_generation_agent)
    
    # chapter3: Evaluation
    graph.add_node("final_eval_agent", final_eval_agent)
    
    graph.set_entry_point("session_manager")

    # session_manager -> (어떤 노드를 탈지) 조건부 라우팅
    graph.add_conditional_edges(
        "session_manager",
        route_loop,
        {
            "problem_intro_agent": "problem_intro_agent",
            "answer_classify_agent":"answer_classify_agent",
            "problem_solving_eval_agent": "problem_solving_eval_agent",
            "code_quality_agent":"code_quality_agent",
            "hint_agent":"hint_agent",
            "question_generation_agent":"question_generation_agent",
            "final_eval_agent":"final_eval_agent",
            "idle": END
        },
    )

    # 워커 노드들은 일을 끝내고 항상 main_loop로 돌아온다
    graph.add_edge("problem_intro_agent", "session_manager")
    graph.add_edge("problem_solving_eval_agent", "session_manager")
    graph.add_edge("code_quality_agent","session_manager")
    graph.add_edge("hint_agent","session_manager")
    graph.add_edge("question_generation_agent","session_manager")
    graph.add_edge("final_eval_agent", END)    
    
    return  graph.compile()



graph = create_graph_flow()