"""
LangGraph evidence_coach를 샘플 입력으로 직접 실행하는 스크립트입니다.
- .env에서 OPENAI_API_KEY를 로드해 모델 호출이 가능하면 실제로 돌립니다.
- 출력: completion_level, missing/ambiguous/lint, annotated_draft 요약.
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

# .env에서 키 로드 시도
DOTENV_PATH = ROOT / ".env"
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if not os.getenv("OPENAI_API_KEY"):
    if load_dotenv:
        load_dotenv(DOTENV_PATH)
    elif DOTENV_PATH.exists():
        for line in DOTENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            if key and key not in os.environ:
                os.environ[key] = val

from backend.planner.deep_coach.graph import create_evidence_coach_graph  # noqa: E402


# 샘플 입력
SAMPLE_VIDEO_SUMMARY = """
DFS(깊이 우선 탐색)와 BFS(너비 우선 탐색)는 그래프 탐색 알고리즘으로, 각각의 특징에 따라 문제를 해결하는 방식이 다릅니다. DFS는 한 경로를 끝까지 탐색한 후 다른 경로로 이동하는 방식으로, 재귀함수를 통해 구현됩니다. 예를 들어, 타겟넘버 문제에서는 주어진 숫자들을 더하거나 빼서 목표 숫자를 만드는 모든 경우를 탐색합니다. 반면, BFS는 여러 경로를 동시에 탐색하며 큐를 사용하여 순서대로 처리합니다. 여행경로 문제에서 모든 항공권을 활용하는 경로를 찾는 데 적합합니다.

DFS는 동작 검증이 용이하고 코드가 간결해지는 장점이 있지만, 최악의 경우 모든 조합을 탐색해야 할 수 있어 시간이 초과될 위험이 있습니다. BFS는 모든 경우를 한 단계씩 탐색하므로 시간 복잡도가 낮고, 특정 조건에서 더 효율적일 수 있습니다. 문제의 난이도와 유형에 따라 적절한 알고리즘을 선택하는 것이 중요합니다.

- DFS는 재귀함수로 구현하며, 특정 경로를 끝까지 탐색.
- BFS는 큐를 사용하여 여러 경로를 동시에 탐색.
- DFS는 동작 검증이 쉽고 코드가 간결하지만, 최악의 경우 시간이 초과될 수 있음.
- BFS는 시간 복잡도가 낮고, 특정 문제에서 더 효율적일 수 있음.
- 문제 유형에 따라 DFS와 BFS를 적절히 선택하여 해결하는 것이 중요.
""".strip()

SAMPLE_DRAFT = """
이 영상은 문제를 해결하기 위해 핵심 아이디어를 먼저 정의한 뒤,
그 아이디어를 바탕으로 알고리즘 흐름을 구성하는 과정을 설명한다.

먼저 입력 데이터를 어떻게 해석해야 하는지 정리하고,
그 다음 단계별로 어떤 연산을 수행하는지 순서대로 설명한다.
이 과정에서 불필요한 연산을 줄이기 위해 조건 분기와 자료구조를 적절히 사용한다.

이 방법은 입력 크기가 커질 때도 안정적으로 동작하며,
시간 복잡도는 문제 조건을 만족하는 수준으로 유지된다.
다만 모든 경우에 적용되는 것은 아니며,
특정 조건에서는 다른 접근 방식이 더 적합할 수 있다.
""".strip()




def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ OPENAI_API_KEY가 없습니다. .env를 확인하세요.")
        return

    graph = create_evidence_coach_graph()
    state = {"video_summary": SAMPLE_VIDEO_SUMMARY, "draft": SAMPLE_DRAFT}
    print("▶ 그래프 실행 중...\n")
    state = graph.invoke(state)

    print(f"completion_level: {state.get('completion_level')}")
    print(f"missing_slots: {state.get('missing_slots')}")
    print(f"ambiguous_slots: {state.get('ambiguous_slots')}")
    print(f"lint: {state.get('lint')}")
    coach = state.get("coach_output")
    print("\n--- annotated_draft ---")
    print(coach)


if __name__ == "__main__":
    main()
