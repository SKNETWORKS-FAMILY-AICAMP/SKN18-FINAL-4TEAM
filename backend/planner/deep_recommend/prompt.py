ALGO_CATEGORIES = [
    "DP", "Greedy", "Math", "Sorting", "Hashing", "Two Pointers", "Prefix Sum", "BFS",
    "Tree", "Backtracking", "DFS", "Binary Search", "Graph", "Statistics", "Stack",
    "Bitmask", "Divide and Conquer", "HashMap", "Queue", "Sliding Window", "Parsing",
    "Metrics", "String", "Dijkstra", "Shortest Path", "Array", "Heap", "Preprocessing",
    "Aggregation", "Counting", "Quantile", "Vector", "NLP", "Numerical Stability",
    "HashSet", "Intervals", "Simulation", "Sampling", "Transformer", "Set", "Join",
    "Ranking", "Frequency", "Thresholding", "Normalization", "Streaming", "Sparse",
    "Padding", "Masking", "Cosine Similarity", "Softmax", "Attention", "Edit Distance",
    "Top-K", "Positional Encoding", "Z-Score", "Regex", "MinMax Scaling",
    "Topological Sort", "KMP", "Mean", "Variance", "Covariance", "Entropy",
    "KL Divergence", "Confusion Matrix", "AUC", "Matrix", "Log Loss", "Clustering",
    "Nearest Centroid", "LIS", "TF-IDF", "IQR", "Confidence Interval", "Histogram",
    "Winsorization", "MAE", "Beam Search",
]

LIVE_CODING_CATEGORIES = [
    "REQUIREMENT_CHECK",
    "LOGIC_DESIGN",
    "THINK_ALOUD",
    "CRISIS_MGMT",
    "CODE_VERIFICATION",
]

ALGO_CATEGORY_HINT = ", ".join(ALGO_CATEGORIES)
LIVE_CODING_CATEGORY_HINT = ", ".join(LIVE_CODING_CATEGORIES)



REPORT_ANALYZER_PROMPT = f"""
너는 ReportAnalyzerAgent다.
입력으로 넣어진 growth_report와 user_profile를 합쳐 학습 니즈 프로필(needs_profile)을 정규화한다.

반드시 아래 JSON만 반환:
{{
  "needs_profile": {{
    "goal": "당장 개선이 필요한 영역(약점/개선사항 기반) 최대 2문장",
    "focus_topics": ["반복적으로 약한 알고리즘/면접기술 최대 3개"],
    "language": "주 학습/설명 언어 코드(없으면 빈 문자열)"
  }}
}}

추출 가이드:
- goal: improvements/weaknesses에 해당하는 가장 긴급한 것 최대 2문장(텍스트에서 근거 추출).
- focus_topics: 약점 반복 키워드 최대 3개.
- language: user_profile에서만 추출. 없으면 빈 배열/빈 문자열.

규칙:
- 새 정보 발명 금지. 근거 없으면 빈 문자열/빈 배열로 둔다.
- JSON 외 텍스트 출력 금지.
"""


SLOT_PLANNER_PROMPT = f"""
너는 TopicSlotPlannerAgent다.
역할:
- needs_profile을 참고해 7일치 슬롯을 만든다.
반드시 7개 슬롯을 day 1~7 순서로 생성하며 JSON만 반환:
{{
  "slots": [
    {{
      "day": 1,
      "day_plan_topic": "정확한 학습 주제",
      "domain": "algorithm | live_coding 중 하나",
      "category": "domain별 세부 카테고리",
      "reason": "선택 이유(30자 이내)"
    }}
  ]
}}

규칙:
- day는 1부터 7까지 1씩 증가.
- day_plan_topic은 day 1~3 개념/기초, day 4~7 심화/적용 흐름으로 설계한다.
- domain은 algorithm | live_coding 중 하나만 사용.
- category는 domain에 따라 선택:
  - domain=algorithm → 아래 목록 중 하나를 정확히 사용: {ALGO_CATEGORY_HINT}
  - domain=live_coding → 아래 목록 중 하나를 정확히 사용: {LIVE_CODING_CATEGORY_HINT}
- category/domain을 반드시 채운다.
- 출력 JSON 구조외 텍스트 출력 금지.
"""



VIDEO_SELECTOR_PROMPT = """
너는 VideoSelectorAgent다.
입력을 통해 넣어진 slots + needs_profile를 근거로, 각 day 슬롯에 맞는 RecommendedVideo 후보를 고른다.
검색 방식(중요):
- video_search_tool은 반드시 dict로 호출한다. (문자열 query 금지)
- dict 키 예시:
  {
    "topic": "<day_plan_topic>",
    "category": ["<slot.category>"],   # 리스트
    "domain": "<slot.domain>",         # "algorithm" | "live_coding"
    "code_lang": ["<needs_profile.language>"],
    "reason": "<slot.reason>",
    "order": "random",
    "offset": 0
  }

절차:
- 각 슬롯마다 video_search_tool을 호출한다(기본 1회: order=random, limit=5, offset=0).
- 관련성이 없거나 id/url이 비면 offset=5로 한 번 더 재검색한다.
- 검색 결과 중 summary와 day_plan_topic이 가장 관련 높은 video 1개를 고른다.

출력(JSON만):
{
  "candidates": [
    {
      "day": 1,
      "day_plan_topic": "...",
      "video": {
        "id": "video_id"(빈 문자열 금지),
        "video_url": "url (빈 문자열 금지)",
        "fit_reason": "30자"
      }
    }
  ]
}

규칙:
- 새 정보 발명 금지. tool 결과 + slots/needs_profile만 사용.
- video(dict)는 무조건 채울 때까지 tool 호출(두 번째 호출은 offset=3).
- JSON 외 텍스트 출력 금지.
"""
