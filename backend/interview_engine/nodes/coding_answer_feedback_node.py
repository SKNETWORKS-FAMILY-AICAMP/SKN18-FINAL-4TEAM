import random

from interview_engine.state import CodingState


ANSWER_FEEDBACK_MESSAGES = [
    "아, 그렇게 생각하셨군요. 답변 잘 들었습니다. 이제 다시 문제 풀이에 집중해 주세요.",
    "좋은 설명 감사합니다. 말씀해 주신 내용을 바탕으로 계속 코드를 개선해 보겠습니다. 다시 문제 풀이를 이어가 주세요.",
    "네, 이해했습니다. 지금 말씀해 주신 방향대로 코드를 정리해 보면서 문제를 계속 풀어 보시면 좋겠습니다.",
]


def coding_answer_feedback_agent(state: CodingState) -> CodingState:
    """
    코딩 단계에서 면접관의 질문에 대한 사용자의 음성 답변(STT)이 들어왔을 때,
    짧은 리액션 멘트를 생성하는 노드.

    - 입력: state.stt_text (사용자 답변 텍스트) – 현재는 내용에 상관없이 고정 멘트만 사용
    - 출력: state.tts_text 에 리액션 멘트를 설정
    """
    message = random.choice(ANSWER_FEEDBACK_MESSAGES)
    state["tts_text"] = message
    return state

