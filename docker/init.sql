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


--CHECK 제약조건 걸어놓은 컬럼들은 프론트에서 선택하게끔(드롭다운)으로 구현해야 할 듯
CREATE TABLE user_profile(
  user_id         VARCHAR(50) PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
  --최종 학력
  graduated_school VARCHAR(100) CHECK (graduated_school IN ('고졸','전문대졸(2,3년제)','대졸(4년제 이상)','석사 이상','박사 이상')),
  university      VARCHAR(200),     -- 학교명 공공데이터베이스 활용 가능, 프론트에서 학교명 검색해서 선택하게끔
  major           VARCHAR(20) CHECK (major IN ('전공','비전공')),
  academic_status VARCHAR(20) CHECK (academic_status IN ('재학','휴학','졸업','중퇴')),
  graduation_year INT,              -- 졸업(예정) 연도
  career_level    VARCHAR(50) CHECK(career_level IN ('junior (0~3년차)', 'mid (4~7년차)', 'senior (8~10년차)', 'lead (10년차~)')),  -- 경력 사항
  current_status  VARCHAR(50) CHECK (current_status IN ('재직중','퇴사','구직중','프리랜서','기타')),
  tech_stack      TEXT[] CHECK (tech_stack IS NULL OR tech_stack <@ ARRAY['Python','NumPy','Pandas','SciPy','Scikit-learn','XGBoost','LightGBM','CatBoost','TensorFlow','Keras','PyTorch','Transformers','LangChain','LangGraph','OpenAI API','HuggingFace Hub','SentenceTransformers','spaCy','NLTK','MLflow','Airflow','DVC','Optuna','Jupyter Notebook','JupyterLab']::text[]),
  desired_role    TEXT[] CHECK (desired_role IS NULL OR desired_role <@ ARRAY['AI/ML 엔지니어','데이터 사이언티스트','LLM 엔지니어','컴퓨터비전 엔지니어','자연어처리 엔지니어','음성인식 엔지니어','MLOps 엔지니어','데이터 엔지니어','AI 서비스 개발자']::text[]), -- 희망 직무 (상위)
  detailed_role   TEXT[] CHECK (detailed_role IS NULL OR detailed_role <@ ARRAY['딥러닝 모델링','지도/비지도 학습','강화학습','추천 시스템','시계열 예측','자연어 처리', '텍스트 분류/분석', '텍스트 생성/요약', '프롬프트 엔지니어링', 'LLM 파인튜닝/서빙', '컴퓨터 비전', '이미지 분류/탐지', 'OCR/문서 인식', '음성 인식/TTS', 'MLOps/파이프라인', '모델 서빙/배포', '데이터 파이프라인', 'AI 보안/안전']::text[]), -- 세부 희망 직무
  region          TEXT[] CHECK(region IS NULL OR region <@ ARRAY['서울', '인천', '부산', '대구', '대전', '세종', '울산', '광주']),     -- 희망 근무지
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

-- Profile option master table
CREATE TABLE IF NOT EXISTS profile_option (
  id SERIAL PRIMARY KEY,
  category VARCHAR(50) NOT NULL, -- e.g., graduated_school, major, career_level...
  value VARCHAR(200) NOT NULL,
  display_order INT DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_profile_option_category ON profile_option(category);

-- Seed profile options (idempotent)
INSERT INTO profile_option (category, value, display_order)
SELECT cat, val, ord FROM (
  VALUES
    -- graduated_school
    ('graduated_school','고졸',1),
    ('graduated_school','전문대졸(2,3년제)',2),
    ('graduated_school','대졸(4년제 이상)',3),
    ('graduated_school','석사 이상',4),
    ('graduated_school','박사 이상',5),
    -- major
    ('major','전공',1),
    ('major','비전공',2),
    -- academic_status
    ('academic_status','재학',1),
    ('academic_status','휴학',2),
    ('academic_status','졸업',3),
    ('academic_status','중퇴',4),
    -- career_level
    ('career_level','junior (0~3년차)',1),
    ('career_level','mid (4~7년차)',2),
    ('career_level','senior (8~10년차)',3),
    ('career_level','lead (10년차~)',4),
    -- current_status
    ('current_status','재직중',1),
    ('current_status','퇴사',2),
    ('current_status','구직중',3),
    ('current_status','프리랜서',4),
    ('current_status','기타',5),
    -- tech_stack
    ('tech_stack','Python',1),
    ('tech_stack','NumPy',2),
    ('tech_stack','Pandas',3),
    ('tech_stack','SciPy',4),
    ('tech_stack','Scikit-learn',5),
    ('tech_stack','XGBoost',6),
    ('tech_stack','LightGBM',7),
    ('tech_stack','CatBoost',8),
    ('tech_stack','TensorFlow',9),
    ('tech_stack','Keras',10),
    ('tech_stack','PyTorch',11),
    ('tech_stack','Transformers',12),
    ('tech_stack','LangChain',13),
    ('tech_stack','LangGraph',14),
    ('tech_stack','OpenAI API',15),
    ('tech_stack','HuggingFace Hub',16),
    ('tech_stack','SentenceTransformers',17),
    ('tech_stack','spaCy',18),
    ('tech_stack','NLTK',19),
    ('tech_stack','MLflow',20),
    ('tech_stack','Airflow',21),
    ('tech_stack','DVC',22),
    ('tech_stack','Optuna',23),
    ('tech_stack','Jupyter Notebook',24),
    ('tech_stack','JupyterLab',25),
    -- desired_role
    ('desired_role','AI/ML 엔지니어',1),
    ('desired_role','데이터 사이언티스트',2),
    ('desired_role','LLM 엔지니어',3),
    ('desired_role','컴퓨터비전 엔지니어',4),
    ('desired_role','자연어처리 엔지니어',5),
    ('desired_role','음성인식 엔지니어',6),
    ('desired_role','MLOps 엔지니어',7),
    ('desired_role','데이터 엔지니어',8),
    ('desired_role','AI 서비스 개발자',9),
    -- detailed_role
    ('detailed_role','딥러닝 모델링',1),
    ('detailed_role','지도/비지도 학습',2),
    ('detailed_role','강화학습',3),
    ('detailed_role','추천 시스템',4),
    ('detailed_role','시계열 예측',5),
    ('detailed_role','자연어 처리',6),
    ('detailed_role','텍스트 분류/분석',7),
    ('detailed_role','텍스트 생성/요약',8),
    ('detailed_role','프롬프트 엔지니어링',9),
    ('detailed_role','LLM 파인튜닝/서빙',10),
    ('detailed_role','컴퓨터 비전',11),
    ('detailed_role','이미지 분류/탐지',12),
    ('detailed_role','OCR/문서 인식',13),
    ('detailed_role','음성 인식/TTS',14),
    ('detailed_role','MLOps/파이프라인',15),
    ('detailed_role','모델 서빙/배포',16),
    ('detailed_role','데이터 파이프라인',17),
    ('detailed_role','AI 보안/안전',18),
    -- region
    ('region','서울',1),
    ('region','인천',2),
    ('region','부산',3),
    ('region','대구',4),
    ('region','대전',5),
    ('region','세종',6),
    ('region','울산',7),
    ('region','광주',8)
) AS seed(cat,val,ord)
WHERE NOT EXISTS (
  SELECT 1 FROM profile_option po WHERE po.category = seed.cat AND po.value = seed.val
);
