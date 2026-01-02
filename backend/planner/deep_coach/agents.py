import json
from deepagents import create_deep_agent
from langchain.agents.structured_output import ResponseFormat
from utils import judge_calc_tool

# judge 노드 출력 스키마: completion_level + missing_slots + lint + confidence
judge_schema = {
    "name": "JudgeOut",
    "schema": {
        "type": "object",
        "properties": {
            "completion_level": {"type": "string", "enum": ["COMPLETE", "NEEDS_WORK", "POLISH"]},
            "missing_slots": {"type": "array", "items": {"type": "string"}},
            "lint": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"tag": {"type": "string"}, "message": {"type": "string"}},
                    "required": ["tag", "message"],
                },
            },
        },
        "required": ["completion_level", "missing_slots", "lint"],
    },
}



# 서브에이전트용 프롬프트
SLOT_PROMPT = """
너는 slot-matcher다.
입력: 영상 요약(video_summary)과 사용자 글 요약(draft).
출력: present/missing/ambiguous 3개 배열(JSON)
- present: 사용자 글에 해당 포인트가 명확히 포함
- missing: 전혀 언급되지 않음
- ambiguous: 언급은 있으나 모호/부분적/부분 반영
video_summary(기준 요약)에서 핵심 포인트/필수 요소를 3~7개로 뽑아 슬롯으로 삼아 위 3분류를 채워라.
오직 JSON만 반환.
"""

LINT_PROMPT = """
너는 lint-checker다.
입력: 영상 요약(video_summary)과 사용자 글 요약(draft).
- 요약 품질/왜곡 위험 신호를 lint 배열에 {tag, message}로만 짧게 기록한다.
- 태그 기준:
  - fact: 사실 오류, 기준 요약과의 명백한 불일치, 오개념
  - logic: 논리 흐름 문제(인과/근거/연결), 모순
  - format: 요약 형식/요구사항 위반
  - style: 가독성/문장 구조/표현 방식 문제
오직 JSON만 반환.
"""


def create_judge_agent():
    """
    입력: video_summary(영상 요약), draft(사용자 글)
    출력: completion_level, missing_slots, lint

    메인 에이전트는 slot-matcher와 lint-checker를 task로 호출해 결과를 합산한다.
    """
    return create_deep_agent(
        model="openai:gpt-4o-mini",
        tools=[judge_calc_tool],
        subagents=[
            {
                "name": "slot-matcher",
                "description": "영상 요약에서 핵심 포인트를 슬롯으로 삼아 누락 여부 판정",
                "system_prompt": SLOT_PROMPT,
                "tools": [],
                "model": "openai:gpt-4o-mini",
            },
            {
                "name": "lint-checker",
                "description": "논리/사실/형식 린트 수집",
                "system_prompt": LINT_PROMPT,
                "tools": [],
                "model": "openai:gpt-4o-mini",
            },
        ],
        response_format=ResponseFormat.from_json_schema(judge_schema, method="json_schema"),
        system_prompt="""
            너는 메인 판정 노드다. 한 턴에 slot-matcher와 lint-checker를 모두 task 툴로 호출해 결과를 합산하고,
            completion_level, missing_slots, lint만 JSON 스키마로 반환하라.

            - slot-matcher 호출: subagent_type='slot-matcher', description에 video_summary와 draft를 간단히 요약해 넣어라.
            * slot-matcher의 missing 리스트를 최종 missing_slots로 사용하라.
            - lint-checker 호출: subagent_type='lint-checker', 같은 입력을 넣어라.
            * lint는 요약 품질/왜곡 위험 신호(tag+짧은 message)만 담는다.
            - judge_calc_tool 호출: slot-matcher의 missing과 lint-checker의 lint를 넣어 completion_level을 계산하는 가이드라인으로 활용하라.
            * 필요시 맥락을 고려해 최소한으로 조정할 수 있음.

        """,
    )
