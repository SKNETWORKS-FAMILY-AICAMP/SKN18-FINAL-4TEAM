<template>
  <div class="login-page">
    <div class="bg-grid"></div>

    <nav class="nav-header">
      <RouterLink to="/" class="brand">JOBTORY</RouterLink>
    </nav>

    <div class="login-container">
      <div class="login-wrapper">
        
        <section class="login-card">
          <div class="login-intro">
            <p class="eyebrow">WELCOME BACK</p>
            <h1 class="login-title">Login to<br>JobTory</h1>
            <p class="login-desc">
              로그인을 통해 면접 준비부터<br>AI 라이브 코딩 테스트까지 경험해 보세요.
            </p>
          </div>

          <div class="login-form-area">
            <form class="login-form" @submit.prevent="handleSubmit">
              
              <div class="form-group">
                <label class="form-label">아이디</label>
                <input
                  class="form-input"
                  v-model="identifier"
                  type="text"
                  placeholder="아이디 또는 이메일"
                  autocomplete="username"
                />
              </div>

              <div class="form-group">
                <label class="form-label">비밀번호</label>
                <div class="password-wrapper">
                  <input
                    class="form-input"
                    v-model="password"
                    :type="showPassword ? 'text' : 'password'"
                    placeholder="비밀번호 입력"
                    autocomplete="current-password"
                  />
                  <button
                    type="button"
                    class="password-toggle"
                    @click="togglePassword"
                    :aria-label="showPassword ? '비밀번호 숨기기' : '비밀번호 보기'"
                  >
                    <svg v-if="!showPassword" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                      <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                    <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                      <line x1="1" y1="1" x2="23" y2="23"></line>
                    </svg>
                  </button>
                </div>
              </div>

              <p v-if="errorMessage" class="error-text">
                {{ errorMessage }}
              </p>

              <button type="submit" class="btn-submit">로그인</button>

              <div class="helper-row">
                <button type="button" class="link-btn" @click="isFindIdOpen = true">아이디 찾기</button>
                <span class="divider-dot">·</span>
                <button type="button" class="link-btn" @click="isFindPasswordOpen = true">비밀번호 찾기</button>
              </div>

              <div class="divider">
                <span>or</span>
              </div>

              <button type="button" class="btn-google" @click="handleGoogleLogin">
                <svg viewBox="0 0 24 24" width="18" height="18" xmlns="http://www.w3.org/2000/svg">
                  <g transform="matrix(1, 0, 0, 1, 27.009001, -39.238998)">
                    <path fill="#4285F4" d="M -3.264 51.509 C -3.264 50.719 -3.334 49.969 -3.454 49.239 L -14.754 49.239 L -14.754 53.749 L -8.284 53.749 C -8.574 55.229 -9.424 56.479 -10.684 57.329 L -10.684 60.329 L -6.824 60.329 C -4.564 58.239 -3.264 55.159 -3.264 51.509 Z"/>
                    <path fill="#34A853" d="M -14.754 63.239 C -11.514 63.239 -8.804 62.159 -6.824 60.329 L -10.684 57.329 C -11.764 58.049 -13.134 58.489 -14.754 58.489 C -17.884 58.489 -20.534 56.379 -21.484 53.529 L -25.464 53.529 L -25.464 56.619 C -23.494 60.539 -19.444 63.239 -14.754 63.239 Z"/>
                    <path fill="#FBBC05" d="M -21.484 53.529 C -21.734 52.809 -21.864 52.039 -21.864 51.239 C -21.864 50.439 -21.734 49.669 -21.484 48.949 L -21.484 45.859 L -25.464 45.859 C -26.284 47.479 -26.754 49.299 -26.754 51.239 C -26.754 53.179 -26.284 54.999 -25.464 56.619 L -21.484 53.529 Z"/>
                    <path fill="#EA4335" d="M -14.754 43.989 C -12.984 43.989 -11.404 44.599 -10.154 45.789 L -6.734 42.369 C -8.804 40.429 -11.514 39.239 -14.754 39.239 C -19.444 39.239 -23.494 41.939 -25.464 45.859 L -21.484 48.949 C -20.534 46.099 -17.884 43.989 -14.754 43.989 Z"/>
                  </g>
                </svg>
                <span>Google 계정으로 로그인</span>
              </button>

              <div class="signup-link">
                계정이 없으신가요? <RouterLink to="/signup" class="link-bold">회원가입 하기</RouterLink>
              </div>
            </form>
          </div>
        </section>
      </div>
    </div>

    <div v-if="isFindIdOpen" class="modal-backdrop" @click.self="closeFindId">
      <div class="modal-box">
        <h2 class="modal-title">아이디 찾기</h2>
        <p class="modal-subtitle">가입 시 등록한 이메일을 입력해 주세요.</p>
        <form @submit.prevent="handleFindId">
          <input v-model="findIdEmail" type="email" class="form-input" placeholder="이메일 입력" />
          <div class="modal-actions">
            <button type="button" class="btn-ghost" @click="closeFindId">취소</button>
            <button type="submit" class="btn-primary">확인</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="isFindPasswordOpen" class="modal-backdrop" @click.self="closeFindPassword">
      <div class="modal-box">
        <h2 class="modal-title">비밀번호 찾기</h2>
        <p class="modal-subtitle">가입 정보를 입력하면 임시 비밀번호를 발송해 드립니다.</p>
        <form class="modal-form" @submit.prevent="handleFindPassword">
          <input v-model="findPwName" type="text" class="form-input" placeholder="이름" />
          <input v-model="findPwUserId" type="text" class="form-input" placeholder="아이디" />
          <input v-model="findPwEmail" type="email" class="form-input" placeholder="이메일" />
          <div class="modal-actions">
            <button type="button" class="btn-ghost" @click="closeFindPassword">취소</button>
            <button type="submit" class="btn-primary">발송</button>
          </div>
        </form>
      </div>
    </div>

    <transition name="toast-fade">
      <div v-if="toastVisible" class="toast">{{ toastMessage }}</div>
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
    if (isFindIdOpen.value) return closeFindId();
    if (isFindPasswordOpen.value) closeFindPassword();
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
const redirectUri =
  import.meta.env.VITE_GOOGLE_REDIRECT_URI ||
  `${window.location.origin}/login`;

