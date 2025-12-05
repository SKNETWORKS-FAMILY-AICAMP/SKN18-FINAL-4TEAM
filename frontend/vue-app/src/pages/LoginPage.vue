<template>
  <div class="login-page">
    <header class="login-header">
      <RouterLink to="/" class="brand">
        <span class="brand-mark">JOBTORY</span>
      </RouterLink>
    </header>

    <main class="login-main">
      <section class="login-card">
        <div class="login-copy">
          <p class="eyebrow">라이브 인터뷰 플랫폼</p>
          <h1 class="login-title">Login</h1>
          <p class="login-subtitle">
            한 번의 로그인으로 면접준비 부터 라이브 코딩까지.
          </p>
        </div>

        <form class="login-form" @submit.prevent="handleSubmit">
          <label class="field">
            <span class="field-label">아이디</span>
            <div class="field-shell">
              <input
                class="field-input field-input--email"
                v-model="identifier"
                type="text"
                placeholder="아이디 또는 이메일"
                autocomplete="username"
              />
            </div>
          </label>

          <label class="field">
            <span class="field-label">비밀번호</span>
            <div class="field-shell">
              <input
                class="field-input field-input--password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="비밀번호를 입력하세요"
                autocomplete="current-password"
              />
              <button
                type="button"
                class="password-toggle"
                :aria-label="showPassword ? '비밀번호 숨기기' : '비밀번호 보기'"
                @click="togglePassword"
              >
                <svg viewBox="0 0 24 24" class="icon">
                  <path
                    fill="currentColor"
                    d="M12 5c-4.5 0-8.3 2.7-10 7 1.7 4.3 5.5 7 10 7s8.3-2.7 10-7c-1.7-4.3-5.5-7-10-7Zm0 12a5 5 0 1 1 0-10 5 5 0 0 1 0 10Zm0-2a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"
                  />
                </svg>
              </button>
            </div>
          </label>

          <button type="submit" class="submit-button">다음</button>

          <p v-if="errorMessage" class="error-text">
            {{ errorMessage }}
          </p>

          <div class="helper-row">
            <button type="button" class="link-button subtle" @click="isFindIdOpen = true">
              아이디 찾기
            </button>
            <span class="divider-dot">·</span>
            <button type="button" class="link-button subtle" @click="isFindPasswordOpen = true">
              비밀번호 찾기
            </button>
          </div>

          <div class="divider">
            <span></span>
            <p>or</p>
            <span></span>
          </div>

          <button type="button" class="google-button" @click="handleGoogleLogin">
            <svg viewBox="0 0 533.5 544.3" class="google-icon">
              <path
                fill="#4285f4"
                d="M533.5 278.4c0-17.4-1.6-34.1-4.6-50.3H272v95.2h146.9c-6.4 34.7-25.8 64-55 83.6v68.9h88.8c51.9-47.8 80.8-118.2 80.8-197.4Z"
              />
              <path
                fill="#34a853"
                d="M272 544.3c74 0 136-24.4 181.3-66.5l-88.8-68.9c-24.7 16.6-56.4 26.3-92.5 26.3-71 0-131.2-47.9-152.8-112.2H26v70.7C71.2 477.7 165.6 544.3 272 544.3Z"
              />
              <path
                fill="#fbbc04"
                d="M119.2 322.9c-5.6-16.6-8.8-34.4-8.8-52.9s3.2-36.3 8.8-52.9V146.4H26C9.4 179.6 0 219 0 270s9.4 90.4 26 123.6l93.2-70.7Z"
              />
              <path
                fill="#ea4335"
                d="M272 107.7c40.3 0 76.5 13.9 105 41.2l78.6-78.6C408 24.2 346 0 272 0 165.6 0 71.2 66.6 26 146.4l93.2 70.7C140.8 155.6 201 107.7 272 107.7Z"
              />
            </svg>
            <span>Continue with Google</span>
          </button>

      <p class="helper">
        Don't have an account yet?
        <RouterLink to="/signup" class="helper-link">Register for free</RouterLink>
      </p>
    </form>
  </section>
    </main>

    <div v-if="isFindIdOpen" class="modal-backdrop">
      <div class="modal-box">
        <h2 class="modal-title">아이디 찾기</h2>
        <p class="modal-subtitle">회원가입 시 사용한 이메일을 입력해 주세요.</p>
        <form class="modal-form" @submit.prevent="handleFindId">
          <input
            v-model="findIdEmail"
            type="email"
            class="modal-input"
            placeholder="username@gmail.com"
          />
          <div class="modal-actions">
            <button type="button" class="modal-button ghost" @click="closeFindId">
              취소
            </button>
            <button type="submit" class="modal-button primary">
              아이디 찾기
            </button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="isFindPasswordOpen" class="modal-backdrop">
      <div class="modal-box">
        <h2 class="modal-title">비밀번호 찾기</h2>
        <p class="modal-subtitle">이름, 아이디, 이메일을 입력하면 임시 비밀번호를 보내드립니다.</p>
        <form class="modal-form" @submit.prevent="handleFindPassword">
          <input
            v-model="findPwName"
            type="text"
            class="modal-input"
            placeholder="이름"
          />
          <input
            v-model="findPwUserId"
            type="text"
            class="modal-input"
            placeholder="아이디"
          />
          <input
            v-model="findPwEmail"
            type="email"
            class="modal-input"
            placeholder="username@gmail.com"
          />
          <div class="modal-actions">
            <button type="button" class="modal-button ghost" @click="closeFindPassword">
              취소
            </button>
            <button type="submit" class="modal-button primary">
              임시 비밀번호 받기
            </button>
          </div>
        </form>
      </div>
    </div>

    <transition name="toast-fade">
      <div v-if="toastVisible" class="toast">
        {{ toastMessage }}
      </div>
    </transition>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import { RouterLink, useRouter, useRoute } from "vue-router";
