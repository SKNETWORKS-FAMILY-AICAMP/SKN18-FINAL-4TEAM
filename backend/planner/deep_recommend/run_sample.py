"""
간단한 샘플 실행 스크립트.
환경: OPENAI_API_KEY 필요, deepagents/LLM 의존.
"""

from nodes import report_analyzer,slot_planner,video_selector
from tools import video_search_tool


def main():
    
    inputs = {
        'needs_profile': {
            'goal': '그래프/BFS 및 이분 탐색 문제의 큰 전략은 잘 잡지만, 이를 실행 가능한 코드로 완성하는 구현 마무리 단계에서 자주 멈춘다.', 
            'focus_topics': ['그래프', 'BFS', '이분 탐색'], 
            'preferences': ['Python 중심', 'AI/ML 직무 지향', '딥러닝 모델링 관심'], 
            'language': 'Python'
        },
        'slots':[
            {
                'day': 1, 
                'day_plan_topic': '그래프 및 BFS 기초 구현', 
                'domain': 'algorithm', 
                'category': 'BFS', 
                'reason': '그래프 및 BFS 기초 구현 체득'
            }, 
            {
                'day': 2, 
                'day_plan_topic': '그래프 탐색의 차이: BFS vs DFS 실전 비교', 
                'domain': 'algorithm', 
                'category': 'DFS', 
                'reason': 'BFS와의 차이 이해를 위한 실전 비교'
            }, 
            {
                'day': 3, 
                'day_plan_topic': '이분 탐색의 원리와 Python 구현', 
                'domain': 'algorithm', 
                'category': 'Binary Search', 
                'reason': '이분 탐색 기본 구현 강화'
            },
            {
                'day': 4, 
                'day_plan_topic': '정렬된 배열에서의 이분 탐색 응용문제 풀이', 
                'domain': 'algorithm', 
                'category': 'Binary Search',
                'reason': '응용 문제 해결력 강화'   
            },
            {
                'day': 5, 
                'day_plan_topic': '그래프에서 BFS를 이용한 최단경로 문제 예제', 
                'domain': 'algorithm', 
                'category': 'BFS', 
                'reason': '실전 최단경로 문제를 BFS로 해결 전략 익히기'
            }, 
            {
                'day': 6, 
                'day_plan_topic': '그래프 구현에서 큐와 방문처리 최적화', 
                'domain': 'algorithm', 
                'category': 'BFS', 
                'reason': '실전 최단경로 문제를 BFS로 해결 전략 익히기'
                }, 
            {
                'day': 7, 
                'day_plan_topic': '실전 BFS 코드 구현 및 시연', 
                'domain': 'live_coding', 
                'category': 'CODE_VERIFICATION', 
                'reason': '실전 코드 검증 시연'
            }]
    }
    agent = video_selector(inputs)
    print(agent)


if __name__ == "__main__":
    import os, sys, pathlib, django
    sys.path.append(str(pathlib.Path(__file__).resolve().parents[2])) # backend 디렉터리 추가
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()
    main()