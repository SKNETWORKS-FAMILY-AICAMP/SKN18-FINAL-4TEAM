<template>
  <div class="signup-page">
    <div class="bg-grid"></div>

    <div class="signup-container">
      <header class="signup-header">
        <p class="eyebrow">MEMBERSHIP</p>
        <h1 class="page-title">
          Join JobTory
        </h1>
        <p class="page-description">
          서비스 이용을 위해 회원 유형을 선택해 주세요.
        </p>
      </header>

      <div class="choice-grid">
        <button class="choice-card card-personal" type="button" @click="goToTerms('personal')">
          <div class="card-inner">
            <div class="icon-circle personal-icon-bg">
              <img :src="personalIcon" alt="개인 회원" class="card-icon" />
            </div>
            <div class="text-group">
              <h2 class="card-title">개인 회원</h2>
              <p class="card-desc">취업 준비생 / 일반 사용자</p>
            </div>
            <div class="arrow-btn">
              <span class="arrow-icon">→</span>
            </div>
          </div>
        </button>

        <button class="choice-card card-company" type="button" @click="goToTerms('company')">
          <div class="card-inner">
            <div class="icon-circle company-icon-bg">
              <img :src="companyIcon" alt="기업 회원" class="card-icon" />
            </div>
            <div class="text-group">
              <h2 class="card-title">기업 회원</h2>
              <p class="card-desc">채용 담당자 / 기업 관리자</p>
            </div>
            <div class="arrow-btn">
              <span class="arrow-icon">→</span>
            </div>
          </div>
        </button>
      </div>

      <div class="footer-link">
        <p>이미 계정이 있으신가요? <a @click="router.push({name: 'login'})">로그인하기</a></p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from "vue-router";

const router = useRouter();

const personalIcon = new URL("../assets/개인회원.png", import.meta.url).href;
const companyIcon = new URL("../assets/기업회원.png", import.meta.url).href;

const goToTerms = (type) => {
  if (type === "company") {
    router.push({ name: "signup-company" });
  } else {
    router.push({ name: "signup-personal" });
  }
};
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&display=swap");

/* 1. 전체 화면 고정 (스크롤 제거) */
.signup-page {
  position: relative;
  width: 100vw;
  height: 100vh; /* 화면 꽉 채움 */
  background: #f8f4eb;
  font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #111827;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden; /* 바깥쪽 스크롤 원천 차단 */
}

/* 배경 그리드 */
.bg-grid {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  z-index: 0;
  background-size: 40px 40px;
  background-image:
    linear-gradient(to right, rgba(0, 0, 0, 0.05) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(0, 0, 0, 0.05) 1px, transparent 1px);
  mask-image: linear-gradient(to bottom, black 40%, transparent 100%);
  pointer-events: none;
}

/* 2. 내부 컨테이너 (필요시 내부 스크롤) */
.signup-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 900px;
  display: flex;
  flex-direction: column;
  gap: 60px;
  
  /* 화면 높이를 초과할 경우 내부 스크롤 허용 */
  max-height: 100vh;
  overflow-y: auto;
  padding: 40px 20px; /* 패딩을 컨테이너 내부로 이동 */

  /* 스크롤바 숨기기 */
  scrollbar-width: none;  /* Firefox */
  -ms-overflow-style: none; /* IE, Edge */
}

/* 크롬, 사파리 스크롤바 숨김 */
.signup-container::-webkit-scrollbar {
  display: none;
}

/* --- 이하 스타일 동일 --- */

.signup-header {
  text-align: center;
  animation: fadeUp 0.8s ease-out;
}

.eyebrow {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 700;
  color: #9ca3af;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.page-title {
  margin: 0 0 16px;
  font-size: 56px;
  font-weight: 900;
  color: #111827;
  line-height: 1.1;
}

.page-description {
  margin: 0;
  font-size: 18px;
  color: #4b5563;
}

/* 선택 카드 그리드 */
.choice-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 32px;
  justify-content: center;
}

.choice-card {
  position: relative;
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 24px;
  padding: 48px 32px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.card-inner {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

.choice-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 22px 40px rgba(15, 23, 42, 0.12);
  border-color: rgba(0, 0, 0, 0.1);
}

.icon-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
  transition: transform 0.3s ease;
}

.card-icon {
  width: 60%;
  height: 60%;
  object-fit: contain;
}

.personal-icon-bg { background: #f9c5d5; }
.company-icon-bg { background: #f7d56f; }

.choice-card:hover .icon-circle { transform: scale(1.1); }

.text-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card-title {
  margin: 0;
  font-size: 28px;
  font-weight: 800;
  color: #111827;
}

.card-desc {
  margin: 0;
  font-size: 16px;
  color: #6b7280;
  font-weight: 500;
}

.arrow-btn {
  margin-top: 16px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.arrow-icon {
  font-size: 20px;
  font-weight: 600;
  color: #111827;
}

.choice-card:hover .arrow-btn {
  background: #111827;
  transform: translateX(5px);
}

.choice-card:hover .arrow-icon { color: #ffffff; }

.footer-link {
  text-align: center;
  font-size: 15px;
  color: #6b7280;
}

.footer-link a {
  font-weight: 700;
  color: #111827;
  text-decoration: underline;
  cursor: pointer;
  margin-left: 4px;
}

.footer-link a:hover { color: #000; }

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 640px) {
  .page-title { font-size: 40px; }
  .choice-card { padding: 32px 24px; }
  .icon-circle { width: 100px; height: 100px; }
}
</style>