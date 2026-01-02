from langgraph.graph import StateGraph, END
from nodes import (
    evidence_ingest_node,
    judge_progress_agent_node,
    final_feedback_agent_node
)
from state import (
    EvidenceCoachState
)

def create_evidence_coach_graph():
    '''
    1. evidence_ingest_node 
    2. judge_progress_agent_node
    3. final_feedback_agent_node

    '''
    graph = StateGraph(EvidenceCoachState)
    
    graph.add_node("evidence_ingest_node", evidence_ingest_node)
    graph.add_node("judge_progress_agent_node", judge_progress_agent_node)
    graph.add_node("final_feedback_agent_node", final_feedback_agent_node)
    
    def router(state: EvidenceCoachState) -> str:
        mode = "coach" # default 정의
        if state.get("completion_level") == "COMPLETE":
            mode = "done"
        return mode

    graph.set_entry_point("evidence_ingest_node")
    graph.add_edge("evidence_ingest_node", "judge_progress_agent_node")
    graph.add_conditional_edges(
        "judge_progress_agent_node",
        router,
        {
            "done": END,
            "coach": "final_feedback_agent_node",
        },
    )
    graph.add_edge("final_feedback_agent_node", END)

    return graph.compile()
