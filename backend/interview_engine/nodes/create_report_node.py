# backend/interview_engine/nodes/create_report_node.py
from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime, timezone
from interview_engine.llm import get_llm
from interview_engine.utils.checkpoint_reader import load_chapter_channel_values
from langchain_core.messages import SystemMessage, HumanMessage
from django.core.cache import cache


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clamp01(x: float) -> float:
    try:
        x = float(x)
    except Exception:
        return 0.0
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def _grade_from_score(score01: float) -> str:
    s = _clamp01(score01)
    if s >= 0.95:
        return "A+"
    if s >= 0.90:
        return "A"
    if s >= 0.85:
        return "B+"
    if s >= 0.80:
        return "B"
    if s >= 0.75:
        return "C+"
    if s >= 0.70:
        return "C"
    if s >= 0.60:
        return "D"
    return "F"


def _safe_str(x: Any) -> str:
    return "" if x is None else str(x)


def _level_from_count(count: int) -> str:
    if count >= 20:
        return "확실"
    if count >= 10:
        return "의심"
    if count >= 5:
        return "주의"
    return "정상"


def _format_qa_history(qa_history: List[Dict]) -> str:
    """QA 히스토리를 텍스트로 포맷팅"""
    if not qa_history:
        return "(질문/응답 내역 없음)"
    
    lines: List[str] = []
    for i, qa in enumerate(qa_history, 1):
        q = qa.get("question", "")
        a = qa.get("answer", "")
        lines.append(f"Q{i}: {q}")
        lines.append(f"A{i}: {a}")
        lines.append("")
    
    return "\n".join(lines)


def _generate_problem_solving_evaluation(
    initial_strategy: str,
    final_code: str,
    problem_text: str,
    qa_history: List[Dict],
) -> Dict[str, Any]:
    """
    문제 해결 능력 평가 생성
    """
    system_prompt = """당신은 코딩 면접 평가 전문가입니다. 
응시자의 초기 전략 답변과 최종 코드를 비교하여 문제 해결 능력을 평가하세요."""

    qa_text = _format_qa_history(qa_history)
    
    user_prompt = f"""
## 문제
{problem_text[:800]}

## 초기 전략 답변
{initial_strategy if initial_strategy else "(전략 답변 없음)"}

## 최종 제출 코드
```python
{final_code[:1500]}
```

## 면접 중 질문/응답
{qa_text}

---

다음 형식으로 평가해주세요:

### PROBLEM_UNDERSTANDING
(문제를 정확히 이해했는지: "우수", "양호", "부족" 중 하나만 작성)

### UNDERSTANDING_FEEDBACK
(문제 이해도에 대한 2-3문장 설명)

### APPROACH_VALIDITY
(접근 방법의 적절성: "우수", "양호", "부족" 중 하나만 작성)

### CONSISTENCY_STATUS
(전략과 실제 구현의 일치도: "일치", "개선하여 구현", "불일치" 중 하나만 작성)

### CONSISTENCY_FEEDBACK
(일관성에 대한 구체적 설명 3-4문장. 초기 전략과 최종 코드를 비교하여 어떻게 구현했는지 설명)
"""

    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        print("[LLM][_generate_problem_eval_with_llm] system_prompt:", system_prompt, flush=True)
        print("[LLM][_generate_problem_eval_with_llm] user_prompt:", user_prompt, flush=True)
        model = get_llm("report")
        response = model.invoke(messages)
        content = response.content
        
        # 응답 파싱
        result = {
            "problem_understanding": "평가 중",
            "understanding_feedback": "",
            "approach_validity": "평가 중",
            "consistency_status": "분석 중",
            "consistency_feedback": "",
        }
        
        sections = content.split("###")
        for section in sections:
            section = section.strip()
            if section.upper().startswith("PROBLEM_UNDERSTANDING"):
                text = section.replace("PROBLEM_UNDERSTANDING", "", 1).strip()
                result["problem_understanding"] = text[:50]  # 첫 50자만
            elif section.upper().startswith("UNDERSTANDING_FEEDBACK"):
                result["understanding_feedback"] = section.replace("UNDERSTANDING_FEEDBACK", "", 1).strip()
            elif section.upper().startswith("APPROACH_VALIDITY"):
                text = section.replace("APPROACH_VALIDITY", "", 1).strip()
                result["approach_validity"] = text[:50]
            elif section.upper().startswith("CONSISTENCY_STATUS"):
                text = section.replace("CONSISTENCY_STATUS", "", 1).strip()
                result["consistency_status"] = text[:50]
            elif section.upper().startswith("CONSISTENCY_FEEDBACK"):
                result["consistency_feedback"] = section.replace("CONSISTENCY_FEEDBACK", "", 1).strip()
        
        return result
        
    except Exception as e:
        print(f"[문제 해결 능력 평가 생성 실패] {e}", flush=True)
        import traceback
        traceback.print_exc()
        
        return {
            "problem_understanding": "평가 오류",
            "understanding_feedback": "평가 시스템에 일시적인 문제가 있습니다.",
            "approach_validity": "평가 오류",
            "consistency_status": "분석 실패",
            "consistency_feedback": "평가를 완료하지 못했습니다.",
        }


