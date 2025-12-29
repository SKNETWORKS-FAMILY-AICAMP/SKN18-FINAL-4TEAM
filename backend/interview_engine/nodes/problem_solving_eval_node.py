# backend/interview_engine/nodes/problem_solving_eval_node.py
from __future__ import annotations
from interview_engine.utils.checkpoint_reader import load_chapter_channel_values
from interview_engine.llm import LLM
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Any, Dict, List, Tuple
import re
import json

from django.core.cache import cache
from django.db import connection


def _clamp01(x: float) -> float:
    try:
        x = float(x)
    except Exception:
        return 0.0
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


def _safe_str(x: Any) -> str:
    return "" if x is None else str(x)


# ==================== LLM 테스트 케이스 평가 ====================

def _evaluate_test_cases_with_llm(
    user_code: str, 
    test_cases: List[Dict[str, Any]], 
    problem_text: str = "",
    function_name: str = "solution"
) -> Dict[str, Any]:
    """
    LLM을 사용하여 사용자 코드와 테스트 케이스를 평가
    """
    if not user_code or not user_code.strip():
        return {"passed": 0, "total": len(test_cases), "pass_rate": 0.0, "error": "코드가 비어있습니다"}
    
    if not test_cases:
        return {"passed": 0, "total": 0, "pass_rate": 0.0, "error": "테스트 케이스가 없습니다"}
    
    # 최대 10개 케이스만 평가 (토큰 제한)
    test_cases_limited = test_cases[:10]
    
    # 테스트 케이스 포맷팅
    test_cases_str = ""
    for idx, tc in enumerate(test_cases_limited):
        test_cases_str += f"\n{idx+1}. Input: {tc.get('input')}\n   Expected: {tc.get('expected')}\n"
    
    system_prompt = """당신은 코딩 테스트 평가 전문가입니다.
주어진 코드와 테스트 케이스를 보고 각 케이스의 통과 여부를 판단하세요.

**평가 기준:**
- 코드의 로직을 정확히 분석
- 각 테스트 케이스에 대해 올바른 출력 생성 여부 판단
- 문법 오류, 논리 오류, 예외 발생 가능성 고려
- 반드시 JSON 형식으로만 응답"""

    user_prompt = f"""## 문제
{problem_text[:500] if problem_text else "문제 설명 없음"}

## 사용자 코드
```python
{user_code[:2000]}
```

## 테스트 케이스
{test_cases_str}

## 평가 요청
위 코드가 각 테스트 케이스에 대해 올바른 출력을 생성하는지 판단하여 JSON으로 응답하세요:

{{
  "results": [
    {{"case_index": 1, "passed": true, "reason": "정확한 로직"}},
    {{"case_index": 2, "passed": false, "reason": "edge case 미처리"}}
  ]
}}

**주의:** JSON만 출력, passed는 true/false, reason은 한 문장"""

    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = LLM.invoke(messages)
        content = response.content.strip()
        
        # JSON 추출
        if "```json" in content:
            content = content.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in content:
            content = content.split("```", 1)[1].split("```", 1)[0]
        
        data = json.loads(content.strip())
        results = data.get("results", [])
        
        # 통과 수 계산
        passed = sum(1 for r in results if r.get("passed") is True)
        total = len(test_cases_limited)
        pass_rate = passed / total if total > 0 else 0.0
        
        # 결과 포맷팅
        formatted_results = []
        for r in results:
            idx = r.get("case_index", 1) - 1
            if 0 <= idx < len(test_cases_limited):
                formatted_results.append({
                    "case_index": idx,
                    "input": test_cases_limited[idx].get("input"),
                    "expected": test_cases_limited[idx].get("expected"),
                    "passed": r.get("passed", False),
                    "reason": r.get("reason", "")
                })
        
        # ✅ 상세 로그 출력
        print(f"\n{'='*60}")
        print(f"[LLM 테스트 평가 결과]")
        print(f"{'='*60}")
        print(f"총 테스트: {total}개")
        print(f"통과: {passed}개 | 실패: {total - passed}개")
        print(f"통과율: {pass_rate:.2%}")
        print(f"{'-'*60}")
        
        for r in formatted_results:
            status = "✅ PASS" if r["passed"] else "❌ FAIL"
            print(f"케이스 {r['case_index'] + 1}: {status}")
            print(f"  Input: {r['input']}")
            print(f"  Expected: {r['expected']}")
            print(f"  판단: {r['reason']}")
            print(f"{'-'*60}")
        
        print(f"{'='*60}\n")
        
        return {
            "passed": passed,
            "total": total,
            "pass_rate": round(pass_rate, 4),
            "results": formatted_results,
            "error": None
        }
        
    except Exception as e:
        print(f"[ERROR] LLM 테스트 평가 실패: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "passed": 0,
            "total": len(test_cases_limited),
            "pass_rate": 0.0,
            "results": [],
            "error": f"LLM 평가 실패: {str(e)[:100]}"
        }


# ==================== DB 테스트 케이스 ====================

def _get_test_cases_from_db(problem_id: int) -> List[Dict[str, Any]]:
    """DB에서 테스트 케이스 가져오기"""
    if not problem_id:
        return []
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT input, output
                FROM test_case
                WHERE problem_id = %s
                ORDER BY id
            """, [problem_id])
            
            rows = cursor.fetchall()
            test_cases = []
            
            for row in rows:
                try:
                    import ast
                    test_input = ast.literal_eval(row[0])
                    test_output = ast.literal_eval(row[1])
                    test_cases.append({
                        "input": test_input,
                        "expected": test_output
                    })
                except Exception:
                    continue
            
            return test_cases
    except Exception as e:
        print(f"[ERROR] DB 테스트 케이스 조회 실패: {e}")
        return []


def _is_starter_like(code: str, starter: str) -> bool:
    c = re.sub(r"\s+", "", code or "")
    s = re.sub(r"\s+", "", starter or "")
    if not c or not s:
        return False
    return c == s


def _evaluate_strategy_hybrid(
    strategy_text: str,
    code: str,
    problem_text: str = ""
) -> Tuple[float, float, str]:
    """
    하이브리드 전략 평가: 룰베이스 기본 + LLM 보정
    
    Returns:
        (strategy_score: 0~4, consistency_score: 0~4, feedback: str)
    """
    if not strategy_text or len(strategy_text.strip()) < 20:
        return 0.0, 0.0, "전략 답변이 너무 짧거나 없음"
    
    if not code or not code.strip():
        return 0.0, 0.0, "코드가 없음"
    
    # ========== 1단계: 룰베이스 기본 점수 (안정성) ==========
    
    # 1-1. 전략 품질 룰베이스 (0~4점)
    rule_strategy_score = 0.0
    char_count = len(strategy_text.strip())
    
    # 길이 점수 (최대 1.5점)
    if char_count >= 100:
        rule_strategy_score += 1.5
    elif char_count >= 50:
        rule_strategy_score += 1.0
    elif char_count >= 20:
        rule_strategy_score += 0.5
    
    # 복잡도 언급 (1.0점)
    if re.search(r"O\([NnMm\d\s\*\+log]+\)", strategy_text) or "복잡도" in strategy_text or "시간" in strategy_text:
        rule_strategy_score += 1.0
    
    # 알고리즘 키워드 (최대 1.5점)
    keywords = ["해시", "딕셔너리", "dict", "배열", "리스트", "DP", "dp", "그래프", "정렬", 
                "스택", "큐", "탐색", "검색", "완전탐색", "이진탐색", "재귀", "반복"]
    matched_keywords = sum(1 for kw in keywords if kw in strategy_text)
    rule_strategy_score += min(matched_keywords * 0.5, 1.5)
    
    rule_strategy_score = min(rule_strategy_score, 4.0)
    
    # 1-2. 전략-코드 일치 룰베이스 (0~4점) - AST 기반
    rule_consistency_score = 0.0
    strategy_lower = strategy_text.lower()
    
    try:
        # AST 파싱으로 실제 사용 확인
        import ast
        tree = ast.parse(code)
        
        # 함수 호출 추출
        function_calls = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    function_calls.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    function_calls.add(node.func.attr)
        
        # 변수명 추출
        variable_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                variable_names.add(node.id.lower())
        
        # 딕셔너리 사용 확인
        has_dict = any(isinstance(node, ast.Dict) for node in ast.walk(tree))
        
        # 리스트 사용 확인
        has_list = any(isinstance(node, ast.List) for node in ast.walk(tree))
        
        # 자료구조 매칭 (각 1점)
        if ("해시" in strategy_lower or "dict" in strategy_lower):
            if has_dict or "dict" in function_calls or any("dict" in v for v in variable_names):
                rule_consistency_score += 1.0
                
        if ("배열" in strategy_lower or "리스트" in strategy_lower):
            if has_list or "[" in code:
                rule_consistency_score += 1.0
        
        # 알고리즘 매칭 (각 1점)
        if ("정렬" in strategy_lower or "sort" in strategy_lower):
            if "sort" in function_calls or "sorted" in function_calls:
                rule_consistency_score += 1.0
        
        if "dp" in strategy_lower:
            # dp 변수명 또는 2차원 배열 패턴
            if any("dp" in v for v in variable_names) or "[[" in code:
                rule_consistency_score += 1.0
        
        if ("스택" in strategy_lower or "stack" in strategy_lower):
            if "append" in function_calls and "pop" in function_calls:
                rule_consistency_score += 1.0
        
        if ("큐" in strategy_lower or "queue" in strategy_lower):
            if "deque" in str(tree) or "Queue" in str(tree):
                rule_consistency_score += 1.0
        
        if ("완전탐색" in strategy_lower or "모든" in strategy_lower or "조합" in strategy_lower):
            # for 문 또는 itertools.permutations/combinations
            has_for = any(isinstance(node, ast.For) for node in ast.walk(tree))
            has_combinations = "permutations" in function_calls or "combinations" in function_calls
            if has_for or has_combinations:
                rule_consistency_score += 0.5
        
    except Exception:
        # AST 파싱 실패시 기존 키워드 방식으로 폴백
        code_lower = code.lower()
        if ("해시" in strategy_lower or "dict" in strategy_lower) and ("{" in code or "dict" in code_lower):
            rule_consistency_score += 0.5
        if ("배열" in strategy_lower or "리스트" in strategy_lower) and "[" in code:
            rule_consistency_score += 0.5
        if ("정렬" in strategy_lower or "sort" in strategy_lower) and "sort" in code_lower:
            rule_consistency_score += 0.5
    
    rule_consistency_score = min(rule_consistency_score, 4.0)
    
    print(f"[룰베이스 평가] 전략: {rule_strategy_score:.1f}/4, 일치: {rule_consistency_score:.1f}/4", flush=True)
    
    # ========== 2단계: LLM 보정 (선택적, 안정성 우선) ==========
    
    llm_strategy_score = rule_strategy_score
    llm_consistency_score = rule_consistency_score
    llm_feedback = ""
    
    # LLM 호출 조건: 룰베이스 점수가 애매할 때만
    use_llm = (
        (rule_strategy_score < 2.0 and char_count >= 80) or  # 전략이 있는데 점수가 낮음
        (rule_consistency_score == 0 and len(code) > 100)     # 코드는 있는데 일치 0점
    )
    
    if use_llm:
        try:
            system_prompt = """당신은 코딩 면접 평가 전문가입니다.
