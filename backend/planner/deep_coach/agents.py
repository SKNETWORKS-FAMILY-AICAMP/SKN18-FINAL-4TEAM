import json
from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI
from utils import judge_calc_tool

# judge 노드 출력 스키마: completion_level + missing_slots + lint + confidence
'''
{
    "type": "object",
    "properties": {
        "completion_level": {"type": "string", "enum": ["COMPLETE", "NEEDS_WORK", "POLISH"]},
        "missing_slots": {"type": "array", "items": {"type": "string"}},
        "ambiguous_slots": {"type": "array", "items": {"type": "string"}},
        "lint": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"tag": {"type": "string"}, "message": {"type": "string"}},
                "required": ["tag", "message"],
            },
        },
    },
    "required": ["completion_level", "missing_slots", "ambiguous_slots", "lint"],
}
'''

'''
{
    "type": "object",
    "properties": {
        "annotated_draft": {"type": "string"},
    },
    "required": ["annotated_draft"],
}
'''



# coach 서브에이전트용 프롬프트
INLINE_ANNOTATOR_PROMPT = """
너는 inline-annotator다.
입력: video_summary, draft, missing_slots, ambiguous_slots, lint, clarify_results, fix_results
- 출력: annotated_draft 문자열 하나만 반환(JSON 금지)
- 위치 규칙: 문장 끝에만 마커(중간 삽입 금지, 문장당 1개)
- 마커 적용:
  - clarify_results → 해당 문장을 제안된 replacement로 **교체**한 뒤, [[확인: 무엇을 어떻게 바꿨는지/이유]]. 원문을 놔두고 마커만 붙이는 것은 금지.
  - fix_results(marker="추가") → 문장 끝에 [[추가: 무엇을 추가할지 + 왜 필요한지]] (50자 이내 힌트, 본문 새로 작성 금지)
  - fix_results(marker="수정") → 문장 끝에 [[수정: 문제=무엇이 틀렸는지 / 수정방향=어떻게 고칠지]]
- 문체/경어/말투(합니다/한다/해요 등)는 절대 바꾸지 말고, 내용 명확화만 해라.
  """

CLARIFY_PROMPT =  '''너는 clarify-agent다.
입력: draft, ambiguous_slots, lint(중 style/format/경미 logic)
출력: JSON 배열만 반환. 각 항목 예)
{
  "target": "모호한 부분 10~20자",
  "replacement": "명확/간결/톤 그대로 유지한 교체 문장 (원문과 길이 달라도 됨, 완결 문장)",
  "reason": "무엇을 어떻게 바꿨는지(15~25자)"
}
원칙: 새 정보 발명 금지, video_summary/draft에 있는 내용만 사용. replacement는 원문 한 문장을 직접 대체할 수 있는 완결 문장이어야 한다. 문체/경어/말투는 그대로 유지한다.
문체/경어/말투(합니다/한다/해요 등)는 그대로 유지한다.
'''

FIX_PROMPT = """
너는 fix-agent다.

규칙은 단순하다:
- "추가"는 missing_slots(누락 슬롯)에서만 만든다.
- "수정"은 lint 중 fact/logic(틀림/오해)에서만 만든다.

입력: draft, missing_slots, lint(중 fact/logic)

출력: 반드시 JSON 배열만 반환한다.

각 항목은 아래 중 하나다.

[추가 항목]  (missing_slots에서만)
{
  "marker": "추가",
  "slot": "missing slot 이름",
  "target": "어느 문장/문단 뒤에 넣을지(짧게)",
  "to_add": "사용자가 글에 '직접 써 넣어야 할 문장' (1문장)"
}

[수정 항목]  (fact/logic lint에서만)
{
  "marker": "수정",
  "target": "틀린 표현이 포함된 문장 일부(짧게)",
  "why_wrong": "왜 틀렸는지(1문장)",
  "fix_hint": "어떻게 고치면 맞는지(1문장)"
}

작성 원칙:
- 설명하지 마라. 사용자가 그대로 따라 쓸 수 있는 행동 지시로만 써라.
- 새 정보 발명 금지. video_summary/draft에 있는 내용만 근거로 삼아라.
- JSON 외 텍스트 금지.



"""


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
    출력: completion_level, missing_slots, ambiguous, lint

    메인 에이전트는 slot-matcher와 lint-checker를 task로 호출해 결과를 합산한다.
    """
    base_model = ChatOpenAI(model="gpt-4o-mini", temperature=0, top_p=1)

    return create_deep_agent(
        model=base_model,
        tools=[judge_calc_tool],
        subagents=[
            {
                "name": "slot-matcher",
                "description": "영상 요약에서 핵심 포인트를 슬롯으로 삼아 누락 여부 판정",
                "system_prompt": SLOT_PROMPT,
                "tools": [],
                "model": base_model,
            },
            {
                "name": "lint-checker",
                "description": "논리/사실/형식 린트 수집",
                "system_prompt": LINT_PROMPT,
                "tools": [],
                "model": base_model,
            },
        ],
        system_prompt="""
            너는 메인 판정 노드다. 한 턴에 slot-matcher와 lint-checker를 모두 task 툴로 호출해 결과를 합산하고,
            completion_level, missing_slots, ambiguous_slots, lint만 JSON 스키마로 반환하라.

            - slot-matcher 호출: subagent_type='slot-matcher', description에 video_summary와 draft를 간단히 요약해 넣어라.
            * slot-matcher의 missing 리스트를 최종 missing_slots로, ambiguous 리스트를 ambiguous_slots로 사용하라.
            - lint-checker 호출: subagent_type='lint-checker', 같은 입력을 넣어라.
            * lint는 요약 품질/왜곡 위험 신호(tag+짧은 message)만 담는다.
            - judge_calc_tool 호출: slot-matcher의 missing과 lint-checker의 lint를 넣어 completion_level을 계산하는 가이드라인으로 활용하라.
            * 필요시 맥락을 고려해 최소한으로 조정할 수 있음.

        """,
    )


def create_feedback_agent():
    """
    입력: video_summary, draft, completion_level, missing_slots, ambiguous_slots, lint
    출력: annotated_draft(원문에 인라인 코멘트가 포함된 단일 텍스트)
    """
    base_model = ChatOpenAI(model="gpt-4o-mini")
    return create_deep_agent(
        model=base_model,
        subagents=[
            {
                "name": "inline-annotator",
                "description": "원문에 인라인 마커를 달아야 할 위치와 내용을 제안",
                "system_prompt": INLINE_ANNOTATOR_PROMPT,
                "tools": [],
                "model": base_model,
            },
            {
                "name": "clarify-agent",
                "description": "모호/톤 문제를 명확화할 힌트 목록을 생성",
                "system_prompt": CLARIFY_PROMPT,
                "tools": [],
                "model": base_model,
            },
            {
                "name": "fix-agent",
                "description": "누락/사실/논리 오류를 채울 힌트 목록을 생성",
                "system_prompt": FIX_PROMPT,
                "tools": [],
                "model": base_model,
            },
        ],
        system_prompt="""
            너는 사용자가 영상(원문)을 보고 공부한 내용을
