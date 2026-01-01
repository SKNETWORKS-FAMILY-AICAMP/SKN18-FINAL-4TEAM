// Neo4j schema + seed data

// Constraints
CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE;
CREATE CONSTRAINT interview_id_unique IF NOT EXISTS FOR (i:Interview) REQUIRE i.session_id IS UNIQUE;
CREATE CONSTRAINT problem_id_unique IF NOT EXISTS FOR (p:Problem) REQUIRE p.problem_id IS UNIQUE;
CREATE CONSTRAINT role_name_unique IF NOT EXISTS FOR (r:Role) REQUIRE r.name IS UNIQUE;
CREATE CONSTRAINT algoskill_name_unique IF NOT EXISTS FOR (s:AlgoSkill) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT difficulty_level_unique IF NOT EXISTS FOR (d:Difficulty) REQUIRE d.level IS UNIQUE;

// Indexes (optional for faster lookups)
CREATE INDEX user_id_idx IF NOT EXISTS FOR (u:User) ON (u.user_id);
CREATE INDEX problem_id_idx IF NOT EXISTS FOR (p:Problem) ON (p.problem_id);
CREATE INDEX interview_created_idx IF NOT EXISTS FOR (i:Interview) ON (i.created_at);

// Seed roles (category)
MERGE (:Role {name: 'Python Developer'});
MERGE (:Role {name: 'Data Analyst'});
MERGE (:Role {name: 'Data Scientist'});
MERGE (:Role {name: 'AI Engineer'});

// Seed difficulties
MERGE (:Difficulty {level: 'normal'});
MERGE (:Difficulty {level: 'hard'});
