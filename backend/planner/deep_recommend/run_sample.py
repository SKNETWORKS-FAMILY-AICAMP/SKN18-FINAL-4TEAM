"""
간단한 샘플 실행 스크립트.
환경: OPENAI_API_KEY 필요, deepagents/LLM 의존.
"""

import time
from agents import create_weekly_study_planner_agent


def main():
    agent = create_weekly_study_planner_agent()
    growth_reports = """
    [핵심 강점]  
    문제 제약에 맞는 시간·공간 복잡도를 의식하며, 불필요한 연산·자료구조 없이 설계하는 능력이 안정적으로 드러난다. 
    문제를 수학적·함수적 모델로 추상화하고, 전략 단계에서 세운 핵심 알고리즘을 코드 구조에 일관되게 녹여내는 힘이 강하다.

    [개선 필요 영역]  
    그래프/BFS·이분 탐색과 같은 알고리즘의 큰 전략은 잘 잡지만, 이를 끝까지 실행 가능한 코드로 완성하는 구현 마무리 단계에서 자주 멈춘다. 
    기본적인 실행 가능성, 특히 파이썬 들여쓰기·포매팅 검증이 미흡하고, 면접 상황에서 사고 과정과 전략을 말로 공유하는 커뮤니케이션이 거의 드러나지 않는다.

    [개선 액션 플랜]  
    그래프/BFS·이분 탐색 문제에서는 코딩 전 A4 절반에 자료구조 목록, 메인 루프 조건, 보조 함수 시그니처, 
    종료/리턴 조건 4줄을 먼저 적고 이를 그대로 코드에 옮겨 실행 가능한 최소 골격부터 완성한다. 
    코드 제출 전에는 `print('CHECK')`로 파싱 여부 확인, 블록 시작 다음 줄 들여쓰기를 전부 스페이스 4개로 통일, 
    가장 단순한 테스트 입력을 하드코딩해 실제 출력까지 확인하는 3단계 로컬 검증 루틴을 반복한다. 
    면접에서는 3분 안에 “이 문제를 ___ 문제로 보고 ___ 알고리즘을 쓰겠다”, 
    “주요 변수/자료구조와 역할”, “코드를 3단계로 나누는 계획”을 구두로 설명한 뒤, 
    각 단계 구현이 끝날 때마다 현재 진행 상황과 다음 작업을 한 문장 이상으로 업데이트한다.

    [다음 단계에서의 기대]  
    위 루틴이 습관화되면, 전략 수립 능력에 비해 뒤처져 있던 구현 완성도와 실행 안정성이 빠르게 따라붙고, 
    면접관 입장에서도 “생각-설계-구현”의 전 과정을 신뢰할 수 있게 된다.
    """
    user_profile = {
        "tech_stack": ["python"],
        "desired_role": "AI/ML 엔지니어",
        "detailed_role": "딥러닝 모델링"
    }
    inputs = {
        "user_id": "sonju",
        "growth_reports": growth_reports,
        "user_profile": user_profile,
    }
    last_err = None
    for attempt in range(3):
        try:
            print(agent.invoke(inputs))
            last_err = None
            break
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(1.0)  # rate limit 완화용 딜레이
    if last_err:
        raise last_err


if __name__ == "__main__":
    main()
