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
