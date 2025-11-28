# service/conditional_edges.py
from service.state import InterviewState

# The focus values map directly to node names today. Use a validation set
# so callers can safely return the focus when it matches a node name.
VALID_FOCI = {"problem_solving", "collaboration", "code_quality"}

def route_main_loop(state: InterviewState) -> str:
    if state.get("await_human"):
        return "idle"

    if state.get("supervisor_mode", "none") in {"classify", "judge"}:
        return "supervisor"

    next_node = state.get("next_node")
    if next_node:
        state["next_node"] = None
        return next_node

    if state.get("phase", "init") == "init":
        return "problem_intro"

    handlers = {
        "answer_submitted": _handle_answer_submitted,
        "code_snapshot": _handle_code_snapshot,
        "finish": _handle_finish,
    }

    handler = handlers.get(state.get("event_type", "none"))
    if handler:
        return handler(state)

    return "idle"

def route_from_supervisor(state: InterviewState) -> str:
    mapping = {
        "generator_question": "to_generator",
        "qa_summary": "to_summary",
    }
    next_node = state.get("next_node")
    target = mapping.get(next_node or "")
    if target:
        state["next_node"] = None
        return target
    return "idle"

def _handle_answer_submitted(state: InterviewState) -> str:
    state["await_human"] = None
    state["event_type"] = "none"

    if state.get("phase") == "strategy_intro" and state.get("current_focus") is None:
        state["current_focus"] = "problem_solving"
        state["phase"] = "live_loop"
        return "problem_solving"

    focus = state.get("current_focus")
    if focus in VALID_FOCI:
        return focus
    return "idle"

def _handle_code_snapshot(state: InterviewState) -> str:
    state["supervisor_mode"] = "classify"
    state["event_type"] = "none"
    return "supervisor"

def _handle_finish(state: InterviewState) -> str:
    state["await_human"] = None
    payload = dict(state.get("event_payload") or {})
    payload["finalizing"] = True
    state["event_payload"] = payload
    state["event_type"] = "none"
    return "qa_summary"