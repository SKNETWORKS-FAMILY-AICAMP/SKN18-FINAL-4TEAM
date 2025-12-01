<template>
  <div class="main-page">
    <header class="hero">
      <h1 class="logo">JobTory</h1>
      <p class="tagline">AI 면접 & 라이브 코딩 평가 플랫폼</p>
      <p class="description">
        자기소개서 분석부터 행동 면접, 라이브 코딩 테스트까지
        한 화면에서 자연스럽게 이어지는 실전 면접 경험을 제공합니다.
      </p>
      <div class="actions">
        <RouterLink to="/login" class="primary">로그인하기</RouterLink>
        <RouterLink to="/interview" class="ghost">실전 면접 보기</RouterLink>
      </div>
      <div class="links">
        <RouterLink to="/coding-test" class="link">라이브 코딩 테스트 보기</RouterLink>
      </div>
    </header>
  </div>
</template>

<script setup>
import { RouterLink } from "vue-router";
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap");

.main-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  background: linear-gradient(135deg, #e2f0da, #b9d6b1);
  font-family: "Nunito", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #1f2933;
}

.hero {
  max-width: 720px;
  text-align: center;
}

.logo {
  font-size: 40px;
  font-weight: 800;
  letter-spacing: 0.06em;
  margin-bottom: 8px;
  color: #21415d;
}

.tagline {
  margin: 0 0 12px;
  font-size: 18px;
  color: #364152;
}

.description {
  margin: 0 0 28px;
  color: #52606d;
  line-height: 1.6;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.primary,
.ghost {
  border-radius: 999px;
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}

.primary {
  border: none;
  background: linear-gradient(180deg, #f48f54, #e67235);
  color: #fff;
  box-shadow: 0 10px 20px rgba(228, 114, 53, 0.35);
  text-decoration: none;
}

.ghost {
  border: 1px solid #9fb3c8;
  background: rgba(255, 255, 255, 0.7);
  color: #364152;
}

.links {
  margin-top: 10px;
}

.link {
  font-size: 13px;
  color: #52606d;
  text-decoration: underline;
}
</style>
