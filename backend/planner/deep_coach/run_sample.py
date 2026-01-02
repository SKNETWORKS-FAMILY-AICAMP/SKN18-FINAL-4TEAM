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
DFS(깊이 우선 탐색)와 BFS(너비 우선 탐색)는 그래프 탐색 알고리즘으로, 여러 개체가 연결된 구조에서 특정 경로를 탐색하거나 조건을 만족하는 경우를 찾는 데 사용된다. 이 영상에서는 두 알고리즘의 개념을 드라마를 보는 방식에 비유해 설명하며, DFS는 하나의 경로를 처음부터 끝까지 탐색하는 방식이고 BFS는 여러 경로를 한 단계씩 동시에 탐색하는 방식이라고 설명한다.

DFS는 한 경로를 끝까지 탐색한 뒤 되돌아와 다른 경로를 탐색하는 특성 때문에 재귀 함수(또는 스택)를 사용해 구현하는 것이 일반적이다. 예를 들어 타겟넘버 문제에서는 숫자를 더하거나 빼는 모든 조합을 재귀적으로 탐색하며, 하나의 조합이 완성되면 결과를 확인하고 다시 다른 조합으로 이동하는 방식으로 동작한다. 이러한 특성 때문에 DFS는 동작 과정을 검증하기 쉽고 코드가 간결하다는 장점이 있다.

반면 BFS는 여러 경로를 동시에 한 단계씩 확장해 나가는 방식으로, 큐를 사용해 구현한다. 여행경로 문제처럼 시작 지점에서 연결된 모든 경우를 순서대로 탐색해야 하는 상황에서 적합하며, 먼저 들어온 경로부터 처리되기 때문에 탐색 순서가 보장된다. BFS는 초반에는 느려 보일 수 있지만, 최악의 경우에도 탐색 깊이가 제한되어 있어 수행 시간이 비교적 안정적이라는 특징이 있다.

영상에서는 DFS와 BFS를 활용하는 대표적인 문제 유형으로 경로 탐색 문제, 네트워크 연결 여부를 판단하는 문제, 그리고 모든 조합을 만들어 비교해야 하는 조합형 문제를 제시한다. 또한 두 알고리즘 모두 정답을 찾을 수 있지만, 문제의 난이도와 시간 제한에 따라 선택이 달라져야 한다고 설명한다. 구현과 검증이 빠른 DFS가 유리한 경우도 있지만, 탐색 시간이 길어질 가능성이 있는 문제에서는 BFS가 더 적합할 수 있다.

결론적으로 코딩 테스트에서는 문제 유형과 조건을 빠르게 파악한 뒤 DFS와 BFS 중 더 적합한 알고리즘을 선택하는 것이 중요하며, 한 문제를 두 방식으로 모두 연습해보는 것이 알고리즘 이해와 실전 대비에 도움이 된다고 정리할 수 있다.
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
