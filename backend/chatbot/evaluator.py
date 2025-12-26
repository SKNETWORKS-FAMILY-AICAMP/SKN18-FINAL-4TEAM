#-----------------------
# agent.py 
#-----------------------

"""
handle_request는 기존 로직에서 변경되었으며, Evaluator 검증 로직이 추가되었습니다.
"""

def handle_request(payload: Dict[str, Any], store=None):
    """
    Main Agent 실행 -> (필요시) Evaluator 검증 -> 결과 반환
    """
    # 1. Context Pack 구성 (기존 로직)
    context_pack = build_context_pack(payload)
    
    # 2. 필수 프로필 검증 (기존 로직)
    missing = missing_profile_fields(context_pack["profile"])
    if missing:
        ask = f"프로필 보완이 필요해요. {', '.join(missing)} 값을 알려주시면 계획을 세울게요."
        return {"messages": [AIMessage(content=ask)], "agent": "main", "context": context_pack}

    # 3. 에이전트 준비
    user_id = context_pack["request"].get("user_id", "unknown")
    main_agent = create_main_agent(user_id=user_id, store=store)
    
    # 초기 입력 상태 설정
    current_state = {
        **context_pack,
        "messages": [HumanMessage(content=context_pack["request"].get("message", ""))]
    }

    # -------------------------------------------------------
    # [안전 장치 1] 평가가 필요한 의도인지 확인 (잡담은 패스)
    # -------------------------------------------------------
    intent = context_pack["request"].get("intent", "")
    should_evaluate = intent in ["plan", "research"]  # 평가할 Intent 목록
    
    # 평가가 필요 없다면 바로 실행 후 리턴 (기존 로직과 동일)
    if not should_evaluate:
        return main_agent.invoke(current_state)

    # -------------------------------------------------------
    # [Loop] 평가 및 재시도 로직
    # -------------------------------------------------------
    evaluator = evaluator_agent()
    MAX_RETRIES = 2
    
    # 최종 반환값을 담을 변수 (실패 시 마지막 시도라도 반환하기 위해)
    last_response = None 

    for attempt in range(MAX_RETRIES + 1):
        # (A) Main Agent 실행
        # invoke 시 마다 이전 대화(재시도 포함)가 current_state['messages']에 누적되어 전달됨
        response = main_agent.invoke(current_state)
        last_response = response 

        # (B) Evaluator 실행
        # Main Agent의 응답을 평가자가 읽을 수 있도록 전달
        eval_context = {**context_pack, "latest_response": response}
        
        try:
            eval_result = evaluator.invoke(eval_context)
            verdict = eval_result["evaluation"]
        except Exception as e:
            # [안전 장치 2] 평가기 에러 시 Main 결과 그대로 반환 (사용자 경험 보호)
            print(f"⚠️ Evaluator Error: {e}")
            return response

        # (C) PASS 판정 시 즉시 리턴
        if verdict["decision"] == "PASS":
            response["evaluation_meta"] = verdict
            return response
            
        # (D) REJECT 판정 시 재시도 준비
        if attempt < MAX_RETRIES:
            print(f"🔄 반려됨 ({attempt+1}/{MAX_RETRIES}): {verdict['violation']}")
            
            feedback_msg = (
                f"[System Notice] 생성된 계획이 품질 기준에 미달하여 재작성합니다.\n"
                f"- 문제점: {verdict['violation']}\n"
                f"- 수정 지침: {verdict['feedback']}"
            )
            
            # [안전 장치 3] 메시지 히스토리 관리
            # Main Agent가 뱉은 결과(response['messages'])와 피드백을
            # 다음 턴의 입력(current_state['messages'])에 추가
            if "messages" in response:
                current_state["messages"].extend(response["messages"])
            current_state["messages"].append(HumanMessage(content=feedback_msg))
            
        else:
            # 재시도 횟수 초과 -> 실패했지만 일단 결과 반환 (Warning 포함)
            response["evaluation_meta"] = verdict
            response["warning"] = "검증 기준을 완전히 통과하지 못했습니다."
            return response

    return last_response


