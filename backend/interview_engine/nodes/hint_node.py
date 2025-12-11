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
    conversation_log = state.get("conversation_log", [])

    # 2. 상황 판단 로직
    
    # [NEW] 코드가 비어있는지 확인 (공백 제거 후 길이 체크)
    is_empty_code = not current_user_code or len(current_user_code.strip()) == 0

    # 전략 불일치 감지
    is_strategy_mismatch = (
        user_algorithm_category != "" 
        and real_algorithm_category != ""
        and user_algorithm_category != real_algorithm_category
    )

    # 3. 프롬프트 구성

    # [상황별 가이드라인 생성]
    if is_empty_code:
        # 코드가 없을 때: 시작 가이드 모드
        situation_instruction = (
            "현재 사용자는 **아직 코드를 한 줄도 작성하지 않았습니다.**\n"
            "코드 분석을 하지 말고, 문제 해결을 위한 **초기 접근법**을 생각하도록 도와주세요.\n"
            "- 문제의 핵심 요구사항을 이해했는지 물어보거나\n"
            "- 입출력 예시를 통해 규칙을 파악하도록 유도하거나\n"
            "- 어떤 자료구조나 알고리즘을 쓸 생각인지 질문하세요."
        )
    else:
        # 코드가 있을 때: 코드 분석 및 디버깅 모드
        situation_instruction = (
            "현재 사용자가 **코드를 작성 중**입니다.\n"
            "작성된 코드를 분석하여 논리적 오류, 놓친 엣지 케이스, 비효율적인 부분을 찾으세요.\n"
            "구현이 막힌 부분이 어디인지 파악하고 뚫어줄 수 있는 질문을 던지세요."
        )

    # [전략 불일치 시 추가 지시사항] (기존 로직 유지하되, 빈 코드일 때도 카테고리는 선택했을 수 있으므로 적용)
    strategy_instruction = ""
    if is_strategy_mismatch:
        strategy_instruction = (
            f"""
            [중요 감지!] 사용자는 '{user_algorithm_category}' 방식을 선택했으나, 정답은 '{real_algorithm_category}'입니다.
            구현 시작 전에 이 접근 방식이 맞는지 다시 한 번 고민하게 만드세요.
            예: "이 문제의 입력 크기를 고려했을 때, 선택하신 알고리즘이 효율적일까요?"
            """
        )

    # [힌트 깊이 조절]
    depth_instruction = (
        f"현재 힌트 사용 횟수는 {hint_count}회입니다. 횟수가 많을수록 더 구체적으로 조언하세요."
    )

    system_prompt = (
        "당신은 라이브 코딩 테스트의 친절하고 통찰력 있는 '힌트 AI'입니다.\n"
        "절대로 정답을 직접 알려주지 말고, 소크라테스식 문답법을 사용하세요.\n\n"
        "[문제 정보]\n"
        f"- 문제 내용: {problem_description}\n"
        f"- 사용자 예상 카테고리: {user_algorithm_category}\n"
        f"- 실제 정답 카테고리: {real_algorithm_category}\n\n"
        "[생성 지침]\n"
        f"1. **현재 상황**: {situation_instruction}\n"
        f"2. {strategy_instruction}\n"
        f"3. {depth_instruction}\n"
        "4. **출력 형식**: 마크다운 없이 줄바꿈으로 구분된 2~3문장의 텍스트. (한국어 구어체, 정중한 존댓말)\n"
    )

    # [Human Prompt 분기 처리]
    if is_empty_code: # 코드가 비어있는 경우
        human_prompt = (
            "사용자가 아직 코드를 작성하지 않았습니다."
            "문제 풀이를 시작할 수 있도록 힌트를 주세요."
        )
    else: # 코드가 있는 경우
        human_prompt = (
            f"""
            아래는 사용자의 현재 코드입니다.
            ```{current_user_code}```
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
