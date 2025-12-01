<template>
  <div class="signup-page">
    <header class="signup-header">
      <p class="page-label">기업용 회원가입</p>
    </header>

    <main class="signup-main">
      <section class="card">
        <h1 class="title">Sign in</h1>

        <div class="form-grid">
          <div class="field-block">
            <label class="field-label">아이디</label>
            <div class="field-line">
              <input class="field-input" type="text" />
            </div>
          </div>

          <div class="field-block">
            <label class="field-label">담당자 이름</label>
            <div class="field-line">
              <input class="field-input" type="text" />
            </div>
          </div>

          <div class="field-block">
            <label class="field-label">비밀번호</label>
            <div class="field-line">
              <input v-model="password" class="field-input" type="password" />
            </div>
          </div>

          <div class="field-block">
            <label class="field-label">담당자 전화번호</label>
            <div class="field-line phone-line">
              <input class="field-input phone-input" type="tel" maxlength="3" />
              <span class="hyphen">-</span>
              <input class="field-input phone-input" type="tel" maxlength="4" />
              <span class="hyphen">-</span>
              <input class="field-input phone-input" type="tel" maxlength="4" />
            </div>
          </div>

          <div class="field-block">
            <label class="field-label">비밀번호 확인</label>
            <div
              class="field-line"
              :class="{ 'error-line': showPasswordError, 'success-line': showPasswordMatch }"
            >
              <input v-model="passwordConfirm" class="field-input" type="password" />
            </div>
            <p v-if="showPasswordMatch" class="password-hint success">비밀번호가 일치합니다.</p>
            <p v-else-if="showPasswordError" class="password-hint error">
              비밀번호가 일치하지 않습니다.
            </p>
          </div>

          <div class="field-block">
            <label class="field-label">회사 이메일</label>
            <div class="field-line email-line">
              <input class="field-input email-local" type="text" />
              <span class="at">@</span>
              <input
                v-model="emailDomainInput"
                class="field-input email-domain-input"
                type="text"
                placeholder="example.com"
              />
              <select v-model="emailDomainSelect" class="email-domain">
                <option value="">직접 입력</option>
                <option value="gmail.com">gmail.com</option>
                <option value="naver.com">naver.com</option>
                <option value="daum.net">daum.net</option>
                <option value="kakao.com">kakao.com</option>
              </select>
              <button type="button" class="pill-button email-send-button">인증번호 발송</button>
            </div>
          </div>

          <div class="field-block">
            <label class="field-label">기업명</label>
            <div class="field-line">
              <input class="field-input" type="text" />
            </div>
          </div>

          <div class="field-block">
            <label class="field-label">인증번호</label>
            <div class="field-line">
              <input class="field-input" type="text" />
              <button type="button" class="pill-button">인증</button>
            </div>
          </div>
        </div>

        <button type="button" class="submit-button" @click="handleSubmit">회원가입</button>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, ref, watch } from "vue";

const password = ref("");
const passwordConfirm = ref("");

const emailDomainInput = ref("");
const emailDomainSelect = ref("");

watch(emailDomainSelect, (val) => {
  if (val) {
    emailDomainInput.value = val;
  }
});

const showPasswordMatch = computed(
  () => !!password.value && !!passwordConfirm.value && password.value === passwordConfirm.value
);

const showPasswordError = computed(
  () => !!password.value && !!passwordConfirm.value && password.value !== passwordConfirm.value
);

const handleSubmit = () => {
  if (!password.value || !passwordConfirm.value) {
    window.alert("비밀번호와 비밀번호 확인을 모두 입력해 주세요.");
    return;
  }

  if (password.value !== passwordConfirm.value) {
    window.alert("비밀번호와 비밀번호 확인이 일치하지 않습니다.");
    return;
  }

  // 실제 회원가입 로직은 추후 연동 예정
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
  max-width: 980px;
  background: #f8f6ee;
  border-radius: 8px;
  padding: 56px 52px 64px;
}

.title {
  margin: 0 0 40px;
  text-align: center;
  font-size: 52px;
  font-weight: 800;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: 72px;
  row-gap: 24px;
}

.field-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field-label {
  font-size: 16px;
  font-weight: 800;
}

.field-line {
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid #111827;
  padding-bottom: 4px;
}

.field-input {
  flex: 1;
  border: none;
  background: transparent;
  outline: none;
  font-size: 14px;
}

.phone-line {
  gap: 6px;
}

.phone-input {
  flex: 0 0 64px;
  text-align: center;
}

.hyphen {
  flex: 0 0 auto;
}

.pill-button {
  padding: 4px 12px;
  border-radius: 999px;
  border: none;
  background: #111827;
  color: #f9fafb;
  font-size: 12px;
  cursor: pointer;
}

.email-line {
  gap: 2px;
}

.email-local {
  flex: 0 0 70px;
  padding-bottom: 0;
}

.at {
  padding: 0 4px;
}

.email-domain {
  flex: 0 0 90px;
  border-radius: 999px;
  border: 1px solid #d1d5db;
  padding: 4px 10px;
  font-size: 12px;
}

.email-domain-input {
  flex: 1 1 auto;
  border: none;
  background: transparent;
  outline: none;
  font-size: 12px;
  padding-bottom: 0;
}

.email-send-button {
  flex: 0 0 auto;
  margin-left: auto;
  white-space: nowrap;
}

.password-hint {
  margin: 2px 0 0;
  font-size: 12px;
}

.password-hint.success {
  color: #16a34a;
}

.password-hint.error {
  color: #dc2626;
}

.error-line {
  border-bottom-color: #dc2626;
}

.success-line {
  border-bottom-color: #16a34a;
}

.submit-button {
  display: block;
  margin: 40px auto 0;
  padding: 11px 40px;
  border-radius: 999px;
  border: none;
  background: #111827;
  color: #f9fafb;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.3);
}

@media (max-width: 768px) {
  .card {
    padding: 40px 24px 48px;
  }

  .form-grid {
    grid-template-columns: 1fr;
    column-gap: 0;
  }
}
</style>
