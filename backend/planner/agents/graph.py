from langgraph.graph import StateGraph, END
from .state import PlanState
from .nodes import planner_node, searcher_node, validator_node, replanner_node

def check_validation(state: PlanState):
    # 1. 다 찾았으면 종료
    if not state["incomplete_days"]:
        print("\n🎉 모든 커리큘럼 완성!")
        return "end"
    
    # 2. 최대 3번 시도했으면 종료 (무한루프 방지)
    if state["retry_count"] >= 3:
        print("\n🛑 최대 재시도 횟수 도달. 현재 상태로 종료.")
        # 실패한 건들에 대해 Fallback 링크 채워넣기는 View에서 처리하거나 여기서 마무리 로직 추가 가능
        return "end"
    
    # 3. 아니면 다시 시도
    return "retry"

def create_agent_graph():
    workflow = StateGraph(PlanState)
    
    workflow.add_node("planner", planner_node)
    workflow.add_node("searcher", searcher_node)
    workflow.add_node("validator", validator_node)
    workflow.add_node("replanner", replanner_node)

    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "searcher")
    workflow.add_edge("searcher", "validator")
    
    workflow.add_conditional_edges(
        "validator",
        check_validation,
        {"end": END, "retry": "replanner"}
    )
    workflow.add_edge("replanner", "searcher")

    return workflow.compile()

agent_app = create_agent_graph()