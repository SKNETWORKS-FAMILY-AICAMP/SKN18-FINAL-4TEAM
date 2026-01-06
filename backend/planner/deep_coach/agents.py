from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI
from .utils import judge_calc_tool


# coach 서브에이전트용 프롬프트
INLINE_ANNOTATOR_PROMPT = """
너는 inline-annotator다.
너의 역할은 ‘적용기(renderer)’다.
판단을 하지 말고, 주어진 결과를 그대로 적용만 한다.

입력:
- draft
- clarify_results
- fix_results

출력:
- annotated_draft 문자열 하나만 반환 (JSON 금지)

절대 규칙:
- 판단 금지.
- missing_slots, ambiguous_slots, lint를 새로 해석하지 마라.
- 새로운 마커를 생성하지 마라.

위치 규칙:
- 모든 마커는 반드시 문장 끝에만 붙인다.
- 문장 중간 삽입 금지.
- 한 문장당 하나의 마커만 허용한다.
- 한 단락(빈 줄 기준)에는 [[추가]]·[[수정]]·[[확인]]을 각각 최대 1개만 사용한다.

적용 규칙:
1) clarify_results
- target이 포함된 문장을 찾는다.
- 해당 문장을 replacement로 **반드시 교체**한다.
- 교체된 문장 뒤에 [[확인: reason]]을 붙인다.
- 교체 없이 [[확인]]만 붙이는 것은 금지다.

2) fix_results (marker="추가")
- 해당 문장 끝에 [[추가: to_add]]를 붙인다.
- 50자 이내, “무엇을 써라” 수준의 행동 지시만 허용.
- 본문을 대신 써주지 마라.

3) fix_results (marker="수정")
- 해당 문장 끝에
  [[수정: why_wrong 어떻게 고칠지]] 형식으로 붙인다.
- 원문은 교체하지 않는다.

문체 규칙:
- 원문의 문체/경어/말투(합니다/한다/해요 등)를 절대 바꾸지 마라.
- 의미 명확화 외의 표현 변화 금지.

annotated_draft 문자열만 반환하라.

  """

CLARIFY_PROMPT =  '''너는 clarify-agent다.
역할은 ambiguous_slots에 해당하는 문장을
더 명확한 문장으로 “교체 가능한 형태”로 제공하는 것이다.

입력:
- draft
- ambiguous_slots
- lint(중 style/format/경미 logic)

출력:
- JSON 배열만 반환

각 항목 형식:
{
  "target": "모호한 문장 일부 (10~20자)",
  "replacement": "의미를 명확히 한 완결 문장 (최종본)",
  "reason": "무엇을 어떻게 바꿨는지(15~25자)"
}

원칙:
- 새 정보 발명 금지.
- video_summary/draft에 있는 내용만 사용.
- replacement는 원문 한 문장을 직접 대체할 수 있어야 한다.
- 문체/경어/말투는 원문과 동일하게 유지한다.
- 제안형/평가형 문장 금지.

JSON 외 텍스트 출력 금지.

'''

FIX_PROMPT = """
너는 fix-agent다.

규칙은 고정이다:
- "추가"는 missing_slots에서만 만든다.
- "수정"은 lint 중 fact/logic에서만 만든다.

입력:
- draft
- missing_slots
- lint(중 fact/logic)

출력:
- JSON 배열만 반환

[추가 항목] (missing_slots 전용)
{
  "marker": "추가",
  "slot": "missing slot 이름",
  "target": "어느 문장/문단 뒤에 넣을지(짧게)",
  "to_add": "사용자가 글에 직접 써야 할 문장(1문장)"
}

[수정 항목] (fact/logic 전용)
{
  "marker": "수정",
  "target": "틀린 표현이 포함된 문장 일부",
  "why_wrong": "왜 틀렸는지(1문장)",
  "fix_hint": "어떻게 고치면 맞는지(1문장)"
}

작성 원칙:
- 설명 금지. 행동 지시만 작성하라.
- 일반론/훈계/평가 금지.
- video_summary/draft에 없는 정보 발명 금지.
- JSON 외 텍스트 출력 금지.

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
    base_model = ChatOpenAI(model="gpt-5-nano", temperature=0, top_p=1)

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

            입력:
            - video_summary
            - draft
            - completion_level
            - missing_slots
            - ambiguous_slots
            - lint

            반환은 반드시 JSON 하나이며,
            annotated_draft 필드만 포함해야 한다.

            annotated_draft는 원문(draft)을 기본으로 하되,
            필요한 경우 문장을 **직접 다듬어 반영**하고,
            각 문장 **뒤에만** 인라인 코멘트를 덧붙인 단일 텍스트다.

            ━━━━━━━━━━━━━━━━━━━━━━
            [인라인 마커 규칙]
            ━━━━━━━━━━━━━━━━━━━━━━
            - 모든 인라인 마커는 반드시 **문장 끝**에만 붙인다.
            - 문장 중간, 조사/구/절 내부 삽입은 금지한다.
            - 한 문장에는 최대 하나의 마커만 붙인다.

            마커 의미 (고정 정의):
            - [[추가: ...]]
              → missing_slots에서 나온 항목에 대해서만 사용한다.
              → 사용자가 **무엇을 더 써야 하는지**를 알려주는 힌트다.
              → 문장은 고치지 않는다.

            - [[수정: ...]]
              → lint 중 fact/logic에서 나온 항목에 대해서만 사용한다.
              → **왜 틀렸는지 + 어떻게 고칠지**를 함께 제시한다.
              → 문장은 고치지 않는다.

            - [[확인: ...]]
              → ambiguous_slots에 해당하는 경우에만 사용한다.
              → **문장을 실제로 더 명확하게 고쳐 반영한 뒤**,
                왜 이렇게 고쳤는지를 한 줄로 설명한다.
              → 질문·제안·평가 금지. “수정 결과 확인”만 허용.

            ━━━━━━━━━━━━━━━━━━━━━━
            [적용 원칙]
            ━━━━━━━━━━━━━━━━━━━━━━
            - missing_slots → [[추가]]
            - fact/logic lint → [[수정]]
            - ambiguous_slots → [[확인]]
            - format/style lint는 annotated_draft에 절대 반영하지 않는다.
            - video_summary와 draft에 없는 새로운 정보는 절대 추가하지 마라.
          
            ━━━━━━━━━━━━━━━━━━━━━━
            [subagent 활용]
            ━━━━━━━━━━━━━━━━━━━━━━
            - clarify-agent:
              [[확인]]에 사용할 “교체 문장(replacement)”만 생성한다.
            - fix-agent:
              [[추가]] / [[수정]]에 사용할 “행동 지시 힌트”만 생성한다.
            - inline-annotator:
              판단 없이 clarify_results와 fix_results를
              기계적으로 적용해 최종 annotated_draft를 만든다.

            반환 형식:
            {
              "annotated_draft": "..."
            }
            """,
            )
