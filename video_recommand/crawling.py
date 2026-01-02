from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
import csv
from typing import Dict, Iterable, List, Optional, Set
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv
from tavily import TavilyClient
try:
    from tavily.errors import ForbiddenError
except Exception:
    ForbiddenError = None

# 판단축
'''
core_concepts	핵심 개념을 이해했는가
algorithm_flow	동작 흐름을 이해했는가
when_to_use	언제 쓰는지 아는가
when_not_to_use	언제 쓰면 안 되는지 아는가
complexity	복잡도를 인식하는가
examples	예제/문제로 연결하는가
'''

# =========================================================
# 1) Category (ko/en)
# =========================================================
@dataclass(frozen=True)
class Category:
    ko: str
    en: str

CATEGORIES: List[Category] = [
    Category("BFS", "BFS"),
    Category("DFS", "DFS"),
    Category("DP", "Dynamic Programming"),
    Category("Greedy", "Greedy"),
    Category("Binary Search", "Binary Search"),
    Category("Two Pointers", "Two Pointers"),
    Category("Sliding Window", "Sliding Window"),
    Category("Hashing", "Hashing"),
    Category("Sorting", "Sorting"),
    Category("Stack", "Stack"),
    Category("Queue", "Queue"),
    Category("Heap", "Heap"),
    Category("Backtracking", "Backtracking"),
    Category("Bitmask", "Bitmask"),
    Category("Math", "Math"),
    Category("Prefix Sum", "Prefix Sum"),
    Category("Dijkstra", "Dijkstra"),
    Category("Shortest Path", "Shortest Path"),
    Category("Topological Sort", "Topological Sort"),
    Category("Divide and Conquer", "Divide and Conquer"),
    Category("Parsing", "Parsing"),
    Category("String", "String"),
    Category("Graph", "Graph"),
    Category("Tree", "Tree"),
]

# 프로그래밍 언어별 검색 키워드(인간 언어별)
CODE_LANG_KEYWORDS: Dict[str, Dict[str, List[str]]] = {
    "python": {
        "ko": ["파이썬"],
        "en": ["python"],
    },
    "java": {
        "ko": ["자바"],
        "en": ["java"],
    },
    "c": {
        "ko": ["C언어", "C 언어"],
        "en": ["C"],
    },
    "cpp": {
        "ko": ["C++"],
        "en": ["C++", "cpp"],
    },
}

# category별 키워드(너무 과세분화 없이 3~4개)
KEYWORDS: Dict[str, Dict[str, List[str]]] = {
    "BFS": {
        "ko": ["너비 우선 탐색", "BFS", "그래프 탐색"],
        "en": ["breadth first search", "BFS", "graph traversal"],
    },
    "DFS": {
        "ko": ["깊이 우선 탐색", "DFS", "그래프 탐색", "재귀"],
        "en": ["depth first search", "DFS", "graph traversal", "recursion"],
    },
    "DP": {
        "ko": ["동적 계획법", "DP", "점화식", "메모이제이션"],
        "en": ["dynamic programming", "dp", "recurrence", "memoization"],
    },
    "Greedy": {
        "ko": ["그리디", "탐욕법", "최적 선택"],
        "en": ["greedy", "greedy choice", "optimal choice"],
    },
    "Binary Search": {
        "ko": ["이진 탐색", "파라메트릭 서치"],
        "en": ["binary search", "parametric search"],
    },
    "Two Pointers": {
        "ko": ["투 포인터", "두 포인터", "슬라이딩 윈도우"],
        "en": ["two pointers", "two-pointer technique", "sliding window"],
    },
    "Sliding Window": {
        "ko": ["슬라이딩 윈도우", "구간 합", "부분 배열"],
        "en": ["sliding window", "subarray", "window technique"],
    },
    "Hashing": {
        "ko": ["해싱", "해시맵", "충돌 해결"],
        "en": ["hashing", "hash map", "collision resolution"],
    },
    "Sorting": {
        "ko": ["정렬 알고리즘", "커스텀 정렬", "정렬 기준"],
        "en": ["sorting", "sorting algorithm", "custom sort"],
    },
    "Stack": {
        "ko": ["스택", "모노톤 스택", "괄호 검사"],
        "en": ["stack", "monotonic stack", "parentheses"],
    },
    "Queue": {
        "ko": ["큐", "자료구조", "BFS 큐"],
        "en": ["queue", "data structure", "bfs queue"],
    },
    "Heap": {
        "ko": ["힙", "우선순위 큐", "최댓값 최소값"],
        "en": ["heap", "priority queue", "max heap", "min heap"],
    },
    "Backtracking": {
        "ko": ["백트래킹", "완전 탐색", "분기 한정"],
        "en": ["backtracking", "brute force search", "branch and bound"],
    },
    "Bitmask": {
        "ko": ["비트마스크", "부분집합 비트", "비트 연산"],
        "en": ["bitmask", "bit masking", "bit operations"],
    },
    "Math": {
        "ko": ["수학 문제", "정수론", "확률 통계", "조합"],
        "en": ["math problems", "number theory", "probability", "combinatorics"],
    },
    "Prefix Sum": {
        "ko": ["누적 합", "프리픽스 합", "구간 합"],
        "en": ["prefix sum", "cumulative sum", "range sum"],
    },
    "Dijkstra": {
        "ko": ["다익스트라", "최단경로", "우선순위 큐"],
        "en": ["dijkstra", "shortest path", "priority queue"],
    },
    "Shortest Path": {
        "ko": ["최단 경로", "벨만포드", "플로이드워셜"],
        "en": ["shortest path", "bellman ford", "floyd warshall"],
    },
    "Topological Sort": {
        "ko": ["위상정렬", "사이클 판별", "DAG"],
        "en": ["topological sort", "cycle detection", "DAG"],
    },
    "Divide and Conquer": {
        "ko": ["분할 정복", "재귀 분할", "병합"],
        "en": ["divide and conquer", "recursive divide", "merge"],
    },
    "Parsing": {
        "ko": ["파싱", "문자열 파싱", "구문 분석"],
        "en": ["parsing", "string parsing", "syntax parsing"],
    },
    "String": {
        "ko": ["문자열 처리", "패턴 매칭", "파싱"],
        "en": ["string", "pattern matching", "string parsing"],
    },
    "Graph": {
        "ko": ["그래프", "그래프 탐색", "연결 요소"],
        "en": ["graph", "graph traversal", "connected components"],
    },
    "Tree": {
        "ko": ["트리", "트리 순회", "이진 트리", "LCA"],
        "en": ["tree", "tree traversal", "binary tree", "lca"],
    },
}