def _generate_detailed_feedback_with_llm(
    code: str,
    problem_text: str,
    code_score: float,
    problem_score: float,
    code_feedback: str,
    problem_feedback: str,
    evidence: Dict[str, Any],
) -> Dict[str, str]:
    """
    LLM을 사용해서 상세한 피드백 생성:
    - strength: 강점
    - improvement: 개선점
    - comprehensive_evaluation: 종합 평가
    - annotated_code: 주석 달린 코드
    - cheating_warning: 부정행위 경고 (필요시)
    """
    
    # 힌트 사용 정보
    hint_count = evidence.get("hint_count", 0)
    question_cnt = evidence.get("question_cnt", 0)
    
    system_prompt = """당신은 코딩 면접 평가 전문가입니다. 
응시자의 코드와 면접 과정을 분석하여 상세하고 건설적인 피드백을 제공하세요.
피드백은 구체적이고 실행 가능해야 하며, 응시자의 성장을 돕는 방향으로 작성하세요."""

    user_prompt = f"""
다음 코딩 면접 결과를 분석하고 상세한 피드백을 작성해주세요.

## 문제
{problem_text[:1000]}

## 제출 코드
```python
{code[:2000]}
```

## 평가 점수
- 코드 품질/협업 점수: {code_score:.2f}
- 문제 해결 점수: {problem_score:.2f}

## 자동 평가 피드백
### 코드 품질
{code_feedback[:500]}

### 문제 해결
{problem_feedback[:500]}

## 면접 진행 정보
- 힌트 사용 횟수: {hint_count}회
- 질문/응답 횟수: {question_cnt}회

---

다음 형식으로 피드백을 작성해주세요:

### STRENGTH
(2-3문장으로 응시자의 강점을 구체적으로 설명. 잘한 점, 좋은 접근법, 돋보이는 부분 등)

### IMPROVEMENT
(2-3문장으로 개선이 필요한 부분을 구체적으로 설명. 단순 지적이 아닌 개선 방향 제시)

### COMPREHENSIVE_EVALUATION
(5-7문장으로 종합적인 평가. 전반적인 문제 해결 능력, 코드 품질, 커뮤니케이션 능력, 향후 개발 방향 등을 포괄적으로 평가)

### ANNOTATED_CODE
(원본 코드에 주석을 달아서 제공. 각 부분에 대해 ✅ 좋은 점, ⚠️ 개선 필요, ❌ 감점 요소를 표시)
```python
# 주석이 달린 코드를 여기에 작성
```

### CHEATING_WARNING
(부정행위 의심 사항이 있다면 작성, 없으면 "없음"이라고만 작성)
"""

    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        print("[LLM][_generate_detailed_feedback_with_llm] system_prompt:", system_prompt, flush=True)
        print("[LLM][_generate_detailed_feedback_with_llm] user_prompt:", user_prompt, flush=True)
        model = get_llm("report")
        response = model.invoke(messages)
        content = response.content
        
        # 응답 파싱
        result = {
            "strength": "",
            "improvement": "",
            "comprehensive_evaluation": "",
            "annotated_code": "",
            "cheating_warning": ""
        }
        
        # 간단한 파싱 (### 기준으로 분리)
        sections = content.split("###")
        for section in sections:
            section = section.strip()
            if section.upper().startswith("STRENGTH"):
                result["strength"] = section.replace("STRENGTH", "", 1).strip()
            elif section.upper().startswith("IMPROVEMENT"):
                result["improvement"] = section.replace("IMPROVEMENT", "", 1).strip()
            elif section.upper().startswith("COMPREHENSIVE_EVALUATION"):
                result["comprehensive_evaluation"] = section.replace("COMPREHENSIVE_EVALUATION", "", 1).strip()
            elif section.upper().startswith("ANNOTATED_CODE"):
                # 코드 블록 추출
                code_section = section.replace("ANNOTATED_CODE", "", 1).strip()
                # ```python ... ``` 제거
                if "```python" in code_section:
                    code_section = code_section.split("```python", 1)[1]
                    if "```" in code_section:
                        code_section = code_section.split("```", 1)[0]
                result["annotated_code"] = code_section.strip()
            elif section.upper().startswith("CHEATING_WARNING"):
                warning = section.replace("CHEATING_WARNING", "", 1).strip()
                if warning and warning.lower() != "없음":
                    result["cheating_warning"] = warning
        
        # 기본값 설정 (LLM이 제대로 응답하지 않은 경우)
        if not result["strength"]:
            result["strength"] = "데이터를 불러오는 중 문제가 발생했습니다."
        if not result["improvement"]:
            result["improvement"] = "데이터를 불러오는 중 문제가 발생했습니다."
        if not result["comprehensive_evaluation"]:
            result["comprehensive_evaluation"] = "종합 평가 데이터를 불러오는 중입니다."
        if not result["annotated_code"]:
            result["annotated_code"] = code  # 원본 코드라도 표시
            
        return result
        
    except Exception as e:
        print(f"[LLM 피드백 생성 실패] {e}", flush=True)
        import traceback
        traceback.print_exc()
        
        # 폴백: 기본 메시지 반환
        return {
            "strength": "자동 평가 시스템에 일시적인 문제가 있습니다.",
            "improvement": "자동 평가 시스템에 일시적인 문제가 있습니다.",
            "comprehensive_evaluation": "자동 평가를 완료하지 못했습니다. 관리자에게 문의하세요.",
            "annotated_code": code,
            "cheating_warning": ""
        }


