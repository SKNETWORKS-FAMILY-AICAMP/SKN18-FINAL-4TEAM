-- Coding test schema

CREATE TABLE IF NOT EXISTS coding_problem (
    problem_id   SERIAL PRIMARY KEY,
    problem      TEXT         NOT NULL,
    difficulty   VARCHAR(50)  NOT NULL,
    category     VARCHAR(500) NOT NULL,
    algorithm    JSONB
);

CREATE TABLE IF NOT EXISTS coding_problem_language (
    id           SERIAL       PRIMARY KEY,
    problem_id   INT          NOT NULL,
    function_name VARCHAR(500) NOT NULL,
    starter_code  TEXT         NOT NULL,
    language      VARCHAR(50)  NOT NULL,
    CONSTRAINT fk_coding_problem_language_problem
        FOREIGN KEY (problem_id)
        REFERENCES coding_problem (problem_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS test_case (
    id          SERIAL       PRIMARY KEY,
    problem_id  INT          NOT NULL,
    input       TEXT  NOT NULL,
    output      TEXT,
    CONSTRAINT fk_test_case_problem
        FOREIGN KEY (problem_id)
        REFERENCES coding_problem (problem_id)
        ON DELETE CASCADE
);

CREATE TABLE users (
  user_id       VARCHAR(50) PRIMARY KEY,
  email         VARCHAR(255) NOT NULL UNIQUE,
  name          VARCHAR(50) NOT NULL,
  phone_number  VARCHAR(30) UNIQUE,
  password_hash VARCHAR(255),              -- 로컬만 값, 소셜-only는 NULL
  birthdate     DATE,
  created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE auth_identities (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(50) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  provider VARCHAR(20) NOT NULL,              -- 'local' | 'google'
  provider_user_id VARCHAR(255) NOT NULL,     -- 구글 sub 또는 로컬 user_id/email 등
  refresh_token TEXT,                         -- 필요하면 암호화/별도 저장
  token_expires_at TIMESTAMP,
  scope TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (provider, provider_user_id),
  UNIQUE (user_id, provider)
);

-- Livecoding final reports
CREATE TABLE IF NOT EXISTS livecoding_reports (
    id                SERIAL PRIMARY KEY,
    session_id        VARCHAR(100) NOT NULL UNIQUE,
    user_id           VARCHAR(50)  NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    report_md         TEXT NOT NULL,
    final_score       NUMERIC(6,2),
    final_grade       VARCHAR(8),
    graph_output      JSONB        DEFAULT '{}'::jsonb,
    problem_text            TEXT,
    code_feedback           TEXT,
    problem_solving_evaluation JSONB,
    initial_strategy        TEXT,
    approach_validity       TEXT,
    consistency_status      TEXT,
    consistency_feedback    TEXT,
    submitted_code          TEXT,
    annotated_code          TEXT,
    strength                TEXT,
    improvement             TEXT,
    comprehensive_evaluation TEXT,
    anti_cheat_summary      JSONB,
    problem_eval_score NUMERIC(6,4),
    problem_eval_feedback TEXT,
    code_collab_score NUMERIC(6,4),
    code_collab_feedback TEXT,
    problem_evidence  JSONB,
    code_collab_evidence JSONB,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_livecoding_reports_user_id ON livecoding_reports(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_livecoding_reports_session_id ON livecoding_reports(session_id);


-- CREATE TABLE IF NOT EXISTS livecoding_reports (
--     id                SERIAL PRIMARY KEY, -- auto increment된 ID
--     session_id        VARCHAR(100) NOT NULL UNIQUE, -- 세션 고유 ID
--     user_id           VARCHAR(50)  NOT NULL REFERENCES users(user_id) ON DELETE CASCADE, -- 사용자 ID
--     report_md         TEXT NOT NULL, -- 마크다운 형식의 리포트 내용(레포트 본문)
--     -- 총점 / 등급
--     final_score       NUMERIC(6,2),
--     final_grade       VARCHAR(8),
  
--     graph_output      JSONB        DEFAULT '{}'::jsonb,
--     -- graph_output 안에 있는 필드 중 일부를 별도 컬럼으로 분리
--     problem_text            TEXT, --문제 원문
--     code_feedback                 TEXT, -- 코드 평가 피드백

--     problem_solving_evaluation    JSONB, -- 문제 해결 능력 평가 피드백
--     -- 사용자 전략 및 코드와 그에 대한 피드백
--     initial_strategy              TEXT, -- 초기 전략 설명
--     approach_validity             TEXT, -- 접근 방식 타당성 판단
--     consistency_status            TEXT, -- 일관성 상태
--     consistency_feedback          TEXT, -- 일관성 피드백
--     submitted_code                TEXT, -- 최종 제출 코드
--     annotated_code                TEXT, -- 주석으로 피드백 제공해준 코드

--     -- 종합 피드백 제공
--     strength                      TEXT, -- 사용자의 강점 피드백
--     improvement                   TEXT, -- 사용자의 개선점 피드백
--     comprehensive_evaluation      TEXT, -- 종합 평가 피드백
--     anti_cheat_summary            JSONB, -- 부정행위 경고 메시지
    
--     problem_eval_score NUMERIC(6,4),
--     problem_eval_feedback TEXT,
--     code_collab_score NUMERIC(6,4),
--     code_collab_feedback TEXT,
--     problem_evidence  JSONB, -- testcase 통과 및 기본 solution 함수 작성 여부, 
--     code_collab_evidence JSONB, -- 품질과 협업 능력에서 도출된 ruff 증거들
--     created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );
