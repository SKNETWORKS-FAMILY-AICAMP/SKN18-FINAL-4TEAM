# AWS 배포 가이드라인
## AWS 요소들

---

## 1. VPC (Virtual Private Cloud)
- 사용자가 정의하는 AWS 계정 사용자 전용 가상의 네트워크
- 사용자가 자기가 원하는 대로 IP 주소 범위 선택, 서브넷 생성, 라우팅 테이블 및 네트워크 게이트웨이 구성 등 가상 네트워크 환경을 구성해 VPC 생성 가능

---

## VPC 관련 언어 정리 및 기초 지식

### IP (Internet Protocol)
- 인터넷에 연결되어 있는 모든 장치들(컴퓨터, 서버 장비, 스마트폰 등)을 식별하기 위해 부여되는 고유 주소

### IP 주소 구성
- IP는 **네트워크 ID + 호스트 주소**로 구성

> ***IP는 더 깊이 들어가면 설명할 내용이 많지만, 본 프로젝트 범위에서는 핵심 요소가 아니므로 생략***

---

### 서브넷 (Subnet)
- B 클래스 기준 Host ID는 약 6만 개로, 한 기업이 모두 사용하지 않을 경우 IP 자원이 낭비됨
- C 클래스는 IP 자원이 부족
- 이러한 문제를 해결하기 위해 **IP를 효율적으로 분할하여 사용하는 방식**이 서브넷

<img src="subnet.png" width="600"/>

---

### 라우팅 테이블 (Routing Table)
- 각 Subnet은 서로 다른 네트워크 영역을 소유
- Subnet 간 통신을 위해 Routing 필요
- 라우팅 테이블은 **트래픽을 어디로 전달할지 결정하는 표지판 역할** 수행

-------------------------------------------------

## 2. EC2 (Elastic Compute Cloud)
- AWS에서 제공하는 클라우드 컴퓨팅 서비스
- 독립된 가상 컴퓨터를 임대해 사용하는 개념

-------------------------------------------------

## 2-1. EC2 특징
① 컴퓨팅 요구사항에 따라 컴퓨팅 파워 조절 가능  
② 실제 사용한 만큼 비용 지불  
③ Linux / Windows OS 선택 가능  
④ 수 분 내 전 세계에 서버 수백 대 생성 가능  
⑤ Web Server, ML, Game Server 등 다양한 용도 지원  
⑥ 다른 AWS 서비스와 유기적 연동 가능  

-------------------------------------------------

## 2-2. EC2 구성 요소 (Instance, EBS, AMI)
- 일반적인 서버 구성  
  - 연산(CPU/RAM) → Instance  
  - 저장공간 → EBS  
  - 서버 이미지 → AMI  

### ① EC2 인스턴스
- AWS에서 사용하는 가상 컴퓨터
- CPU, 메모리 등 연산 작업 담당

### ② EBS (Elastic Block Storage)
- 데이터를 저장하는 스토리지
- 일반적인 HDD/SSD 역할

### ③ AMI (Amazon Machine Image)
- EC2 인스턴스를 실행하기 위한 템플릿
- OS, 아키텍처, 스토리지 설정, 사전 설치 소프트웨어 포함

-------------------------------------------------

## 2-3. EC2 인스턴스 구축

### ① EC2 인스턴스 시작
<img src="EC2-1.png" width="600"/>
<img src="EC2-2.png" width="600"/>

### ② 인스턴스 이름 / AMI 설정
<img src="EC2-3.png" width="600"/>
<img src="EC2-4.png" width="600"/>

### ③ 서버 생성
<img src="EC2-5.png" width="600"/>

-------------------------------------------------

## 3. RDS (Relational Database Service)
- AWS에서 제공하는 관리형 관계형 데이터베이스
- 데이터베이스 설정, 패치, 백업 작업 자동화
- 확장성과 안정성이 뛰어남

-------------------------------------------------

## 3-1. RDS 역할
① Django의 영구 데이터 저장  
② 사용자 정보, 문제 데이터, 제출 기록, 로그 메타데이터 저장  

-------------------------------------------------

## 3-2. EC2 DB vs RDS

| EC2 직접 설치 | RDS |
|--------------|-----|
| 백업/복구 직접 관리 | 자동 백업 |
| 장애 시 복구 어려움 | 안정적 |
| 운영 부담 큼 | 운영 부담 적음 |

-------------------------------------------------

## 3-3. RDS 구축

### ① RDS 생성
<img src="RDS-1.png" width="600"/>
<img src="RDS-2.png" width="600"/>
<img src="RDS-3.png" width="600"/>

### ② DB 인스턴스 및 마스터 사용자 설정
<img src="RDS-4.png" width="600"/>

### ③ 인스턴스 구성 및 스토리지
<img src="RDS-5.png" width="600"/>
<img src="RDS-6.png" width="600"/>

### ④ 생성한 RDS EC2에 연결
<img src="RDS-7.png" width="600"/>

> ***테스트 목적일 경우 퍼블릭 Access 활성화 가능***
<img src="RDS-8.png" width="600"/>

### ⑤ 데이터베이스 인증
<img src="RDS-9.png" width="600"/>

### ⑥ 모니터링
- 모니터링 활성화 시 추가 비용 발생 (선택)
<img src="RDS-10.png" width="600"/>

### ⑦ 추가 구성
<img src="RDS-11.png" width="600"/>

-------------------------------------------------

## 3-4. RDS 파라미터 설정

### ① 파라미터 그룹 생성
<img src="RDS-12.png" width="600"/>
<img src="RDS-13.png" width="600"/>

> ***Database Engine 버전과 파라미터 그룹 버전은 반드시 일치해야 함***
<img src="RDS-14.png" width="600"/>

<img src="RDS-15.png" width="600"/>

### ② 서울 시간 설정
<img src="RDS-16.png" width="600"/>

### ③ 최대 연결 수 변경 (선택)
<img src="RDS-17.png" width="600"/>

### ④ 파라미터 적용
<img src="RDS-18.png" width="600"/>
<img src="RDS-19.png" width="600"/>
<img src="RDS-20.png" width="600"/>

-------------------------------------------------

## 3-5. RDS 접속

### ① 보안 그룹 인바운드 규칙 설정
<img src="RDS-21.png" width="600"/>

### ② EC2 보안 그룹 추가
<img src="RDS-22.png" width="600"/>


--------------------------


# 현재 진행 상황
- Duck DNS + Caddy로 현재 Cerification 모든 동작 작동 확인 완료 
- 도메인명: https://jobtory.duckdns.org
- Freenom(도메인제공 사이트)가 현재 서비스 중단으로 인해 무료 도메인은 불가능


## Param Store(SSM) 등록 - 정상 동작 기준

> REGION=ap-northeast-2, PREFIX=/jobtory/prod

```bash
REGION=ap-northeast-2
PREFIX=/jobtory/prod

# Django
aws ssm put-parameter --name "$PREFIX/DJANGO_SECRET_KEY" --value "<DJANGO_SECRET_KEY>" --type SecureString --overwrite --region $REGION
aws ssm put-parameter --name "$PREFIX/DJANGO_DEBUG" --value "false" --type SecureString --overwrite --region $REGION
aws ssm put-parameter --name "$PREFIX/DJANGO_ALLOWED_HOSTS" --value "jobtory.duckdns.org,15.164.232.11" --type SecureString --overwrite --region $REGION

# CORS/CSRF
aws ssm put-parameter --name "$PREFIX/CORS_ALLOW_ALL_ORIGINS" --value "false" --type SecureString --overwrite --region $REGION
aws ssm put-parameter --name "$PREFIX/CORS_ALLOWED_ORIGINS" --value "https://jobtory.duckdns.org" --type SecureString --overwrite --region $REGION
aws ssm put-parameter --name "$PREFIX/CORS_ALLOW_CREDENTIALS" --value "false" --type SecureString --overwrite --region $REGION
aws ssm put-parameter --name "$PREFIX/CSRF_TRUSTED_ORIGINS" --value "https://jobtory.duckdns.org" --type SecureString --overwrite --region $REGION

# DB (RDS)
aws ssm put-parameter --name "$PREFIX/DB_HOST" --value "<RDS_ENDPOINT>" --type SecureString --overwrite --region $REGION
aws ssm put-parameter --name "$PREFIX/DB_PORT" --value "5432" --type SecureString --overwrite --region $REGION
aws ssm put-parameter --name "$PREFIX/DB_NAME" --value "postgres" --type SecureString --overwrite --region $REGION
aws ssm put-parameter --name "$PREFIX/DB_USER" --value "<DB_USER>" --type SecureString --overwrite --region $REGION
aws ssm put-parameter --name "$PREFIX/DB_PASSWORD" --value "<DB_PASSWORD>" --type SecureString --overwrite --region $REGION

# Redis
aws ssm put-parameter --name "$PREFIX/REDIS_URL" --value "redis://redis:6379/0" --type SecureString --overwrite --region $REGION

# Frontend (Vite)
aws ssm put-parameter --name "$PREFIX/VITE_API_BASE" --value "https://jobtory.duckdns.org" --type SecureString --overwrite --region $REGION
aws ssm put-parameter --name "$PREFIX/VITE_FRONTEND_BASE" --value "https://jobtory.duckdns.org/" --type SecureString --overwrite --region $REGION
aws ssm put-parameter --name "$PREFIX/VITE_GOOGLE_CLIENT_ID" --value "<GOOGLE_CLIENT_ID>" --type SecureString --overwrite --region $REGION
aws ssm put-parameter --name "$PREFIX/VITE_GOOGLE_REDIRECT_URI" --value "https://jobtory.duckdns.org/login" --type SecureString --overwrite --region $REGION
aws ssm put-parameter --name "$PREFIX/VITE_WS_BASE" --value "wss://jobtory.duckdns.org" --type SecureString --overwrite --region $REGION

# Backend Google OAuth
aws ssm put-parameter --name "$PREFIX/GOOGLE_CLIENT_ID" --value "<GOOGLE_CLIENT_ID>" --type SecureString --overwrite --region $REGION
aws ssm put-parameter --name "$PREFIX/GOOGLE_CLIENT_SECRET" --value "<GOOGLE_CLIENT_SECRET>" --type SecureString --overwrite --region $REGION
aws ssm put-parameter --name "$PREFIX/GOOGLE_REDIRECT_URI" --value "https://jobtory.duckdns.org/login" --type SecureString --overwrite --region $REGION
aws ssm put-parameter --name "$PREFIX/FRONTEND_BASE_URL" --value "https://jobtory.duckdns.org/" --type SecureString --overwrite --region $REGION

# Email
aws ssm put-parameter --name "$PREFIX/EMAIL_BACKEND" --value "django.core.mail.backends.smtp.EmailBackend" --type SecureString --overwrite --region $REGION
aws ssm put-parameter --name "$PREFIX/EMAIL_HOST" --value "smtp.gmail.com" --type SecureString --overwrite --region $REGION
aws ssm put-parameter --name "$PREFIX/EMAIL_PORT" --value "587" --type SecureString --overwrite --region $REGION
aws ssm put-parameter --name "$PREFIX/EMAIL_HOST_USER" --value "<EMAIL_USER>" --type SecureString --overwrite --region $REGION
aws ssm put-parameter --name "$PREFIX/EMAIL_HOST_PASSWORD" --value "<EMAIL_PASSWORD>" --type SecureString --overwrite --region $REGION
aws ssm put-parameter --name "$PREFIX/EMAIL_USE_TLS" --value "true" --type SecureString --overwrite --region $REGION
aws ssm put-parameter --name "$PREFIX/DEFAULT_FROM_EMAIL" --value "<EMAIL_USER>" --type SecureString --overwrite --region $REGION

# 기타
aws ssm put-parameter --name "$PREFIX/OPENAI_API_KEY" --value "<OPENAI_API_KEY>" --type SecureString --overwrite --region $REGION
```

## SSM -> .env 생성 (정상 동작 기준)

```bash
cd ~/SKN18-FINAL-4TEAM

aws ssm get-parameters-by-path \
  --path "/jobtory/prod/" \
  --with-decryption \
  --output json \
  --no-cli-pager > /tmp/ssm.json

python3 - <<'PY' > .env
import json
with open("/tmp/ssm.json") as f:
    data = json.load(f)
for p in data.get("Parameters", []):
    print(f"{p['Name'].split('/')[-1]}={p['Value']}")
PY

# 값 확인
grep VITE_API_BASE .env
```

## 배포 재시작 (정상 동작 기준)

```bash
# 프론트 빌드 (env 반드시 붙여서 실행)
docker compose --env-file .env -f docker/docker-compose.prod.yml build --no-cache frontend

# 전체 기동
docker compose --env-file .env -f docker/docker-compose.prod.yml up -d
```

## 프론트/백엔드 코드 변경 요약 (localhost 제거 포함)

### 1) 프론트: Google Redirect 하드코딩 제거
- 파일: frontend/vue-app/src/pages/LoginPage.vue
- 변경 내용

```js
const redirectUri = import.meta.env.VITE_GOOGLE_REDIRECT_URI || window.location.origin + "/login";
```

