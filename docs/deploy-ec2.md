# EC2 배포 (Docker Compose)

## 사전 준비
- EC2 Ubuntu 22.04 (또는 Amazon Linux 2)
- Docker + docker compose plugin
- RDS PostgreSQL 엔드포인트
- Redis 엔드포인트 (ElastiCache 또는 로컬 컨테이너)
- OpenAI API 키
- Google OAuth 자격증명(사용 시)
- SMTP 자격증명(사용 시)

## 1) 보안그룹
- 인바운드: 80(HTTP), 22(SSH)
- 아웃바운드: 443(OpenAI/Google/SMTP) 허용

## 2) 서버 준비 (Ubuntu 예시)
```
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
```
docker 그룹 추가 후 로그아웃/로그인 필요.

## 3) .env 준비
- `.env.sample`을 `.env`로 복사
- 다음 값을 채움:
  - DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
  - REDIS_URL
  - DJANGO_SECRET_KEY, DJANGO_DEBUG, DJANGO_ALLOWED_HOSTS
  - CORS_ALLOWED_ORIGINS, CSRF_TRUSTED_ORIGINS
  - OPENAI_API_KEY, GOOGLE_CLIENT_ID/SECRET, EMAIL_* (사용 시)

예시:
```
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=your-domain.com,EC2_PUBLIC_IP
CORS_ALLOWED_ORIGINS=https://your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com

DB_HOST=your-rds-endpoint
DB_PORT=5432
DB_NAME=jobtory
DB_USER=jobtory
DB_PASSWORD=change-me

REDIS_URL=redis://your-redis-endpoint:6379/0

OPENAI_API_KEY=...
```

## 4) 빌드 및 실행
레포 루트에서:
```
chmod +x docker/run-prod.sh
./docker/run-prod.sh
```

## 5) 검증
- 백엔드 헬스: `http://<EC2_PUBLIC_IP>/api/health/`
- 프론트: `http://<EC2_PUBLIC_IP>/`

## 6) 업데이트
```
# 최신 코드 반영
git pull

# 컨테이너 재빌드/재기동
./docker/run-prod.sh
```
