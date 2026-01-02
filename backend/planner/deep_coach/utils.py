import re
from langchain_core.tools import tool
import json
import re
from typing import Any, Dict


def safe_json_parse(text: str) -> Dict[str, Any]:
    """
    LLM 응답에서 JSON을 최대한 안전하게 파싱한다.
    """
    if not text:
        return {}

    # 1) 바로 파싱 시도
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2) ```json ``` 코드블록 제거
    cleaned = re.sub(r"```json|```", "", text).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # 3) JSON object 부분만 추출
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass

    # 4) 실패 시 로그용 반환
    raise ValueError(f"JSON parsing failed. raw text:\n{text}")


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

    # 완화된 기준: 경미한 lint 2개까지는 COMPLETE 허용, missing/치명 오류 여유폭 확대
    if missing_cnt == 0 or severe == 0 or mild <= 3:
        level = "COMPLETE"
    elif missing_cnt >= 4 or severe >= 2:
        level = "NEEDS_WORK"
    else:
        level = "POLISH"

    return {"completion_level": level}


# 툴과 LLM 결과를 비교해 더 완화된(completion_level이 높은) 쪽 사용
def _calc_tool_level(miss, ln):
    try:
        res_tool = judge_calc_tool.invoke({"missing": miss, "lint": ln})
    except Exception:
        pass
            
    if isinstance(res_tool, dict):
        return res_tool.get("completion_level", "COMPLETE")
    return "COMPLETE"




def _choose_lenient(a, b):
    order = ["NEEDS_WORK", "POLISH", "COMPLETE"]
    try:
        return a if order.index(a) >= order.index(b) else b
    except Exception:
        return a or b or "COMPLETE"