import { useAuth } from "../hooks/useAuth";

const router = useRouter();
const route = useRoute();
const { setSession, BACKEND_BASE } = useAuth();

const showPassword = ref(false);
const identifier = ref("");
const password = ref("");
const errorMessage = ref("");
const isHandlingGoogle = ref(false);

const isFindIdOpen = ref(false);
const findIdEmail = ref("");

const isFindPasswordOpen = ref(false);
const findPwName = ref("");
const findPwUserId = ref("");
const findPwEmail = ref("");

const toastMessage = ref("");
const toastVisible = ref(false);
let toastTimer = null;
const handleGlobalKeydown = (event) => {
  if (event.key === "Escape") {
    if (isFindIdOpen.value) {
      closeFindId();
      return;
    }
    if (isFindPasswordOpen.value) {
      closeFindPassword();
    }
  }
};

const showToast = (msg, duration = 2400) => {
  toastMessage.value = msg;
  toastVisible.value = true;
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toastVisible.value = false;
  }, duration);
};

onUnmounted(() => {
  if (toastTimer) clearTimeout(toastTimer);
  document.removeEventListener("keydown", handleGlobalKeydown);
});

const togglePassword = () => {
  showPassword.value = !showPassword.value;
};

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

// Google 콘솔에 등록한 redirect URI와 정확히 일치하도록 고정
// 로컬 개발 기준: http://localhost:5174/login
const redirectUri = "http://localhost:5174/login";

const buildGoogleAuthUrl = () => {
  const params = new URLSearchParams({
    client_id: GOOGLE_CLIENT_ID,
    redirect_uri: redirectUri,
    response_type: "code",
    scope: "openid email profile",
    access_type: "offline",
    prompt: "consent"
  });
  return `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
};

const handleGoogleLogin = () => {
  if (!GOOGLE_CLIENT_ID) {
    alert("구글 클라이언트 ID가 설정되지 않았습니다. 관리자에게 문의하세요.");
    return;
  }
  window.location.href = buildGoogleAuthUrl();
};

const closeFindId = () => {
  isFindIdOpen.value = false;
  findIdEmail.value = "";
};

const handleFindId = () => {
  const email = findIdEmail.value.trim();
  if (!email) {
    window.alert("이메일을 입력해 주세요.");
    return;
  }

  (async () => {
    try {
      const resp = await fetch(`${BACKEND_BASE}/api/auth/find-id/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ email })
      });

      const data = await resp.json().catch(() => ({}));

      if (!resp.ok) {
        const detail = data.detail || "해당 이메일로 가입된 아이디가 없습니다.";
        window.alert(detail);
        return;
      }

      window.alert("입력하신 이메일로 아이디 안내 메일을 발송했습니다.");
      closeFindId();
    } catch (err) {
      console.error(err);
      window.alert("아이디 찾기 처리 중 오류가 발생했습니다.");
    }
  })();
};

const closeFindPassword = () => {
  isFindPasswordOpen.value = false;
  findPwName.value = "";
  findPwUserId.value = "";
  findPwEmail.value = "";
};

