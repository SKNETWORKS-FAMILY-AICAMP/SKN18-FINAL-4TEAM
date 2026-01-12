from typing import Any, Dict, List, TypedDict


class ReportState(TypedDict, total=False):
    # 이전 성장 리포트가 있을 때 True로 설정하거나 growth_report를 채웁니다.
    growth_true: bool
    reports: str
    growth_report: Any  # 이전 성장 리포트 원문/객체
    growth_delta: Dict[str, Any]
    strengths: List[Dict[str, Any]]
    improvements: List[Dict[str, Any]]
    final_report: str
    high_algorithm_list:List[str]
    low_algorithm_list:List[str]