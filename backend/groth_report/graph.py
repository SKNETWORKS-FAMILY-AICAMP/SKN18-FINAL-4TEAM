from langgraph.graph import StateGraph, END
from typing import List, Dict, Any, TypedDict
from .node import (
    growth_delta_analyst,
    weakness_analyst,
    strength_analyst,
    improvement_analyst,
    create_report_node,
    ReportState,
)
_compiled_graph = None

def create_grothreport_graph_flow():
    graph = StateGraph(ReportState)
    
    graph.add_node("growth_delta_analyst", growth_delta_analyst)
    graph.add_node("weakness_analyst", weakness_analyst)
    graph.add_node("strength_analyst", strength_analyst)
    graph.add_node("improvement_analyst", improvement_analyst)
    graph.add_node("create_report_node",create_report_node)
    
    def router(state: ReportState) -> str:
        has_prev_flag = bool(state.get("growth_true"))
        return "growth_delta_analyst" if has_prev_flag else "create_report_node"

    graph.set_entry_point("weakness_analyst")
    graph.add_edge("weakness_analyst", "strength_analyst")
    graph.add_edge("strength_analyst", "improvement_analyst")
    graph.add_conditional_edges(
        "improvement_analyst",
        router,
        {
            "growth_delta_analyst": "growth_delta_analyst",
            "create_report_node": "create_report_node",
        },
    )
    graph.add_edge("growth_delta_analyst", "create_report_node")
    graph.add_edge("create_report_node", END)

    return graph.compile()

def run_growth_report(reports: List[Dict[str, Any]], growth_report: Any = None) -> Dict[str, Any]:
    """
    LangGraph를 실행해 성장 리포트를 생성한다.
    - reports: [{"session_id": str, "report_md": str}]
    - growth_report: 이전 성장 리포트(문자열/객체). 없으면 변화 섹션 생략.
    """
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = create_grothreport_graph_flow()

    state: ReportState = {
        "reports": reports or [],
        "growth_report": growth_report,
        "growth_true": bool(growth_report),
    }
    result = _compiled_graph.invoke(state)
    return result
