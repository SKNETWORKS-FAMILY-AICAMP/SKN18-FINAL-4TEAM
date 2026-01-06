Deep Recommend Graph (Neo4j + ES)

요약
- GraphDB는 리포트 기반 Evidence/Gap/Similarity 경로로 문제 후보를 만들고,
  ES가 임베딩+키워드 재랭킹을 수행한다.
- User-Role 직접 연결은 제거한다. Role은 사용하지 않는다.
- 리포트 생성 시 자동으로 Postgres → Neo4j 동기화 큐가 돌고,
  추천은 Neo4j 후보 → ES 재랭킹으로 결정된다.

입력/출력
- 입력(리포트): livecoding_reports (graph_output 포함)
- 출력(추천): graph_output.recommended_problems


1. 구성 요소

1) Neo4j
- 문제 그래프: Problem, AlgoSkill, Difficulty
- 유저 그래프: User, Evidence + 엣지 weight/ts
- 유사도: User-SIMILAR, AlgoSkill-RELATED

2) ES
- 인덱스: coding_problem
- 문서: problem_id, problem, category, algorithm, difficulty, embedding
- 임베딩 모델: text-embedding-3-large (OPENAI_EMBEDDING_MODEL로 변경 가능)

3) Backend 동기화
- graph_sync/neo4j_sync.py: 스키마/문제 그래프/리포트 갱신
- graph_sync/user_similarity.py: 유저 유사도 계산
- graph_sync/recommendations.py: 후보 추출 + ES 재랭킹
- graph_sync/graph_queue.py: 비동기 큐 워커
- graph_sync/es_sync.py: ES 인덱스/문서/임베딩 생성


2. 그래프 구조 (현재 구현)

노드
- User
- Evidence
- AlgoSkill
- Problem
- Difficulty

관계
- (User)-[:SHOWED_GAP {weight, ts}]->(AlgoSkill)
- (User)-[:HAS_EVIDENCE {weight, ts}]->(Evidence)
- (Evidence)-[:SUPPORTS {weight}]->(AlgoSkill)
- (Problem)-[:USES_ALGO]->(AlgoSkill)
- (Problem)-[:HAS_DIFFICULTY]->(Difficulty)
- (User)-[:SIMILAR {score, overlap, activity_weight, ts}]->(User)
- (AlgoSkill)-[:RELATED {score, reason}]->(AlgoSkill)

주의
- Role 노드/관계는 제거됨 (category는 Problem 속성으로 사용).


3. 리포트 → Neo4j 반영 규칙

입력 source
- livecoding_reports.graph_output
  - problem_algorithms, strategy_algorithms
  - problem_solving_evaluation.consistency_status

생성 규칙
1) Gap 스킬 결정
- problem_algorithms 있으면 그것을 gap으로 사용
- 없으면 strategy_algorithms 사용

2) Evidence
- strategy_mismatch: gap_algos 중 strategy_algorithms에 없는 것
- implementation_mismatch: consistency_status가 "불일치" 또는 "개선하여 구현"

3) 엣지 속성
- SHOWED_GAP.weight = 1.0, ts=created_at
- HAS_EVIDENCE.weight = 1.0 또는 consistency_weight, ts=created_at
- SUPPORTS.weight = 1.0 또는 consistency_weight

적용 위치
- backend/graph_sync/neo4j_sync.py: sync_report()


4. Algo 유사도 (RELATED)

초기 수동 테이블 (예시)
- BFS ↔ DFS (0.7)
- DFS ↔ Backtracking (0.6)
- DP ↔ Knapsack (0.7)
- Greedy ↔ Priority Queue (0.55)
- Dijkstra ↔ Priority Queue (0.8)
- Graph ↔ Tree (0.5)
- Two Pointers ↔ Sliding Window (0.6)
- Binary Search ↔ Parametric Search (0.7)

생성 위치
- backend/graph_sync/neo4j_sync.py: ensure_algo_similarity()


