<template>
  <div class="live-page">
    <nav class="nav-header">
      <a data-v-7f42e975="" href="/" class="brand">JOBTORY</a>
    </nav>

    <div class="bg-grid"></div>

    <div class="content-wrapper">
      
      <div class="live-hero">
        <div class="hero-text fade-in-up">
          <div class="badge">JobTory Live Coding</div>
          <h1 class="title">
            Ready to<br />
            <span class="highlight">Debug Your Potential?</span>
          </h1>
          <p class="subtitle">
            실전과 동일한 환경에서 당신의 논리를 증명하세요.<br />
            지금 바로 라이브 코딩 테스트를 시작할 수 있습니다.
          </p>
          
          <div class="action-area">
            <button type="button" class="start-btn" @click="handleStartClick">
              <span>테스트 시작하기</span>
              <svg class="arrow-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M5 12h14M12 5l7 7-7 7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
        </div>

        <div class="hero-visual fade-in-up delay-1">
          <div class="glow-orb"></div>
          <img :src="typingLogo" alt="Live coding illustration" class="hero-image floating-anim" />
        </div>
      </div>

      <div class="feature-grid fade-in-up delay-2">
        <div class="feature-card spotlight-card" @mousemove="handleMouseMove">
          <div class="spotlight-overlay"></div>
          <div class="card-content">
            <div class="feature-icon icon-one">🖥️</div>
            <div class="text-group">
              <h3>실전 시험 환경</h3>
              <p>화면 공유와 입력 감지</p>
            </div>
          </div>
        </div>

        <div class="feature-card spotlight-card" @mousemove="handleMouseMove">
          <div class="spotlight-overlay"></div>
          <div class="card-content">
            <div class="feature-icon icon-two">📊</div>
            <div class="text-group">
              <h3>실전형 문제구성</h3>
              <p>직무별 맞춤 알고리즘</p>
            </div>
          </div>
        </div>

        <div class="feature-card spotlight-card" @mousemove="handleMouseMove">
          <div class="spotlight-overlay"></div>
          <div class="card-content">
            <div class="feature-icon icon-three">✅</div>
            <div class="text-group">
              <h3>자동 채점 시스템</h3>
              <p>즉시 결과 및 분석 제공</p>
            </div>
          </div>
        </div>
      </div>

      <Transition name="fade">
        <div v-if="showSessionChoice" class="session-alert-overlay">
          <div class="session-alert-card">
            <div class="alert-content">
              <span class="alert-icon">⚠️</span>
              <div>
                <h4>진행 중인 세션 발견</h4>
                <p>이전 세션을 이어서 진행하시겠습니까?</p>
              </div>
            </div>
            <div class="alert-buttons">
              <button type="button" class="choice-btn resume" @click="handleResumeSession">이어하기</button>
              <button type="button" class="choice-btn new" @click="handleStartNewSession">새로 시작</button>
            </div>
          </div>
        </div>
      </Transition>

    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const typingLogo = new URL("../assets/mainpage_image2.png", import.meta.url).href;
const BACKEND_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

const activeSessionId = ref(null);
const showSessionChoice = ref(false);
const isCheckingActiveSession = ref(false);
const hasCheckedActiveSession = ref(false);

const hasActiveSession = computed(() => !!activeSessionId.value);

// 뒤로가기 함수
const goBack = () => {
  router.back();
};

const handleMouseMove = (e) => {
  const card = e.currentTarget;
  const rect = card.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;
  
  card.style.setProperty("--mouse-x", `${x}px`);
  card.style.setProperty("--mouse-y", `${y}px`);
};

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
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap");
@import url("https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500&display=swap");

.live-page {
  /* [핵심] 한 화면에 꽉 차게 설정 */
  height: 100vh;
  width: 100vw;
  overflow: hidden; /* 스크롤 제거 */
  
  background: #0B1120;
  color: #f8fafc;
  font-family: "Inter", sans-serif;
  position: relative;
  display: flex;
  flex-direction: column;
}

/* 네비게이션 (뒤로가기) */
.nav-header {
  position: absolute;
  top: 32px;
  left: 32px;
  z-index: 100;
}

.brand {
  font-family: "JetBrains Mono", monospace; /* 또는 Inter */
  font-weight: 800;
  font-size: 24px;
  text-decoration: none;
  
  /* 그라데이션 적용 */
  background: linear-gradient(to right, #818cf8, #c084fc);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  
  transition: opacity 0.3s;
}

.brand:hover {
  opacity: 0.8;
}

.back-icon {
  width: 24px;
  height: 24px;
}

/* 배경 그리드 */
.bg-grid {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  background-image: 
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
  z-index: 0;
}

/* 메인 컨텐츠 래퍼: 수직 중앙 정렬 */
.content-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center; /* 수직 중앙 */
  align-items: center;
  padding: 0 5%;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  height: 100%;
  position: relative;
  z-index: 1;
}

/* 히어로 섹션 */
.live-hero {
  display: grid;
  grid-template-columns: 1fr 1fr;
  align-items: center;
  gap: 40px;
  width: 100%;
  margin-bottom: 4vh; /* 하단 카드와의 간격 */
}

/* 텍스트 영역 */
.hero-text {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  position: relative;
}

