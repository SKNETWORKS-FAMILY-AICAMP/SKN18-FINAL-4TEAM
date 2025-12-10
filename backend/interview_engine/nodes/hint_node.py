from interview_engine.state import InterviewState
from typing import TypedDict, List, Any, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from interview_engine.llm import LLM 


def hint_agent(state: InterviewState) -> InterviewState:
    """
        Step 2: Hint Agent

        사용하는 state 필드:
            - current_user_code: 현재 사용자의 코드 (str)
            - problem_description: 문제 설명 텍스트 (str)
            - user_algorithm_category: 사용자가 예상한 알고리즘 카테고리 (str)
            - real_algorithm_category: 실제 정답 알고리즘 카테고리 (str)
            - test_cases: 테스트 케이스 정보 (str or JSON string)
            - hint_count: 지금까지 사용한 힌트 횟수 (int)
            - conversation_log: 힌트/대화 로그 리스트 (list)

        동작:
            - 현재 코드/문제/카테고리 정보를 바탕으로 맞춤형 힌트를 생성
                - LLM을 호출해 힌트 텍스트 생성
                - 대화 로그에 힌트를 기록
                - hint_count를 1 증가
                - tts_text에 hint_text를 저장 (TTS 재생용)
    """

    # 1. Redis 상태에서 데이터 로드
    current_user_code = state.get("current_user_code", "")
    problem_description = state.get("problem_description", "")
    user_algorithm_category = state.get("user_algorithm_category", "")
    real_algorithm_category = state.get("real_algorithm_category", "")
    test_cases = state.get("test_cases", "제공되지 않음")
    hint_count = state.get("hint_count", 0)
    
    # conversation_log는 기존 내역을 가져오거나 새로 만듦
    conversation_log = state.get("conversation_log", [])

    # 2. 상황 판단 로직
    # 전략 불일치 감지: 사용자가 생각한 방식과 실제 정답 방식이 다른 경우
    is_strategy_mismatch = (
        user_algorithm_category != "" 
        and real_algorithm_category != ""
        and user_algorithm_category != real_algorithm_category
    )

    # 3. 프롬프트 구성
    # [전략 불일치 시 추가 지시사항]
    strategy_instruction = ""
    if is_strategy_mismatch:
        strategy_instruction = (
            f"""
            [중요 감지!] 사용자는 이 문제를 '{user_algorithm_category}' 방식으로 풀겠다고 했으나,
            실제로는 '{real_algorithm_category}' 방식이 적합합니다.
            현재 코드가 잘못된 접근 방식을 고수하고 있다면, 구현 디테일보다는
            알고리즘 접근 방식 자체를 재고하도록 유도하는 질문을 최우선으로 던지세요.
            """
        )

    # [힌트 깊이 조절]
    depth_instruction = (
        f"""
        현재 힌트 사용 횟수는 {hint_count}회입니다.
        횟수가 0~1회라면 추상적인 개념이나 방향만 제시하고,
        횟수가 많아질수록 조금 더 구체적인 코드 로직이나 놓친 엣지 케이스를 언급하세요.
        """
    )

    system_prompt = (
        "당신은 라이브 코딩 테스트의 친절하고 통찰력 있는 '힌트 AI'입니다.\n"
        "정답 코드를 절대 직접 알려주지 말고, 소크라테스식 문답법으로 사용자가 스스로 깨닫게 하세요.\n\n"
        "[문제 정보]\n"
        f"- 문제 내용: {problem_description}\n"
        f"- 사용자 예상 카테고리: {user_algorithm_category}\n"
        f"- 실제 정답 카테고리: {real_algorithm_category}\n"
        f"- 테스트 케이스 정보: {test_cases}\n\n"
        "[생성 지침]\n"
        f"1. {strategy_instruction}\n"
        f"2. {depth_instruction}\n"
        "3. **출력 형식**: 마크다운 없이 줄바꿈으로 구분된 2~3문장의 텍스트. (한국어 구어체, 존댓말)\n"
        "4. **내용 구성**: \n"
        "   - (공감/상태인식): '지금 ~~부분을 구현하고 계시네요' 또는 '접근 방식이 흥미롭습니다'.\n"
        "   - (핵심 질문): '혹시 ~~한 경우는 고려해보셨나요?' 또는 '~~자료구조를 쓰면 어떨까요?'\n"
    )

    human_prompt = (
        f"""
        아래는 사용자의 현재 코드입니다.
        ```{current_user_code or '코드가 비어 있습니다.'}```
        위 코드를 분석하고 가장 적절한 힌트를 주세요.
        """
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ]

    try:
        response = LLM.invoke(messages)
        hint_text = getattr(response, "content", "").strip()

        if hint_text:
            # 대화 로그에 힌트 기록 (Context 공유용)
            new_log_entry = {
                "role": "assistant",
                "content": hint_text,
                "type": "hint",
                "timestamp": "now()" # 필요 시 실제 timestamp 함수 사용
            }
            updated_logs = conversation_log + [new_log_entry]

            # 상태 반환 (LangGraph가 Merge 처리)
            return {
                "hint_text": hint_text,
                "hint_count": hint_count + 1,
                "conversation_log": updated_logs,
                "tts_text": hint_text, # TTS 재생용 텍스트
            }
            
    except Exception as e:
        # 에러 발생 시 로그만 남기고 상태 변경 없음
        print(f"[HintAgent Error] {e}")
        return {}

    return {}
