<template>
  <div class="signup-page">
    <header class="signup-header">
      <p class="page-label">개인/기업용 회원가입</p>
    </header>

    <main class="signup-main">
      <section class="card">
        <h1 class="title">Sign in</h1>

        <div class="choice-grid">
          <button class="choice-card" type="button" @click="goToTerms('personal')">
            <div class="choice-icon">
              <img :src="personalIcon" alt="개인 회원" />
            </div>
            <div class="choice-label">개인 회원</div>
          </button>

          <button class="choice-card" type="button" @click="goToTerms('company')">
            <div class="choice-icon">
              <img :src="companyIcon" alt="기업 회원" />
            </div>
            <div class="choice-label">기업 회원</div>
          </button>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { useRouter } from "vue-router";

const router = useRouter();

const personalIcon = new URL("../assets/개인회원.png", import.meta.url).href;
const companyIcon = new URL("../assets/기업회원.png", import.meta.url).href;

const goToTerms = (type) => {
  router.push({ name: "signup-terms", query: { type } });
};
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap");

.signup-page {
  min-height: 100vh;
  background: #f6f5ef;
  font-family: "Nunito", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #111827;
  display: flex;
  flex-direction: column;
}

.signup-header {
  padding: 12px 24px 0;
}

.page-label {
  margin: 0;
  font-size: 14px;
  color: #9ca3af;
}

.signup-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 16px 48px;
}

.card {
  width: 100%;
  max-width: 900px;
  background: #f8f6ee;
  border-radius: 8px;
  padding: 64px 48px 72px;
}

.title {
  margin: 0 0 56px;
  text-align: center;
  font-size: 52px;
  font-weight: 800;
}

.choice-grid {
  display: flex;
  justify-content: center;
  gap: 48px;
  flex-wrap: wrap;
}

.choice-card {
  width: 300px;
  height: 280px;
  border-radius: 28px;
  border: none;
  background: linear-gradient(135deg, #f9fafb, #e5f0e3);
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.18);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 22px;
  cursor: pointer;
  transition: transform 0.14s ease, box-shadow 0.14s ease, background 0.14s ease;
}

.choice-icon {
  width: 160px;
  height: 160px;
}

.choice-icon img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.choice-label {
  font-size: 24px;
  font-weight: 800;
}

.choice-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.24);
  background: linear-gradient(135deg, #ffffff, #e3f3e6);
}

.choice-card:active {
  transform: translateY(1px);
  box-shadow: 0 8px 16px rgba(15, 23, 42, 0.18);
}

@media (max-width: 640px) {
  .card {
    padding: 48px 20px 56px;
  }

  .title {
    font-size: 40px;
    margin-bottom: 40px;
  }

  .choice-card {
    width: 240px;
    height: 240px;
  }
}
</style>
