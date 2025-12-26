from langgraph.graph import StateGraph, END
from chatbot.coach.state import CoachState
from chatbot.coach.nodes import (
    load_user_state_node,
    coach_classify_node,
    daily_weekly_node,
    long_term_agent,
    review_agent,
    normalize_to_actions,
)


def coach_graph_flow():
    '''
    load_user_state_node : Postgre 조회
    coach_classify_node:

        ① 일일/주간 실행 계획
        ② 장기 계획(목표 회사·취준 로드맵, 코딩테스트 준비 방법 등)
        ③ 리뷰(회고·조정)
    mode별 분기
        - daily_weekly_node(mode별 동작)
        - long_term_agent
        - review_agent
    normalize_to_actions: 양식 정규화
    '''
    workflow = StateGraph(CoachState)

    workflow.add_node("load_user_state_node", load_user_state_node)
    workflow.add_node("coach_classify_node", coach_classify_node)
    workflow.add_node("daily_weekly_node", daily_weekly_node)
    workflow.add_node("long_term_agent", long_term_agent)
    workflow.add_node("review_agent", review_agent)
    workflow.add_node("normalize_to_actions", normalize_to_actions)

    workflow.set_entry_point("load_user_state_node")
    workflow.add_edge("load_user_state_node", "coach_classify_node")
    workflow.add_conditional_edges(
        "coach_classify_node",
        lambda state: state.get("plan_kind", "EXEC_PLAN"),
        {
            "EXEC_PLAN": "daily_weekly_node",
            "LONG_TERM_PLAN": "long_term_agent",
            "REVIEW": "review_agent",
        },
    )
    workflow.add_edge("daily_weekly_node", "normalize_to_actions")
    workflow.add_edge("long_term_agent", "normalize_to_actions")
    workflow.add_edge("review_agent", "normalize_to_actions")
    workflow.add_edge("normalize_to_actions", END)

    
    return workflow.compile()
