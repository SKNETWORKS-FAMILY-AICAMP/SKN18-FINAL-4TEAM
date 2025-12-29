from interview_engine.state import CodingState
from langchain_core.messages import HumanMessage, SystemMessage
from interview_engine.llm import get_llm 


def hint_agent(state: CodingState) -> CodingState:
    """
        Step 2: Hint Agent

        사용하는 state 필드:
            - current_user_code: 현재 사용자의 코드 (str)
            - problem_description: 문제 설명 텍스트 (str)
            - real_algorithm_category: 실제 정답 알고리즘 카테고리 (str)
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
    real_algorithm_category = state.get("real_algorithm_category", "")
    hint_count = state.get("hint_count", 0)
    conversation_log = state.get("conversation_log", [])
    hint_request_text = (state.get("stt_text") or "").strip()

    situation_instruction = (
        "현재 사용자가 **코드를 작성 중**입니다.\n"
        "작성된 코드를 분석하여 논리적 오류, 놓친 엣지 케이스, 비효율적인 부분을 찾으세요.\n"
        "구현이 막힌 부분이 어디인지 파악하고 뚫어줄 수 있는 질문을 던지세요."
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
        f"- 실제 정답 카테고리: {real_algorithm_category}\n"
        f"- 이번 힌트를 요청하며 사용자가 말한 내용: {hint_request_text}\n\n"
        "[생성 지침]\n"
        f"1. 사용자가 방금 힌트를 요청하며 말한 내용을 반드시 반영해서,\n"
            "어떤 부분(예: 특정 테스트케이스, 알고리즘 아이디어, 구현 단계)에서 막혔는지 먼저 한 문장으로 정리한 뒤,\n"
            "그 부분을 뚫어줄 수 있는 질문/힌트를 중심으로 2~3문장을 생성하세요.\n "
        f"2. {depth_instruction}\n"
        f"3. **현재 상황**: {situation_instruction}\n"
        f"4. 출력 형식: 마크다운 없이 줄바꿈으로 구분된 2~3문장의 텍스트. (한국어 구어체, 정중한 존댓말)\n"
    )

    human_prompt = (
        "아래는 사용자의 현재 코드입니다.\n"
        f"```{current_user_code}```\n"
        f"아래는 사용자의 힌트요청 내용입니다.\n"
        f"{hint_request_text}\n"
        "위 코드를 분석하고, 사용자가 막힌 부분(사용자의 힌트 요청 내용)을 기준으로 "
        "가장 적절한 힌트를 주세요.\n"
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ]

    try:
        print("[LLM][hint_agent] system_prompt:", system_prompt, flush=True)
        print("[LLM][hint_agent] human_prompt:", human_prompt, flush=True)
        model = get_llm("hint")
        response = model.invoke(messages, max_tokens=200)
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
