import re
from langchain_core.tools import tool




def _normalize_for_judge(text: str, max_chars: int = 20000) -> str:
    """
    Judge/분석용 정규화:
    - 줄바꿈 통일
    - 각 줄 양끝 공백 제거
    - 연속 스페이스/탭 축약
    - 길이 컷
    """
    text = "" if text is None else str(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines).strip()
    text = re.compile(r"[ \t]+").sub(" ", text)
    if len(text) > max_chars:
        text = text[:max_chars]
    return text

@tool
def judge_calc_tool(missing: list, lint: list) -> dict:
    """
    missing_slots와 lint를 받아 completion_level을 계산하는 가이드라인 툴이다.
    - missing: 누락된 슬롯 목록
    - lint: [{tag, message}], tag는 fact/logic/format/style
    """
    missing_cnt = len(missing or [])
    severe = sum(1 for x in (lint or []) if (x.get("tag") or "").lower() in {"logic", "fact"})
    mild = max(0, len(lint or []) - severe)

    if missing_cnt == 0 and severe == 0 and mild <= 1:
        level = "COMPLETE"
    elif missing_cnt >= 2 or severe >= 1:
        level = "NEEDS_WORK"
    else:
        level = "POLISH"

    return {"completion_level": level}