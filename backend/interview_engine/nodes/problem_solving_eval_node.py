# backend/interview_engine/nodes/problem_solving_eval_node.py
from __future__ import annotations
from interview_engine.utils.checkpoint_reader import load_chapter_channel_values
from interview_engine.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Any, Dict, List, Tuple
import re
import json

from django.core.cache import cache
from django.db import connection


def _safe_str(x: Any) -> str:
    return "" if x is None else str(x)


STRATEGY_KEYWORDS = {
    "array": [
        "배열",
        "배열형",
        "리스트",
        "리스트형",
        "어레이",
        "어레",
        "어레이리스트",
        "배열리스트",
        "array",
        "arrays",
        "list",
        "lists",
        "인덱스",
        "순회",
        "반복",
        "구간합",
        "구간 합",
        "누적합",
        "누적 합",
        "prefix",
        "prefix sum",
        "누적",
        "슬라이딩",
        "슬라이딩윈도우",
        "슬라이딩 윈도우",
        "윈도우",
        "윈도우 기법",
    ],
    "dp": [
        "동적계획법",
        "다이나믹 프로그래밍",
        "다이나믹",
        "다이내믹 프로그래밍",
        "다이내믹",
        "동적 계획법",
        "dp",
        "dynamic programming",
        "메모이제이션",
        "메모이제이션",
        "메모",
        "점화식",
        "상태",
        "전이",
        "상태 전이",
    ],
    "graph": [
        "그래프",
        "그래프탐색",
        "그래프 탐색",
        "graph",
        "graphs",
        "bfs",
        "dfs",
        "탐색",
        "순회",
        "방문",
        "인접",
        "인접리스트",
        "인접 리스트",
        "인접행렬",
        "인접 행렬",
        "최단",
        "최단거리",
        "최단 거리",
        "다익스트라",
        "다이크스트라",
        "다익스트라 알고리즘",
        "위상",
        "위상정렬",
        "위상 정렬",
    ],
    "string": [
        "문자열",
        "스트링",
        "string",
        "strings",
        "인덱스",
        "슬라이싱",
        "치환",
        "비교",
        "패턴",
        "패턴매칭",
        "패턴 매칭",
        "접두",
        "접미",
        "접두사",
        "접미사",
        "lcs",
        "kmp",
        "regex",
        "정규식",
    ],
    "hash_table": [
        "해시",
        "해시테이블",
        "딕셔너리",
        "집합",
        "맵",
        "hash",
        "hash table",
        "hashmap",
        "hashset",
        "dict",
        "set",
        "map",
        "맵핑",
        "매핑",
    ],
    "two_pointer": [
        "투포인터",
        "투 포인터",
        "투포인타",
        "2포인터",
        "2 포인터",
        "two pointer",
        "two pointers",
        "two-pointer",
        "two-pointer technique",
        "left",
        "right",
        "포인터",
        "윈도우",
        "슬라이딩",
    ],
    "stack": ["스택", "stack"],
    "queue": ["큐", "queue", "deque"],
    "sort": ["정렬", "sort", "sorted", "sorting", "order", "ordering"],
    "search": [
        "완전탐색",
        "이진탐색",
        "binary search",
        "탐색",
        "검색",
        "재귀",
        "반복",
        "backtracking",
        "divide and conquer",
        "분할정복",
        "분할 정복",
    ],
    "math": [
        "수학",
        "math",
        "mathematics",
        "정수",
        "소수",
        "mod",
        "모듈러",
        "약수",
        "gcd",
        "lcm",
        "조합",
        "순열",
        "경우의수",
        "경우의 수",
    ],
    "tree": [
        "트리",
        "tree",
        "이진트리",
        "이진 트리",
        "bst",
        "힙트리",
        "힙 트리",
    ],
    "greedy": ["그리디", "greedy", "탐욕"],
    "simulation": ["시뮬레이션", "simulation", "모의", "구현"],
    "bit_manipulation": [
        "비트",
        "bit",
        "bitwise",
        "xor",
        "and",
        "or",
        "shift",
        "bit_count",
        "popcount",
        "비트연산",
        "비트 연산",
        "시프트",
    ],
    "design": ["설계", "design", "클래스", "class", "인터페이스", "interface"],
    "heap": [
        "힙",
        "heap",
        "priority queue",
        "우선순위",
        "우선순위큐",
        "우선순위 큐",
        "heapq",
        "heappush",
        "heappop",
    ],
    "statistics": [
        "통계",
        "statistics",
        "metric",
        "metrics",
        "평균",
        "mean",
        "분산",
        "variance",
        "표준편차",
        "std",
        "stddev",
        "분위수",
        "quantile",
        "사분위",
        "iqr",
        "히스토그램",
        "histogram",
        "신뢰구간",
        "confidence interval",
        "정규화",
        "normalization",
        "z-score",
        "z score",
        "minmax",
        "min-max",
        "스케일링",
        "scaling",
        "엔트로피",
        "entropy",
        "kl",
        "kl divergence",
        "auc",
        "log loss",
        "로그손실",
        "mae",
        "혼동행렬",
        "confusion matrix",
        "지표",
        "메트릭",
        "정확도",
        "정밀도",
        "재현율",
        "f1",
        "f1-score",
    ],
    "nlp": [
        "nlp",
        "자연어",
        "토큰",
        "token",
        "tokens",
        "임베딩",
        "embedding",
        "transformer",
        "attention",
        "softmax",
        "cosine",
        "tf-idf",
        "tfidf",
        "beam",
        "beam search",
        "positional",
        "masking",
        "padding",
        "토크나이즈",
        "토큰화",
        "토큰화",
    ],
    "ml": [
        "클러스터링",
        "군집",
        "clustering",
        "cluster",
        "centroid",
        "nearest centroid",
        "거리",
        "유사도",
        "similarity",
        "분류",
        "classification",
        "회귀",
        "regression",
    ],
}


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