def create_report_node(state: Dict[str, Any]) -> Dict[str, Any]:
    print("[create_report_node] ENTER", flush=True)
    try:
        # 점수 추출
        code_feedback = _safe_str(state.get("code_collab_feedback") or "")

        problem_score = _clamp01(
            state.get("problem_eval_score")
            if state.get("problem_eval_score") is not None
            else state.get("problem_score")
            or 0.0
        )
        problem_feedback = _safe_str(
            state.get("problem_eval_feedback")
            if state.get("problem_eval_feedback") is not None
            else state.get("problem_feedback")
            or ""
        )

        # evidence
        problem_evidence = dict(state.get("problem_evidence") or {})
        code_collab_evidence = dict(state.get("code_collab_evidence") or {})

        # 35/30/35 기준 원점수 합산으로 최종 점수 계산
        code_quality_score_raw_35 = float(state.get("code_quality_score_35") or 0.0)
        code_collab_score_raw_30 = float(state.get("code_collab_score_30") or 0.0)
        problem_score_raw_35 = round(problem_score * 35.0, 2)

        code_quality_score_raw_35 = max(0.0, min(35.0, code_quality_score_raw_35))
        code_collab_score_raw_30 = max(0.0, min(30.0, code_collab_score_raw_30))
        problem_score_raw_35 = max(0.0, min(35.0, problem_score_raw_35))

        final_score_raw_100 = round(
            code_quality_score_raw_35 + code_collab_score_raw_30 + problem_score_raw_35,
            2,
        )
        code_quality_percent = round((code_quality_score_raw_35 / 35.0) * 100.0, 2)
        code_collab_percent = round((code_collab_score_raw_30 / 30.0) * 100.0, 2)
        problem_score_percent = round((problem_score_raw_35 / 35.0) * 100.0, 2)
        final_score01 = _clamp01(final_score_raw_100 / 100.0)
        final_grade = _grade_from_score(final_score01)

        # 코드와 문제 텍스트 추출
        code = _safe_str(problem_evidence.get("submitted_code") or "")
        problem_text = _safe_str(problem_evidence.get("problem_text") or "")
        
        # ✅ 세션 ID 가져오기
        meta = state.get("meta") or {}
        session_id = _safe_str(meta.get("session_id"))
        
        # ✅ 카테고리/난이도 초기화
        problem_category = "미분류"
        problem_difficulty = "미정"
        
        # ✅ problem_evidence가 비어있으면 직접 가져오기
        if not code and session_id:
            print("[DEBUG] problem_evidence에 코드 없음, 직접 Redis에서 가져옴", flush=True)
            code_key = f"livecoding:{session_id}:code"
            code_data = cache.get(code_key) or {}
            latest = code_data.get("latest") or {}
            code = _safe_str(latest.get("code") or "")
            print(f"[DEBUG] Redis에서 가져온 코드 길이: {len(code)}", flush=True)
        
        if not problem_text and session_id:
            print("[DEBUG] problem_evidence에 문제 없음, Redis problem_payload에서 가져옴", flush=True)
            # ✅ checkpoint 대신 problem_payload 사용!
            problem_key = f"livecoding:{session_id}:problem"
            problem_payload = cache.get(problem_key) or {}
            problem_text = _safe_str(problem_payload.get("problem") or "")
            print(f"[DEBUG] Redis problem_payload에서 가져온 문제 길이: {len(problem_text)}", flush=True)
            
            # ✅ 카테고리/난이도도 같이 가져오기!
            if "category" in problem_payload:
                problem_category = problem_payload.get("category") or "미분류"
                print(f"[DEBUG] Redis에서 카테고리 가져옴: {problem_category}", flush=True)
            
            if "difficulty" in problem_payload:
                problem_difficulty = problem_payload.get("difficulty") or "미정"
                print(f"[DEBUG] Redis에서 난이도 가져옴: {problem_difficulty}", flush=True)
            
            # ✅ 그래도 없으면 checkpoint 시도
            if not problem_text:
                print("[DEBUG] problem_payload도 없음, checkpoint에서 시도", flush=True)
                chap1 = load_chapter_channel_values(session_id, "chapter1")
                problem_text = _safe_str(chap1.get("problem_data") or "")
                print(f"[DEBUG] checkpoint에서 가져온 문제 길이: {len(problem_text)}", flush=True)
        
        # ✅ 2순위: 여전히 "미분류"/"미정"이면 meta에서 problem_id 가져와서 DB 조회
        if (problem_category == "미분류" or problem_difficulty == "미정"):
            # meta에서 problem_id 가져오기
            problem_id = meta.get("problem_id")
            
            # Redis meta에도 있을 수 있음
            if not problem_id and session_id:
                try:
                    meta_key = f"livecoding:{session_id}:meta"
                    cached_meta = cache.get(meta_key) or {}
                    problem_id = cached_meta.get("problem_id")
                    print(f"[DEBUG] Redis meta에서 problem_id 가져옴: {problem_id}", flush=True)
                except Exception as e:
                    print(f"[WARNING] Redis meta 조회 실패: {e}", flush=True)
            
            # DB 조회
            if problem_id:
                try:
                    from django.db import connection
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT category, difficulty
                            FROM coding_problem
                            WHERE problem_id = %s
                            LIMIT 1
                        """, [problem_id])
                        row = cursor.fetchone()
                        if row:
                            if problem_category == "미분류":
                                problem_category = row[0] or "미분류"
                            if problem_difficulty == "미정":
                                problem_difficulty = row[1] or "미정"
                            print(f"[DEBUG] DB에서 가져온 정보: 카테고리={problem_category}, 난이도={problem_difficulty}", flush=True)
                except Exception as e:
                    print(f"[WARNING] DB 조회 실패: {e}", flush=True)
                    
        # ✅ problem_evidence가 비어있으면 직접 가져오기
        if not code and session_id:
            print("[DEBUG] problem_evidence에 코드 없음, 직접 Redis에서 가져옴", flush=True)
            code_key = f"livecoding:{session_id}:code"
            code_data = cache.get(code_key) or {}
            latest = code_data.get("latest") or {}
            code = _safe_str(latest.get("code") or "")
            print(f"[DEBUG] Redis에서 가져온 코드 길이: {len(code)}", flush=True)
        
        if not problem_text and session_id:
            print("[DEBUG] problem_evidence에 문제 없음, Redis problem_payload에서 가져옴", flush=True)
            # ✅ checkpoint 대신 problem_payload 사용!
            problem_key = f"livecoding:{session_id}:problem"
            problem_payload = cache.get(problem_key) or {}
            problem_text = _safe_str(problem_payload.get("problem") or "")
            print(f"[DEBUG] Redis problem_payload에서 가져온 문제 길이: {len(problem_text)}", flush=True)
            
            # ✅ 그래도 없으면 checkpoint 시도
            if not problem_text:
                print("[DEBUG] problem_payload도 없음, checkpoint에서 시도", flush=True)
                chap1 = load_chapter_channel_values(session_id, "chapter1")
                problem_text = _safe_str(chap1.get("problem_data") or "")
                print(f"[DEBUG] checkpoint에서 가져온 문제 길이: {len(problem_text)}", flush=True)

        # ✅ checkpoint에서 데이터 가져오기
        initial_strategy = ""
        qa_history: List[Dict[str, Any]] = []
        
        if session_id:
            try:
                try:
                    # 1. checkpoint에서 시도
                    chap1 = load_chapter_channel_values(session_id, "chapter1")
                    initial_strategy = chap1.get("user_strategy_answer") or ""
                    
                    # 2. checkpoint에 없으면 Redis cache에서 시도
                    if not initial_strategy:
                        meta_key = f"livecoding:{session_id}:meta"
                        cached_meta = cache.get(meta_key) or {}
                        initial_strategy = cached_meta.get("strategy_answer") or ""
                        print(f"[Fallback] Redis cache에서 전략 답변: {initial_strategy[:50] if initial_strategy else 'None'}")
                    
                except Exception as e:
                    print(f"전략 답변 로드 실패: {e}")
        
                # chapter2에서 질문/응답 로그 가져오기
                chap2 = load_chapter_channel_values(session_id, "chapter2")
                print(f"[DEBUG] chap2 keys: {chap2.keys() if chap2 else 'None'}", flush=True)
        
                questions = chap2.get("question") or []
                answers = chap2.get("user_answers") or []
                print(f"[DEBUG] questions: {len(questions)}, answers: {len(answers)}", flush=True)

                # 첫 번째 답변이 전략 답변일 가능성
                if not initial_strategy and answers:
                    initial_strategy = answers[0]
                    print(f"[Fallback] chapter2 첫 답변 사용: {initial_strategy[:50]}")
                
                # ✅ Redis code 데이터에서 확인 (가장 확실한 방법)
                if not initial_strategy:
                    code_key = f"livecoding:{session_id}:code"
                    code_data = cache.get(code_key) or {}
                    
                    # question_history에 있을 수 있음
                    question_history = code_data.get("question_history") or []
                    if question_history:
                        # 첫 질문의 답변이 전략일 수 있음
                        for item in question_history:
                            if isinstance(item, dict):
                                answer = item.get("answer") or item.get("stt_text")
                                if answer:
                                    initial_strategy = answer
                                    print(f"[Fallback] question_history 사용: {initial_strategy[:50]}")
                                    break
                
                # ✅ 최후의 수단: 프론트엔드 localStorage
                # (프론트엔드에서 보낸 경우)
                if not initial_strategy:
                    # API를 통해 받았다면
                    initial_strategy = state.get("initial_strategy") or ""
                    
            except Exception as e:
                print(f"[Data Load Error] {e}", flush=True)
        
        # ✅ LLM을 사용한 상세 피드백 생성
        print("[create_report_node] LLM 피드백 생성 시작...", flush=True)
        llm_feedback = _generate_detailed_feedback_with_llm(
            code=code,
            problem_text=problem_text,
            code_score=code_collab_percent,
            problem_score=problem_score_percent,
            code_feedback=code_feedback,
            problem_feedback=problem_feedback,
            evidence={
                **problem_evidence,
                **code_collab_evidence,
            }
        )
        print("[create_report_node] LLM 피드백 생성 완료", flush=True)
        
        # ✅ 문제 해결 능력 평가 생성
        print("[create_report_node] 문제 해결 능력 평가 시작...", flush=True)
        ps_evaluation = _generate_problem_solving_evaluation(
            initial_strategy=initial_strategy,
            final_code=code,
            problem_text=problem_text,
            qa_history=qa_history,
        )
        print("[create_report_node] 문제 해결 능력 평가 완료", flush=True)

        # flags
        flags: List[str] = list(state.get("final_flags") or [])
        if final_score01 < 0.3 and "low_score" not in flags:
            flags.append("low_score")
        if code_quality_percent < 20.0 and "code_quality_risk" not in flags:
            flags.append("code_quality_risk")
        if problem_score_percent < 20.0 and "problem_solving_risk" not in flags:
            flags.append("problem_solving_risk")

        collab_rule_20 = float(code_collab_evidence.get("collab_rule_20") or 0.0)
        collab_llm_score_10 = float(code_collab_evidence.get("collab_llm_score_10") or 0.0)

        anti_cheat_summary: Dict[str, Any] = {}
        if session_id:
            event_key = f"livecoding:{session_id}:anti-cheat-events"
            event_payload = cache.get(event_key) or {}
            typing = event_payload.get("typing") or {}
            camera = event_payload.get("camera") or {}
            typing_count = sum(int(v or 0) for v in typing.values())
            camera_count = sum(int(v or 0) for v in camera.values())
            anti_cheat_summary = {
                "typing": {
                    "count": typing_count,
                    "level": _level_from_count(typing_count),
                    "details": typing,
                },
                "camera": {
                    "count": camera_count,
                    "level": _level_from_count(camera_count),
                    "details": camera,
                },
            }

        md = f"""# 코딩 테스트 결과 리포트

