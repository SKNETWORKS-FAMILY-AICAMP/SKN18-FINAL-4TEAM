-- Coding test schema

CREATE TABLE IF NOT EXISTS coding_problem (
    problem_id   SERIAL PRIMARY KEY,
    problem      TEXT         NOT NULL,
    difficulty   VARCHAR(50)  NOT NULL,
    category     VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS coding_problem_language (
    id           SERIAL       PRIMARY KEY,
    problem_id   INT          NOT NULL,
    function_name VARCHAR(100) NOT NULL,
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
  user_id       SERIAL PRIMARY KEY,
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
  user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  provider VARCHAR(20) NOT NULL,              -- 'local' | 'google'
  provider_user_id VARCHAR(255) NOT NULL,     -- 구글 sub 또는 로컬 user_id/email 등
  refresh_token TEXT,                         -- 필요하면 암호화/별도 저장
  token_expires_at TIMESTAMP,
  scope TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (provider, provider_user_id),
  UNIQUE (user_id, provider)
);