## 함수명
평가 대상 함수: `{function_name}()`

## 테스트 케이스
{test_cases_str}

## 평가 요청
위 코드의 `{function_name}()` 함수가 각 테스트 케이스에 대해 올바른 출력을 생성하는지 판단하여 JSON으로 응답하세요:

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
        
        model = get_llm("solve")
        response = model.invoke(messages)
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
            
            def _parse_input(raw: str):
                import ast
                if raw is None:
                    raise ValueError("empty input")
                text = str(raw).strip()
                if not text:
                    raise ValueError("empty input")

                # 1) Python literal (예: "[1,2,3]" or "{'a':1}")
                try:
                    return ast.literal_eval(text)
                except Exception:
                    pass

                # 2) 공백 분리 포맷: "2 4 [3, 3, 3]" -> [2, 4, [3,3,3]]
                parts = text.split()
                parsed = []
                for part in parts:
                    try:
                        parsed.append(ast.literal_eval(part))
                    except Exception:
                        parsed.append(part)
                if len(parsed) == 1:
                    return parsed[0]
                return parsed

            def _parse_output(raw: str):
                import ast
                if raw is None:
                    raise ValueError("empty output")
                text = str(raw).strip()
                if not text:
                    raise ValueError("empty output")
                try:
                    return ast.literal_eval(text)
                except Exception:
                    return text

            for row in rows:
                try:
                    test_input = _parse_input(row[0])
                    test_output = _parse_output(row[1])
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


def _has_placeholder(code: str) -> bool:
    if not code:
        return True
    if re.search(r"^\s*pass\s*$", code, flags=re.M):
        return True
    if re.search(r"TODO|FIXME", code, flags=re.I):
        return True
    if re.search(r"NotImplementedError", code):
        return True
    if re.search(r"^\s*\.\.\.\s*$", code, flags=re.M):
        return True
    return False


def _normalize_algo_tag(tag: str) -> str:
    t = (tag or "").strip().lower()
    t = re.sub(r"[^a-z0-9가-힣]+", " ", t).strip()
    return t


