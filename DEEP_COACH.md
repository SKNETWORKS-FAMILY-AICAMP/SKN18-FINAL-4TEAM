# Planner Modules Overview

`backend/planner`에는 세 가지 핵심 모듈이 있으며, 각각 다른 단계의 학습 코칭을 담당합니다.

## deep_coach
- 목적: 영상 요약과 사용자 글을 기반으로 진행도 판정 및 인라인 피드백을 생성하는 코치 그래프.
- 핵심 흐름: `graph.py`에서 evidence → judge → coach 단계로 진행하며, 완료 시 조기 종료.
- 출력: `completion_level`, `missing_slots`, `ambiguous_slots`, `lint`, `annotated_draft`.
- 참고: 상세 설계/프롬프트는 `deep_coach/README.md`, `deep_coach/agents.py`에 정의됨.

## deep_recommend
- 목적: 성장 리포트를 입력으로 7일 학습 계획을 생성하는 추천 엔진.
- 핵심 흐름: 분석(ReportAnalyzer) → 슬롯 설계(TopicSlotPlanner) → 영상 후보 선택(VideoSelector) → 플랜 구성(PlanBuilder) → 검증.
- 출력: 7일 `final_plan` (하루 단위 학습 목표/콘텐츠/시간 계획 포함).
- DB 연동: `recommended_videos` 테이블을 `video_search_tool`로 조회 (`deep_recommend/tools.py`).
- 참고: 상세 설계는 `deep_recommend/README.md`.

## growth_report
- 목적: 누적 리포트에서 강점/약점/개선 행동과 변화 요약을 생성하는 성장 리포트 파이프라인.
- 핵심 흐름: 약점 → 강점 → 개선 전략 → (이전 리포트 존재 시) 변화 분석 → 최종 리포트 작성.
- 출력: `final_report`(텍스트), `strengths`, `weaknesses`, `improvements`, `growth_delta`.
- 참고: 노드 구성은 `growth_report/graph.py`, 프롬프트/규칙은 `growth_report/node.py`.