<template>
  <div class="live-page">
    
    <div class="live-hero" @mousemove="handleHeroMove" @mouseleave="resetHero">
      <div class="hero-text">
        <p class="eyebrow">JobTory Live Coding</p>
        <h1 class="title">
          Let's Start
          <br />
          Live Coding Test!
        </h1>
        
        <button type="button" class="start-btn" @click="handleStartClick">
          <span>테스트 시작</span>
          <div class="btn-glow"></div>
        </button>

        <div v-if="showSessionChoice" class="session-choice">
          <p>이전에 진행하던 라이브 코딩 세션이 있습니다.</p>
          <div class="session-choice-buttons">
            <button
              type="button"
              class="session-choice-button session-choice-button--primary"
              @click="handleResumeSession"
            >
              이어하기
            </button>
            <button
              type="button"
              class="session-choice-button session-choice-button--ghost"
              @click="handleStartNewSession"
            >
              새로 시작
            </button>
          </div>
        </div>
      </div>
      
      <div class="hero-visual">
        <img 
          ref="heroImageRef"
          :src="typingLogo" 
          alt="Live coding illustration" 
          class="hero-image"
          :style="heroStyle"
        />
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
import { computed, onMounted, ref, reactive } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const typingLogo = new URL("../assets/mainpage_image2.png", import.meta.url).href;
const BACKEND_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

/* ----- Session Logic (기존 유지) ----- */
const activeSessionId = ref(null);
const showSessionChoice = ref(false);
const isCheckingActiveSession = ref(false);
const hasCheckedActiveSession = ref(false);
const hasActiveSession = computed(() => !!activeSessionId.value);

const loadActiveSession = async (token) => {
  if (isCheckingActiveSession.value || hasCheckedActiveSession.value) return;
  isCheckingActiveSession.value = true;
  try {
    const resp = await fetch(`${BACKEND_BASE}/api/livecoding/session/active/`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` }
    });

    if (!resp.ok) {
      activeSessionId.value = null;
      localStorage.removeItem("jobtory_livecoding_session_id");
      return;
    }

    const data = await resp.json().catch(() => ({}));
    if (data && data.session_id) {
      activeSessionId.value = data.session_id;
      localStorage.setItem("jobtory_livecoding_session_id", data.session_id);
    } else {
      activeSessionId.value = null;
      localStorage.removeItem("jobtory_livecoding_session_id");
    }
  } catch (err) {
    console.error("failed to load active livecoding session", err);
  } finally {
    isCheckingActiveSession.value = false;
    hasCheckedActiveSession.value = true;
  }
};

onMounted(() => {
  const storedSid = localStorage.getItem("jobtory_livecoding_session_id");
  if (storedSid) {
    activeSessionId.value = storedSid;
  }
  const token = localStorage.getItem("jobtory_access_token");
  if (!token) return;
  void loadActiveSession(token);
});

const handleStartClick = async () => {
  const token = localStorage.getItem("jobtory_access_token");
  if (!token) {
    window.alert("라이브 코딩을 시작하려면 먼저 로그인해 주세요.");
    router.push({ name: "login" });
    return;
  }
  if (!hasCheckedActiveSession.value) {
    await loadActiveSession(token);
  }
  if (hasActiveSession.value) {
    showSessionChoice.value = true;
    return;
  }
  router.push({ name: "coding-settings" });
};

const handleResumeSession = () => {
  if (!activeSessionId.value) {
    showSessionChoice.value = false;
    return;
  }
  showSessionChoice.value = false;
  router.push({
    name: "coding-session",
    query: { session_id: activeSessionId.value, resume: "1" },
  });
};

const handleStartNewSession = async () => {
  const token = localStorage.getItem("jobtory_access_token");
  if (!token) {
    window.alert("라이브 코딩을 시작하려면 먼저 로그인해 주세요.");
    router.push({ name: "login" });
    return;
  }
  try {
    if (hasActiveSession.value) {
      await fetch(`${BACKEND_BASE}/api/livecoding/session/end/`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      }).catch(() => {});
      activeSessionId.value = null;
      localStorage.removeItem("jobtory_livecoding_session_id");
    }
    router.push({ name: "coding-settings" });
  } catch (err) {
    console.error(err);
    window.alert("오류가 발생했습니다.");
  } finally {
    showSessionChoice.value = false;
  }
};


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
  overflow: hidden; 
}

/* ----- Hero Section ----- */
.live-hero {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  align-items: center;
  gap: 32px;
  perspective: 1000px; /* 3D 효과를 위한 원근감 */
}

.hero-text {
  display: flex;
  flex-direction: column;
  gap: 18px;
  z-index: 10;
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

/* 버튼 스타일 강화 */
.start-btn {
  position: relative;
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
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  overflow: hidden;
  border: none;
  cursor: pointer;
}

.start-btn span {
  position: relative;
  z-index: 2;
}

/* 버튼 내부 글로우 효과 */
.btn-glow {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  background: linear-gradient(120deg, transparent, rgba(255,255,255,0.4), transparent);
  transform: translateX(-100%);
  transition: 0.5s;
  z-index: 1;
}

.start-btn:hover {
  transform: translateY(-4px) scale(1.02);
  box-shadow: 0 20px 30px rgba(0, 0, 0, 0.3);
  background: #fff;
}

.start-btn:hover .btn-glow {
  transform: translateX(100%);
}

.start-btn:active {
  transform: translateY(0) scale(0.98);
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
  filter: drop-shadow(0 20px 40px rgba(0,0,0,0.5));
  will-change: transform;
}

.feature-grid {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 18px;
}

.feature-card {
  position: relative;
  border-radius: 20px;
  padding: 60px 20px;
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 12px;
  align-items: center;
  box-shadow: 0 14px 30px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  color: #111827;
  transition: transform 0.3s ease; /* 기본 호버 움직임 */
}

.feature-card:hover {
  transform: translateY(-5px); /* 깔끔하게 위로 살짝 뜨는 효과만 유지 */
}

.feature-one { background: #f6c7d9; }
.feature-two { background: #f8d46f; }
.feature-three { background: #c5b3f5; }

.feature-icon, .feature-content {
  position: relative;
  z-index: 2;
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
  backdrop-filter: blur(4px);
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

/* ----- Session Choice ----- */
.session-choice {
  margin-top: 16px;
  padding: 14px 18px;
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.85);
  color: #f9fafb;
  display: inline-flex;
  flex-direction: column;
  gap: 8px;
  backdrop-filter: blur(10px);
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.session-choice-buttons {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

.session-choice-button {
  padding: 8px 14px;
  border-radius: 999px;
  border: none;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: transform 0.2s, filter 0.2s;
}

.session-choice-button:hover {
  transform: scale(1.05);
  filter: brightness(1.1);
}

.session-choice-button--primary {
  background: #f97316;
  color: #111827;
}

.session-choice-button--ghost {
  background: transparent;
  border: 1px solid rgba(249, 250, 251, 0.6);
  color: #f9fafb;
}
</style>