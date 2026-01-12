# 💻 JobTory – AI Live Coding Interview 플랫폼

AI 면접관과 함께 라이브 코딩 테스트를 진행하는 웹 서비스입니다.  
지원자는 브라우저에서 **환경 세팅 → 라이브 코딩 → 자동 평가**까지 한 번에 경험하고,  
백엔드는 STT/TTS·LangGraph·Ruff·Redis를 이용해 **코드 품질과 협업 능력**을 평가합니다.

---

## 👥 팀 소개

|      | 김규리 | 김준규 | 김민주 | 손주영 | 정동석 | 채린 |
| --- | --- | --- | --- | --- | --- | --- |
| 프로필 | <img src="images/judy.jpg" width="100"> | <img src="images/Nick.jpg" width="100"> | <img src="images/Clawhauser.png" width="100"> | <img src="images/Brian.jpg" width="100"> | <img src="images/gazelle.jpg" width="100"> | <img src="images/Flash.jpg" width="100"> |
| 역할 | PM | APM | 팀원 | 팀원 | 팀원 | 팀원 |
| GitHub | [@GyuriKimm](https://github.com/GyuriKimm) | [@JungyuOO](https://github.com/JungyuOO) | [@kmjj0801](https://github.com/kmjj0801) | [@sonjuyeong-00](https://github.com/sonjuyeong-00) | [@dsj-1004](https://github.com/dsj-1004) | [@cofls99](https://github.com/cofls99) |

---

## 🤖 서비스 목표

> **“현실에 가까운 라이브 코딩 인터뷰 경험”**  
> 단순 정답/오답을 넘어, **코드 품질·협업 능력·설명력**까지 자동으로 평가하는 AI 면접관을 만드는 것이 목표입니다.

- STT/TTS 기반 음성 인터랙션으로 실제 면접처럼 **말로 질문·답변**할 수 있는 환경 제공
- LangGraph 기반 단계(인트로 → 코딩 → 종합평가)별 에이전트 오케스트레이션
- Ruff 정적 분석 결과 + 코드 변화량을 활용한 **코드 품질·협업 평가**
- Redis에 저장된 코드 히스토리/발화 로그를 통해 **이어하기·사후 평가 리포트** 제공
- 테스트 결과를 기반한 **성장 리포트** 제공
- 실력 향상을 위한 **문제 추천**, **7일 학습 플랜** 제공
---

## 🧠 배경 및 문제 인식

### 기존 코딩 테스트/면접의 한계

- 대부분의 서비스는 **정답/실행 시간** 중심 평가에 머무름
- 코드 리뷰, 협업 능력, 커뮤니케이션 등은 사람이 직접 인터뷰를 해야만 파악 가능
- 많은 인원을 인터뷰해야 할 때, 면접관 리소스 부족과 평가 기준의 편차가 커짐

### 우리가 해결하고 싶은 것

- **지원자 입장**  
  - 집에서 편하게 접속해 실제 면접처럼 대화하며 코딩 테스트를 치르고 싶다.  
  - 단순 점수만이 아니라 **어디서 실수했고, 코드 스타일/커뮤니케이션이 어떤지** 피드백을 받고 싶다.
- **면접관/HR 입장**  
  - 라이브 코딩 과정을 녹화·분석해, 리뷰해야 할 포인트만 골라보고 싶다.  
  - 지원자별 **코드 변화 히스토리 + AI 평가 리포트**로 빠르게 비교하고 싶다.

JobTory는 이 문제를 해결하기 위해, **라이브 코딩 + AI 면접관 + 코드 리포트**를 하나의 플로우로 엮은 플랫폼입니다.

---

## 📌 제공하는 서비스 

| 구분 | 기능 | 설명 |
| --- | --- | --- |
| 환경 설정 | 카메라/마이크 체크, 네트워크 확인 | 라이브코딩 시작 전 시스템 점검 및 동의 |
| Intro Stage | 문제 설명 TTS, 전략 질문 + STT | 문제 이해 여부 및 풀이 전략 파악, 코딩 단계 진입 조건 결정 |
| Coding Stage | 코드 에디터, 자동 코드 스냅샷, 질문/힌트 | 1.5초 정지 시 코드 히스토리 저장, 2분마다 질문 생성, 힌트 요청 버튼 |
| STT/TTS | 음성 STT + TTS 질문/피드백 | Whisper 기반 STT, OpenAI TTS-1 기반 문제 설명/질문/피드백 음성 출력 |
| 코드 품질/협업 평가 | Ruff 기반 정적 분석 + LangGraph 에이전트 | 코딩 중간·종료 시점에 코드 품질, 협업 친화도 점수 및 피드백 생성 |
| 이어하기 | 중단 세션 복구 | Redis에 저장된 메타·코드·그래프 상태를 활용해 중간부터 재진행 |
| 최종 평가 리포트 | 종합 평가 및 리포트 생성 | 코드 품질, 협업 능력, 문제해결 능력을 종합한 등급(S~F)과 상세 피드백 제공 |
| 성장 리포트 | 누적 면접 결과 분석 | 3회 이상 테스트 응시 시, 이전 결과와 비교해 강점·약점·개선 여부를 시각화하여 성장 추이를 제공 |
| 맞춤 문제 추천 | 약점 기반 문제 큐레이션 | 평가 결과에서 드러난 취약 알고리즘·풀이 패턴을 기준으로 실력 향상에 최적화된 문제 추천 |
| 7일 학습 플랜 | 개인 맞춤 학습 로드맵 생성 | 테스트 결과를 바탕으로 기초 → 응용 단계로 구성된 7일 학습 계획 제공 및 진행 상황 점검 |
| 학습 영상 추천 | 개념 보완용 영상 추천 | 약점 알고리즘 및 문제 해결 과정 보완을 위한 핵심 개념 중심 학습 영상 자동 추천 |

---

## 🔍 서비스 이점 및 차별성

| 항목 | 기존 코딩 테스트 | 기존 화상/면접 서비스 | JobTory |
| --- | --- | --- | --- |
| 평가 범위 | 정답 여부, 실행 시간 | 대면 면접관 중심 | 정답 + 코드 품질 + 협업 능력 + 설명력 |
| 인터랙션 방식 | 코드만 제출 | 화상/음성 위주 | 코드 + 음성(STT/TTS) + 자동 질문/힌트 |
| 코드 분석 | 제출 시 한 번 평가 | 수동 리뷰 | 코딩 과정 전체 스냅샷 + Ruff 분석 |
| 상태 관리 | 브라우저/DB 위주 | 세션 단위 | Redis 기반 세션/그래프/코드/대화 상태 통합 관리 |
| 이어하기 | 일부만 지원 | 거의 없음 | 세션/코드/그래프 상태 모두 복원 가능 |

---

## 🧩 시스템 아키텍처 & 주요 플로우

> 상세 다이어그램은 [시스템 아키텍처 문서](https://docs.google.com/document/d/10WTTrO3g1uwa_P4MdwcbhA52s4dwlMNI/edit?usp=sharing&ouid=116457762953203703245&rtpof=true&sd=true) 에서 확인할 수 있습니다.

## 🔄 Live Coding Interview End-to-End Pipeline

JOBTORY의 라이브 코딩 면접은  
**환경 설정 → 실시간 인터뷰 → 자동 평가 → 성장 분석 → 학습 추천**으로 이어지는
단일 세션 기반 파이프라인으로 구성됩니다.

---

### 1️⃣ Environment Setup (면접 시작 준비)

1. 사용자는 환경 설정 페이지에서 다음 항목을 순차적으로 점검합니다.
   - 카메라 권한 및 얼굴 인식 확인
   - 마이크 입력 감도 테스트
   - 스피커 출력 테스트
   - 네트워크 연결 상태 확인
2. 모든 항목이 통과되면 **[라이브 코딩 시작]** 버튼이 활성화됩니다.

---

### 2️⃣ Session Initialization (세션 생성 및 상태 초기화)

1. 사용자가 시작 버튼을 클릭하면 Django 백엔드가  
   `/api/livecoding/start/` 엔드포인트를 통해 새로운 라이브 코딩 세션을 생성합니다.
2. 이 시점에 다음 데이터가 Redis에 초기화됩니다.

   - `livecoding:{session_id}:meta`  
     → 현재 stage, 타이머, 힌트 사용 횟수, 상태 플래그
   - `livecoding:{session_id}:problem`  
     → 문제 원문, 난이도, 알고리즘 태그
   - `livecoding:{session_id}:code`  
     → 현재 코드 스냅샷 및 히스토리
   - LangGraph Checkpoint  
     → `thread_id = session_id` 기반으로 Intro / Coding / Evaluation 그래프 상태 저장

---

### 3️⃣ Intro Stage (문제 이해 & 전략 인터뷰)

1. 프론트엔드는 라이브 코딩 페이지 진입 후  
   `/api/livecoding/session/`을 주기적으로 호출하여
   - 현재 stage
   - 문제 정보
   - 남은 시간
   을 조회합니다.
2. stage가 `intro`인 경우:
   - 문제 설명 TTS가 자동 재생됩니다.
   - AI 면접관이 **풀이 전략 질문**을 음성(TTS)으로 제시합니다.
3. 사용자의 음성 응답은 다음 흐름으로 처리됩니다.

   - `/api/stt/transcribe/`  
     → Whisper 기반 STT로 텍스트 변환
   - `/api/interview/event/`  
     → LangGraph **Chapter 1 (Intro Graph)** 호출
     - 응답 분류 (전략 / 질문 / 무관 발화)
     - 전략 품질 판단
     - 다음 질문 또는 코딩 단계 진입 여부 결정
4. 노드 결과로 생성된 `tts_text / tts_audio`가 즉시 음성으로 재생됩니다.

---

### 4️⃣ Coding Stage (실시간 코딩 + 인터뷰)

1. Intro가 완료되면 stage가 `coding`으로 전환됩니다.
2. 코딩 단계에서는 다음 이벤트가 병렬로 발생합니다.

   **① 코드 히스토리 수집**
   - 사용자의 코드 입력이 **1.5초 이상 정지**될 경우
   - `/api/livecoding/session/code/`로 코드 스냅샷 저장
   - 이후 코드 변화량 기반 분석에 사용

   **② 실시간 질문 생성**
   - **2분마다** `/api/livecoding/session/question/` 호출
   - 입력 데이터:
     - 현재 코드
     - 이전 코드 대비 변경점(diff)
     - 이전 질문/답변 로그
   - Ruff 기반 정적 분석 + LLM을 결합해
     - 코드 구조
     - 예외 처리
     - 시간 복잡도 관점 질문 생성

   **③ 힌트 요청**
   - 사용자가 힌트 버튼을 클릭하면
   - LangGraph 힌트 노드 실행 → TTS로 힌트 제공
   - 힌트 사용 횟수는 협업/태도 평가에 반영

3. 모든 음성 인터랙션은 STT → LLM → TTS 파이프라인으로 실시간 처리됩니다.

---

### 5️⃣ Session End & Evaluation (종합 평가)

1. 제한 시간이 종료되거나 사용자가 **제출하기**를 누르면  
   `/api/livecoding/session/end/`가 호출됩니다.
2. LangGraph **Chapter 3 (Evaluation Graph)**가 실행되어 다음을 종합 평가합니다.

   - 코드 품질 (Ruff rule-based + LLM 보조)
   - 문제 해결 능력
     - 초기 전략과 최종 코드의 일관성
     - 테스트 케이스 통과율
   - 협업 능력
     - 질문 응답 품질
     - 힌트 의존도
     - 실시간 피드백 반영 여부
3. 평가 결과는 등급(A+~F)과 함께
   - 점수 산출 근거
   - 코드 주석 기반 리뷰
   - 자연어 종합 피드백
   형태로 리포트화됩니다.

---

### 6️⃣ Growth & Learning Pipeline (사후 학습 연계)

1. 사용자가 **3회 이상** 라이브 코딩 테스트에 응시하면,
   - 누적 리포트를 기반으로 **성장 리포트**가 생성됩니다.
   - 강점 / 약점 / 개선된 부분 / 변화 추이를 분석합니다.
2. 라이브 코딩 테스트 리포트를 입력으로 하여:
   - **맞춤 문제 추천**
     - Neo4j 기반 약점 알고리즘 후보 생성
     - Elasticsearch + Vector Search로 하이브리드 재랭크
   - **7일 학습 플랜**
     - 기초 → 응용 단계로 구성된 개인 맞춤 로드맵 생성
   - **학습 영상 추천**
     - 약점 알고리즘 보완을 위한 핵심 개념 영상 제공
3. 모든 학습 결과와 진행 상태는 사용자 이력으로 저장되어
   다음 면접 세션과 성장 분석에 재사용됩니다.

---

## 🧠 LangGraph 설계 
### 라이브 코딩 테스트 → 종합 평가 → 성장 분석 → 문제 추천 → 학습 설계 → 실행 코칭

### Stage 구성

- **Chapter 1 – Intro Stage**
  - 문제 설명 TTS + 전략 확인 질문
  - 사용자의 STT 답변을 분석해 `user_answer_class` (strategy / etc) 판별
  - 전략이 충분히 설명되었다고 판단되면 stage를 `coding` 으로 변경

- **Chapter 2 – Coding Stage**
  - `coding_intro` 노드: 코딩 시작 안내 멘트(TTS)
  - `code_quality_collabo_node`:
    - Ruff 실행(`ruff check`) 결과를 파싱
    - 코드 품질 prefix(F,E,W,B,C,S,UP,A,TID,RUF)와 협업 prefix(N,D,Q,I,ERA)를 분리 평가
  - `question_generate_node`:
    - 현재 코드 vs 이전 코드(prev_code) 비교
    - 라인 diff / 문자 편집 거리 / AST 변화량 기반 변화 스코어 계산
    - 변화량이 충분하고 starter code와 달라졌을 때, Ruff 피드백과 함께 질문 생성
    - 이미 사용한 Ruff 규칙 코드는 메타에 누적 저장하고, **새로운 규칙 위주**로 질문 생성
  - `coding_answer_feedback_node`:
    - 질문에 대한 STT 답변을 듣고, 짧은 리액션 멘트(TTS) 제공
  - `hint_node`:
    - 힌트 버튼 클릭 시 현재 코드/문제 상황을 기반으로 힌트 생성 (TTS 포함)

- **Chapter 3 – 종합 평가(Stage 3)**
  - 제출하기 버튼 클릭 시 `POST /api/livecoding/final-eval/start/` 로 `chapter3` 그래프 실행 시작
  - **병렬 평가 노드**:
    - `code_collabo_eval_node`:
      - Redis에서 코드/메타 정보, 대화 로그 조회
      - Ruff 분석 결과 + 질문/답변 히스토리 기반 **코드 품질(35점)·협업/커뮤니케이션(30점)** 점수 산출
      - 각 영역별 상세 피드백 생성
    - `problem_solving_eval_node`:
      - 최종 제출 코드의 테스트 케이스 실행 결과 분석
      - 코드 변화 히스토리(intro 전략 → 최종 코드) 기반 **문제 해결 능력(35점)** 점수 산출
      - 알고리즘 효율성 및 접근 방식 피드백 생성
  - **종합 리포트 생성**:
    - 3가지 점수 합산 → 100점 만점 환산 → A+~F 등급 부여
    - Markdown 형식의 상세 리포트(강점/약점/개선점) 생성
    - `GET /api/livecoding/final-eval/status/` 로 진행 상태 폴링(`rendering.vue`)
    - `GET /api/livecoding/final-eval/report/` 로 최종 리포트/점수/등급을 조회(`showreport.vue`)

- **Chapter 4 – 성장 리포트 생성 (Growth Report Stage)**

  - 실행 조건
    - 사용자가 라이브 코딩 테스트를 **3회 이상 완료**한 경우 자동 실행
  - **입력 데이터**
    - 과거 N회(`>=3`)의 최종 평가 리포트
    - 회차별 점수(코드 품질 / 문제 해결 / 협업)
    - 알고리즘 태그, Ruff prefix, 전략 요약, 힌트 사용 이력
  - 리포트 수집 및 정제
    - 단발성 결과 제거를 위해 **2회 이상 반복된 패턴만 유효 신호로 채택**
    - 점수 구간별 알고리즘/행동 패턴 집계
  - 성장 분석 노드
    - `strength_analysis_node`  
      - 반복적으로 높은 점수를 기록한 영역 및 알고리즘 추출
    - `weakness_analysis_node`  
      - 지속적으로 낮은 점수를 기록한 영역 식별
    - `delta_analysis_node`  
      - 직전 성장 리포트 대비 **개선·정체·퇴보 변화** 분석
  - 출력
    - 강점(최대 3개)
    - 개선점(최대 3개)
    - 변화 요약(이전 대비 성장 포인트)
    - 요약형 성장 리포트 텍스트(6~8문장)

---

- **Chapter 5 – 맞춤 문제 추천 (Problem Recommendation Stage)**

  - 입력
    - 최신 성장 리포트
    - 취약 알고리즘, 전략 미흡 패턴, 적정 난이도 범위
  - 그래프 기반 후보 생성
    - 약점 알고리즘 → **Neo4j GraphDB**를 활용해 문제 후보 추출
    - 사용자–알고리즘–문제 간 관계 기반 탐색
  - 하이브리드 재랭크
    - Elasticsearch 키워드 검색
    - Vector Embedding 기반 의미 유사도 검색
    - 알고리즘 일치도 + 난이도 적합도 종합 점수화
  - 후보 필터링
    - 이미 풀이한 문제 제거
    - 난이도 급상승 문제 제한
  - 출력
    - 최종 추천 문제 리스트(기본 3문제)
    - 각 문제별 추천 이유 및 예상 학습 포인트

---

- **Chapter 6 – 학습 코치 & 7일 학습 플랜 (Learning Coach Stage)**

  - **6-1. 학습 상태 진단**

  - 성장 리포트 및 사용자 프로필 기반 분석
  - 현재 실력 구간 및 집중 학습 영역 도출
  - 학습 상태 프로파일 생성
    - `focus_topics`
    - `recommended_depth` (개념 / 적용 / 실전)

  ---

  - **6-2. 7일 학습 플랜 설계**

  - 약점 보완과 강점 유지를 동시에 고려한 학습 목표 설정
  - **기초 → 응용 구조**의 7일 로드맵 생성
    - Day 1~3: 개념 학습
    - Day 4~7: 실전 문제 및 면접 대응
  - 각 Day별 학습 주제, 알고리즘 카테고리, 콘텐츠 매핑

  ---

  - **6-3. 학습 콘텐츠 탐색**

  - 사전 구축된 학습 영상/자료 DB 조회
  - 알고리즘, 난이도, 길이 기준 필터링
  - 중복 제거 후 **1일 1콘텐츠 매칭**

  ---

  - **6-4. 학습 피드백 생성 (실행 코치)**

  - 사용자가 학습 후 회고 텍스트를 작성
  - Deep Agent 기반 검증 수행
    - 영상 핵심 내용 포함 여부
    - 논리 / 사실 / 표현 오류(lint) 탐지
  - 출력
    - 이해도 판정 (미흡 / 보완 필요 / 완료)
    - 문장 단위 인라인 피드백
    - 다음 학습을 위한 구체적 개선 코멘트

---

### LangGraph & Redis 연동

- 체크포인트: `langgraph.checkpoint.redis.RedisSaver`
- thread_id: 기본적으로 `session_id` (chapter2는 `f"{session_id}:chapter2"` 등으로 분리 가능)
- Redis에는
  - 그래프/세션 상태(`meta.stage`, `last_question_text` 등)
  - 코드 정보(`latest`, `history`, `question_history`, `question_cnt`)
  - STT/TTS 로그(`conv:{session_id}`)
  가 저장되어, 새로고침·이어하기 시에도 상태를 복원합니다.

---

## GraphDB + HybridRAG
 - Neo4j 그래프 기반 추천 + Elastic 하이브리드 서치 리랭킹
 - GraphDB를 통해 구조적 관계기반 1차 추출, HybridRAG를 통해 의미/키워드 유사도로 정확성 높이는 2차 추출

### GraphDB
 - input: `livecoding_reports` / output: `graph_output.recommended_problems`

 - Problem / AlgoSkill / Difficulty + 사용자 Evidence/Gap/Similarity
  - Evidence(3-hop), Gap(2-hop), User-Sim(4-hop), Algo-Sim(4-hop) 경로 가중치를 가산해서 추천할  후보 problem의 점수 생성

### HybridRAG(Elastic Re-Rank)
 - input: Neo4j에서 후보 `problem_id`와 `graph_output.recommendation_query` / output: `graph_output.recommended_problems`

 - 키워드 매칭(problem), 코사인 유사도, 단어 필터링(problem_id, difficulty) 조합해서 Re-Rank

---

## 📊 평가 시스템

### 3단계 종합 평가 프로세스

JobTory는 단순한 정답 확인을 넘어 **3가지 핵심 역량**을 자동으로 평가합니다:

#### 1️⃣ 코드 품질 평가 (35점)
- **Ruff 정적 분석 기반**
  - 코드 스타일 준수도 (PEP8, Naming Convention 등)
  - 잠재적 버그 및 안티패턴 탐지
  - 코드 복잡도 및 가독성 분석
- 평가 기준: F, E, W, B, C, S, UP, A, TID, RUF 등 규칙 위반 횟수 및 심각도

#### 2️⃣ 협업 및 커뮤니케이션 능력 (30점)
- **AI 기반 대화 분석**
  - 질문에 대한 답변의 명확성 및 논리성
  - 힌트 요청 횟수 및 활용도
  - 문제 해결 과정에서의 설명 능력
- **Ruff 협업 관련 규칙**: N, D, Q, I, ERA (문서화, 주석, import 정리 등)
- 평가 근거: STT 대화 로그, 질문/답변 히스토리, 코드 변화 패턴

#### 3️⃣ 문제 해결 능력 (35점)
- **코드 실행 결과 분석**
  - 테스트 케이스 통과율
  - 알고리즘 효율성 (시간/공간 복잡도)
- **문제 접근 방식**
  - Intro 단계에서의 전략 수립
  - 코딩 과정에서의 점진적 개선 (코드 변화량 분석)

### 등급 체계
- **A+등급 (90점 이상)**: 탁월한 코드 품질과 협업 능력
- **A등급 (80-89점)**: 우수한 전반적 역량
- **B등급 (70-79점)**: 양호한 수준
- **C등급 (60-69점)**: 보통 수준
- **D등급 (50-59점)**: 개선 필요
- **F등급 (50점 미만)**: 미흡

---

## 🧰 기술 스택

| 범주 | 기술 | 설명 |
|------|------|------|
| **Frontend** | Vue 3, Vite, CodeMirror | 라이브코딩 UI, 타이머, STT/TTS 제어 |
| **Backend** | Django, Django REST Framework | 인증, 세션 관리, API 서버 |
| **LLM** | LangGraph, OpenAI `gpt-5-nano` | 질문/피드백 생성 |
| **정적 분석** | Ruff | Python 코드 품질·협업 관련 규칙 분리 평가 |
| **STT** | Whisper 계열 (faster-whisper 등) | 한국어 STT, 전략·답변 인식 |
| **TTS** | OpenAI `openai 4o mini` (`nova` 등) | 문제 설명, 질문, 피드백 음성 출력 |
| **Storage** | PostgreSQL, Redis | 영구 데이터(PostgreSQL), 세션/그래프/코드/버퍼(Redis) |
| **Infra** | Docker, AWS | 로컬/배포 환경 컨테이너 구성 |
| **GraphDB** | Neo4j | 사용자 리포트 기반 약점 알고리즘–문제 관계 그래프 구성 및 맞춤 문제 추천 |

---

## 📚 Redis 키 설계 (요약)

| 키 패턴 | 설명 | 주요 필드 |
|--------|------|----------|
| `livecoding:{session_id}:meta` | 세션 메타 정보 | `stage`, `intro_flow_done`, `language`, `user_id` 등 |
| `livecoding:{session_id}:problem` | 코딩 문제 정보 | `title`, `problem`, `starter_code`, `test_cases`, `time_limit_seconds` 등 |
| `livecoding:{session_id}:code` | 코드 스냅샷 | `latest`, `history[]`, `question_history[]`, `question_cnt` |
| `conv:{session_id}` | STT/TTS 대화 로그 | 질문/답변 텍스트, 타임스탬프, 발화 타입 등 |
| LangGraph checkpoint | 그래프 상태 | LangGraph에서 내부적으로 사용하는 키 |
| LLM | LangGraph, OpenAI GPT-4o-mini | 질문/피드백 생성, 종합 평가 |

---

## 📁 폴더 구조

```text
SKN18-FINAL-4TEAM/
├── backend/                  # Django + LangGraph 백엔드
│   ├── anti_cheat/           # Vision 기반 부정행위 감지 파이프라인
│   ├── api/                  # REST API (livecoding, STT/TTS, 인증 등)
│   ├── graph_sync/           # 문제 추천을 위한 GraphDB/검색 동기화 파이프라인
│   ├── interview_engine/     # LangGraph 그래프/노드 정의
│   ├── planner/              # 성장 리포트 및 학습 코치 파이프라인
│   ├── stt/                  # STT 파이프라인
│   ├── tts_client.py         # TTS 유틸리티 
│   └── ...                   # 설정, 모델 등
├── frontend/
│   └── vue-app/              # Vue 3 + Vite 프론트엔드
│       ├── src/pages/
│       │   ├── LiveCodingSettingPage.vue
│       │   └── LiveCodingSessionPage.vue
│       └── ...               # 컴포넌트, 라우터 등
├── docker/                   # Docker / 배포 설정
├── requirements.txt          # Python 의존성
└── README.md                 # 본 문서
```

---

## 🚀 설치 & 실행 (요약)

### 1) Backend 

```bash

docker-compose -f docker/docker-compose.yml --env-file .env up -d
python -m venv .venv --python 3.12
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cd backend
python manage.py migrate
python manage.py makemigration api
python manage.py runserver
```

### 2) Frontend

```bash
cd frontend/vue-app
npm install
npm run dev
```

이후 브라우저에서 `http://localhost:5174/` 로 접속해  
환경 설정 페이지 → 라이브 코딩 페이지로 진입하면 JobTory 라이브 코딩 인터뷰를 테스트할 수 있습니다.