const handleFindPassword = () => {
  const name = findPwName.value.trim();
  const userId = findPwUserId.value.trim();
  const email = findPwEmail.value.trim();

  if (!name) {
    window.alert("이름을 입력해 주세요.");
    return;
  }
  if (!userId) {
    window.alert("아이디를 입력해 주세요.");
    return;
  }
  if (!email) {
    window.alert("이메일을 입력해 주세요.");
    return;
  }

  (async () => {
    try {
      const resp = await fetch(`${BACKEND_BASE}/api/auth/find-password/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ name, user_id: userId, email })
      });

      const data = await resp.json().catch(() => ({}));

      if (!resp.ok) {
        const detail =
          data.detail || "입력하신 정보와 일치하는 계정을 찾을 수 없습니다.";
        window.alert(detail);
        return;
      }

      window.alert("임시 비밀번호를 이메일로 발송했습니다. 메일을 확인해 주세요.");
      closeFindPassword();
    } catch (err) {
      console.error(err);
      window.alert("비밀번호 찾기 처리 중 오류가 발생했습니다.");
    }
  })();
};

const handleGoogleCallback = async () => {
  const code = route.query.code;
  if (!code || isHandlingGoogle.value) return;

  isHandlingGoogle.value = true;
  errorMessage.value = "";
  showToast("Google 로그인 중...");

  try {
    const resp = await fetch(`${BACKEND_BASE}/api/auth/google/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ code })
    });

    const data = await resp.json().catch(() => ({}));

    if (!resp.ok) {
      const detail = data.detail || "Google 로그인에 실패했습니다.";
      errorMessage.value = detail;
      showToast(detail);
      return;
    }

    if (data.access_token) {
      // 프로필은 콜백 응답으로 채우고, 화면은 즉시 이동
      void setSession(data.access_token, {
        user_id: data.user_id,
        email: data.email,
        name: data.name
      });
    }

    const redirectTo = route.query.redirect || "/";
    router.replace({ path: redirectTo, query: {} });
  } catch (err) {
    console.error(err);
    errorMessage.value = "Google 로그인 처리 중 오류가 발생했습니다.";
    showToast(errorMessage.value);
  } finally {
    isHandlingGoogle.value = false;
  }
};

onMounted(() => {
  document.addEventListener("keydown", handleGlobalKeydown);
  void handleGoogleCallback();
});