5. User 유사도 (SIMILAR)

입력
- livecoding_reports.graph_output의 알고리즘 리스트
- created_at, final_score

프로파일
- 알고리즘별 가중치 합산 + 최근성 가중치 적용
- recent_weight = exp(-days/30)

활동량/성장성
- activity_score = log(1 + report_count) * recent_weight
- growth_score = (최신점수 - 최초점수) / (count - 1)
- activity_level
  - count >= 5 && growth_score > 0 → heavy_growth
  - count >= 5 && growth_score <= 0 → heavy_rand
  - else → light

추천 경로 반영(heavy/light 분기)
- heavy_growth: SIMILAR 경로 가중치 1.3x
- heavy_rand: SIMILAR 경로 가중치 0.6x
- light: SIMILAR 경로 제외(0x)

유사도 점수
- cosine(profile_u, profile_v) * (1 + sqrt(activity_u * activity_v))

생성 위치
- backend/graph_sync/user_similarity.py
- 리포트 저장 후 큐에서 자동 갱신


6. 추천 경로 (Hop)

현재 후보 합산 경로
1) Evidence 경로 (3-hop)
  User → Evidence → AlgoSkill → Problem

2) Gap 경로 (2-hop)
  User → AlgoSkill → Problem

3) User-Sim 경로 (4-hop)
  User → SIMILAR(User) → SHOWED_GAP → AlgoSkill → Problem

4) Algo-Sim 경로 (4-hop)
  User → AlgoSkill → RELATED → AlgoSkill → Problem

Neo4j 후보 쿼리
- backend/graph_sync/recommendations.py
- 각 경로에서 weight를 모아 Problem score 합산 후 상위 N개 추출


7. ES 하이브리드 재랭킹

입력
- Neo4j 후보 problem_id 리스트
- graph_output.recommendation_query (LLM 요약)

쿼리
- keyword match(problem)
- knn(embedding, cosine)
- terms filter: problem_id, difficulty
- RRF 결합(가능 시)

구현
- backend/graph_sync/recommendations.py::_es_hybrid_rerank


8. 실행 흐름

1) 백엔드 실행 (자동 큐 워커 시작)
```
python backend/manage.py runserver
```

2) 리포트 생성 시 자동 동기화
- views.py에서 report 저장 후 큐에 작업 등록
- graph_sync/graph_queue.py가 Neo4j/ES 동기화 및 추천 생성

3) 초기 데이터 전체 동기화 (1회)
```
python backend/graph_sync/sync_from_postgres.py
```

4) 리포트 CSV 적재(light_user/heavy_user 만든 거 용도)
```
python backend/graph_sync/import_seed_data.py
```


9. 환경 변수
- NEO4J_AUTH=neo4j/<password>
- ELASTIC_PASSWORD=<password>
- OPENAI_API_KEY=<key>
- OPENAI_EMBEDDING_MODEL (옵션, 기본: text-embedding-3-large)


10. 운영/개발 시 체크리스트

추천이 안 나오는 경우
- Neo4j 동기화 여부 확인
- graph_output.recommendation_query 생성 여부 확인
- ES 인덱스/임베딩 생성 여부 확인

User-Role 잔존 엣지 제거
```
MATCH (:User)-[r:WANTS_ROLE]->(:Role) DELETE r;
```

추천 개수 변경
- backend/graph_sync/graph_queue.py의 limit 조정


11. 추가로 발전해야 할 부분

1) Algo 유사도 자동화
- co-occurrence 기반으로 RELATED 갱신 (배치 작업)

2) User 유사도 고도화
- 최근 N회 기반 프로파일
- 성장형 점수에 알고리즘 다양성 포함

3) 설명 생성
- LLM이 “어떤 경로로 추천됐는지” 요약하도록 추가

4) ES 재랭킹 실패시 fallback 강화
- Neo4j 점수 + 문자열 매칭 혼합 점수