const handleGoogleLogin = () => {
  if (!GOOGLE_CLIENT_ID) {
    alert("구글 클라이언트 ID가 설정되지 않았습니다.");
    return;
  }
  const params = new URLSearchParams({
    client_id: GOOGLE_CLIENT_ID,
    redirect_uri: redirectUri,
    response_type: "code",
    scope: "openid email profile",
    access_type: "offline",
    prompt: "consent"
  });
  window.location.href = `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
};

const closeFindId = () => { isFindIdOpen.value = false; findIdEmail.value = ""; };
const handleFindId = async () => {
  // 아이디 찾기 로직 (기존 동일)
  if(!findIdEmail.value) return alert("이메일을 입력해주세요.");
  // ... fetch API ...
  closeFindId();
};

const closeFindPassword = () => {
  isFindPasswordOpen.value = false;
  findPwName.value = ""; findPwUserId.value = ""; findPwEmail.value = "";
};
const handleFindPassword = async () => {
  // 비밀번호 찾기 로직 (기존 동일)
  if(!findPwName.value || !findPwUserId.value || !findPwEmail.value) return alert("모든 정보를 입력해주세요.");
  // ... fetch API ...
  closeFindPassword();
};

const handleGoogleCallback = async () => {
  const code = route.query.code;
  if (!code || isHandlingGoogle.value) return;
  isHandlingGoogle.value = true;
  showToast("Google 로그인 중...");
  
  try {
    const resp = await fetch(`${BACKEND_BASE}/api/auth/google/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code })
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || "로그인 실패");
    
    if (data.access_token) {
      await setSession(data.access_token, {
        user_id: data.user_id, email: data.email, name: data.name
      });
    }
    router.replace({ path: route.query.redirect || "/", query: {} });
  } catch (err) {
    errorMessage.value = err.message;
    showToast(err.message);
  } finally {
    isHandlingGoogle.value = false;
  }
};

onMounted(() => {
  document.addEventListener("keydown", handleGlobalKeydown);
  handleGoogleCallback();
});

