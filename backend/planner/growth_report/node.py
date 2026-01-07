import json
from .state import ReportState
from .utils import (
    _call_llm,
    _reports_to_text,
    _parse_json,
    collect_low_score_algorithms,
    collect_high_score_algorithms,
)


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
    reports = state.get("reports")
    user_prompt = f"""
    ### 이전 성장 리포트
    {prev_text}

    ### 현재 분석 대상 리포트
    {reports}
    """
    content = _call_llm(system_prompt, user_prompt)
    parsed = _parse_json(content)
    state["growth_delta"] = parsed if isinstance(parsed, dict) else {"raw": content}
    return state


def strength_analyst(state: ReportState) -> ReportState:
    system_prompt = """
        # ROLE
        너는 사용자의 라이브코딩 면접 누적 기록을 분석하는 강점 패턴 분석 노드다.

        # TASK
        - 누적 report 전체에서 반복적으로 관찰된 긍정적 행동/알고리즘 패턴만 추출한다.
          (알고리즘/자료구조 태그 problem_algorithm 및 report_md/code_feedback를 함께 고려)

        # CONSTRAINTS
        - 최소 2개 이상의 report에서 반복된 패턴만 인정한다.
        - 정확히 3개만 작성한다.
        - 각 항목은 80자 이내 한 문장이다.
        - 추측·일반론·칭찬성 표현 금지.

        # OUTPUT FORMAT (JSON Only)
        {
            "strengths": [
                {"title": "강점 요약(알고리즘/행동 포함)", "evidence": "반복된 행동/알고리즘 또는 report_ids"},
                {"title": "강점 요약(알고리즘/행동 포함)", "evidence": "..."},
                {"title": "강점 요약(알고리즘/행동 포함)", "evidence": "..."}
            ]
        }
    """
    high_algos_text= state.get("high_algorithm_list")
    reports = state.get("reports")
    user_prompt = f"{reports}\n\n### 강한 알고리즘 리스트\n{high_algos_text}"
    content = _call_llm(system_prompt, user_prompt)
    parsed = _parse_json(content)
    state["strengths"] = parsed.get("strengths") if isinstance(parsed, dict) else []
    return state


def improvement_analyst(state: ReportState) -> ReportState:
    system_prompt = """
        # ROLE
        너는 사용자의 리포트를 근거로 개선해야할 점을 요약하는 분석가다.

        # TASK
        - reports를 근거로 "어떤 점을 개선해야하는지"를 구체적으로 요약한다.

        # CONSTRAINTS
        - 정확히 3개
        - 각 항목은 80자 이내 한 문장
        - 추상적 조언 금지, 관찰된 부족만 요약

        # OUTPUT FORMAT (JSON Only)
        {
            "improvements": [
                {"title": "개선점 요약(알고리즘/행동 포함)", "evidence": "반복 패턴 또는 report_ids"},
                {"title": "...", "evidence": "..."},
                {"title": "...", "evidence": "..."}
            ]
        }
    """
    low_algos_text= state.get("low_algorithm_list")
    reports = state.get("reports")
    user_prompt = f"{reports}\n\n### 약한 알고리즘 리스트\n{low_algos_text}"
    content = _call_llm(system_prompt, user_prompt)
    parsed = _parse_json(content)
    state["improvements"] = parsed.get("improvements") if isinstance(parsed, dict) else []
    return state


def create_report_node(state: ReportState) -> ReportState:
    system_prompt = """
        # ROLE
        너는 여러 분석 노드의 결과를 종합해
        사용자에게 보여줄 '최종 성장 리포트 문장'을 작성하는 노드다.

        # WRITING RULES (중요)
        - 전체 분량은 **최대 6~8문장**을 넘지 않는다.
        - 각 섹션은 **1~2문장 이내**로 작성한다.
        - 문단 나누기 금지, 불필요한 접속사/완곡 표현 금지.
        - 코칭 톤이되 요약 리포트처럼 간결하게 쓴다.

        # CONTENT RULES
        - 이전 리포트가 없으면 "이전 대비 변화" 섹션 자체를 작성하지 않는다.
        - 이전 리포트가 있으면 변화는 **원인·의미 중심으로만** 서술한다.
        - 데이터 부족 안내, 기준선 안내, 추측성 표현 금지.
        - 관찰된 사실 → 의미 순서로 쓴다.

        # OUTPUT
        - PLAIN TEXT ONLY
        - 섹션 제목은 유지하되 설명은 최소화한다.
        - 불필요한 예시, 반복 설명 금지.
    """

    
    payload = {
        "strengths": state.get("strengths") or [],
        "improvements": state.get("improvements") or [],
        "growth_delta": state.get("growth_delta", []) 

    }
    user_prompt = json.dumps(payload, ensure_ascii=False, indent=2)
    content = _call_llm(system_prompt, user_prompt)
    state["final_report"] = content
    return state
