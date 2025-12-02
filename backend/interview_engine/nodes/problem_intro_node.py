from interview_engine.state import InterviewState
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain.chat_models import init_chat_model

def __problem_intro_template():
    return [
        (
        "system",
        '''
        당신은 라이브 코딩 인터뷰의 "Problem Intro Agent"입니다.

        당신의 작업:
        1) 입력된 코딩 문제 설명을 TTS로 읽기 좋은 자연스러운 한국어로 다시 설명합니다.
        2) 사용자가 문제 해결 전략을 말하도록 유도하는 전략 질문을 생성합니다.
        3) 사용자가 긴장을 풀 수 있도록 스몰톡을 포함

        [출력(JSON)]
        반드시 아래 형식만 출력하세요:

        {{
        "smalltalk": "<인사 또는 긴장 완화 멘트>",
        "intro": "<문제를 TTS 친화적으로 풀어쓴 설명>",
        "strategy_question": "<문제 해결 접근 전략을 묻는 질문>"
        }}

        [작성 규칙]
        - smalltalk: 짧은 문장으로 1~2문장 구성.
        - intro: 구어체, 짧은 문장 위주, 핵심 요구사항 중심.
        - strategy_question: 알고리즘/접근 방식/복잡도를 설명하도록 유도.
        - JSON 외 텍스트 절대 금지.
        '''),
        (
            "human",
            """
                아래 JSON을 참고해서 출력 JSON을 만들어 주세요.

                입력:
                {{
                "user_name": "{user_name}",
                "problem_description": "{problem_description}"
                }}
            """
        )
    ]
    
    
    
def problem_intro_agent(state:InterviewState) -> InterviewState:
    
    problem_intro_prompt = ChatPromptTemplate.from_messages(__problem_intro_template())
    problem_intro_parser = JsonOutputParser()
    model = init_chat_model("gpt-5-nano")

    problem_intro_chain = problem_intro_prompt | model | problem_intro_parser
    llm_input = {
        "user_name": state["user_name"],
        "problem_description": state["problem_description"],
    }
    try:
        data = problem_intro_chain.invoke(llm_input)
        # data는 dict 형태라고 가정 (JsonOutputParser 사용)
    except Exception as e:
        # LLM/파싱 에러가 나면 state에 남기고 그대로 리턴
        state["problem_intro_error"] = str(e)
        return state
    
    # 2) 결과 꺼내기
    smalltalk = (data.get("smalltalk") or "").strip()
    intro = (data.get("intro") or "").strip()
    strategy_question = (data.get("strategy_question") or "").strip()
    
    # 3) tts and HITL
    state["current_question_text"] =  "\n".join([p for p in [smalltalk, intro, strategy_question] if p])
    state["await_human"] = True
    
    return state