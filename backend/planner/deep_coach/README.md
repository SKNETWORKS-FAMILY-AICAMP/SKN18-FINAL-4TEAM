# Deep Coach (LangGraph + Deepagents)

증거 기반 요약 코치 그래프를 LangGraph와 deepagent 조합으로 완성한 설계/사용 가이드입니다. 영상 요약(video_summary)과 사용자 글(draft)을 받아 진행도 판정과 인라인 피드백을 생성합니다.

## 입출력 스키마
- 입력: video_summary, draft (옵션: user_id, video_id)
- 중간 상태: normalized_draft (정규화된 사용자 글)
- 출력: completion_level ("COMPLETE"|"POLISH"|"NEEDS_WORK"), missing_slots, ambiguous_slots, lint [{tag, message}], coach_output(annotated_draft)
- 판정 한글 대응: COMPLETE=학습완료, POLISH=추가 보완 필요, NEEDS_WORK=미흡

### judge 노드 기대 JSON 예시
```json
{
  "completion_level": "POLISH",
  "missing_slots": ["BFS 활용 시 효율성"],
  "ambiguous_slots": ["DFS 시간 복잡도 언급"],
  "lint": [{"tag": "logic", "message": "DFS/BFS 비교 근거 불명확"}]
}
```

### coach 노드 출력 예시
```json
{
  "annotated_draft": "...사용자 문장... [[추가: BFS 효율 조건 추가]]"
}
```

## LangGraph 플로우
1) evidence_ingest_node: draft를 정규화해 normalized_draft에 저장.
2) judge_progress_agent_node: deepagent 기반 메인 판정 에이전트가 slot-matcher와 lint-checker 서브에이전트를 호출 후 judge_calc_tool로 completion_level을 산출.
3) final_feedback_agent_node: 판정 결과를 받아 clarify/fix/inline 서브에이전트로 annotated_draft 생성.
4) COMPLETE일 때는 judge 이후 종료, 그 외에는 coach 노드까지 진행.

## 에이전트 구성
- 메인 judge 에이전트
  - subagent: slot-matcher (present/missing/ambiguous 분류)
  - subagent: lint-checker (fact/logic/format/style 린트)
  - tool: judge_calc_tool(missing, lint) → completion_level 가이드라인, 이후 _choose_lenient으로 완화 적용.
- 코치 에이전트
  - subagent: clarify-agent (ambiguous_slots 문장 교체안 생성 → [[확인]])
  - subagent: fix-agent (missing → [[추가]], fact/logic lint → [[수정]])
  - subagent: inline-annotator (교체·마커를 draft에 적용, 문장 끝에만 부착)

## 판정/마커 규칙 요약
- missing_slots 없음 && lint 경미 → COMPLETE
- 핵심 missing 또는 치명적 fact/logic → NEEDS_WORK
- 그 외 → POLISH
- 마커: missing → [[추가]], fact/logic → [[수정]], ambiguous → [[확인]] (format/style은 마커 미반영)

## 실행 방법 (샘플)
1) .env에 OPENAI_API_KEY 설정 (.env.sample 참고)
2) 의존성: requirements.txt 기준 deepagents, langgraph, langchain-openai 등 설치
3) 샘플 실행: 프로젝트 루트에서 `python backend/planner/deep_coach/run_sample.py`
   - 출력: completion_level, missing_slots/ambiguous_slots/lint, annotated_draft

## 커스터마이즈 포인트
- 프롬프트: backend/planner/deep_coach/agents.py 내 SLOT_PROMPT/LINT_PROMPT/CLARIFY_PROMPT/FIX_PROMPT/INLINE_ANNOTATOR_PROMPT 수정
- 판정 기준: utils.py의 judge_calc_tool 및 _choose_lenient 조정
- 그래프 흐름: graph.py 라우터(router)에서 COMPLETE 시 바로 종료하도록 구성 (필요 시 브랜치 추가 가능)
