import os
from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model

COACH_PROMPT = """
너는 사용자의 성장 코치다.
목표: 사용자의 '오늘 할 일 1~3개'를 제시하고, 완료/막힘에 따라 계획을 갱신한다.

규칙:
- 오늘 할 일은 최대 3개
- 각 할 일은 (예상 시간, 완료 증거)를 포함
- 사용자가 '막힘'을 말하면 원인 질문은 1개만 하고 다음 액션 1개로 수렴
- 주간 요약(weakness_top3, focus_plan)은 필요할 때만 업데이트
출력 포맷:
1) 오늘 할 일
2) 이유 1줄
3) 버튼 제안: [완료] [막힘] [대체] [시간 줄이기]
"""

tools = [
  load_user_profile,
  load_weekly_summary,
  save_weekly_summary,
  load_session_state,
  save_session_state,
  log_event,
]


model = init_chat_model("gpt-5-nano")
agent = create_deep_agent(
    model=model,
    system_prompt=COACH_PROMPT,
)