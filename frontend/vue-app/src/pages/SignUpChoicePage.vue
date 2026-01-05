<template>
  <div class="signup-page">
    <div class="bg-grid"></div>

    <nav class="nav-header">
      <RouterLink to="/" class="brand">JOBTORY</RouterLink>
    </nav>

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
import { useRouter, RouterLink } from "vue-router"; // RouterLink 추가

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
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap");

/* --- [추가된 스타일] 상단 네비게이션 --- */
.nav-header {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  padding: 24px 40px;
  z-index: 50;
  display: flex;
  align-items: center;
}

.brand {
  font-family: "Inter", sans-serif;
  font-size: 24px;
  font-weight: 900;
  color: #111827;
  text-decoration: none;
  letter-spacing: -0.02em;
  cursor: pointer;
}

/* 모바일 대응 */
@media (max-width: 768px) {
  .nav-header {
    padding: 20px;
    justify-content: center;
  }
}

/* -------------------------------------- */
/* ... 기존 스타일 그대로 유지 ... */

.signup-page {
  position: relative;
  width: 100vw;
  height: 100vh;
  background: #f8f4eb;
  font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #111827;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

/* ... (나머지 스타일 동일) ... */
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

.signup-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 900px;
  display: flex;
  flex-direction: column;
  gap: 60px;
  max-height: 100vh;
  overflow-y: auto;
  padding: 40px 20px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.signup-container::-webkit-scrollbar {
  display: none;
}

.signup-header {
  text-align: center;
  animation: fadeUp 0.8s ease-out;
  margin-top: 40px; /* 로고와 겹치지 않게 여백 추가 */
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