전략과 코드를 비교하여 점수를 보정하세요.

**평가 기준:**
- 전략 품질 (0~4점): 문제 이해도, 알고리즘 언급, 구체성
- 일치도 (0~4점): 전략과 코드의 알고리즘/자료구조 일치 여부"""

            user_prompt = f"""## 전략 (룰베이스 점수: {rule_strategy_score:.1f}/4)
{strategy_text[:400]}

## 코드 (일치 룰베이스: {rule_consistency_score:.1f}/4)
```python
{code[:1000]}
```

룰베이스 점수를 참고하여 보정된 점수를 JSON으로 제시:

{{
  "strategy_score": 2.5,
  "consistency_score": 1.5,
  "reason": "완전탐색 의도를 코드로 구현했으나 최적화 부족"
}}

**주의:** 
- 룰베이스 점수에서 ±1.0 이내로만 보정
- 명백한 오류가 아니면 룰베이스 점수 유지"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = LLM.invoke(messages)
            content = response.content.strip()
            
            if "```json" in content:
                content = content.split("```json", 1)[1].split("```", 1)[0]
            elif "```" in content:
                content = content.split("```", 1)[1].split("```", 1)[0]
            
            data = json.loads(content.strip())
            
            llm_strategy = float(data.get("strategy_score", rule_strategy_score))
            llm_consistency = float(data.get("consistency_score", rule_consistency_score))
            llm_feedback = data.get("reason", "")
            
            # ✅ 안정성: 룰베이스 ±1.0 범위로 제한
            llm_strategy_score = max(0.0, min(4.0, 
                max(rule_strategy_score - 1.0, min(rule_strategy_score + 1.0, llm_strategy))
            ))
            llm_consistency_score = max(0.0, min(4.0,
                max(rule_consistency_score - 1.0, min(rule_consistency_score + 1.0, llm_consistency))
            ))
            
            print(f"[LLM 보정] 전략: {rule_strategy_score:.1f}→{llm_strategy_score:.1f}, "
                  f"일치: {rule_consistency_score:.1f}→{llm_consistency_score:.1f}", flush=True)
            
        except Exception as e:
            print(f"[WARNING] LLM 보정 실패, 룰베이스 점수 유지: {e}", flush=True)
            llm_strategy_score = rule_strategy_score
            llm_consistency_score = rule_consistency_score
    
    # ========== 3단계: 최종 점수 ==========
    final_strategy = round(llm_strategy_score, 1)
    final_consistency = round(llm_consistency_score, 1)
    
    feedback = llm_feedback if llm_feedback else "룰베이스 평가"
    
    return final_strategy, final_consistency, feedback


