from langgraph.graph import StateGraph, END
from .nodes import (
    report_analyzer,
    slot_planner,
    video_selector,
    plan_builder  
)
from .state import (
    RecommendState
)

def create_recommend_graph():
    '''
    1. report-analyzer
    2. slot-planner
    3. video-selector
    4. plan-builder
    5. validate_node(선택)
    '''
    graph = StateGraph(RecommendState)
    
    graph.add_node("report_analyzer", report_analyzer)
    graph.add_node("slot_planner", slot_planner)
    graph.add_node("video_selector", video_selector)
    graph.add_node("plan_builder",plan_builder)
    

    graph.set_entry_point("report_analyzer")
    graph.add_edge("report_analyzer", "slot_planner")
    graph.add_edge("slot_planner", "video_selector")
    graph.add_edge("video_selector", "plan_builder")
    graph.add_edge("plan_builder", END)

    return graph.compile()
