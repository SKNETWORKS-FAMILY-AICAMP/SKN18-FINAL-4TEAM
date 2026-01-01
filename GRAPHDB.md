1. .env에
```
NEO4J_AUTH=neo4j/gyulcross0113
ELASTIC_PASSWORD=gyulcross0113
KIBANA_PASSWORD=gyulcross0113
```
값 먼저 추가한다.


2. 
```
 docker-compose -f docker/docker-compose.yml --env-file .env up -d   
```
 로 먼저 docker 실행 up 해줌

```
 docker compose -f docker/docker-compose.yml --env-file .env up -d setup
```

이거로 setup 별도 실행 후 
```
docker compose -f docker/docker-compose.yml --env-file .env exec neo4j cypher-shell -u neo4j -p gyulcross0113 -f /var/lib/neo4j/import/schema.cypher
```
로 Neo4j Schema적용함

그럼 실제로 localhost:7474에서 .env에 적힌 계정 값으로 입력 후 로그인 하면 
![alt text](docs/neo4j/neo4j-1.png)
사진과 같이 확인 가능


3. 인덱스 생성(*혹시몰라서 해야함)
```
curl.exe -u elastic:gyulcross0113 -X PUT "http://localhost:9200/coding_problem" -H "Content-Type: application/json" --data-binary "@docker/elasticsearch/coding_problem_mapping.json"
```

4. csv를 Neo4j import에 복사
```
powershell -ExecutionPolicy Bypass -File docker/scripts/sync_neo4j_import.ps1
```

5. Neo4j 문제 로드
```
docker compose -f docker/docker-compose.yml --env-file .env exec neo4j cypher-shell -u neo4j -p gyulcross0113 -f /var/lib/neo4j/import/load_coding_problems.cypher
```

6. ES 인덱싱 진행
```
python docker/scripts/index_coding_problems_es.py --es-password gyulcross0113
```

> Done이 뜨면 된거

7. 임베딩 확인
```
$body = @{ query = @{ match_all = @{} }; _source = @("embedding") } | ConvertTo-Json -Compress
Invoke-RestMethod -Method Post -Uri "http://localhost:9200/coding_problem/_search?size=1" -Headers @{Authorization=("Basic " + [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("elastic:gyulcross0113")))} -ContentType "application/json" -Body $body
```

7-1. 임베딩 필드 값 확인

```
$body = @{ query = @{ match_all = @{} }; _source = @("embedding") } | ConvertTo-Json -Compress
$res = Invoke-RestMethod -Method Post -Uri "http://localhost:9200/coding_problem/_search?size=1" -Headers @{Authorization=("Basic " + [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("elastic:gyulcross0113")))} -ContentType "application/json" -Body $body
$res.hits.hits[0]._source.embedding
```

8. 리포트 생성 후에
```
powershell -ExecutionPolicy Bypass -File docker/scripts/export_livecoding_reports_to_neo4j.ps1
```
로 리포트 데이터 csv export함

8-1. 
```
docker compose -f docker/docker-compose.yml --env-file .env exec neo4j cypher-shell -u neo4j -p gyulcross0113 -f /var/lib/neo4j/import/load_livecoding_reports.cypher
```
로  Neo4j에 로드함

8-2. 
```
MATCH (u:User)-[:TOOK]->(i:Interview)-[:SHOWED_GAP]->(s:AlgoSkill)
RETURN u, i, s LIMIT 25
```
위 명령어를 localhost:7474에 접속해서 브라우저에서 실행하면 연결 뜸 그거 보고 된지 확인 필요


9.
``` 
python docker/scripts/recommend_from_neo4j_es.py --user-id asd5456677 --query "dp 최적화 전략" --auto-grade --top-k 10
```
로 이제 추천 문제들 뽑을 수 있음
근데 이건 일단 테스트를 위해 직접 csv들을 export하는 방식임


10. 현재 그래프 구조/경로 개념

- 노드: User, Interview, Problem, AlgoSkill, Difficulty, Role, Evidence
- 핵심 경로(기본):
  User → Interview → AlgoSkill → Problem
- Evidence 기반 경로:
  User → Interview → Evidence → AlgoSkill → Problem

Hop / Distance
- hop = 관계 1번 이동
- 예시 3-hop 경로: User → Interview → AlgoSkill → Problem
- distance = 최단 hop 수

왜 이렇게 구성했는지
- 리포트의 “무엇이 부족했는지”를 Evidence로 명시하면 추천 근거를 경로로 설명 가능
- 테스트 실패/전략 불일치/전략-문제 불일치 같은 신호를 Evidence로 분리해 점수화
- GraphDB는 경로 기반 추천과 근거 추적이 강점, ES는 문장/의미 기반 재랭킹에 강점

Evidence 생성 규칙(현재)
- strategy_mismatch: 전략에서 언급하지 않은 요구 알고리즘
- implementation_mismatch: consistency_status가 불일치/개선하여 구현

Evidence 반영 방식
- Neo4j 로딩 시 Evidence 노드 생성
- Evidence → AlgoSkill로 SUPPORTS(가중치) 생성
- 추천 후보 추출 시 Evidence가 있으면 Evidence 기반 스코어를 우선 사용

추가로 해야될 일(다음 단계)
- Evidence 가중치/스코어 조정 (리포트 신뢰도에 따라 가중치 튜닝)
- 사용자 희망 직무(Role) 가중치 강화
- 2~3 hop 확장 경로(선수지식 REQUIRES) 추가
- 실시간 동기화 방식 결정(Outbox or 동시 쓰기)








내일 아마 수정할 예정
방식은 총 2가지

1) 애플리케이션에서 동시에 쓰기

livecoding_reports 저장될 때 Postgres + Neo4j 같이 저장
실패 대비로 재시도 큐 사용
장점: 실시간, 단순

2) Outbox 패턴 + 워커 (실무 표준)

Postgres에 outbox 테이블 기록
워커가 읽어서 Neo4j에 반영
장점: 안정성 높음, 장애 복구 쉬움
