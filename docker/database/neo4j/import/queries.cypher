// Sample: latest interview gap -> problem recommendations (graph score only)
// Params: {"user_id":"...", "limit":10, "allowed_difficulties":["normal","hard"]}
MATCH (u:User {user_id:$user_id})-[:TOOK]->(i:Interview)
WITH u, i
ORDER BY i.created_at DESC
LIMIT 1
MATCH (i)-[g:SHOWED_GAP]->(s:AlgoSkill)
MATCH (s)<-[:USES_ALGO]-(p:Problem)-[:IN_ROLE]->(r:Role)
OPTIONAL MATCH (u)-[:WANTS_ROLE]->(r)
OPTIONAL MATCH (p)-[:HAS_DIFFICULTY]->(d:Difficulty)
WITH p, r, d, u, s, g
WITH p,
     collect(distinct s.name) AS gap_skills,
     sum(coalesce(g.weight, 1.0)) AS gap_score,
     max(CASE WHEN (u)-[:WANTS_ROLE]->(r) THEN 1.2 ELSE 1.0 END) AS role_boost,
     max(CASE WHEN d.level IN $allowed_difficulties THEN 1.1 ELSE 1.0 END) AS diff_boost
RETURN p.problem_id AS problem_id,
       p.problem AS problem,
       gap_skills,
       gap_score * role_boost * diff_boost AS score
ORDER BY score DESC
LIMIT $limit;

// Sample: evidence-aware recommendations (uses Evidence if present)
// Params: {"user_id":"...", "limit":10, "allowed_difficulties":["normal","hard"]}
MATCH (u:User {user_id:$user_id})-[:TOOK]->(i:Interview)
WITH i ORDER BY i.created_at DESC LIMIT 1
OPTIONAL MATCH (i)-[:HAS_EVIDENCE]->(e:Evidence)-[sup:SUPPORTS]->(s:AlgoSkill)
WITH i, collect({skill: s, weight: coalesce(sup.weight, e.weight, 1.0)}) AS ev
CALL {
  WITH i, ev
  WITH i, ev
  WHERE size(ev) > 0
  UNWIND ev AS item
  RETURN item.skill AS skill, item.weight AS weight
  UNION
  WITH i, ev
  WHERE size(ev) = 0
  MATCH (i)-[g:SHOWED_GAP]->(s2:AlgoSkill)
  RETURN s2 AS skill, coalesce(g.weight, 1.0) AS weight
}
MATCH (skill)<-[:USES_ALGO]-(p:Problem)
OPTIONAL MATCH (p)-[:HAS_DIFFICULTY]->(d:Difficulty)
WITH p, d, sum(weight) AS score
WHERE d.level IN $allowed_difficulties
RETURN p.problem_id AS problem_id,
       p.problem AS problem,
       score AS score
ORDER BY score DESC
LIMIT $limit;

// Sample: pull candidate problem_ids for ES rerank
// Params: {"user_id":"...", "limit":200}
MATCH (u:User {user_id:$user_id})-[:TOOK]->(i:Interview)
WITH i ORDER BY i.created_at DESC LIMIT 1
OPTIONAL MATCH (i)-[:HAS_EVIDENCE]->(e:Evidence)-[sup:SUPPORTS]->(s:AlgoSkill)
WITH i, collect({skill: s, weight: coalesce(sup.weight, e.weight, 1.0)}) AS ev
CALL {
  WITH i, ev
  WITH i, ev
  WHERE size(ev) > 0
  UNWIND ev AS item
  RETURN item.skill AS skill, item.weight AS weight
  UNION
  WITH i, ev
  WHERE size(ev) = 0
  MATCH (i)-[g:SHOWED_GAP]->(s2:AlgoSkill)
  RETURN s2 AS skill, coalesce(g.weight, 1.0) AS weight
}
MATCH (skill)<-[:USES_ALGO]-(p:Problem)
WITH p, sum(weight) AS score
RETURN p.problem_id AS problem_id
ORDER BY score DESC
LIMIT $limit;