### 2) 프론트: API_BASE 기본값을 현재 도메인으로 통일
- 변경 대상
  - frontend/vue-app/src/hooks/useAuth.js
  - frontend/vue-app/src/pages/ProfileEditPage.vue
  - frontend/vue-app/src/pages/ProfileEditPage_final.vue
  - frontend/vue-app/src/pages/LiveCodingPage.vue
  - frontend/vue-app/src/pages/LiveCodingSessionPage.vue
  - frontend/vue-app/src/pages/LiveCodingSettingPage.vue
  - frontend/vue-app/src/pages/SignUpPersonalPage.vue
  - frontend/vue-app/src/pages/showreport.vue
  - frontend/vue-app/src/pages/rendering.vue

- 변경 내용 예시(들어가면 안되는 값이라 저렇게 해놨음)

```js
const API_BASE = import.meta.env.VITE_API_BASE || window.location.origin;
```

### 3) 프론트: Vite 빌드 시 환경 변수 주입
- 파일: frontend/vue-app/Dockerfile
- 내용: ARG/ENV로 VITE_* 전달 후 npm run build

```dockerfile
ARG VITE_API_BASE
ARG VITE_GOOGLE_CLIENT_ID
ARG VITE_FRONTEND_BASE
ARG VITE_GOOGLE_REDIRECT_URI
ARG VITE_WS_BASE

ENV VITE_API_BASE=$VITE_API_BASE
ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID
ENV VITE_FRONTEND_BASE=$VITE_FRONTEND_BASE
ENV VITE_GOOGLE_REDIRECT_URI=$VITE_GOOGLE_REDIRECT_URI
ENV VITE_WS_BASE=$VITE_WS_BASE
```

### 4) 백엔드: ALLOWED_HOSTS에 도메인 추가
- Param Store 값

```
DJANGO_ALLOWED_HOSTS=jobtory.duckdns.org,15.164.232.11
```

## 도메인 변경 시 반영 체크리스트

- Param Store
  - VITE_API_BASE
  - VITE_FRONTEND_BASE
  - VITE_GOOGLE_REDIRECT_URI
  - FRONTEND_BASE_URL
  - GOOGLE_REDIRECT_URI
  - CORS_ALLOWED_ORIGINS
  - CSRF_TRUSTED_ORIGINS
  - DJANGO_ALLOWED_HOSTS

- Google OAuth 콘솔
  - 승인된 JavaScript 원본
  - 승인된 리디렉션 URI

- 배포 재빌드
  - docker compose --env-file .env -f docker/docker-compose.prod.yml build --no-cache frontend
  - docker compose --env-file .env -f docker/docker-compose.prod.yml up -d


# 추후 진행 상황
- Route 53 + ALB + Auto Scaling 적용
- 이를 위해 도메인 구매 금액 및 사이트 선정이 팀원들과 상의 후 선정 필요해 보임

## 도메인 구매 사이트 
1. Porkbun: .com/.net 저렴, 숨은 비용 적음, WHOIS 무료
2. Cloudflare Registrar: 갱신가가 거의 원가(중간 마진 없음)라 장기 운영에 유리. (단, Cloudflare DNS 사용 필요)
3. Gabia/가비아: .kr/한국 도메인 편하지만 가격은 해외보다 비싼 편

## 추후 계획
1. 도메인 팀원과 상의 후 구매 선정

2. Route 53 Hosted Zone 생성 
- 구매처에서 네임서버를 Route 53 NS로 변경

3. ACM 인증서 발급
* 단 서울 region 으로 발급해야 함
* ex) jobtory.com, www.jobtory.com .com으로 구매하면 둘다 포함시켜야함

4. ALB 생성 + HTTPS 리스너
- 443 리스너에 ACM 인증서 연결해야함
- Target Group을 EC2 혹은 ECS 둘중 바뀌면 해당하는 걸로 연결해야 함

5. EC2에서 직접 HTTPS 종료 제거
- Caddy는 제거하거나, ALB 뒤에서 80포트만 사용해야함 

6. Auto Scaling Group 구성
- Launch Template + 스케링 정책 (Min: 12 or Max : 24로 생각중)

7. 환경 변수 업데이트
- 파람스토어 활용중이므로 VITE_API_BASE, FRONTEND_BASE_URL, GOOGLE_REDIRECT_URI 등 적용되있는 값을 변경된 도메인으로 반영

8. Google OAuth 설정도 변경된 도메인으로 재등록 필요
- 승인된 JS + Redirection url 변경 도메인으로 교체# --- 자동 추가: Param Store/배포/코드 변경 정리 (정상 동작 기준) ---

