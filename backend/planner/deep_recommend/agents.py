from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from tools import video_search_tool, validate_plan_tool
load_dotenv()

# 기본 모델명: 튜플이 되지 않도록 쉼표를 제거한다.
DEFAULT_MODEL_NAME = "gpt-4o-mini"

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



REPORT_ANALYZER_PROMPT = """
너는 ReportAnalyzerAgent다.
입력: growth_reports(누적 코딩테스트 강점/약점/변화/개선사항 텍스트) + user_profile(선호 직무/언어/시간 예산 등).
둘을 합쳐 학습 니즈 프로필을 정규화한다.

반드시 아래 JSON만 반환:
{
  "needs_profile": {
    "goal": "당장 개선이 필요한 영역(약점/개선사항 기반)",
    "current_level": "전체 수준 또는 최근 등급/점수",
    "focus_topics": ["반복적으로 약한 알고리즘/도메인 최대 3개"],
    "review_topics": ["최근 악화/잊은 영역 1~2개"],
    "strengths": ["유지/활용할 강점 1~2개"],
    "preferences": ["user_profile 기반 선호 주제/형식"],
    "language": "주 학습/설명 언어 코드",
  }
}

추출 가이드:
- growth_reports에서 goal/current_level/focus_topics/review_topics/strengths만 뽑고, 없으면 빈값.
- user_profile에서 preferences/language 채운다. 없으면 빈 문자열/빈 배열
- goal: improvements/weaknesses에서 가장 긴급한 것 1문장.
- focus_topics: 반복된 약점 알고리즘/도메인 키워드 위주 최대 3개.
- review_topics: 최근 악화/퇴보/미완료 영역이 있으면 1~2개.

규칙:
- 새 정보 발명 금지. 근거 없으면 null/빈 문자열/빈 배열/로 둔다.
- JSON 외 텍스트 출력 금지.
"""


SLOT_PLANNER_PROMPT = """
너는 TopicSlotPlannerAgent다.
needs_profile을 참고해 7일치 슬롯을 만든다.

반드시 7개 슬롯을 day 1~7 순서로 생성하며 JSON만 반환:
{
  "slots": [
    {
      "day": 1,
      "day_plan_topic": "정확한 학습 주제",
      "domain": "algorithm | live_coding 중 하나",
      "category": "domain별 세부 카테고리",
      "reason": "선택 이유(30자 이내)"
    }
  ]
}

규칙:
- day는 1부터 7까지 1씩 증가.
- topic 중복 금지.
- domain은 algorithm | live_coding 중 하나만 사용.
- category는 domain에 따라 선택:
    - domain=algorithm → ALGO_CATEGORIES 중 선택 (예: DP, Greedy, BFS)
    - domain=live_coding → LIVE_CODING_CATEGORIES 중 선택 (REQUIREMENT_CHECK 등)
- focus_topics는 algorithm 도메인을 우선 채우고, review_topics는 review/유사 카테고리로 최소 1개 배정, strengths는 최대 1개.
- video_search_tool이 topic+category+domain+difficulty로 쿼리할 수 있도록 category/domain을 반드시 채운다.
- needs_profile.preferences/avoid 반영.
"""


VIDEO_SELECTOR_PROMPT = """
너는 VideoSelectorAgent다.
입력 슬롯(slots)과 needs_profile을 받아 슬롯별 영상 후보를 선정한다.

절차:
- 각 슬롯마다 video_search_tool을 호출해 query를 날리고 후보 3~5개를 고른다.
- query는 topic+category+domain 포함한다.
- 각 후보에 fit_reason(왜 맞는지)을 포함한다.

출력(JSON만):
{
  "candidates": [
    {
      "day": 1,
      "day_plan_topic": "...",
      "videos": [
        {
          "id": "video_id",
          "fit_reason": "30자",
        }
      ]
    }
  ]
}
"""


PLAN_BUILDER_PROMPT = """
너는 PlanBuilderAgent다.
slots와 candidates를 받아 최종 7일 플랜(final_plan)을 만든다.

출력(JSON만):
{
  "final_plan": [
    {
      "day": 1,
      "day_plan_title": "...",
      "video_id": "...",
      "learning_goals": ["2~3개"],
      "success_criteria": ["2개"],
      "why_selected": "30자",
    }
  ]
}

규칙:
- day 1~7 순서 맞추기, video_id 중복 금지
- learning_goals는 슬롯 topic과 직결.
- success_criteria는 사용자의 이해도 점검 기준이 될 수 있도록 성공 기준 설정
"""


MAIN_PROMPT = """
너는 WeeklyStudyPlannerDeepAgent다.
입력: user_id, user_profile, growth_reports
출력: final_plan(7개), slots, needs_profile

호출 순서:
1) report-analyzer task → needs_profile 생성
2) slot-planner task → slots 생성
3) video-selector task → candidates 생성
4) plan-builder task → final_plan 생성
5) validate_plan_tool → 검증

실패 대응:
- 검증 실패 시 slots를 한 번 조정하거나 video-selector 재호출 후 plan-builder 재호출.
- 여전히 실패면 plan-builder를 간소화 모드(성공기준 1개, time_plan 요약)로 다시 실행 후 validate.

반환은 반드시 JSON:
{
  "needs_profile": {...},
  "slots": [...],
  "candidates": [...],
  "final_plan": [...],
  "validation": {"ok": bool, "issues": [...]}
}

규칙:
- 새로운 정보 발명 금지, growth_reports/slots/candidates 내 데이터만 사용.
- video_search_tool은 하루 최대 2회 호출.
- description 필드에는 입력 요약 2~3줄만 넣어 토큰을 절약한다.
"""


def create_weekly_study_planner_agent(model_name: str = None):
    """7일 학습 추천 deep-agent를 생성한다."""
    resolved_model = model_name or DEFAULT_MODEL_NAME
    base_model = ChatOpenAI(model=resolved_model, temperature=0)

    return create_deep_agent(
        model=base_model,
        tools=[validate_plan_tool, video_search_tool],
        subagents=[
            {
                "name": "report-analyzer",
                "description": "growth_reports를 needs_profile로 정규화",
                "system_prompt": REPORT_ANALYZER_PROMPT,
                "tools": [],
                "model": base_model,
            },
            {
                "name": "slot-planner",
                "description": "7일 슬롯(topic/category/difficulty) 설계",
                "system_prompt": SLOT_PLANNER_PROMPT,
                "tools": [],
                "model": base_model,
            },
            {
                "name": "video-selector",
                "description": "슬롯에 맞는 영상 후보 검색 및 점수화",
                "system_prompt": VIDEO_SELECTOR_PROMPT,
                "tools": [video_search_tool],
                "model": base_model,
            },
            {
                "name": "plan-builder",
                "description": "7일 최종 플랜 생성",
                "system_prompt": PLAN_BUILDER_PROMPT,
                "tools": [],
                "model": base_model,
            },
        ],
        system_prompt=MAIN_PROMPT,
    )