def _algo_tags_to_groups(problem_algorithms: List[str]) -> set:
    algo_group_map = {
        "dp": "dp",
        "dynamic programming": "dp",
        "lis": "dp",
        "greedy": "greedy",
        "sorting": "sort",
        "ranking": "sort",
        "hashing": "hash_table",
        "hashmap": "hash_table",
        "hashset": "hash_table",
        "set": "hash_table",
        "join": "hash_table",
        "two pointers": "two_pointer",
        "two pointer": "two_pointer",
        "sliding window": "two_pointer",
        "intervals": "two_pointer",
        "prefix sum": "array",
        "array": "array",
        "preprocessing": "array",
        "bfs": "graph",
        "dfs": "graph",
        "graph": "graph",
        "shortest path": "graph",
        "dijkstra": "graph",
        "topological sort": "graph",
        "tree": "tree",
        "stack": "stack",
        "queue": "queue",
        "streaming": "queue",
        "binary search": "search",
        "divide and conquer": "search",
        "backtracking": "search",
        "math": "math",
        "vector": "math",
        "matrix": "math",
        "sparse": "math",
        "simulation": "simulation",
        "heap": "heap",
        "top k": "heap",
        "bitmask": "bit_manipulation",
        "string": "string",
        "parsing": "string",
        "regex": "string",
        "kmp": "string",
        "edit distance": "string",
        "statistics": "statistics",
        "metrics": "statistics",
        "aggregation": "statistics",
        "counting": "statistics",
        "quantile": "statistics",
        "numerical stability": "statistics",
        "sampling": "statistics",
        "frequency": "statistics",
        "thresholding": "statistics",
        "normalization": "statistics",
        "z score": "statistics",
        "minmax scaling": "statistics",
        "mean": "statistics",
        "variance": "statistics",
        "covariance": "statistics",
        "entropy": "statistics",
        "kl divergence": "statistics",
        "confusion matrix": "statistics",
        "auc": "statistics",
        "log loss": "statistics",
        "iqr": "statistics",
        "confidence interval": "statistics",
        "histogram": "statistics",
        "winsorization": "statistics",
        "mae": "statistics",
        "nlp": "nlp",
        "transformer": "nlp",
        "attention": "nlp",
        "softmax": "nlp",
        "padding": "nlp",
        "masking": "nlp",
        "positional encoding": "nlp",
        "cosine similarity": "nlp",
        "tf idf": "nlp",
        "beam search": "nlp",
        "clustering": "ml",
        "nearest centroid": "ml",
    }
    groups = set()
    for tag in problem_algorithms:
        normalized = _normalize_algo_tag(tag)
        if not normalized:
            continue
        mapped = algo_group_map.get(normalized)
        if mapped:
            groups.add(mapped)
    return groups


