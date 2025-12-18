import random

from interview_engine.state import CodingState


CODING_INTRO_MESSAGES = [
    "좋습니다. 이제 코딩 테스트를 시작하겠습니다. 문제를 읽으면서 차분하게 풀이를 진행해 주세요.",
    "이제부터 본격적으로 코딩 테스트를 진행하겠습니다. 너무 긴장하지 마시고, 평소 하시던 방식대로 풀이를 설명해 주세요.",
    "코딩 테스트를 시작하겠습니다. 정답도 중요하지만, 어떻게 사고하고 문제를 풀어가는지가 더 중요합니다.",
    "이제 코드를 작성해 보겠습니다. 필요하시면 중간중간 본인의 생각을 말로 설명해 주셔도 좋습니다.",
]


def coding_stage_intro_agent(state: CodingState) -> CodingState:
    """
    코딩 스테이지 진입 시 한 번 재생할 안내 멘트를 생성하는 노드.

    - 여러 개의 하드코딩된 문구 중 하나를 랜덤으로 선택해 tts_text에 설정한다.
    - 이번 호출 이후에는 event_type을 'coding_intro_done'으로 바꿔,
      이후 같은 그래프(chapter2)를 호출할 때는 code_quality/질문 경로로만 진입하도록 한다.
    """
    message = random.choice(CODING_INTRO_MESSAGES)
    state["tts_text"] = message
    # 인트로가 한 번 실행된 이후에는 다시 entry에서 coding_intro로 분기되지 않도록 플래그 변경
    state["event_type"] = "coding_intro_done"
    return state
