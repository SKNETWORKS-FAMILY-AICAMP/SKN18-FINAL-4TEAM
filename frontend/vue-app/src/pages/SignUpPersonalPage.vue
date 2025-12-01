<template>
  <div class="signup-page">
    <header class="signup-header">
      <p class="page-label">개인용 회원가입</p>
    </header>

    <main class="signup-main">
      <section class="card">
        <h1 class="title">Sign in</h1>

        <div class="form-grid">
          <div class="field-block">
            <label class="field-label">아이디</label>
            <div class="field-line">
              <input v-model="username" class="field-input" type="text" placeholder="아이디" />
              <button type="button" class="pill-button" @click="handleCheckUsername">중복확인</button>
            </div>
            <p v-if="usernameStatus === 'ok'" class="hint-text success">사용 가능한 아이디입니다.</p>
            <p v-else-if="usernameStatus === 'taken'" class="hint-text error">이미 사용 중인 아이디입니다.</p>
            <p v-else-if="usernameStatus === 'empty'" class="hint-text error">아이디를 입력해 주세요.</p>
          </div>

          <div class="field-block">
            <label class="field-label">이름</label>
            <div class="field-line">
              <input v-model="name" class="field-input" type="text" placeholder="홍길동" />
            </div>
          </div>

          <div class="field-block">
            <label class="field-label">비밀번호</label>
            <div class="field-line">
              <input v-model="password" class="field-input" type="password" />
            </div>
          </div>

          <div class="field-block">
            <label class="field-label">전화번호</label>
            <div class="field-line phone-line">
              <input v-model="phone1" class="field-input phone-input" type="tel" maxlength="3" />
              <span class="hyphen">-</span>
              <input v-model="phone2" class="field-input phone-input" type="tel" maxlength="4" />
              <span class="hyphen">-</span>
              <input v-model="phone3" class="field-input phone-input" type="tel" maxlength="4" />
            </div>
          </div>

          <div class="field-block">
            <label class="field-label">비밀번호 확인</label>
            <div class="field-line" :class="{ 'error-line': showPasswordError, 'success-line': showPasswordMatch }">
              <input v-model="passwordConfirm" class="field-input" type="password" />
            </div>
            <p v-if="showPasswordMatch" class="password-hint success">비밀번호가 일치합니다.</p>
            <p v-else-if="showPasswordError" class="password-hint error">비밀번호가 일치하지 않습니다.</p>
          </div>

          <div class="field-block">
            <label class="field-label">이메일</label>
            <div class="field-line email-line">
              <input v-model="emailLocal" class="field-input email-local" type="text" placeholder="username" />
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
              <button
                type="button"
                class="pill-button email-send-button"
                :disabled="emailSending"
                @click="handleSendEmailCode"
              >
                {{ emailSending ? "발송 중..." : "인증번호 발송" }}
              </button>
            </div>
            <p v-if="emailInlineMessage" :class="['email-inline-msg', emailInlineType]">
              {{ emailInlineMessage }}
            </p>
          </div>

          <div class="field-block">
            <label class="field-label">생년월일</label>
            <div class="birth-row">
              <select v-model="birthYear" class="birth-select">
                <option value="">년</option>
                <option v-for="year in years" :key="year" :value="year">
                  {{ year }}
                </option>
              </select>
              <select v-model="birthMonth" class="birth-select">
                <option value="">월</option>
                <option v-for="month in months" :key="month" :value="month">
                  {{ month }}
                </option>
              </select>
              <select v-model="birthDay" class="birth-select">
                <option value="">일</option>
                <option v-for="day in days" :key="day" :value="day">
                  {{ day }}
                </option>
              </select>
            </div>
          </div>

          <div class="field-block">
            <label class="field-label">인증번호</label>
            <div class="field-line">
              <input v-model="emailCode" class="field-input" type="text" placeholder="인증번호 입력" />
              <button
                type="button"
                class="pill-button"
                :disabled="emailVerifying"
                @click="handleVerifyEmailCode"
              >
                {{ emailVerifying ? "확인 중..." : "인증" }}
              </button>
            </div>
          </div>
        </div>

        <button type="button" class="submit-button" :disabled="pending" @click="handleSubmit">
          {{ pending ? "가입 중..." : "회원가입" }}
        </button>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { useRouter } from "vue-router";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const router = useRouter();