# =========================================================
# 2) Query generator
# =========================================================
def _filters() -> str:
    # Tavily/검색엔진 공통 필터
    return "site:youtube.com -shorts"


def build_queries(cat: Category, per_lang: int = 4) -> Dict[str, List[str]]:
    kw = KEYWORDS.get(cat.ko, {"ko": [], "en": []})
    ko_kws = kw["ko"][:per_lang]
    en_kws = kw["en"][:per_lang]

    ko_base = cat.ko.replace(" / ", " ")
    en_base = cat.en

    ko = [f"{ko_base} {k} 강의 설명 {_filters()}" for k in ko_kws] or [
        f"{ko_base} 코딩테스트 강의 {_filters()}"
    ]
    en = [f"{en_base} {k} tutorial {_filters()}" for k in en_kws] or [
        f"{en_base} tutorial {_filters()}"
    ]

    return {"ko": ko, "en": en}


def build_all_queries(per_lang: int = 4) -> Dict[str, Dict[str, List[str]]]:
    out: Dict[str, Dict[str, List[str]]] = {}
    for c in CATEGORIES:
        out[c.ko] = build_queries(c, per_lang=per_lang)
    return out


# =========================================================
# 3) URL extraction / normalization
# =========================================================
_YT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def extract_video_id(url: str) -> Optional[str]:
    """Support:
    - youtube.com/watch?v=ID
    - youtu.be/ID
    - youtube.com/shorts/ID
    - youtube.com/embed/ID
    """
    u = (url or "").strip()
    if not u:
        return None

    p = urlparse(u)
    host = (p.netloc or "").lower()
    path = p.path or ""

    if "youtu.be" in host:
        vid = path.lstrip("/").split("/")[0]
        return vid if _YT_ID_RE.match(vid or "") else None

    if "youtube.com" in host:
        if path.startswith("/watch"):
            q = parse_qs(p.query)
            vid = (q.get("v") or [""])[0]
            return vid if _YT_ID_RE.match(vid or "") else None

        if path.startswith("/shorts/"):
            vid = path.split("/shorts/")[1].split("/")[0]
            return vid if _YT_ID_RE.match(vid or "") else None

        if path.startswith("/embed/"):
            vid = path.split("/embed/")[1].split("/")[0]
            return vid if _YT_ID_RE.match(vid or "") else None

    return None


def canonical_watch_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def is_shorts(url: str) -> bool:
    u = (url or "").lower()
    return "/shorts/" in u or "shorts" in u


# =========================================================
# 4) Tavily collection
# =========================================================
@dataclass
class UrlRow:
    category_ko: str
    category_en: str
    code_lang: str  # programming language filter (e.g., "C", "Python", "JavaScript", or "general")
    query: str
    url: str
    video_id: str