const handleSubmit = async () => {
  errorMessage.value = "";
  if (!identifier.value || !password.value) {
    errorMessage.value = "아이디와 비밀번호를 입력해주세요.";
    return;
  }
  
  try {
    const resp = await fetch(`${BACKEND_BASE}/api/auth/login/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: identifier.value, password: password.value })
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || "로그인 실패");
    
    if (data.access_token) {
      await setSession(data.access_token, {
        user_id: data.user_id, email: data.email, name: data.name
      });
    }
    router.push(route.query.redirect || "/");
  } catch (err) {
    errorMessage.value = err.message;
  }
};
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap");

/* 전체 페이지 레이아웃 */
.login-page {
  position: relative;
  width: 100vw;
  height: 100vh;
  background: #f8f4eb;
  font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #111827;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

/* 배경 그리드 패턴 */
.bg-grid {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  z-index: 0;
  background-size: 40px 40px;
  background-image:
    linear-gradient(to right, rgba(0, 0, 0, 0.05) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(0, 0, 0, 0.05) 1px, transparent 1px);
  mask-image: linear-gradient(to bottom, black 40%, transparent 100%);
  pointer-events: none;
}

/* 상단 네비게이션 */
.nav-header {
  position: absolute;
  top: 0; left: 0; width: 100%;
  padding: 24px 40px;
  z-index: 50;
  display: flex;
  align-items: center;
}

.brand {
  font-family: "Inter", sans-serif;
  font-size: 24px;
  font-weight: 900;
  color: #111827;
  text-decoration: none;
  letter-spacing: -0.02em;
  cursor: pointer;
}

.login-container {
  position: relative;
  z-index: 10;
  width: 100%;
  
  /* [수정] 화면 전체 높이를 최소한으로 잡고, 내용이 많으면 스크롤 되도록 */
  min-height: 100vh;
  padding: 10px 10px;
  display: flex;
  justify-content: center;
  align-items: center; /* 수직 중앙 정렬 */
  box-sizing: border-box; /* 패딩 포함 크기 계산 */
  overflow-y: auto; /* 화면보다 카드가 길어지면 스크롤 생김 */
}

.login-wrapper {
  width: 100%;
  max-width: 750px;  
  min-height: 450px;
  animation: fadeUp 0.6s ease-out;
}

/* 로그인 카드 */
.login-card {
  background: #ffffff;
  border-radius: 24px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(0, 0, 0, 0.05);
  display: grid;
  grid-template-columns: 1fr 1fr;
  overflow: hidden; /* 모서리 둥글게 유지 */
  height: 100%; /* wrapper 높이에 맞춤 */
}

/* 왼쪽 인트로 영역 */
.login-intro {
  background: #fdfbf7;
  padding: 60px 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  border-right: 1px solid #f3f4f6;
}

.eyebrow {
  font-size: 13px;
  font-weight: 700;
  color: #9ca3af;
  letter-spacing: 0.05em;
  margin-bottom: 16px;
}

.login-title {
  font-size: 48px;
  font-weight: 900;
  line-height: 1.1;
  color: #111827;
  margin-bottom: 24px;
}

.login-desc {
  font-size: 16px;
  line-height: 1.6;
  color: #4b5563;
}

/* 오른쪽 폼 영역 */
.login-form-area {
  padding: 45px 50px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

/* 입력 필드 스타일 */
.form-input {
  width: 90%;
  height: 48px;
  padding: 0 16px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  font-size: 15px;
  color: #111827;
  outline: none;
  transition: all 0.2s;
}

.form-input:focus {
  background: #fff;
  border-color: #111827;
  box-shadow: 0 0 0 1px #111827;
}

.password-wrapper {
  position: relative;
}

.password-toggle {
  position: absolute;
  right: 0;
  top: 0;
  height: 100%;
  padding: 0 14px;
  background: transparent;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  display: flex;
  align-items: center;
}

.password-toggle:hover {
  color: #4b5563;
}

/* 버튼 스타일 */
.btn-submit {
  width: 100%;
  height: 50px;
  margin-top: 8px;
  border-radius: 999px;
  background: #111827;
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  border: none;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.btn-submit:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0,0,0,0.15);
}

.btn-google {
  width: 100%;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-radius: 999px;
  background: #fff;
  border: 1px solid #e5e7eb;
  font-size: 14px;
  font-weight: 600;
  color: #111827;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-google:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}

/* 유틸리티 링크 */
.helper-row {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  font-size: 13px;
  color: #6b7280;
}

.link-btn {
  background: none;
  border: none;
  color: #6b7280;
  cursor: pointer;
  font-size: 13px;
  padding: 0;
}

.link-btn:hover {
  text-decoration: underline;
}

.divider {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 24px 0;
  position: relative;
}

.divider::before {
  content: "";
  position: absolute;
  top: 50%;
  left: 0;
  width: 100%;
  height: 1px;
  background: #e5e7eb;
  z-index: 0;
}

.divider span {
  background: #fff;
  padding: 0 12px;
  color: #9ca3af;
  font-size: 12px;
  font-weight: 500;
  position: relative;
  z-index: 1;
}

.signup-link {
  margin-top: 24px;
  text-align: center;
  font-size: 14px;
  color: #6b7280;
}

.link-bold {
  color: #111827;
  font-weight: 700;
  text-decoration: underline;
  margin-left: 4px;
}

.error-text {
  color: #dc2626;
  font-size: 13px;
  margin-top: 4px;
}

/* 모달 스타일 */
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.modal-box {
  width: min(440px, 90vw); background: #fff; border-radius: 16px; padding: 32px;
  box-shadow: 0 20px 40px rgba(0,0,0,0.2);
}
.modal-title { font-size: 20px; font-weight: 800; margin-bottom: 8px; }
.modal-subtitle { font-size: 14px; color: #6b7280; margin-bottom: 20px; }
.modal-form { display: flex; flex-direction: column; gap: 12px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 8px; }
.btn-primary { 
  padding: 10px 20px; background: #111827; color: #fff; border-radius: 8px; border: none; font-weight: 600; cursor: pointer; 
}
.btn-ghost { 
  padding: 10px 20px; background: #f3f4f6; color: #374151; border-radius: 8px; border: none; font-weight: 600; cursor: pointer; 
}

/* 토스트 메시지 */
.toast {
  position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%);
  background: #111827; color: #fff; padding: 12px 24px; border-radius: 99px;
  font-size: 14px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); z-index: 200;
}
.toast-fade-enter-active, .toast-fade-leave-active { transition: opacity 0.3s; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; }

/* 애니메이션 */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 모바일 대응 */
@media (max-width: 768px) {
  .nav-header { padding: 20px; justify-content: center; }
  .login-card { grid-template-columns: 1fr; max-width: 480px; }
  .login-intro { padding: 32px 24px; text-align: center; border-right: none; border-bottom: 1px solid #f3f4f6; }
  .login-form-area { padding: 32px 24px; }
  .login-title { font-size: 32px; }
}
</style>
