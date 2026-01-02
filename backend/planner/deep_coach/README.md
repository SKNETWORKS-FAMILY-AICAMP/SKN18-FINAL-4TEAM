# Deep Coach Judge Design

이 문서는 evidence 코치의 진행도 판정 노드(judge)를 deepagent로 구성하는 설계 요약입니다.

## 목표
- 입력: `video_summary`(영상 요약), `draft`(정규화된 사용자 글)
- 출력: `completion_level`(학습완료|추가 보완 필요|미흡), `missing_slots`, `lint`, `confidence`
- 품질 판단을 서브에이전트로 분리해 커버리지(요약 충실도)와 이해/정합성(왜곡 여부)을 각각 평가하고, 메인 에이전트가 종합해 일관된 판정과 점수를 낸다.

## 컴포넌트
- Slot Matcher (subagent)
  - 영상 원문을 요약해 만든 기준 요약문(video_summary)을 기준으로 사용자가 작성한 요약 글(draft)에서 각 요약문이 의미적으로 충분히 반영되었는지 전혀 반영되지 않았는지 부분적으로만 반영되었거나 모호한지 를 판단하여 분류한다.
  
  출력 예시(JSON): `{ "present": [...], "missing": [...], "ambiguous": [...] }`
  - 기준:
    - present: 사용자 글에 명확히 포함
    - missing: 전혀 언급 없음
    - ambiguous: 언급 있으나 모호/부분적

- Lint Checker (subagent)
  - 역할: 요약 품질/왜곡 위험 신호를 태그+짧은 메시지로 기록.
  - 출력 예시(JSON): `{ "lint": [ { "tag": "logic", "message": "인과가 뒤집힘" }, ... ] }`
  - 태그 기준: 
    - `fact`: 사실 오류, 기준 요약과의 명백한 불일치, 오개념
    - `logic`: 논리 흐름 문제 (인과, 근거, 연결), 
    - `format`: 요약 형식/요구사항 위반
    - `style`: 가독성/문장 구조/표현 방식의 문제

- Main Judge (orchestrator)
  - 사용자의 요약이 영상 요약을 얼마나 충실히 반영했는지와 어떤 부분이 부족한지를 Slot Matcher와 Lint Checker 결과를 바탕으로 종합 판정하는 역할
  - 최종 출력: `completion_level`, `missing_slots`(=slot missing), `lint`
  - 툴(가이드용): judge_calc_tool(missing, lint)로 하드 룰/가중치 기반 level 산출(일관성 확보용, 필요시 최소 조정 허용)

## 판정 규칙(예시)
- missing_slots 없음 && lint 경미 → COMPLETE(학습 완료)
- 핵심 missing 또는 치명적 fact/logic 오류 → NEEDS_WORK(미흡/틀림)
- 그 외 → POLISH(추가 보완 필요)

## 향후 발전 아이디어
- confidence 복원: missing·lint 개수/심각도 기반 휴리스틱을 점수화해 UI 표기/재시도 트리거에 활용
- judge_calc_tool 가중치 튜닝: tag별 가중치/임계값 조정, ambiguous 처리 규칙 세분화
- 서브에이전트 확대: 형식/길이 준수 체크 전용 에이전트 추가 등
