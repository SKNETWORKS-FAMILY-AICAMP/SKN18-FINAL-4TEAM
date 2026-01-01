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

// Sample: pull candidate problem_ids for ES rerank
// Params: {"user_id":"...", "limit":200}
MATCH (u:User {user_id:$user_id})-[:TOOK]->(i:Interview)
WITH i ORDER BY i.created_at DESC LIMIT 1
MATCH (i)-[:SHOWED_GAP]->(s:AlgoSkill)
MATCH (s)<-[:USES_ALGO]-(p:Problem)
RETURN DISTINCT p.problem_id AS problem_id
LIMIT $limit;
