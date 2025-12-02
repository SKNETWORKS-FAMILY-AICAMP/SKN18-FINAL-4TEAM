<template>
  <div class="live-page">
    <div class="live-hero">
      <div class="hero-text">
        <p class="eyebrow">JobTory Live Coding</p>
        <h1 class="title">
          Let's Start
          <br />
          Live Coding Test!
        </h1>
        <RouterLink to="/coding-test/settings" class="start-btn">테스트 시작</RouterLink>
      </div>
      <div class="hero-visual">
        <img :src="typingLogo" alt="Live coding illustration" class="hero-image" />
      </div>
    </div>

    <div class="feature-grid">
      <div class="feature-card feature-one">
        <div class="feature-icon">🖥️</div>
        <div class="feature-content">
          <h3>실전 시험 환경</h3>
          <p>화면 공유와 입력 감지로 현장 같은 테스트</p>
        </div>
      </div>
      <div class="feature-card feature-two">
        <div class="feature-icon">📊</div>
        <div class="feature-content">
          <h3>실전형 문제구성</h3>
          <p>유형·난이도별 맞춤 문제 제공</p>
        </div>
      </div>
      <div class="feature-card feature-three">
        <div class="feature-icon">✅</div>
        <div class="feature-content">
          <h3>자동 채점 시스템</h3>
          <p>상세 리포트로 통합 점·역량 분석 제공</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { RouterLink } from "vue-router";

const typingLogo = new URL("../assets/mainpage_image2.png", import.meta.url).href;
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap");

.live-page {
  min-height: 81vh;
  padding: 72px 40px 96px;
  background: #262728;
  color: #f8fafc;
  font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  display: flex;
  flex-direction: column;
  gap: 64px;
}

.live-hero {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  align-items: center;
  gap: 32px;
}

.hero-text {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.eyebrow {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #94a3b8;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.title {
  margin: 0;
  font-size: 50px;
  line-height: 1.12;
  font-weight: 800;
  color: #f8fafc;
}

.start-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-top: 12px;
  padding: 14px 28px;
  border-radius: 12px;
  background: #e5e7eb;
  color: #111827;
  font-weight: 700;
  font-size: 18px;
  text-decoration: none;
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.18);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.start-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 32px rgba(0, 0, 0, 0.22);
}

.hero-visual {
  display: flex;
  justify-content: center;
}

.hero-image {
  width: 100%;
  max-width: 455px;
  height: auto;
  display: block;
}

.feature-grid {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 18px;
}

.feature-card {
  border-radius: 20px;
  padding: 60px 20px;
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 12px;
  align-items: center;
  box-shadow: 0 14px 30px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(0, 0, 0, 0.06);
  color: #111827;
}

.feature-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  background: rgba(255, 255, 255, 0.35);
}

.feature-content h3 {
  margin: 0 0 6px;
  font-size: 18px;
  font-weight: 800;
}

.feature-content p {
  margin: 0;
  font-size: 14px;
  color: #374151;
}

.feature-one {
  background: #f6c7d9;
}

.feature-two {
  background: #f8d46f;
}

.feature-three {
  background: #c5b3f5;
}

@media (max-width: 640px) {
  .live-page {
    padding: 56px 20px 80px;
  }

  .title {
    font-size: 38px;
  }

  .start-btn {
    width: fit-content;
  }
}
</style>
