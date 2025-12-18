<template>
  <div class="signup-page">
    <header class="signup-header">
      <p class="page-label">회원가입 약관동의</p>
    </header>

    <main class="signup-main">
      <section class="card">
        <h1 class="title">Sign in</h1>

        <div class="terms-list">
          <div class="term-box">
            <div class="term-content"></div>
            <div class="term-footer">
              <span>개인정보 수집정보 동의 (필수)</span>
              <label class="checkbox-wrap">
                <input v-model="term1" type="checkbox" />
              </label>
            </div>
          </div>

          <div class="term-box">
            <div class="term-content"></div>
            <div class="term-footer">
              <span>개인정보 수집정보 동의 (필수)</span>
              <label class="checkbox-wrap">
                <input v-model="term2" type="checkbox" />
              </label>
            </div>
          </div>

          <div class="term-box">
            <div class="term-content"></div>
            <div class="term-footer">
              <span>개인정보 수집정보 동의 (필수)</span>
              <label class="checkbox-wrap">
                <input v-model="term3" type="checkbox" />
              </label>
            </div>
            <p class="age-text">만 14세 이상입니다.</p>
          </div>
        </div>

        <button type="button" class="next-button" @click="goNext">다음</button>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();

const term1 = ref(false);
const term2 = ref(false);
const term3 = ref(false);

const goNext = () => {
  if (!term1.value || !term2.value || !term3.value) {
    window.alert("필수 약관에 모두 동의해야 다음 단계로 이동할 수 있습니다.");
    return;
  }

  const type = route.query.type === "company" ? "company" : "personal";
  if (type === "company") {
    router.push({ name: "signup-company" });
  } else {
    router.push({ name: "signup-personal" });
  }
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
  padding: 60px 52px 72px;
}

.title {
  margin: 0 0 40px;
  text-align: center;
  font-size: 52px;
  font-weight: 800;
}

.terms-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.term-box {
  background: #ffffff;
  border-radius: 14px;
  padding: 18px 18px 14px;
  box-shadow: 0 4px 10px rgba(15, 23, 42, 0.08);
}

.term-content {
  height: 70px;
  background: #f3f4f6;
  border-radius: 10px;
}

.term-footer {
  margin-top: 6px;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.checkbox-wrap input {
  width: 14px;
  height: 14px;
}

.age-text {
  margin: 4px 0 0;
  font-size: 13px;
  text-align: right;
}

.next-button {
  display: block;
  margin: 40px auto 0;
  padding: 11px 46px;
  border-radius: 999px;
  border: none;
  background: #111827;
  color: #f9fafb;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.3);
}

@media (max-width: 640px) {
  .card {
    padding: 40px 20px 56px;
  }

  .title {
    font-size: 40px;
  }
}
</style>
