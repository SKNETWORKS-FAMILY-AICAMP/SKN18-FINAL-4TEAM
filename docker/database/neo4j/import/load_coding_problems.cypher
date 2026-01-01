// Load coding problems + algorithm tags into Neo4j
// Assumes CSVs are present in Neo4j import dir

LOAD CSV WITH HEADERS FROM 'file:///coding_problems.csv' AS row
WITH row
WHERE row.problem_id IS NOT NULL
MERGE (p:Problem {problem_id: toInteger(row.problem_id)})
SET p.problem = row.problem,
    p.difficulty = row.difficulty,
    p.category = row.category
MERGE (r:Role {name: row.category})
MERGE (p)-[:IN_ROLE]->(r)
MERGE (d:Difficulty {level: row.difficulty})
MERGE (p)-[:HAS_DIFFICULTY]->(d)
WITH p, row,
     CASE
       WHEN row.algorithm IS NULL OR trim(row.algorithm) = '' THEN []
       ELSE apoc.convert.fromJsonList(row.algorithm)
     END AS algos
UNWIND algos AS algo
MERGE (a:AlgoSkill {name: algo})
MERGE (p)-[:USES_ALGO]->(a);