## 요약
- 최종 점수: **{final_score_raw_100:.2f}**
- 최종 등급: **{final_grade}**
- 코드 품질 원점수: **{code_quality_score_raw_35:.2f}/35**
- 협업 능력 원점수: **{code_collab_score_raw_30:.2f}/30** (rule {collab_rule_20:.2f}/20 + LLM {collab_llm_score_10:.2f}/10)

## 강점
{llm_feedback['strength']}

## 개선점
{llm_feedback['improvement']}

## 부정행위 기록 (참고용, 점수 반영 없음)
- 캠 기반: {anti_cheat_summary.get('camera', {}).get('count', 0)}회 ({anti_cheat_summary.get('camera', {}).get('level', '정상')})
- 타이핑/화면 이탈: {anti_cheat_summary.get('typing', {}).get('count', 0)}회 ({anti_cheat_summary.get('typing', {}).get('level', '정상')})

## 종합 평가
{llm_feedback['comprehensive_evaluation']}
"""

        # ✅ FinalEvalState에 모든 필드 저장
        state["final_score"] = round(final_score_raw_100, 0)
        state["final_grade"] = final_grade
        state["final_report_markdown"] = md
        state["final_flags"] = flags

        state["problem_eval_score"] = round(problem_score, 4)
        state["problem_eval_feedback"] = problem_feedback

        # ✅ graph_output에 프론트엔드가 필요한 모든 필드 포함
        state["graph_output"] = {
            # 점수들 (100점 만점)
            "prompt_score": round(code_quality_percent, 0),  # 프롬프트 점수 (코드 품질 점수 사용)
            "problem_solving_score": round(problem_score_percent, 2),
            "collaboration_score": round(code_collab_percent, 2),
            "code_quality_score": round(code_quality_percent, 2),
                        
            "collaboration_score_raw_30": round(code_collab_score_raw_30, 2),
            "code_quality_score_raw_35": round(code_quality_score_raw_35, 2),
            "problem_solving_score_raw_35": round(problem_score_raw_35, 2),
            "collaboration_rule_20": round(collab_rule_20, 2),
            "collaboration_llm_10": round(collab_llm_score_10, 2),

            "final_score": round(final_score_raw_100, 0),
            "final_grade": final_grade,
            
            # LLM 생성 피드백
            "strength": llm_feedback["strength"],
            "improvement": llm_feedback["improvement"],
            "comprehensive_evaluation": llm_feedback["comprehensive_evaluation"],
            "annotated_code": llm_feedback["annotated_code"],
            "cheating_warning": llm_feedback["cheating_warning"],
            "anti_cheat_summary": anti_cheat_summary,

            "problem_category": problem_category,
            "problem_difficulty": problem_difficulty,

            # 문제 해결 능력 평가 추가
            "problem_solving_evaluation": {
                "initial_strategy": initial_strategy or "초기 전략 답변이 기록되지 않았습니다.",
                "problem_understanding": ps_evaluation["problem_understanding"],
                "understanding_feedback": ps_evaluation["understanding_feedback"],
                "approach_validity": ps_evaluation["approach_validity"],
                "consistency_status": ps_evaluation["consistency_status"],
                "consistency_feedback": ps_evaluation["consistency_feedback"],
                "qa_history": qa_history,
            },
            
            # ✅ 문제 텍스트 추가
            "problem_text": problem_text,
            "submitted_code": code,
            
            # 추가 정보
            "flags": flags,
            "code_feedback": code_feedback,
            "problem_feedback": problem_feedback,
        }

        # 완료 상태
        state["step"] = "saved"
        state["status"] = "done"
        state["error"] = None

        print(f"[create_report_node] 완료 - 최종점수: {final_score_raw_100:.2f}, 등급: {final_grade}", flush=True)
        return state

    except Exception as e:
        import traceback
        traceback.print_exc()

        state["step"] = "error"
        state["status"] = "error"
        state["error"] = f"{type(e).__name__}: {e}"
        state["graph_output"] = {
            "error": str(e),
            "strength": "평가 중 오류가 발생했습니다.",
            "improvement": "평가 중 오류가 발생했습니다.",
            "comprehensive_evaluation": "시스템 오류로 평가를 완료하지 못했습니다.",
            "annotated_code": "# 오류 발생",
        }
        return state