def _evaluate_35_points(
    code: str,
    starter_code: str,
    strategy_text: str,
    test_results: Dict[str, Any],
    problem_text: str = ""
) -> Tuple[float, List[str]]:
    """
    35점 만점 평가 (전략 4 + 일치 4 + 테스트 25 + 기본 2)
    - LLM 기반 전략 평가 사용
    """
    fb: List[str] = []
    
    # ========== 코드가 없으면 0점 ==========
    if not code or not code.strip():
        return 0.0, ["- 코드가 비어 있습니다."]
    
    # ========== Starter와 동일하면 0점 ==========
    if starter_code and _is_starter_like(code, starter_code):
        return 0.5, ["- 제출 코드가 starter_code와 거의 동일합니다."]
    
    # ========== 1. 전략 품질 + 2. 전략-코드 일치 (하이브리드 평가) ==========
    strategy_score = 0.0
    consistency_score = 0.0
    
    if strategy_text and len(strategy_text.strip()) >= 20:
        strategy_score, consistency_score, hybrid_feedback = _evaluate_strategy_hybrid(
            strategy_text=strategy_text,
            code=code,
            problem_text=problem_text
        )
        fb.append(f"- 전략 품질: {strategy_score:.1f}/4")
        fb.append(f"- 전략-코드 일치: {consistency_score:.1f}/4")
        if hybrid_feedback and hybrid_feedback != "룰베이스 평가":
            fb.append(f"  ({hybrid_feedback})")
    else:
        fb.append(f"- 전략 품질: 0.0/4 (전략 답변 없음)")
        fb.append(f"- 전략-코드 일치: 0.0/4")
    
    # ========== 3. 테스트 통과율 (25점) ==========
    test_score = 0.0
    
    if test_results and "pass_rate" in test_results:
        # ✅ 실제 테스트 결과 사용
        test_score = test_results["pass_rate"] * 25.0
        passed = test_results.get("passed", 0)
        total = test_results.get("total", 0)
        fb.append(f"- 테스트 통과: {passed}/{total} ({test_score:.1f}/25)")
    else:
        # ❌ 테스트 없으면 0점
        test_score = 0.0
        fb.append(f"- 테스트 통과: 0/0 (0.0/25) - 테스트 결과 없음")
    
    # ========== 4. 기본 규칙 (2점) ==========
    basic_score = 0.0
    
    has_function = bool(re.search(r"def\s+\w+", code))
    has_return = "return" in code
    
    if has_function and has_return:
        basic_score = 2.0
    elif has_function or has_return:
        basic_score = 1.0
    else:
        basic_score = 0.4
    
    fb.append(f"- 기본 규칙: {basic_score:.1f}/2")
    
    # ========== 총점 ==========
    total_score = strategy_score + consistency_score + test_score + basic_score
    
    return round(total_score, 2), fb


