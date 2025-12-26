from datetime import datetime
import pytz
from langchain_openai import ChatOpenAI

LLM = ChatOpenAI(
    model="gpt-5-nano",
    reasoning_effort="high",  # 논리성 강화
)


def _week_id_seoul() -> str:
    tz = pytz.timezone("Asia/Seoul")
    now = datetime.now(tz)
    y, w, _ = now.isocalendar()
    return f"{y}-W{w:02d}"


def _detect_period(message: str) -> str:
    text = (message or "").lower()
    if any(k in text for k in ["이번주", "이번 주", "주간", "week", "weekly"]):
        return "week"
    if any(k in text for k in ["오늘", "하루", "day", "daily"]):
        return "day"
    return "week"  # default