def evaluator_agent():
    """결과물 품질 검증 및 정합성 체크 에이전트."""

    # 평가 기준이 명시된 시스템 프롬프트
    EVALUATOR_SYSTEM_PROMPT = """
    당신은 엄격한 'AI 코칭 품질 관리자(QA)'입니다.
    Main Agent가 생성한 계획이나 답변이 사용자의 프로필과 제약조건을 준수했는지 검증하세요.

    [검증 기준]
    1. **프로필 정합성**: 
    - 사용자의 'skill_level'에 맞는 난이도인가?
    - 'weekly_hours'(주간 가용 시간) 내에 소화 가능한 분량인가?
    2. **요구사항 충족**:
    - 사용자의 질문(Message)과 의도(Intent)를 정확히 해결했는가?
    - 필수 필드(week_goals, focus_areas 등)가 누락되지 않았는가?
    3. **논리적 완결성**:
    - 목표(Goal)와 세부 액션(Action)이 논리적으로 연결되는가?
    - 날짜나 기한이 현실적인가?

    결과는 반드시 JSON 포맷으로 반환하세요.
    """

    evaluator_prompt = ChatPromptTemplate.from_messages([
        ("system", EVALUATOR_SYSTEM_PROMPT),
        ("human", 
        "--- [사용자 프로필] ---\n{profile}\n\n"
        "--- [사용자 요청] ---\n{request}\n\n"
        "--- [Main Agent 답변] ---\n{agent_output}\n\n"
        "위 내용을 바탕으로 평가(JSON)를 수행해:"
        )
    ])

    def run(context: Dict[str, Any]) -> Dict[str, Any]:
        # Main Agent의 출력물 추출 (context['messages']의 마지막 AIMessage 혹은 특정 키)
        # 여기서는 context에 'latest_response' 혹은 Main Agent의 결과가 병합되어 있다고 가정
        agent_output = context.get("latest_response", "")
        
        # 만약 Main Agent가 구조화된 plan을 뱉었다면 그걸 검증
        if isinstance(agent_output, dict) and "plan" in agent_output:
            agent_output_str = str(agent_output["plan"])
        elif isinstance(agent_output, AIMessage):
            agent_output_str = agent_output.content
        else:
            agent_output_str = str(agent_output)

        inputs = {
            "profile": context.get("profile", {}),
            "request": context.get("request", {}),
            "agent_output": agent_output_str
        }

        try:
            # LLM 호출 (Evaluator는 논리력이 중요하므로 Main과 같은 고성능 모델 권장)
            verdict: EvaluationVerdict = (evaluator_prompt | LLM | evaluator_parser).invoke(inputs)
            verdict_dict = verdict.model_dump()
        except Exception as e:
            # 파싱 에러 시 안전하게 PASS 처리하거나 에러 로그 반환
            verdict_dict = {
                "decision": "PASS", 
                "score": 50, 
                "feedback": f"평가 중 에러 발생(자동 통과): {str(e)}", 
                "violation": None
            }

        return {
            "agent": "evaluator",
            "evaluation": verdict_dict,
            "context": context
        }

    return RunnableLambda(run)


#-----------------------
# models.py
#-----------------------
from typing import Literal, Optional
from langchain_core.pydantic_v1 import BaseModel, Field

class EvaluationVerdict(BaseModel):
    decision: Literal["PASS", "REJECT"] = Field(..., description="통과 여부")
    score: int = Field(..., description="0~100 사이의 품질 점수")
    feedback: Optional[str] = Field(None, description="REJECT일 경우 수정 지침, PASS면 칭찬이나 코멘트")
    violation: Optional[str] = Field(None, description="위반한 제약조건이 있다면 명시 (예: 시간 초과, 레벨 불일치)")

# 평가자 전용 파서
evaluator_parser = JsonOutputParser(pydantic_object=EvaluationVerdict)


# 기존 로직에서 조금 변경됨
class UserNextAction(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id")
    action_id = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    due = models.DateTimeField(null=True, blank=True)
    priority = models.CharField(max_length=20, null=True, blank=True)
    status = models.CharDateTimeField(auto_now_add=True)
    updated_at = modelField(max_length=20, null=True, blank=True)  # todo/doing/done
    created_at = models.s.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_next_actions"
        constraints = [
            models.UniqueConstraint(fields=["user", "action_id"], name="uq_user_action")
        ]
        indexes = [
            models.Index(fields=["user", "status"], name="idx_next_actions_status"),
        ]


#-----------------------
# views.py
#-----------------------
from .agent_service import handle_request 

class ChatView(APIView):
    def post(self, request):
        payload = request.data
        
        # 여기서 'handle_request'를 호출하면
        # 내부적으로 평가 루프가 다 돌아간 뒤의 '최종 결과'만 리턴됩니다.
        response_data = handle_request(payload) 
        
        return Response(response_data)