const currentYear = new Date().getFullYear();
const years = Array.from({ length: 70 }, (_, i) => currentYear - i);
const months = Array.from({ length: 12 }, (_, i) => i + 1);
const days = Array.from({ length: 31 }, (_, i) => i + 1);

const birthYear = ref("");
const birthMonth = ref("");
const birthDay = ref("");
const name = ref("");
const username = ref("");
const phone1 = ref("");
const phone2 = ref("");
const phone3 = ref("");

const password = ref("");
const passwordConfirm = ref("");

const emailLocal = ref("");
const emailDomainInput = ref("");
const emailDomainSelect = ref("");
const pending = ref(false);
const message = ref("");
const messageType = ref("info");
const emailVerified = ref(false);
const emailCode = ref("");
const emailSending = ref(false);
const emailVerifying = ref(false);
const emailInlineMessage = ref("");
const emailInlineType = ref("info");
const usernameStatus = ref(""); // '', 'ok', 'taken', 'empty'

watch(emailDomainSelect, (val) => {
  if (val) {
    emailDomainInput.value = val;
  }
});

// 아이디를 수정하면 중복검사 상태를 초기화
watch(username, () => {
  usernameStatus.value = "";
});

const handleCheckUsername = async () => {
  const value = username.value.trim();
  if (!value) {
    usernameStatus.value = "empty";
    return;
  }

  try {
    const res = await fetch(
      `${API_BASE}/api/auth/user-id/check/?user_id=${encodeURIComponent(value)}`,
      {
        method: "GET"
      }
    );
    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      const detail = data?.detail || "아이디 중복 확인에 실패했습니다.";
      throw new Error(detail);
    }

    usernameStatus.value = data.available ? "ok" : "taken";
  } catch (err) {
    usernameStatus.value = "";
    message.value = err.message || "아이디 중복 확인 중 오류가 발생했습니다.";
    messageType.value = "error";
  }
};

const showPasswordMatch = computed(
  () => !!password.value && !!passwordConfirm.value && password.value === passwordConfirm.value
);

const showPasswordError = computed(
  () => !!password.value && !!passwordConfirm.value && password.value !== passwordConfirm.value
);

const buildEmail = () => {
  const domain = emailDomainSelect.value || emailDomainInput.value;
  if (!emailLocal.value || !domain) return "";
  return `${emailLocal.value}@${domain}`;
};

const buildPhone = () => {
  if (!phone1.value || !phone2.value || !phone3.value) return "";
  return `${phone1.value}-${phone2.value}-${phone3.value}`;
};

const buildBirthdate = () => {
  if (!birthYear.value || !birthMonth.value || !birthDay.value) return null;
  const month = String(birthMonth.value).padStart(2, "0");
  const day = String(birthDay.value).padStart(2, "0");
  return `${birthYear.value}-${month}-${day}`;
};

