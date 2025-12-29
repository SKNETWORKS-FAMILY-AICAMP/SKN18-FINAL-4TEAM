from dotenv import load_dotenv
load_dotenv() # API 키 로드

import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from .state import PlanState
from .tools import search_youtube_videos

llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

# [Node 1] Planner: 기간별 맞춤 전략 수립
def planner_node(state: PlanState):
    duration = state['duration']
    print(f"\n🧠 [Planner] '{state['user_weakness']}' ({duration}일) 전략 수립 중...")

    # 기간에 따른 프롬프트 분기
    if duration == 30:
        strategy = "30일(4주) 과정이므로 '주차별(Weekly)' 단계적 성장을 목표로 주제를 구성하세요. (1주:기초 -> 2주:구현 -> 3주:심화 -> 4주:프로젝트)"
    else:
        strategy = "7일(1주) 과정이므로 불필요한 이론을 줄이고 '핵심 기능 실습' 위주로 구성하세요."

    prompt = ChatPromptTemplate.from_template(
        """
        당신은 IT 교육 커리큘럼 설계자입니다.
        약점: '{weakness}' / 기간: {duration}일
        
        [지침] {strategy}
        
        {duration}일간의 계획을 JSON으로 작성하세요.
        각 항목은 "day", "topic", "search_query"를 가져야 합니다.
        "search_query"는 유튜브 검색용 구체적인 키워드(영어/한글 혼용 권장)여야 합니다.
        
        [예시]
        [ {{ "day": 1, "topic": "...", "search_query": "Django ViewSet tutorial" }} ]
        
        오직 JSON만 반환하세요.
        """
    )
    
    chain = prompt | llm
    response = chain.invoke({"weakness": state["user_weakness"], "duration": duration, "strategy": strategy})
    
    try:
        content = response.content.strip().replace("```json", "").replace("```", "")
        curriculum = json.loads(content)
    except:
        curriculum = [{"day": i+1, "topic": "Study", "search_query": f"{state['user_weakness']} tutorial"} for i in range(duration)]

    return {
        "curriculum": curriculum,
        "final_schedule": [None] * duration, # 결과 담을 공간 확보
        "retry_count": 0,
        "incomplete_days": [c['day'] for c in curriculum] # 처음엔 다 미완성
    }

# [Node 2] Searcher: 필요한 날짜만 검색
def searcher_node(state: PlanState):
    print(f"\n🔍 [Searcher] 자료 수집 중... (시도 {state['retry_count'] + 1}회차)")
    
    curriculum = state["curriculum"]
    schedule = list(state["final_schedule"])
    target_days = state["incomplete_days"]

    for item in curriculum:
        day = item['day']
        if day not in target_days: continue # 이미 찾은 날은 패스
            
        query = item['search_query']
        print(f"   👉 Day {day} 검색: '{query}'")
        
        results = search_youtube_videos(query, max_results=1)
        
        if results:
            video = results[0]
            schedule[day-1] = {
                "day": day,
                "topic": item['topic'],
                "video_title": video['title'],
                "video_url": video['url'],
                "search_query": query
            }
        else:
            # 못 찾으면 비워둠 (Validator가 처리)
            schedule[day-1] = None

    return {"final_schedule": schedule}

# [Node 3] Validator: 품질 검증
def validator_node(state: PlanState):
    print("\n🧐 [Validator] 검색 결과 검증 중...")
    schedule = state["final_schedule"]
    incomplete_days = []
    feedback_list = []

    for i, item in enumerate(schedule):
        day = i + 1
        if not item or not item.get('video_url'):
            print(f"   ❌ Day {day}: 누락됨")
            incomplete_days.append(day)
            # 피드백 생성 (현재 쿼리 정보 포함)
            current_query = state['curriculum'][i]['search_query']
            feedback_list.append(f"Day {day} 실패 (Query: {current_query})")
        else:
            print(f"   ✅ Day {day}: 통과")

    return {
        "incomplete_days": incomplete_days,
        "validation_feedback": "; ".join(feedback_list)
    }

# [Node 4] Replanner: 쿼리 수정 (LLM 사용)
def replanner_node(state: PlanState):
    retry = state["retry_count"] + 1
    print(f"\n🔄 [Replanner] 검색어 전략 수정 중... ({retry}회차)")
    
    incomplete_days = state["incomplete_days"]
    curriculum = state["curriculum"]
    
    # LLM에게 더 쉬운 검색어로 바꿔달라고 요청
    prompt = ChatPromptTemplate.from_template(
        """
        유튜브 검색에 실패했습니다. 다음 날짜들의 검색어를 '더 단순하고 대중적인 키워드'로 수정하세요.
        ("tutorial for beginners" 등을 활용)
        
        실패한 날짜들: {target_days}
        실패 내역: {feedback}
        
        [반환 형식]
        [ {{ "day": 1, "search_query": "New Simple Query" }} ]
        오직 JSON만 반환하세요.
        """
    )
    
    chain = prompt | llm
    response = chain.invoke({
        "target_days": str(incomplete_days),
        "feedback": state["validation_feedback"]
    })
    
    try:
        new_queries = json.loads(response.content.strip().replace("```json", "").replace("```", ""))
        # 커리큘럼 업데이트
        for new_item in new_queries:
            for original in curriculum:
                if original['day'] == new_item['day']:
                    print(f"   ✏️ 수정: '{original['search_query']}' -> '{new_item['search_query']}'")
                    original['search_query'] = new_item['search_query']
    except:
        # LLM 에러 시 룰 베이스 단순화
        for item in curriculum:
            if item['day'] in incomplete_days:
                item['search_query'] = f"{item['topic']} tutorial"

    return {"curriculum": curriculum, "retry_count": retry}