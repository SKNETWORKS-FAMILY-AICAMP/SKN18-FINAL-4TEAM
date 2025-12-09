from interview_engine.state import IntroState
from langchain_core.messages import HumanMessage, SystemMessage
from interview_engine.llm import LLM 


def _get_problem_text(state: IntroState) -> str:
    """state.problem_data는 문자열만 기대한다."""
    return str(state.get("problem_data") or "")


def problem_intro_agent(state: IntroState) -> IntroState:
    """
    Step 1: Problem Introduction

    사용하는 state 필드:
        - problem_data: 문제 설명 텍스트 (str)
        - intro_text: 문제 성명 텍스트 (str)

    동작:
        - smalltalk + 문제 요약 + 풀이 전략 질문까지 포함된 TTS 멘트 생성
            - intro.intro_text에 저장
            - latency를 줄이기 위해 풀이 전략 질문은 공통지문으로 넣기 
            - tts_text 에 intro_text 저장
        
    """

    # 1) 문제/질문 텍스트 가져오기
    problem: str = _get_problem_text(state)

    problem_context = f"문제 설명:\n{problem}\n"

    system_prompt = ('''
        당신은 AI 기반 코딩 테스트의 음성 면접관입니다.
        당신의 출력은 음성 합성(TTS)을 통해 지원자에게 전달됩니다.
        현재는 문제 소개 단계입니다.
            - 지원자의 긴장을 풀어주는 간단한 인사 한두 문장
            - 이어서 문제 핵심 요약
        규칙
        1) 모든 문장은 '습니다', '니다'로 끝나야 합니다.
        2) TTS 친화적 표현만 사용하세요.
            - Markdown 기호(백틱, 별표, 샵, 대시 등)와 특수문자 사용을 피하세요.
            - 변수명은 괄호로 읽기 쉽게 풀어쓰기 (예: user_id는 '유저 아이디').
            - 수식은 말로 풀어쓰기 (예: a <= 100 → '에이가 백 이하').
    '''
    )

    human_prompt = (
            F'''
            아래는 코딩 테스트 문제 정보입니다.
            {problem_context}
            문제 소개 멘트를 만들어주세요.
            '''
            
        )

    messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),]

    try:
        response = LLM.invoke(messages)
        raw = (getattr(response, "content", "") or "").strip()
        strategy_question = (
                '''
                코드를 작성하시기 전에, 이 문제를 어떤 방식으로 해결할지 풀이 방향을 설명해 주세요.
                사용하실 알고리즘과 예상되는 시간 복잡도까지 함께 말씀해 주시면 됩니다.
                '''
        )
        state['intro_text'] = raw
        state['tts_text'] = raw + "\n" + strategy_question

    except Exception:
            # 실패 시 state 그대로
            return state

    return state

