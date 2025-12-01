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

        <form class="login-form">
          <label class="field">
            <span class="field-label">아이디</span>
            <div class="field-shell">
              <input
                class="field-input field-input--email"
                type="email"
                placeholder="username@gmail.com"
                autocomplete="email"
              />
            </div>
          </label>

          <label class="field">
            <span class="field-label">비밀번호</span>
            <div class="field-shell">
              <input
                class="field-input field-input--password"
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
  </div>
</template>

<script setup>
import { ref } from "vue";
import { RouterLink } from "vue-router";

const showPassword = ref(false);
const togglePassword = () => {
  showPassword.value = !showPassword.value;
};

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;
const BACKEND_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const redirectUri = `${BACKEND_BASE}/api/auth/google/callback`;

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
