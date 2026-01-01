// Load livecoding reports into Neo4j (User -> Interview -> AlgoSkill)

LOAD CSV WITH HEADERS FROM 'file:///livecoding_reports_export.csv' AS row
WITH row
WHERE row.session_id IS NOT NULL AND row.user_id IS NOT NULL
MERGE (u:User {user_id: row.user_id})
MERGE (i:Interview {session_id: row.session_id})
SET i.created_at = row.created_at
MERGE (u)-[:TOOK]->(i)
WITH i, row
WHERE row.problem_id IS NOT NULL AND trim(row.problem_id) <> ''
WITH i, row,
     CASE
       WHEN row.problem_algorithms IS NOT NULL AND trim(row.problem_algorithms) <> '' THEN apoc.convert.fromJsonList(row.problem_algorithms)
       ELSE []
     END AS problem_algos,
     CASE
       WHEN row.strategy_algorithms IS NOT NULL AND trim(row.strategy_algorithms) <> '' THEN apoc.convert.fromJsonList(row.strategy_algorithms)
       ELSE []
     END AS strategy_algos,
     row.consistency_status AS consistency_status
WITH i, row, problem_algos, strategy_algos, pass_rate, consistency_status,
     CASE
       WHEN size(problem_algos) > 0 THEN problem_algos
       ELSE strategy_algos
     END AS skill_algos
UNWIND skill_algos AS algo
MERGE (s:AlgoSkill {name: algo})
MERGE (i)-[:SHOWED_GAP {weight: coalesce(toFloat(row.gap_weight), 1.0)}]->(s)
WITH i, row, skill_algos, strategy_algos, pass_rate, consistency_status
WITH i, row, skill_algos, strategy_algos, pass_rate, consistency_status,
     [a IN skill_algos WHERE NOT a IN strategy_algos] AS missing_algos
FOREACH (a IN CASE WHEN size(strategy_algos) > 0 THEN missing_algos ELSE [] END |
  MERGE (s:AlgoSkill {name: a})
  MERGE (e:Evidence {evidence_id: row.session_id + ':strategy_mismatch:' + a})
  SET e.type = 'strategy_mismatch', e.detail = a, e.weight = 1.0
  MERGE (i)-[:HAS_EVIDENCE]->(e)
  MERGE (e)-[:SUPPORTS {weight: 1.0}]->(s)
)
WITH i, row, skill_algos, consistency_status
WITH i, row, skill_algos,
     CASE
       WHEN consistency_status = '불일치' THEN 1.0
       WHEN consistency_status = '개선하여 구현' THEN 0.6
       ELSE 0.0
     END AS consistency_weight
FOREACH (_ IN CASE WHEN consistency_weight > 0 THEN [1] ELSE [] END |
  MERGE (e:Evidence {evidence_id: row.session_id + ':consistency'})
  SET e.type = 'implementation_mismatch', e.weight = consistency_weight
  MERGE (i)-[:HAS_EVIDENCE]->(e)
  FOREACH (a IN skill_algos |
    MERGE (s:AlgoSkill {name: a})
    MERGE (e)-[:SUPPORTS {weight: consistency_weight}]->(s)
  )
);