.badge {
  display: inline-block;
  padding: 6px 12px;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.4);
  color: #818cf8;
  font-family: "JetBrains Mono", monospace;
  font-size: 13px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.title {
  margin: 0 0 16px;
  /* 폰트 크기 반응형 조절 */
  font-size: clamp(36px, 4.5vw, 60px);
  line-height: 1.1;
  font-weight: 900;
  color: #ffffff;
}

.highlight {
  background: linear-gradient(to right, #818cf8, #c084fc);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  margin: 0 0 32px;
  font-size: 16px;
  color: #94a3b8;
  line-height: 1.6;
  max-width: 500px;
}

/* 시작 버튼 */
.start-btn {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  padding: 14px 28px;
  background: #ffffff;
  color: #0f172a;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 0 20px rgba(255, 255, 255, 0.1);
}

.start-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 0 30px rgba(255, 255, 255, 0.25);
  background: #f1f5f9;
}

.arrow-icon { width: 20px; height: 20px; }

/* [수정] 세션 알림창 (Overlay 스타일로 변경) */
.session-alert-overlay {
  position: fixed; /* 화면 전체 기준 */
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.7); /* 배경 어둡게 */
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999; /* 최상단 보장 */
}

.session-alert-card {
  background: #1e293b;
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 24px;
  border-radius: 16px;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
  animation: slideUp 0.3s ease-out;
}

.alert-content {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 24px;
}

.alert-icon {
  font-size: 24px;
}

.alert-content h4 {
  margin: 0 0 4px;
  font-size: 16px;
  color: #fff;
  font-weight: 700;
}

.alert-content p {
  margin: 0;
  font-size: 14px;
  color: #94a3b8;
  line-height: 1.5;
}

.alert-buttons {
  display: flex;
  gap: 12px;
}

.choice-btn {
  flex: 1;
  padding: 10px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: background 0.2s;
}

.choice-btn.resume {
  background: #6366f1;
  color: white;
}
.choice-btn.resume:hover {
  background: #4f46e5;
}

.choice-btn.new {
  background: transparent;
  border: 1px solid #475569;
  color: #cbd5e1;
}
.choice-btn.new:hover {
  border-color: #94a3b8;
  color: #fff;
  background: rgba(255, 255, 255, 0.05);
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

/* 이미지 영역 */
.hero-visual {
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
}

.glow-orb {
  position: absolute;
  width: 60%;
  padding-bottom: 60%; /* 정사각형 비율 */
  background: radial-gradient(circle, rgba(99, 102, 241, 0.3) 0%, transparent 70%);
  filter: blur(50px);
  z-index: -1;
  animation: pulse 4s infinite ease-in-out;
}

.hero-image {
  width: 100%;
  max-width: 420px; /* 크기 약간 축소하여 한 화면에 맞춤 */
  max-height: 40vh; /* 높이 제한 */
  height: auto;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
  object-fit: contain;
}

/* 기능 소개 그리드 (가로 배치로 변경) */
.feature-grid {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(3, 1fr); /* 3열 고정 */
  gap: 20px;
}

/* Spotlight Card (Compact Version) */
.feature-card {
  background: rgba(30, 41, 59, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 24px 20px; /* 패딩 축소 */
  position: relative;
  overflow: hidden;
  transition: transform 0.3s ease;
  cursor: default;
}

.feature-card:hover {
  transform: translateY(-4px);
  border-color: rgba(255, 255, 255, 0.2);
}

.card-content {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 16px;
}

.feature-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
}

.icon-one { background: rgba(244, 63, 94, 0.1); border: 1px solid rgba(244, 63, 94, 0.3); }
.icon-two { background: rgba(234, 179, 8, 0.1); border: 1px solid rgba(234, 179, 8, 0.3); }
.icon-three { background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); }

.text-group h3 {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 700;
  color: #fff;
}

.text-group p {
  margin: 0;
  font-size: 13px;
  color: #94a3b8;
  line-height: 1.4;
}

.spotlight-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  pointer-events: none;
  background: radial-gradient(
    400px circle at var(--mouse-x) var(--mouse-y),
    rgba(255, 255, 255, 0.06),
    transparent 40%
  );
  opacity: 0;
  transition: opacity 0.3s;
}
.feature-card:hover .spotlight-overlay { opacity: 1; }

/* Animations */
.fade-in-up { opacity: 0; animation: fadeInUp 0.8s ease-out forwards; }
.delay-1 { animation-delay: 0.2s; }
.delay-2 { animation-delay: 0.4s; }

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

@keyframes pulse {
  0%, 100% { opacity: 0.4; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.1); }
}

/* 반응형 처리 */
@media (max-width: 900px) {
  .live-page {
    height: auto; /* 모바일에서는 스크롤 허용 */
    overflow-y: auto;
    padding: 80px 20px;
  }
  .live-hero { grid-template-columns: 1fr; text-align: center; gap: 40px; }
  .hero-text { align-items: center; }
  .feature-grid { grid-template-columns: 1fr; }
  .hero-image { max-width: 300px; }
  
  /* 모바일 알림창 조정 */
  .session-alert-overlay { padding: 20px; }
  .session-alert-card { width: 100%; }
}
</style>