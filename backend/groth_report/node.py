import json
from typing import Any, Dict, List, TypedDict
from langchain_core.messages import SystemMessage, HumanMessage
from interview_engine.llm import get_llm


class ReportState(TypedDict, total=False):
    # 이전 성장 리포트가 있을 때 True로 설정하거나 growth_report를 채웁니다.
    growth_true: bool
    reports: List[Dict[str, Any]]
    growth_report: Any  # 이전 성장 리포트 원문/객체
    growth_delta: Dict[str, Any]
    weaknesses: List[Dict[str, Any]]
    strengths: List[Dict[str, Any]]
    improvements: List[Dict[str, Any]]
    final_report: str


def _call_llm(system_prompt: str, user_prompt: str) -> str:
    model = get_llm("report")
    resp = model.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
    return getattr(resp, "content", None) or str(resp)


def _parse_json(content: str) -> Dict[str, Any]:
    try:
        return json.loads(content)
    except Exception:
        return {}


def _reports_to_text(state: ReportState) -> str:
    reps = state.get("reports") or []
    if not reps:
        return "(보고서 없음)"
    texts: List[str] = []
    for idx, r in enumerate(reps, 1):
        md = (r.get("report_md") or "").strip()
        header = f"[리포트 {idx}]"
        texts.append(f"{header}\n{md}")
    return "\n\n".join(texts)

def growth_delta_analyst(state: ReportState) -> ReportState:
    system_prompt = """
        # ROLE
        너는 이전 성장 리포트와 현재 상태를 비교하는 “성장 변화 해석 노드”다.
        이 노드는 반드시 “변화가 존재한다”는 전제하에 호출된다.

        # TASK
        - 이전 상태 대비 새롭게 등장/사라짐/강화/악화된 패턴만 해석한다.
        - 변화의 ‘의미’에 집중한다.

        # CONSTRAINTS
        - 변화가 없는 항목은 작성하지 않는다.
        - 최대 3개까지만 작성한다.
        - 단순 나열 금지, 반드시 “왜 의미 있는 변화인지” 설명한다.

        # OUTPUT FORMAT (JSON only)
        {
            "deltas": [
                {
                  "type": "new_strength | new_weakness | resolved_weakness | worsened_weakness",
                  "key_point": "무엇이 어떻게 변했는지",
                  "impact": "이 변화가 성장에 갖는 의미"
                }
            ],
            "summary": "한 문장 변화 요약"
        }
    """
    prev = state.get("growth_report")
    prev_text = prev if isinstance(prev, str) else json.dumps(prev, ensure_ascii=False) if prev else "(이전 리포트 없음)"
    user_prompt = f"""
    ### 이전 성장 리포트
    {prev_text}

    ### 현재 분석 대상 리포트
    { _reports_to_text(state) }
    """
    content = _call_llm(system_prompt, user_prompt)
    parsed = _parse_json(content)
    state["growth_delta"] = parsed if isinstance(parsed, dict) else {"raw": content}
    return state


def weakness_analyst(state: ReportState) -> ReportState:
    system_prompt = """
        # ROLE
        너는 사용자의 누적 라이브코딩 면접 기록을 분석하는 약점 패턴 식별 노드다.

        # TASK
        - 반복적으로 관찰된 개선 필요 패턴만 식별한다.

        # CONSTRAINTS
        - 단발성 실수 제외
        - 최소 2개 이상의 report 근거 필요
        - 정확히 3개
        - 각 항목은 80자 이내 한 문장
        - 비난/성격 판단 금지

        # OUTPUT FORMAT (JSON only)
        {
            "weaknesses": [
                {"title": "약점 요약", "evidence": "반복 패턴 또는 report_ids"},
                {"title": "약점 요약", "evidence": "..."},
                {"title": "약점 요약", "evidence": "..."}
            ]
        }
    """
    user_prompt = _reports_to_text(state)
    content = _call_llm(system_prompt, user_prompt)
    parsed = _parse_json(content)
    state["weaknesses"] = parsed.get("weaknesses") if isinstance(parsed, dict) else []
    return state