const handleSubmit = async () => {
  message.value = "";

  // 필수 필드 하나씩 체크하면서 비어 있으면 개별 안내
  if (!username.value) {
    window.alert("아이디를 입력해 주세요.");
    return;
  }

  // 아이디 중복확인 선행
  if (usernameStatus.value !== "ok") {
    window.alert("아이디 중복확인을 먼저 해 주세요.");
    return;
  }

  if (!name.value) {
    window.alert("이름을 입력해 주세요.");
    return;
  }

  // 이메일 로컬파트를 안 적었으면 아이디를 대신 사용
  if (!emailLocal.value && username.value) {
    emailLocal.value = username.value;
  }

  if (!emailLocal.value) {
    window.alert("이메일 아이디(username)를 입력해 주세요.");
    return;
  }

  const hasEmailDomain = emailDomainSelect.value || emailDomainInput.value;
  if (!hasEmailDomain) {
    window.alert("이메일 도메인을 선택하거나 입력해 주세요.");
    return;
  }

  const email = buildEmail();
  if (!email) {
    window.alert("이메일을 올바르게 입력해 주세요.");
    return;
  }

  if (!emailVerified.value) {
    window.alert("이메일 인증을 완료해 주세요.");
    return;
  }

  if (!password.value) {
    window.alert("비밀번호를 입력해 주세요.");
    return;
  }

  if (!passwordConfirm.value) {
    window.alert("비밀번호 확인을 입력해 주세요.");
    return;
  }

  if (password.value !== passwordConfirm.value) {
    window.alert("비밀번호와 비밀번호 확인이 일치하지 않습니다.");
    return;
  }

  if (!birthYear.value || !birthMonth.value || !birthDay.value) {
    window.alert("생년월일을 모두 선택해 주세요.");
    return;
  }

  const phone_number = buildPhone();
  const birthdate = buildBirthdate();

  pending.value = true;
  try {
    const res = await fetch(`${API_BASE}/api/auth/signup/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: username.value,
        email,
        name: name.value,
        password: password.value,
        phone_number: phone_number || null,
        birthdate
      })
    });
    const data = await res.json();
    if (!res.ok) {
      const detail = data?.detail || Object.values(data || {})[0] || "가입에 실패했습니다.";
      throw new Error(detail);
    }
    message.value = "가입이 완료되었습니다. 로그인 페이지로 이동합니다.";
    messageType.value = "success";
    // 성공 안내 후 로그인 페이지로 이동
    window.alert("회원가입이 완료되었습니다. 로그인 페이지로 이동합니다.");
    password.value = "";
    passwordConfirm.value = "";
    router.push("/login");
  } catch (err) {
    message.value = err.message || "가입 중 오류가 발생했습니다.";
    messageType.value = "error";
  } finally {
    pending.value = false;
  }
};

const handleSendEmailCode = async () => {
  const email = buildEmail();
  if (!email) {
    message.value = "이메일을 올바르게 입력해 주세요.";
    messageType.value = "error";
    emailInlineMessage.value = message.value;
    emailInlineType.value = "error";
    return;
  }
  emailSending.value = true;
  message.value = "";
  try {
    const res = await fetch(`${API_BASE}/api/auth/email/send/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email })
    });
    let data = null;
    try {
      data = await res.json();
    } catch (e) {
      // non-JSON 응답일 경우 대비
    }
    if (!res.ok) {
      const detail = data?.detail || `인증번호 발송에 실패했습니다. (status ${res.status})`;
      throw new Error(detail);
    }
    message.value = "인증번호를 전송했습니다. 메일을 확인해 주세요.";
    messageType.value = "success";
    emailInlineMessage.value = message.value;
    emailInlineType.value = "success";
  } catch (err) {
    message.value = err.message || "인증번호 발송 중 오류가 발생했습니다.";
    messageType.value = "error";
    emailInlineMessage.value = message.value;
    emailInlineType.value = "error";
  } finally {
    emailSending.value = false;
  }
};

const handleVerifyEmailCode = async () => {
  const email = buildEmail();
  if (!email || !emailCode.value) {
    message.value = "이메일과 인증번호를 입력해 주세요.";
    messageType.value = "error";
    emailInlineMessage.value = message.value;
    emailInlineType.value = "error";
    return;
  }
  emailVerifying.value = true;
  message.value = "";
  try {
    const res = await fetch(`${API_BASE}/api/auth/email/verify/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, code: emailCode.value })
    });
    let data = null;
    try {
      data = await res.json();
    } catch (e) {
      // non-JSON 응답일 경우 대비
    }
    if (!res.ok) {
      const detail = data?.detail || `인증에 실패했습니다. (status ${res.status})`;
      throw new Error(detail);
    }
    emailVerified.value = true;
    message.value = "이메일 인증이 완료되었습니다.";
    messageType.value = "success";
    emailInlineMessage.value = message.value;
    emailInlineType.value = "success";
  } catch (err) {
    message.value = err.message || "인증 중 오류가 발생했습니다.";
    messageType.value = "error";
    emailInlineMessage.value = message.value;
    emailInlineType.value = "error";
  } finally {
    emailVerifying.value = false;
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

.hint-text {
  margin: 2px 0 0;
  font-size: 12px;
  color: #6b7280;
}

.hint-text.success {
  color: #16a34a;
}

.hint-text.error {
  color: #dc2626;
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

.pill-button {
  padding: 4px 12px;
  border-radius: 999px;
  border: none;
  background: #111827;
  color: #f9fafb;
  font-size: 12px;
  cursor: pointer;
}

.field-line.email-line {
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

.chip {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 999px;
  background: #e5e7eb;
  font-size: 12px;
}

.birth-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.birth-select {
  flex: 1;
  min-width: 0;
  border-radius: 999px;
  border: 1px solid #d1d5db;
  padding: 6px 10px;
  font-size: 12px;
  background: #ffffff;
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

.submit-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}

.email-inline-msg {
  margin: 4px 0 0;
  font-size: 12px;
}

.email-inline-msg.success {
  color: #15803d;
}

.email-inline-msg.error {
  color: #b91c1c;
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
