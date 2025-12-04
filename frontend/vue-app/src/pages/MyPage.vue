<template>
  <div class="mypage">
    <header class="mypage-header">
      <RouterLink to="/" class="brand">JOBTORY</RouterLink>
    </header>

    <main class="mypage-body">
      <div class="card">
        <h1 class="title">마이페이지</h1>
        <p class="subtitle">계정 정보를 확인하고 서비스를 계속 이용하세요.</p>
        <div class="info-grid" v-if="user">
          <div class="info-row">
            <span class="label">아이디</span>
            <span class="value">{{ user.user_id }}</span>
          </div>
          <div class="info-row">
            <span class="label">이름</span>
            <span class="value">{{ user.name }}</span>
          </div>
          <div class="info-row">
            <span class="label">이메일</span>
            <span class="value">{{ user.email }}</span>
          </div>
          <div class="info-row" v-if="user.phone_number">
            <span class="label">전화번호</span>
            <span class="value">{{ user.phone_number }}</span>
          </div>
          <div class="info-row" v-if="user.birthdate">
            <span class="label">생년월일</span>
            <span class="value">{{ user.birthdate }}</span>
          </div>
        </div>
        <p class="hint" v-else>계정 정보를 불러오는 중입니다...</p>
      </div>
    </main>
  </div>
</template>

<script setup>
import { onMounted } from "vue";
import { RouterLink } from "vue-router";
import { useAuth } from "../hooks/useAuth";

const { user, fetchProfile } = useAuth();

onMounted(() => {
  if (!user.value) {
    void fetchProfile();
  }
});
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap");

.mypage {
  min-height: 100vh;
  background: #f8f4eb;
  font-family: "Nunito", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #111827;
}

.mypage-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 32px;
}

.brand {
  font-weight: 800;
  letter-spacing: 0.14em;
  color: #0f172a;
  text-decoration: none;
  font-size: 22px;
}

.mypage-body {
  display: flex;
  justify-content: center;
  padding: 60px 16px;
}

.card {
  width: min(640px, 100%);
  background: #ffffff;
  border-radius: 18px;
  padding: 32px 28px;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.12);
  border: 1px solid #e5e7eb;
  text-align: left;
}

.title {
  margin: 0 0 8px;
  font-size: 32px;
  font-weight: 800;
}

.subtitle {
  margin: 0 0 14px;
  font-size: 16px;
  color: #4b5563;
}

.hint {
  margin: 0;
  font-size: 14px;
  color: #6b7280;
}

.info-grid {
  margin-top: 20px;
  display: grid;
  gap: 12px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  border: 1px solid #e5e7eb;
  padding: 10px 12px;
  border-radius: 10px;
  background: #f9fafb;
}

.label {
  font-weight: 700;
  color: #374151;
}

.value {
  color: #111827;
}
</style>
