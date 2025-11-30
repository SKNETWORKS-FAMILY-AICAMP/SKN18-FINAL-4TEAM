<template>
  <div class="page">
    <main class="hero">
      <section class="hero-left">
        <p class="eyebrow">JobTory</p>
        <h1 class="title">
          JobTory<br />
          <span>Live Coding Test</span>
        </h1>
        <RouterLink to="/coding-test/session" class="primary">테스트 시작하기</RouterLink>

        <div class="features">
          <article class="feature-card">
            <div class="feature-icon monitor"></div>
            <div class="feature-text">
              <h2>실전 시험 환경</h2>
              <p>화면 공유 · 웹캠 감지</p>
            </div>
          </article>
          <article class="feature-card">
            <div class="feature-icon chart"></div>
            <div class="feature-text">
              <h2>실전형 문제 구성</h2>
              <p>유형·난이도별 문제 제공</p>
            </div>
          </article>
          <article class="feature-card">
            <div class="feature-icon checklist"></div>
            <div class="feature-text">
              <h2>자동 채점 시스템</h2>
              <p>상세 리포트로 강·약점 분석</p>
            </div>
          </article>
        </div>
      </section>

      <section class="hero-right">
        <div class="illustration-wrap">
          <img :src="typingLogo" alt="JobTory typing" class="typing-logo" />
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { RouterLink } from "vue-router";

const typingLogo = new URL("../assets/JOBTORY_typing2.png", import.meta.url).href;
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap");

.page {
  min-height: 100vh;
  margin: 0;
  padding: 40px;
  display: flex;
  justify-content: center;
  align-items: stretch;
  background: #d9e9d0;
  font-family: "Nunito", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #1f2933;
}

.hero {
  width: 100%;
  background: #cae6c5;
  border-radius: 24px;
  padding: 40px 48px 36px;
  min-height: calc(100vh - 80px);
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(0, 1fr);
  gap: 32px;
}

.hero-left {
  display: flex;
  flex-direction: column;
}

.eyebrow {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 700;
  color: #a855f7;
}

.title {
  margin: 0 0 20px;
  font-size: 40px;
  line-height: 1.15;
  color: #21415d;
}

.title span {
  font-size: 36px;
}

.primary {
  align-self: flex-start;
  margin-bottom: 32px;
  padding: 12px 26px;
  border-radius: 999px;
  border: none;
  background: linear-gradient(180deg, #f48f54, #e67235);
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 12px 25px rgba(228, 114, 53, 0.4);
}

.features {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.feature-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 12px;
  background: #fdf6ea;
  border-radius: 14px;
  border: 1px solid #f4e3c6;
}

.feature-icon {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  border: 2px solid #1f5e65;
  position: relative;
}

.feature-icon.monitor::before {
  content: "";
  position: absolute;
  inset: 6px 5px 10px;
  border-radius: 6px;
  border: 2px solid #1f5e65;
}

.feature-icon.monitor::after {
  content: "";
  position: absolute;
  bottom: 4px;
  left: 50%;
  width: 10px;
  height: 2px;
  transform: translateX(-50%);
  background: #1f5e65;
}

.feature-icon.chart::before {
  content: "";
  position: absolute;
  inset: 7px 8px;
  border-left: 2px solid #1f5e65;
  border-bottom: 2px solid #1f5e65;
}

.feature-icon.chart::after {
  content: "";
  position: absolute;
  bottom: 8px;
  right: 8px;
  width: 10px;
  height: 12px;
  border: 2px solid #1f5e65;
  border-top: none;
}

.feature-icon.checklist::before {
  content: "";
  position: absolute;
  inset: 5px 7px;
  border-radius: 6px;
  border: 2px solid #1f5e65;
}

.feature-icon.checklist::after {
  content: "";
  position: absolute;
  left: 10px;
  top: 12px;
  width: 10px;
  height: 8px;
  border-left: 2px solid #1f5e65;
  border-bottom: 2px solid #1f5e65;
  transform: rotate(-35deg);
}

.feature-text h2 {
  margin: 0;
  font-size: 15px;
  color: #1f2933;
}

.feature-text p {
  margin: 2px 0 0;
  font-size: 12px;
  color: #6b7280;
}

.hero-right {
  display: flex;
  align-items: center;
  justify-content: center;
}

.illustration-wrap {
  max-width: 360px;
}

.typing-logo {
  width: 100%;
  height: auto;
  display: block;
}

@media (max-width: 800px) {
  .hero {
    grid-template-columns: 1fr;
    padding: 28px 20px 22px;
  }

  .hero-right {
    order: -1;
  }

  .features {
    grid-template-columns: 1fr;
  }
}
</style>
