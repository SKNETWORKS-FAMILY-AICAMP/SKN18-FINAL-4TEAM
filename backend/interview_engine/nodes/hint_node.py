from interview_engine.state import InterviewState
from typing import TypedDict, List, Any, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from interview_engine.llm import LLM 


def hint_agent(state: InterviewState) -> InterviewState:
    """
    Hint Agent 노드
    - 사용자의 코드와 의도(Step1 카테고리)를 분석하여 맞춤형 힌트를 제공합니다.
    - Session Manager 없이 Redis 상태를 기반으로 독립적으로 판단합니다.
    """

    # 1. Redis 상태에서 데이터 로드 (Safe Get)
    current_user_code = state.get("current_user_code", "")
    problem_description = state.get("problem_description", "")
    user_algorithm_category = state.get("user_algorithm_category", "미정")
    real_algorithm_category = state.get("real_algorithm_category", "미정")
    test_cases = state.get("test_cases", "제공되지 않음")
    
    hint_trigger = state.get("hint_trigger", "manual")
    hint_count = state.get("hint_count", 0)
    
    # conversation_log는 기존 내역을 가져오거나 새로 만듦
    conversation_log = state.get("conversation_log", [])

    # 2. 상황 판단 로직 (Router Logic embedded in Prompt)
    
    # 전략 불일치 감지: 사용자가 생각한 방식과 실제 정답 방식이 다른 경우
    is_strategy_mismatch = (
        user_algorithm_category != "미정" 
        and real_algorithm_category != "미정"
        and user_algorithm_category != real_algorithm_category
    )

    # 트리거 타입에 따른 서두 설정
    if hint_trigger == "manual":
        trigger_context = (
            "상황: 사용자가 직접 '힌트' 버튼을 눌러 도움을 요청했습니다. "
            "사용자의 자존감을 지켜주면서도, 막힌 부분을 시원하게 긁어주는 조언이 필요합니다."
        )
    else:  # auto_quality
        trigger_context = (
            "상황: 코드 품질이 낮거나 오랫동안 진전이 없어 시스템이 먼저 개입합니다. "
            "거부감이 들지 않도록 '어려움이 있으신 것 같아 힌트를 준비했어요' 같은 공감 멘트로 시작하세요."
        )

    # 3. 프롬프트 구성 (Prompt Engineering)
    
    # [전략 불일치 시 추가 지시사항]
    strategy_instruction = ""
    if is_strategy_mismatch:
        strategy_instruction = (
            f"\n[중요 감지!] 사용자는 이 문제를 '{user_algorithm_category}' 방식으로 풀겠다고 했으나, "
            f"실제로는 '{real_algorithm_category}' 방식이 적합합니다. "
            "현재 코드가 잘못된 접근 방식을 고수하고 있다면, 구현 디테일보다는 "
            "**'알고리즘 접근 방식 자체를 재고'**하도록 유도하는 질문을 최우선으로 던지세요."
        )

    # [힌트 깊이 조절]
    depth_instruction = (
        f"현재 힌트 사용 횟수는 {hint_count}회입니다. "
        "횟수가 0~1회라면 추상적인 개념이나 방향만 제시하고, "
        "횟수가 많아질수록 조금 더 구체적인 코드 로직이나 놓친 엣지 케이스를 언급하세요."
    )

    system_prompt = (
        "당신은 라이브 코딩 테스트의 친절하고 통찰력 있는 '힌트 AI'입니다.\n"
        "정답 코드를 절대 직접 알려주지 말고, 소크라테스식 문답법으로 사용자가 스스로 깨닫게 하세요.\n\n"
        "[문제 정보]\n"
        f"- 문제 내용: {problem_description}\n"
        f"- 사용자 예상 카테고리: {user_algorithm_category}\n"
        f"- 실제 정답 카테고리: {real_algorithm_category}\n"
        f"- 테스트 케이스 정보: {test_cases}\n\n"
        f"{trigger_context}\n\n"
        "[생성 지침]\n"
        f"1. {strategy_instruction}\n"
        f"2. {depth_instruction}\n"
        "3. **출력 형식**: 마크다운 없이 줄바꿈으로 구분된 2~3문장의 텍스트. (한국어 구어체, 존댓말)\n"
        "4. **내용 구성**: \n"
        "   - (공감/상태인식): '지금 ~~부분을 구현하고 계시네요' 또는 '접근 방식이 흥미롭습니다'.\n"
        "   - (핵심 질문): '혹시 ~~한 경우는 고려해보셨나요?' 또는 '~~자료구조를 쓰면 어떨까요?'\n"
    )

    human_prompt = (
        f"[사용자의 현재 코드]\n"
        f"```{current_user_code or '코드가 비어 있습니다.'}```\n\n"
        "위 코드를 분석하고 가장 적절한 힌트를 주세요."
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ]

    # 4. LLM 실행 및 상태 업데이트
    try:
        # 지정된 LLM 모듈 사용
        response = LLM.invoke(messages)
        hint_text = getattr(response, "content", "").strip()

        if hint_text:
            # (1) 대화 로그에 힌트 기록 (Context 공유용)
            new_log_entry = {
                "role": "assistant",
                "content": hint_text,
                "type": "hint",
                "timestamp": "now()" # 필요 시 실제 timestamp 함수 사용
            }
            updated_logs = conversation_log + [new_log_entry]

            # (2) 상태 반환 (LangGraph Merge 처리)
            return {
                "hint_text": hint_text,
                "hint_count": hint_count + 1,
                "conversation_log": updated_logs,
                "tts_text": hint_text,
            }
            
    except Exception as e:
        # 에러 발생 시 로그만 남기고 상태 변경 없음 (시스템 안정성)
        print(f"[HintAgent Error] {e}")
        return {}

    # 힌트 생성 실패 시 빈 상태 반환
    return {}