def tavily_search_youtube_urls(
    client: TavilyClient,
    query: str,
    max_results: int = 10,
    days: int = 365,
) -> List[str]:
    try:
        resp = client.search(
            query=query,
            max_results=max_results,
            search_depth="basic",
            days=days,
            include_raw_content=False,
            include_answer=False,
        )
    except Exception as exc:
        if ForbiddenError and isinstance(exc, ForbiddenError):
            # Tavily 쿼터 초과 시 명확한 메시지로 중단
            raise RuntimeError("Tavily usage limit exceeded. Reduce queries or upgrade the plan.") from exc
        # 기타 Tavily 에러는 건너뛰고 계속
        print(f"[tavily] warning: {exc} (query skipped)", flush=True)
        return []
    urls: List[str] = []
    for r in resp.get("results", []) or []:
        u = r.get("url")
        if not u:
            continue
        if "youtube.com" in u or "youtu.be" in u:
            urls.append(u)
    return urls


def collect_urls(
    per_lang_queries: int = 4,
    max_results_per_query: int = 10,
    days: int = 365,
    exclude_shorts: bool = True,
    code_langs: Optional[List[str]] = None,  # e.g., ["C", "Python"] to bias results by programming language
) -> List[UrlRow]:
    load_dotenv()
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY is not set. Add it to your environment or .env file.")
    client = TavilyClient(api_key)

    # 우선순위: 함수 인자 > CODE_LANG_KEYWORDS에 정의된 언어들
    code_lang_list = [c.lower() for c in (code_langs or CODE_LANG_KEYWORDS.keys())]

    cat_to_q = build_all_queries(per_lang=per_lang_queries)

    seen_video_ids: Set[str] = set()
    rows: List[UrlRow] = []

    for cat in CATEGORIES:
        qpack = cat_to_q[cat.ko]
        for code_lang in code_lang_list:
            cl_entry = CODE_LANG_KEYWORDS.get(code_lang, {"ko": [], "en": []})

            for base_q in qpack["ko"]:
                ko_keywords = cl_entry.get("ko") or [""]
                for kw in ko_keywords:
                    q_str = f"{base_q} {kw}".strip()
                    try:
                        urls = tavily_search_youtube_urls(
                            client,
                            query=q_str,
                            max_results=max_results_per_query,
                            days=days,
                        )
                    except RuntimeError as exc:
                        print(exc, flush=True)
                        return rows
                    for u in urls:
                        if exclude_shorts and is_shorts(u):
                            continue
                        vid = extract_video_id(u)
                        if not vid:
                            continue
                        if vid in seen_video_ids:
                            continue
                        seen_video_ids.add(vid)
                        rows.append(
                            UrlRow(
                                category_ko=cat.ko,
                                category_en=cat.en,
                                code_lang=code_lang,
                                query=q_str,
                                url=canonical_watch_url(vid),
                                video_id=vid,
                            )
                        )

            for base_q in qpack["en"]:
                en_keywords = cl_entry.get("en") or [""]
                for kw in en_keywords:
                    q_str = f"{base_q} {kw}".strip()
                    try:
                        urls = tavily_search_youtube_urls(
                            client,
                            query=q_str,
                            max_results=max_results_per_query,
                            days=days,
                        )
                    except RuntimeError as exc:
                        print(exc, flush=True)
                        return rows
                    for u in urls:
                        if exclude_shorts and is_shorts(u):
                            continue
                        vid = extract_video_id(u)
                        if not vid:
                            continue
                        if vid in seen_video_ids:
                            continue
                        seen_video_ids.add(vid)
                        rows.append(
                            UrlRow(
                                category_ko=cat.ko,
                                category_en=cat.en,
                                code_lang=code_lang,
                                query=q_str,
                                url=canonical_watch_url(vid),
                                video_id=vid,
                            )
                        )

    return rows


def save_jsonl(path: str, rows: Iterable[UrlRow]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")


def save_csv(path: str, rows: Iterable[UrlRow]) -> None:
    fieldnames = ["category_ko", "category_en", "code_lang", "query", "url", "video_id"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(asdict(r))


# =========================================================
# 5) Run
# =========================================================
if __name__ == "__main__":
    # 환경변수: TAVILY_API_KEY 필요
    # export TAVILY_API_KEY="tvly-...."

    rows = collect_urls(
        per_lang_queries=4,        # 카테고리당 ko/en 각각 몇 개 쿼리 생성할지
        max_results_per_query=10,  # 쿼리당 URL 후보 수
        days=365,                  # 최근 N일 내 결과(너무 짧게하면 자료 적음)
        exclude_shorts=True,
        # code_langs=["python", "java"],  # 사용 시 CODE_LANGS env 대신 이 목록 사용
    )
    save_csv("youtube_urls.csv", rows)
    print(f"saved {len(rows)} urls -> youtube_urls.csv")