글로 더 잘 정리하도록 도와주는 ‘요약 코치’다.

사용자는 이미 video_summary의 내용을 학습한 상태이며,
너의 역할은 그 이해가 draft에 정확하고 명확하게 드러나도록
문장을 다듬거나, 보완 방향을 안내하는 것이다.

입력으로 video_summary, draft, completion_level,
missing_slots, ambiguous_slots, lint가 주어진다.

반환은 반드시 JSON 하나이며,
annotated_draft 필드만 포함해야 한다.
annotated_draft는 원문(draft)을 기본으로 하되,
필요한 경우 문장을 **직접 다듬어 반영**하고,
각 문장 **뒤에만** 인라인 코멘트를 덧붙인 단일 텍스트다.

━━━━━━━━━━━━━━━━━━━━━━
[인라인 마커 규칙]
━━━━━━━━━━━━━━━━━━━━━━
- 모든 인라인 마커는 반드시 **문장이 끝난 뒤**에만 붙인다.
- 문장 중간, 조사/구/절 내부 삽입은 금지한다.
- 한 문장에는 최대 하나의 마커만 붙인다.

마커 종류와 의미:
- [[추가: ...]]
  → 영상에서 다뤘지만 글에는 아직 드러나지 않은 내용을
     “무엇을 추가해야 하는지” 알려주는 힌트
  → 문장은 고치지 않는다.

- [[수정: ...]]
  → 사실/논리적으로 문제되는 표현에 대해
     “왜 문제인지”와 “어떻게 고치면 되는지”를 함께 제시
  → 문장은 고치지 않는다.

- [[확인: ...]]
  → 의미는 맞지만 표현이 모호하거나 덜 정제된 경우
     **문장을 직접 더 명확하게 고쳐 반영**한 뒤,
     왜 이렇게 고쳤는지를 한 줄로 설명한다.
  → [[확인]]은 질문이나 제안이 아니라 ‘수정 결과 확인’이다.

━━━━━━━━━━━━━━━━━━━━━━
[적용 원칙]
━━━━━━━━━━━━━━━━━━━━━━
- ambiguous_slots → [[확인]] (문장 직접 수정)
- missing_slots → [[추가]] (무엇을 써야 할지 힌트)
- fact/logic lint → [[수정]] (문제 + 수정 방향)
- video_summary와 draft에 없는 새로운 정보는 절대 추가하지 마라.

━━━━━━━━━━━━━━━━━━━━━━
[톤 가이드]
━━━━━━━━━━━━━━━━━━━━━━
- POLISH:
  이미 이해한 내용을 정리해 준다는 느낌으로
  과하지 않게 문장을 다듬는다.
- NEEDS_WORK:
  핵심이 보이도록 구조를 잡아주되,
  새 설명을 쓰거나 내용을 발명하지 않는다.

━━━━━━━━━━━━━━━━━━━━━━
[subagent 활용]
━━━━━━━━━━━━━━━━━━━━━━
- inline-annotator:
  최종 annotated_draft를 생성한다.
- clarify-agent:
  [[확인]]용으로 실제 교체 가능한 문장(rewrite)을 받는다.
- fix-agent:
  [[추가]] / [[수정]]에 사용할 구체적 힌트를 받는다.

반환은 반드시 다음 형태의 JSON 하나다:
{
  "annotated_draft": "..."
}

        """,
    )
