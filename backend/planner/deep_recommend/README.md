# Deep Recommend (7일 학습 플래너, Deepagents)

growth_reports 텍스트(누적 코딩테스트 강점/약점/변화/개선)를 받아 7일 학습 계획을 생성하는 deepagent 설계입니다. 추천 영상은 `recommended_videos` 테이블을 조회해 선정합니다.

## 입출력 개요
- 입력: growth_reports(텍스트), user_id, 사용자 프로필(선호 직무/언어 등)
- 출력: final_plan 7개

## 주요 구성 (`agents.py`) — 역할 요약
- `create_weekly_study_planner_agent`: 서브에이전트들을 순서대로 호출해 7일 플랜을 만들고, 검증까지 수행하는 메인 오케스트레이터.
- `ReportAnalyzerAgent`: 단일 텍스트 growth_reports에서 개선 목표, 현재 수준, 반복 약점/최근 악화 영역, 유지할 강점을 뽑는다. 선호/언어/시간 예산은 외부 프로필 입력을 사용한다.
- `TopicSlotPlannerAgent`: 7일 학습 슬롯을 설계한다. base/practice/review 비율 3:3:1, 난이도 1~5 점진 상승, 주제 중복 방지를 적용한다.
- `VideoSelectorAgent`: `video_search_tool`을 통해 `RecommendedVideo` 테이블을 summary/category/domain 기준 부분 검색 후 슬롯별 후보 3~5개를 고른다.
- `PlanBuilderAgent`: 슬롯과 후보를 매칭해 최종 7일 플랜을 작성한다. 학습 목표, 성공 기준, 시간 계획 등 실행 정보를 포함한다.
- `validate_plan_tool`: 슬롯 개수·주제/URL 중복·필수 필드·난이도 범위를 검사해 ok/issues를 반환한다.

## DB 연동
- 테이블: `docker/init.sql` 정의된 `recommended_videos`
- Django 모델: `planner.models.RecommendedVideo`
- 검색 툴: `video_search_tool(query)` — summary/category/domain 부분 검색, 상위 10개 반환