def _evaluate_strategy_hybrid(
    strategy_text: str,
    code: str,
    problem_text: str = "",
    problem_algorithms: List[str] | str = "",
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
    if char_count >= 20:
        rule_strategy_score += 1.5
    elif char_count >= 10:
        rule_strategy_score += 1.0
    elif char_count >= 5:
        rule_strategy_score += 0.5
    
    # 복잡도 언급 (1.0점)
    if re.search(r"O\([NnMm\d\s\*\+log]+\)", strategy_text) or "복잡도" in strategy_text or "시간" in strategy_text:
        rule_strategy_score += 1.0
    
    # 알고리즘 키워드 (카테고리 기반, 최대 1.5점)
    keyword_groups = STRATEGY_KEYWORDS
    strategy_lower = strategy_text.lower()

    algo_list = []
    if isinstance(problem_algorithms, list):
        algo_list = [str(x) for x in problem_algorithms if x]
    elif problem_algorithms:
        algo_list = [str(problem_algorithms)]

    active_groups = _algo_tags_to_groups(algo_list)

    if active_groups:
        keywords_for_strategy = [
            kw for g in active_groups for kw in keyword_groups.get(g, [])
        ]
        category_match = any(kw in strategy_lower for kw in keywords_for_strategy)
        keyword_score = 1.5 if category_match else 0.0
    else:
        keywords_for_strategy = [kw for group in keyword_groups.values() for kw in group]
        matched_keywords = sum(1 for kw in keywords_for_strategy if kw in strategy_lower)
        keyword_score = min(matched_keywords * 0.5, 0.75)

    rule_strategy_score += keyword_score
    
    rule_strategy_score = min(rule_strategy_score, 4.0)
    
    # 1-2. 전략-코드 일치 룰베이스 (0~4점) - AST 기반
    rule_consistency_score = 0.0
    def _mentions_any(text: str, keywords: List[str]) -> bool:
        return any(kw in text for kw in keywords)

    if not active_groups:
        active_groups = set(keyword_groups.keys())
    
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
        
        # 딕셔너리/집합 사용 확인
        has_dict = any(isinstance(node, ast.Dict) for node in ast.walk(tree))
        has_set = any(isinstance(node, ast.Set) for node in ast.walk(tree))
        
        # 리스트 사용 확인
        has_list = any(isinstance(node, ast.List) for node in ast.walk(tree))
        
        # 자료구조 매칭 (각 1점)
        if "hash_table" in active_groups and _mentions_any(strategy_lower, keyword_groups["hash_table"]):
            if has_dict or has_set or "dict" in function_calls or "set" in function_calls or any("dict" in v for v in variable_names):
                rule_consistency_score += 1.0
                
        if "array" in active_groups and _mentions_any(strategy_lower, keyword_groups["array"]):
            if has_list or "[" in code:
                rule_consistency_score += 1.0
        
        # 알고리즘 매칭 (각 1점)
        if "sort" in active_groups and _mentions_any(strategy_lower, keyword_groups["sort"]):
            if "sort" in function_calls or "sorted" in function_calls:
                rule_consistency_score += 1.0
        
        if "dp" in active_groups and _mentions_any(strategy_lower, keyword_groups["dp"]):
            # dp 변수명 또는 2차원 배열 패턴
            if any("dp" in v for v in variable_names) or "[[" in code:
                rule_consistency_score += 1.0
        
        if "stack" in active_groups and _mentions_any(strategy_lower, keyword_groups["stack"]):
            if "append" in function_calls and "pop" in function_calls:
                rule_consistency_score += 1.0
        
        if "queue" in active_groups and _mentions_any(strategy_lower, keyword_groups["queue"]):
            if "deque" in str(tree) or "Queue" in str(tree):
                rule_consistency_score += 1.0

        if "two_pointer" in active_groups and _mentions_any(strategy_lower, keyword_groups["two_pointer"]):
            if {"left", "right"}.issubset(variable_names) or ("left" in code and "right" in code):
                rule_consistency_score += 1.0

        if "graph" in active_groups and _mentions_any(strategy_lower, keyword_groups["graph"]):
            if "deque" in str(tree) or "popleft" in function_calls or any(v in {"graph", "adj", "adj_list"} for v in variable_names):
                rule_consistency_score += 1.0

        if "tree" in active_groups and _mentions_any(strategy_lower, keyword_groups["tree"]):
            has_node = any(v in {"node", "nodes", "root", "left", "right", "parent", "child"} for v in variable_names)
            has_tree_call = any(c in {"dfs", "bfs"} for c in function_calls)
            has_recursion = any(isinstance(n, ast.FunctionDef) for n in ast.walk(tree)) and any(
                isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in {"dfs", "traverse", "search"}
                for n in ast.walk(tree)
            )
            if has_node or has_tree_call or has_recursion:
                rule_consistency_score += 1.0

        if "greedy" in active_groups and _mentions_any(strategy_lower, keyword_groups["greedy"]):
            has_sort = "sort" in function_calls or "sorted" in function_calls
            has_minmax = any(c in {"min", "max"} for c in function_calls)
            if has_sort or has_minmax:
                rule_consistency_score += 0.5

        if "string" in active_groups and _mentions_any(strategy_lower, keyword_groups["string"]):
            if "'" in code or "\"" in code or "str" in function_calls:
                rule_consistency_score += 0.5

        if "bit_manipulation" in active_groups and _mentions_any(strategy_lower, keyword_groups["bit_manipulation"]):
            if any(op in code for op in ["&", "|", "^", "<<", ">>", "~"]) or "bit_count" in code:
                rule_consistency_score += 1.0

        if "heap" in active_groups and _mentions_any(strategy_lower, keyword_groups["heap"]):
            if "heapq" in code or "heappush" in function_calls or "heappop" in function_calls:
                rule_consistency_score += 1.0

        if "design" in active_groups and _mentions_any(strategy_lower, keyword_groups["design"]):
            if any(isinstance(node, ast.ClassDef) for node in ast.walk(tree)):
                rule_consistency_score += 1.0

        if "math" in active_groups and _mentions_any(strategy_lower, keyword_groups["math"]):
            if "math" in code or "gcd" in code or "lcm" in code or "%" in code:
                rule_consistency_score += 0.5

        if "simulation" in active_groups and _mentions_any(strategy_lower, keyword_groups["simulation"]):
            has_loop = any(isinstance(node, (ast.For, ast.While)) for node in ast.walk(tree))
            has_state = any(v in {"state", "cur", "curr", "now", "pos"} for v in variable_names)
            if has_loop and has_state:
                rule_consistency_score += 0.5
        
        if ("완전탐색" in strategy_lower or "모든" in strategy_lower or "조합" in strategy_lower):
            # for 문 또는 itertools.permutations/combinations
            has_for = any(isinstance(node, ast.For) for node in ast.walk(tree))
            has_combinations = "permutations" in function_calls or "combinations" in function_calls
            if has_for or has_combinations:
                rule_consistency_score += 0.5
        
    except Exception:
        # AST 파싱 실패시 기존 키워드 방식으로 폴백
        code_lower = code.lower()
        if "hash_table" in active_groups and _mentions_any(strategy_lower, keyword_groups["hash_table"]) and ("{" in code or "dict" in code_lower or "set" in code_lower):
            rule_consistency_score += 0.5
        if "array" in active_groups and _mentions_any(strategy_lower, keyword_groups["array"]) and "[" in code:
            rule_consistency_score += 0.5
        if "sort" in active_groups and _mentions_any(strategy_lower, keyword_groups["sort"]) and "sort" in code_lower:
            rule_consistency_score += 0.5
        if "two_pointer" in active_groups and _mentions_any(strategy_lower, keyword_groups["two_pointer"]) and ("left" in code_lower and "right" in code_lower):
            rule_consistency_score += 0.5
    
    rule_consistency_score = min(rule_consistency_score, 4.0)
    
    print(f"[룰베이스 평가] 전략: {rule_strategy_score:.1f}/4, 일치: {rule_consistency_score:.1f}/4", flush=True)
    
    # ========== 2단계: LLM 보정 (선택적, 안정성 우선) ==========
    
    llm_strategy_score = rule_strategy_score
    llm_consistency_score = rule_consistency_score
    llm_feedback = ""
    
    # LLM 호출 조건: 매우 좁게 제한해 일관성을 우선
    use_llm = (
        bool(problem_text and len(problem_text.strip()) >= 50)
        and char_count >= 120
        and len(code) >= 200
        and not _has_placeholder(code)
        and 1.0 <= rule_strategy_score <= 2.5
        and rule_consistency_score <= 1.0
    )
    
    if use_llm:
        try:
            system_prompt = """당신은 코딩 면접 평가 전문가입니다.
문제, 전략, 코드를 종합적으로 분석하여 점수를 보정하세요.

**평가 기준:**
- 전략 품질 (0~4점): 문제에 적합한 알고리즘 제시, 구체성
- 일치도 (0~4점): 전략과 코드의 알고리즘/자료구조 일치 여부
- 문제 적합성: 제시한 알고리즘이 문제 특성에 맞는지"""

            user_prompt = f"""## 문제
{problem_text[:500] if problem_text else "문제 정보 없음"}

## 전략 (룰베이스 점수: {rule_strategy_score:.1f}/4)
{strategy_text[:400]}

## 코드 (일치 룰베이스: {rule_consistency_score:.1f}/4)
```python
{code[:1000]}
```

문제를 고려하여 룰베이스 점수를 보정하세요. JSON으로 제시:

{{
  "strategy_score": 2.5,
  "consistency_score": 1.5,
  "reason": "문제에 적합한 완전탐색을 제시하고 구현함"
}}

**주의:** 
- 룰베이스 점수에서 ±1.0 이내로만 보정
- 명백한 오류가 아니면 룰베이스 점수 유지
- 문제 특성과 전략의 적합성 고려"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            model = get_llm("solve")
            response = model.invoke(messages)
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
    problem_text: str = "",
    problem_algorithms: List[str] | str = "",
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
            problem_text=problem_text,
            problem_algorithms=problem_algorithms,
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
    problem_algorithms: List[str] = []
    problem_key = f"livecoding:{session_id}:problem"
    problem_payload = cache.get(problem_key) or {}
    if isinstance(problem_payload, dict) and problem_payload.get("algorithm"):
        raw_algos = problem_payload.get("algorithm")
        if isinstance(raw_algos, list):
            problem_algorithms = [str(a) for a in raw_algos if a]
        elif isinstance(raw_algos, str):
            try:
                parsed = json.loads(raw_algos)
                if isinstance(parsed, list):
                    problem_algorithms = [str(a) for a in parsed if a]
            except Exception:
                problem_algorithms = []
    language = _safe_str(cached_meta.get("language") or "python3")
    
    # ========== LLM 기반 테스트 평가 ==========
    test_results = None
    
    if problem_id and code:
        try:
            # ✅ 1순위: Redis problem_payload에서 function_name 가져오기
            function_name = problem_payload.get("function_name")
            
            if function_name:
                print(f"[DEBUG] Redis에서 function_name 가져옴: {function_name}", flush=True)
            
            # ✅ 2순위: DB 조회
            if not function_name:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT function_name
                        FROM coding_problem_language
                        WHERE problem_id = %s AND language = %s
                        LIMIT 1
                    """, [problem_id, language])
                    row = cursor.fetchone()
                    if row and row[0]:
                        function_name = row[0]
                        print(f"[DEBUG] DB에서 function_name 가져옴: {function_name}", flush=True)

            if not problem_algorithms:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT algorithm
                        FROM coding_problem
                        WHERE problem_id = %s
                        LIMIT 1
                    """, [problem_id])
                    row = cursor.fetchone()
                    if row and row[0]:
                        if isinstance(row[0], list):
                            problem_algorithms = [str(a) for a in row[0] if a]
                        else:
                            try:
                                parsed = json.loads(row[0])
                                if isinstance(parsed, list):
                                    problem_algorithms = [str(a) for a in parsed if a]
                            except Exception:
                                problem_algorithms = []
            
            # ✅ 3순위: 코드에서 자동 추출
            if not function_name:
                import re
                match = re.search(r'def\s+(\w+)\s*\(', code)
                if match:
                    function_name = match.group(1)
                    print(f"[DEBUG] 코드에서 function_name 추출: {function_name}", flush=True)
                else:
                    function_name = "solution"
                    print(f"[WARNING] function_name을 찾을 수 없어 기본값 사용: {function_name}", flush=True)
            
            # 테스트 케이스 가져오기
            test_cases = _get_test_cases_from_db(problem_id)
            
            if test_cases:
                print(f"[INFO] LLM으로 {len(test_cases[:10])}개 테스트 케이스 평가 시작... (함수명: {function_name})")
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
        problem_text=problem_text,
        problem_algorithms=problem_algorithms,
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
        "strategy_algorithms": _extract_strategy_algorithms(strategy_text),
        "chapter2_questions": chap2.get("question") or [],
        "hint_conversation_log": hint.get("conversation_log") or [],
    }
    
    print(f"[problem_solving_eval_node] 완료 - {total_score:.2f}/35점 (스케일: {total_score/35.0:.4f})")
    print(f"[DEBUG] problem_evidence.submitted_code 길이: {len(code)}")
    
    state["status"] = "done"
    return state

def _extract_strategy_algorithms(strategy_text: str) -> List[str]:
    if not strategy_text:
        return []
    strategy_lower = strategy_text.lower()
    groups = set()
    for group, keys in STRATEGY_KEYWORDS.items():
        if any(k.lower() in strategy_lower for k in keys):
            groups.add(group)
    return sorted(groups)