const handleSubmit = async () => {
  errorMessage.value = "";
  const id = identifier.value.trim();
  const pw = password.value;

  if (!id || !pw) {
    errorMessage.value = "아이디(또는 이메일)와 비밀번호를 입력해 주세요.";
    return;
  }

  try {
    const resp = await fetch(`${BACKEND_BASE}/api/auth/login/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ user_id: id, password: pw })
    });

    const data = await resp.json().catch(() => ({}));

    if (!resp.ok) {
      errorMessage.value = data.detail || "로그인에 실패했습니다.";
      return;
    }

    if (data.access_token) {
      await setSession(data.access_token, {
        user_id: data.user_id,
        email: data.email,
        name: data.name
      });
    }

    const redirectTo = route.query.redirect || "/";
    router.push(redirectTo);
  } catch (err) {
    console.error(err);
    errorMessage.value = "서버와 통신할 수 없습니다. 잠시 후 다시 시도해 주세요.";
  }
};
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap");

.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #e2f0da, #f8f4eb);
  font-family: "Nunito", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #111827;
  display: flex;
  flex-direction: column;
}

.login-header {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 18px 24px;
}

.brand {
  text-decoration: none;
}

.brand-mark {
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 0.18em;
  padding: 6px 18px;
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.1);
  background: rgba(248, 250, 252, 0.86);
  color: #111827;
}

.login-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 16px 56px;
}

.login-card {
  width: 100%;
  max-width: 720px;
  border-radius: 32px;
  background: rgba(248, 250, 252, 0.95);
  border: 1px solid rgba(148, 163, 184, 0.45);
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.24);
  padding: 40px 44px 36px;
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr);
  column-gap: 40px;
  row-gap: 24px;
  position: relative;
  overflow: hidden;
}

.login-card::before {
  content: "";
  position: absolute;
  right: -120px;
  bottom: -140px;
  width: 320px;
  height: 320px;
  background: radial-gradient(circle at 30% 10%, rgba(250, 204, 21, 0.32), transparent 60%),
    radial-gradient(circle at 80% 80%, rgba(148, 222, 180, 0.38), transparent 58%);
  opacity: 0.9;
  filter: blur(1px);
}

.login-copy {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 14px;
}

.eyebrow {
  font-size: 12px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #6b7280;
}

.login-title {
  font-size: 42px;
  font-weight: 800;
  margin: 0;
  letter-spacing: 0.04em;
}

.login-subtitle {
  margin: 4px 0 0;
  font-size: 14px;
  color: #4b5563;
  max-width: 260px;
}

.login-form {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: 13px;
  font-weight: 700;
  color: #374151;
}

.field-shell {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-radius: 999px;
  background: #f9fafb;
  border: 1px solid #d1d5db;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.5);
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

.field-input {
  width: 100%;
  padding: 10px 14px;
  border-radius: 999px;
  border: 1px solid #d1d5db;
  background: #f9fafb;
  font-size: 14px;
  outline: none;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

.field-input--password {
  border: none;
  border-radius: 999px;
  padding: 0 10px;
  background: transparent;
}

.field-input--email {
  border: none;
  border-radius: 999px;
  padding: 0 10px;
  background: transparent;
}

.field-input::placeholder {
  color: #9ca3af;
}

.field-input:focus {
  border-color: #84b091;
  box-shadow: 0 0 0 1px rgba(148, 222, 180, 0.6);
  background: #ffffff;
}

.field-shell:focus-within {
  border-color: #84b091;
  box-shadow: 0 0 0 1px rgba(148, 222, 180, 0.55);
  background: #ffffff;
}

.password-toggle {
  border: none;
  background: transparent;
  padding: 0 0 0 6px;
  cursor: pointer;
  color: #9ca3af;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.18s ease, transform 0.12s ease;
}

.password-toggle:hover {
  color: #4b5563;
  transform: translateY(-1px);
}

.icon {
  width: 16px;
  height: 16px;
}

.submit-button {
  margin-top: 10px;
  padding: 11px 18px;
  border-radius: 999px;
  border: none;
  background: linear-gradient(135deg, #111827, #1f2937);
  color: #f9fafb;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.38);
  transition: transform 0.12s ease, box-shadow 0.12s ease, filter 0.12s ease;
}

.submit-button:hover {
  filter: brightness(1.02);
  transform: translateY(-1px);
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.45);
}

.submit-button:active {
  transform: translateY(1px) scale(0.99);
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.4);
}

.error-text {
  margin-top: 10px;
  font-size: 13px;
  color: #dc2626;
}

.divider {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 12px 0 2px;
  font-size: 11px;
  color: #9ca3af;
}

.divider span {
  flex: 1;
  height: 1px;
  background: #e5e7eb;
}

.helper-row {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 6px;
  margin: 6px 0 4px;
  font-size: 12px;
}

.helper-link.subtle {
  color: #6b7280;
  text-decoration: none;
}

.helper-link.subtle:hover {
  text-decoration: underline;
}

.link-button {
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  font: inherit;
  color: #6b7280;
}

.link-button:hover {
  text-decoration: underline;
}

.divider-dot {
  color: #d1d5db;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.25);
  z-index: 40;
}

.modal-box {
  width: min(520px, 92vw);
  background: #f8f6ee;
  border-radius: 24px;
  padding: 24px 28px 20px;
  box-shadow: 0 22px 50px rgba(15, 23, 42, 0.3);
}

.modal-title {
  margin: 0 0 4px;
  font-size: 20px;
  font-weight: 800;
}

.modal-subtitle {
  margin: 0 0 18px;
  font-size: 13px;
  color: #6b7280;
}

.modal-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.modal-input {
  width: 100%;
  box-sizing: border-box;
  padding: 10px 16px;
  border-radius: 999px;
  border: 1px solid #d1d5db;
  font-size: 14px;
  outline: none;
  background: #f9fafb;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 6px;
}

.modal-button {
  padding: 8px 18px;
  border-radius: 999px;
  border: none;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.modal-button.ghost {
  background: #e5e7eb;
  color: #374151;
}

.modal-button.primary {
  background: #111827;
  color: #f9fafb;
}

.google-button {
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 9px 14px;
  border-radius: 999px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  color: #111827;
  transition: box-shadow 0.14s ease, transform 0.12s ease, border-color 0.14s ease;
}

.google-icon {
  width: 18px;
  height: 18px;
}

.google-button:hover {
  border-color: #d1d5db;
  box-shadow: 0 10px 22px rgba(15, 23, 42, 0.18);
  transform: translateY(-1px);
}

.google-button:active {
  transform: translateY(1px) scale(0.99);
  box-shadow: 0 6px 14px rgba(15, 23, 42, 0.18);
}

.helper {
  margin-top: 10px;
  font-size: 12px;
  color: #6b7280;
  text-align: center;
}

.helper-link {
  margin-left: 4px;
  color: #f48f54;
  text-decoration: none;
  font-weight: 700;
}

.helper-link:hover {
  text-decoration: underline;
}

.toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  background: #111827;
  color: #f9fafb;
  padding: 10px 16px;
  border-radius: 10px;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.25);
  font-size: 14px;
  z-index: 60;
}

.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: opacity 0.18s ease;
}

.toast-fade-enter-from,
.toast-fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .login-card {
    grid-template-columns: 1fr;
    padding: 28px 24px 26px;
    border-radius: 26px;
  }

  .login-subtitle {
    max-width: none;
  }
}

@media (max-width: 480px) {
  .brand-mark {
    font-size: 16px;
    padding: 6px 14px;
  }

  .login-main {
    padding-inline: 12px;
  }

  .login-card {
    padding: 24px 18px 22px;
  }

  .login-title {
    font-size: 32px;
  }
}
</style>