def problem_solving_eval_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    문제 해결 평가 노드 - LLM 기반 테스트 케이스 평가
    """
    state["step"] = "problem_eval"
    state["status"] = "running"
    state["error"] = None

    meta = state.get("meta") or {}
    session_id = _safe_str(meta.get("session_id"))

    if not session_id:
        state["status"] = "error"
        state["step"] = "error"
        state["error"] = "meta.session_id가 없습니다."
        state["problem_eval_score"] = 0.0
        state["problem_eval_feedback"] = "- session_id 누락"
        return state

    meta_key = f"livecoding:{session_id}:meta"
    code_key = f"livecoding:{session_id}:code"

    cached_meta = cache.get(meta_key) or {}
    code_data = cache.get(code_key) or {}
    latest = (code_data.get("latest") or {})
    cache_code = _safe_str(latest.get("code") or "")

    chap1 = load_chapter_channel_values(session_id, "chapter1")
    chap2 = load_chapter_channel_values(session_id, "chapter2")
    hint = load_chapter_channel_values(session_id, "chapter2_hint")

    problem_text = _safe_str(chap1.get("problem_data") or hint.get("problem_description") or "")
    ckpt_code = _safe_str(chap2.get("code") or hint.get("current_user_code") or "")

    code = cache_code.strip() or ckpt_code.strip()
    starter_code = _safe_str(cached_meta.get("starter_code") or chap2.get("starter_code") or "")
    
    # ✅ 전략 답변 - 우선순위: Redis > checkpoint
    strategy_text = ""
    
    # 1순위: Redis meta
    if cached_meta.get("strategy_answer"):
        strategy_text = _safe_str(cached_meta.get("strategy_answer"))
        print(f"[전략] Redis meta에서 가져옴: {len(strategy_text)}자 - '{strategy_text[:50]}...'", flush=True)
    
    # 2순위: checkpoint
    if not strategy_text:
        strategy_text = _safe_str(chap1.get("user_strategy_answer") or "")
        if strategy_text:
            print(f"[전략] checkpoint에서 가져옴: {len(strategy_text)}자 - '{strategy_text[:50]}...'", flush=True)
    
    # 디버깅 로그
    if not strategy_text:
        print(f"[WARNING] 전략 답변을 찾을 수 없습니다!", flush=True)
        print(f"[DEBUG] cached_meta keys: {list(cached_meta.keys())}", flush=True)
        print(f"[DEBUG] chap1 keys: {list(chap1.keys()) if chap1 else 'None'}", flush=True)
    
    problem_id = cached_meta.get("problem_id")
    language = _safe_str(cached_meta.get("language") or "python3")
    
    # ========== LLM 기반 테스트 평가 ==========
    test_results = None
    
    if problem_id and code:
        try:
            # function_name 조회
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT function_name
                    FROM coding_problem_language
                    WHERE problem_id = %s AND language = %s
                    LIMIT 1
                """, [problem_id, language])
                row = cursor.fetchone()
                function_name = row[0] if row else "solution"
            
            # 테스트 케이스 가져오기
            test_cases = _get_test_cases_from_db(problem_id)
            
            if test_cases:
                print(f"[INFO] LLM으로 {len(test_cases[:10])}개 테스트 케이스 평가 시작...")
                # ✅ LLM으로 평가!
                test_results = _evaluate_test_cases_with_llm(
                    user_code=code,
                    test_cases=test_cases,
                    problem_text=problem_text,
                    function_name=function_name
                )
                print(f"[INFO] LLM 평가 완료: {test_results['passed']}/{test_results['total']} 통과")
            else:
                print(f"[WARNING] problem_id={problem_id}에 대한 테스트 케이스가 없습니다")
        except Exception as e:
            print(f"[WARNING] 테스트 평가 중 오류: {e}")
            import traceback
            traceback.print_exc()
    else:
        if not problem_id:
            print(f"[WARNING] problem_id를 찾을 수 없어 테스트를 건너뜁니다")
    
    # ========== 35점 평가 ==========
    total_score, feedback_list = _evaluate_35_points(
        code=code,
        starter_code=starter_code,
        strategy_text=strategy_text,
        test_results=test_results,
        problem_text=problem_text  # ✅ 추가!
    )
    
    # ========== State 업데이트 (0~1 스케일로 변환) ==========
    state["problem_eval_score"] = round(total_score / 35.0, 4)
    state["problem_eval_feedback"] = "\n".join(feedback_list)
    state["problem_evidence"] = {
        "problem_text": problem_text,
        "submitted_code": code,
        "starter_code": starter_code,
        "test_results": test_results,
        "strategy_answer": strategy_text,
        "chapter2_questions": chap2.get("question") or [],
        "hint_conversation_log": hint.get("conversation_log") or [],
    }
    
    print(f"[problem_solving_eval_node] 완료 - {total_score:.2f}/35점 (스케일: {total_score/35.0:.4f})")
    print(f"[DEBUG] problem_evidence.submitted_code 길이: {len(code)}")
    
    state["status"] = "done"
    return state