def strength_analyst(state: ReportState) -> ReportState:
    system_prompt = """
        # ROLE
        너는 사용자의 라이브코딩 면접 누적 기록을 분석하는 강점 패턴 분석 노드다.

        # TASK
        - 누적 report 전체에서 반복적으로 관찰된 긍정적 행동 패턴만 추출한다.

        # CONSTRAINTS
        - 최소 2개 이상의 report에서 반복된 패턴만 인정한다.
        - 정확히 3개만 작성한다.
        - 각 항목은 80자 이내 한 문장이다.
        - 추측·일반론·칭찬성 표현 금지.

        # OUTPUT FORMAT (JSON Only)
        {
            "strengths": [
                {"title": "강점 요약", "evidence": "반복된 행동 또는 report_ids"},
                {"title": "강점 요약", "evidence": "..."},
                {"title": "강점 요약", "evidence": "..."}
            ]
        }
    """
    user_prompt = _reports_to_text(state)
    content = _call_llm(system_prompt, user_prompt)
    parsed = _parse_json(content)
    state["strengths"] = parsed.get("strengths") if isinstance(parsed, dict) else []
    return state


def improvement_analyst(state: ReportState) -> ReportState:
    system_prompt = """
        # ROLE
        너는 약점 분석 결과를 실행 가능한 행동으로 변환하는 개선 전략 생성 노드다.

        # TASK
        - 각 약점에 대해 다음 면접에서 바로 실행 가능한 행동을 제안한다.

        # CONSTRAINTS
        - weakness 항목과 1:1 매핑
        - 정확히 3개
        - 추상적 조언 금지
        - 성공 기준은 체크 가능해야 함

        # OUTPUT FORMAT (JSON Only)
        {
            "improvements": [
                {
                    "action": "구체적 행동 지침",
                    "linked_weakness": "약점 요약",
                    "success_criteria": ["체크 가능한 기준 1", "체크 가능한 기준 2"]
                },
                {"action": "...", "linked_weakness": "...", "success_criteria": ["...", "..."]},
                {"action": "...", "linked_weakness": "...", "success_criteria": ["...", "..."]}
            ]
        }
    """
    weaknesses = state.get("weaknesses") or []
    user_prompt = json.dumps({"weaknesses": weaknesses, "reports": state.get("reports")}, ensure_ascii=False)
    content = _call_llm(system_prompt, user_prompt)
    parsed = _parse_json(content)
    state["improvements"] = parsed.get("improvements") if isinstance(parsed, dict) else []
    return state


def create_report_node(state: ReportState) -> ReportState:
    system_prompt = """
    # ROLE
    너는 여러 분석 노드의 결과를 종합해
    사용자에게 보여줄 '최종 성장 리포트 문장'을 작성하는 노드다.

    - 이전 리포트가 없으면 "이전 대비 변화" 섹션을 아예 작성하지 않는다(헤더 포함 금지).
    - 이전 리포트가 있으면 변화는 반드시 의미 중심으로 자연스럽게 서술한다.
    - 데이터 부족 안내, 기준선 안내 같은 표현 금지.
    - 코칭 톤, 간결한 문장, 객관적 관찰 기반.

    # OUTPUT (PLAIN TEXT ONLY)
    위 지침을 따라 섹션별로 한국어로 작성한다.
    """
    
    payload = {
        "strengths": state.get("strengths") or [],
        "weaknesses": state.get("weaknesses") or [],
        "improvements": state.get("improvements") or [],
        "growth_delta": state.get("growth_delta", []) 

    }
    user_prompt = json.dumps(payload, ensure_ascii=False, indent=2)
    content = _call_llm(system_prompt, user_prompt)
    state["final_report"] = content
    return state
