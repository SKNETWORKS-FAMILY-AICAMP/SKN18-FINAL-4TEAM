<template>
  <div class="live-page">
    <div class="bg-grid"></div>

    <div class="live-hero">
      <div class="hero-text fade-in-up">
        <p class="eyebrow">JobTory Live Coding</p>
        <h1 class="title">
          Let's Start
          <br />
          <span class="highlight">Live Coding Test!</span>
        </h1>
        
        <button type="button" class="start-btn" @click="handleStartClick">
          <span>테스트 시작</span>
          <div class="btn-glow"></div>
        </button>

        <div v-if="showSessionChoice" class="session-choice fade-in">
          <div class="choice-content">
            <p class="choice-msg">진행 중인 세션이 있습니다.</p>
            <div class="session-choice-buttons">
              <button
                type="button"
                class="session-choice-button primary"
                @click="handleResumeSession"
              >
                이어하기
              </button>
              <button
                type="button"
                class="session-choice-button ghost"
                @click="handleStartNewSession"
              >
                새로 시작
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <div class="hero-visual fade-in-up delay-1">
        <img 
          :src="typingLogo" 
          alt="Live coding illustration" 
          class="hero-image floating-anim"
        />
      </div>
    </div>

    <div class="feature-grid fade-in-up delay-2">
      <div class="feature-card">
        <div class="feature-icon icon-one">🖥️</div>
        <div class="feature-content">
          <h3>실전 시험 환경</h3>
          <p>화면 공유와 입력 감지로 현장 같은 테스트</p>
        </div>
      </div>
      <div class="feature-card">
        <div class="feature-icon icon-two">📊</div>
        <div class="feature-content">
          <h3>실전형 문제구성</h3>
          <p>유형·난이도별 맞춤 문제 제공</p>
        </div>
      </div>
      <div class="feature-card">
        <div class="feature-icon icon-three">✅</div>
        <div class="feature-content">
          <h3>자동 채점 시스템</h3>
          <p>상세 리포트로 통합 점수·역량 분석 제공</p>
        </div>
      </div>
    </div>

    <div v-if="showRecommendationModal" class="recommend-modal-overlay" @click.self="closeRecommendationModal">
      <div class="recommend-modal">
        <div class="recommend-modal-header">
          <h3>추천 문제</h3>
          <button type="button" class="recommend-close" @click="closeRecommendationModal">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div class="recommend-body custom-scrollbar">
          <p class="recommend-desc">
            최신 분석 리포트를 기반으로 선정된 맞춤형 문제들입니다.
          </p>
          
          <div v-if="recommendedCandidates.length" class="recommend-grid">
            <article
              v-for="item in recommendedCandidates"
              :key="item.problem_id"
              class="recommend-card"
            >
              <div class="card-top">
                <span class="category-badge">{{ item.category || "Algorithm" }}</span>
                <span class="difficulty-badge" :class="difficultyChipClass(item.difficulty)">
                  {{ item.difficulty || "Normal" }}
                </span>
              </div>

              <h4 class="card-title">
                {{ truncateText(item.title || item.problem, 40) }}
              </h4>

              <div class="card-meta">
                <span class="algo-text" v-if="item.algorithm && item.algorithm.length">
                  ⚡ {{ formatAlgoList(item.algorithm) }}
                </span>
              </div>

              <div class="card-preview custom-scrollbar">
                {{ getProblemPreview(item) }}
              </div>

              <button
                type="button"
                class="card-action-btn"
                @click="startWithRecommendation(item)"
              >
                문제 풀기
              </button>
            </article>
          </div>
          
          <div v-else class="recommend-empty">
            추천 문제를 불러오는 중입니다...
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const typingLogo = new URL("../assets/mainpage_image2.png", import.meta.url).href;
const BACKEND_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

/* ----- Session Logic ----- */
const activeSessionId = ref(null);
const showSessionChoice = ref(false);
const isCheckingActiveSession = ref(false);
const hasCheckedActiveSession = ref(false);
const hasActiveSession = computed(() => !!activeSessionId.value);
const showRecommendationModal = ref(false);
const recommendedCandidates = ref([]);
const isLoadingRecommendations = ref(false);

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

onMounted(async () => {
  const storedSid = localStorage.getItem("jobtory_livecoding_session_id");
  if (storedSid) {
    activeSessionId.value = storedSid;
  }
  const token = localStorage.getItem("jobtory_access_token");
  if (!token) return;
  await loadActiveSession(token);
  
  if (!activeSessionId.value) {
    await loadLatestRecommendation(token);
  }
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
  showRecommendationModal.value = false;
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
    showRecommendationModal.value = false;
    router.push({ name: "coding-settings" });
  } catch (err) {
    console.error(err);
    window.alert("오류가 발생했습니다.");
  } finally {
    showSessionChoice.value = false;
  }
};

const loadLatestRecommendation = async (token) => {
  if (isLoadingRecommendations.value) return;
  isLoadingRecommendations.value = true;
  try {
    const listResp = await fetch(`${BACKEND_BASE}/api/livecoding/reports/`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!listResp.ok) return;
    const listData = await listResp.json().catch(() => ({}));
    const latest = Array.isArray(listData.results) ? listData.results[0] : null;
    if (!latest?.session_id) return;

    const detailResp = await fetch(`${BACKEND_BASE}/api/livecoding/reports/${latest.session_id}/`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!detailResp.ok) return;
    const detailData = await detailResp.json().catch(() => ({}));
    const recs = detailData?.graph_output?.recommended_problems;
    if (Array.isArray(recs) && recs.length) {
      recommendedCandidates.value = recs.slice(0, 3);
      showRecommendationModal.value = true;
    }
  } catch (err) {
    console.error("failed to load recommendation modal", err);
  } finally {
    isLoadingRecommendations.value = false;
  }
};

const closeRecommendationModal = () => {
  showRecommendationModal.value = false;
};

const startWithRecommendation = (item) => {
  const token = localStorage.getItem("jobtory_access_token");
  if (!token) {
    window.alert("라이브 코딩을 시작하려면 먼저 로그인해 주세요.");
    router.push({ name: "login" });
    return;
  }
  if (!item) return;
  sessionStorage.setItem("jobtory_livecoding_problem_data", JSON.stringify(item));
  showRecommendationModal.value = false;
  router.push({ name: "coding-settings", query: { from: "recommendation" } });
};

const formatAlgoList = (algos) => {
  if (!algos) return "";
  if (Array.isArray(algos)) return algos.filter(Boolean).join(", ");
  return String(algos);
};

const getProblemPreview = (item) => {
  const raw = String(
    item?.problem_text || item?.problem_description || item?.description || item?.problem || ""
  ).trim();
  if (!raw) return "문제 요약을 불러오지 못했습니다.";
  const preview = raw.replace(/\s+/g, " ").trim().slice(0, 150);
  return preview + (raw.length > 150 ? "..." : "");
};

const truncateText = (value, max) => {
  const text = String(value || "").replace(/\s+/g, " ").trim();
  if (!text) return "제목 없음";
  return text.length > max ? `${text.slice(0, max)}...` : text;
};

const difficultyChipClass = (value) => {
  const diff = String(value || "").toLowerCase();
  if (diff.includes("easy") || diff.includes("쉬움")) return "chip-easy";
  if (diff.includes("medium") || diff.includes("중간") || diff.includes("normal")) return "chip-medium";
  if (diff.includes("hard") || diff.includes("어려움")) return "chip-hard";
  return "chip-default";
};
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap");
@import url("https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500&display=swap");

.live-page {
  min-height: 81vh;
  padding: 80px 40px 96px;
  background: #0B1120; /* Session Page와 동일한 배경색 */
  color: #e5e7eb;
  font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  display: flex;
  flex-direction: column;
  gap: 64px;
  overflow: hidden;
  position: relative;
}

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

/* ----- Hero Section ----- */
.live-hero {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  align-items: center;
  gap: 40px;
  position: relative;
  z-index: 1;
}

.hero-text {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 20px;
}

.eyebrow {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #38bdf8; /* 스카이블루 포인트 */
  letter-spacing: 0.04em;
  text-transform: uppercase;
  background: rgba(56, 189, 248, 0.1);
  padding: 6px 12px;
  border-radius: 4px;
}

.title {
  margin: 0;
  font-size: 56px;
  line-height: 1.1;
  font-weight: 800;
  color: #fff;
}

.highlight {
  background: linear-gradient(to right, #38bdf8, #818cf8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* Start Button */
.start-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-top: 10px;
  padding: 16px 36px;
  border-radius: 14px;
  background: #ffffff;
  color: #0f172a;
  font-weight: 800;
  font-size: 18px;
  border: none;
  cursor: pointer;
  overflow: hidden;
  transition: transform 0.2s;
  box-shadow: 0 0 20px rgba(56, 189, 248, 0.2);
}

.start-btn span { position: relative; z-index: 2; }

.btn-glow {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  background: linear-gradient(120deg, transparent, rgba(56, 189, 248, 0.4), transparent);
  transform: translateX(-100%);
  transition: 0.6s;
  z-index: 1;
}

.start-btn:hover {
  transform: translateY(-3px) scale(1.02);
}

.start-btn:hover .btn-glow {
  transform: translateX(100%);
}

.hero-visual {
  display: flex;
  justify-content: center;
}

.hero-image {
  width: 100%;
  max-width: 480px;
  height: auto;
  display: block;
  filter: drop-shadow(0 25px 50px rgba(0,0,0,0.5));
}

.floating-anim {
  animation: float 6s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-15px); }
}

/* Feature Grid */
.feature-grid {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  z-index: 1;
}

.feature-card {
  position: relative;
  background: rgba(30, 41, 59, 0.4); /* Glassmorphism */
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  padding: 40px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: flex-start;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  transition: transform 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-5px);
  border-color: rgba(56, 189, 248, 0.3);
}

.feature-icon {
  width: 50px; height: 50px;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 24px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.icon-one { color: #f472b6; }
.icon-two { color: #fbbf24; }
.icon-three { color: #34d399; }

.feature-content h3 {
  margin: 0 0 6px;
  font-size: 18px;
  font-weight: 700;
  color: #fff;
}

.feature-content p {
  margin: 0;
  font-size: 14px;
  color: #9ca3af;
  line-height: 1.5;
}

/* Session Choice */
.session-choice {
  margin-top: 20px;
  padding: 16px 20px;
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(56, 189, 248, 0.3);
  display: inline-block;
  backdrop-filter: blur(8px);
}
.choice-msg { margin: 0 0 10px; font-size: 14px; color: #e5e7eb; }
.session-choice-buttons { display: flex; gap: 10px; }
.session-choice-button {
  padding: 8px 16px; border-radius: 8px; border: none;
  font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s;
}
.session-choice-button.primary { background: #38bdf8; color: #0f172a; }
.session-choice-button.primary:hover { background: #0ea5e9; }
.session-choice-button.ghost { background: transparent; border: 1px solid rgba(255,255,255,0.2); color: #e5e7eb; }
.session-choice-button.ghost:hover { border-color: #fff; color: #fff; }

/* =======================================================
   [추천 문제 모달 - Session Page 테마 적용]
   ======================================================= */

.recommend-modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  z-index: 2000; padding: 20px;
  animation: fadeIn 0.3s ease-out;
}

.recommend-modal {
  width: 100%; max-width: 1000px;
  background: #0B1120; /* 배경 통일 */
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
  display: flex; flex-direction: column;
  max-height: 85vh; overflow: hidden;
  color: #e5e7eb;
  animation: slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.recommend-modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(15, 23, 42, 0.6);
}

.recommend-modal-header h3 {
  margin: 0; font-size: 20px; font-weight: 700; color: #fff;
  letter-spacing: -0.01em;
}

.recommend-close {
  background: transparent; border: 1px solid rgba(255, 255, 255, 0.15);
  color: #9ca3af; border-radius: 6px; padding: 6px;
  cursor: pointer; transition: all 0.2s; display: flex;
}
.recommend-close:hover { color: #fff; border-color: #fff; background: rgba(255,255,255,0.1); }

.recommend-body {
  padding: 24px;
  overflow-y: auto;
  background: #0B1120;
}

.recommend-desc {
  margin: 0 0 24px; font-size: 14px; color: #9ca3af; text-align: center;
}

.recommend-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;
}

/* 문제 카드 스타일 (세션 페이지 패널 스타일) */
.recommend-card {
  background: rgba(30, 41, 59, 0.3); /* 반투명 배경 */
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 20px;
  display: flex; flex-direction: column; gap: 12px;
  transition: all 0.2s ease;
  height: 360px; /* 높이 고정 */
}

.recommend-card:hover {
  transform: translateY(-4px);
  background: rgba(30, 41, 59, 0.6);
  border-color: rgba(56, 189, 248, 0.4); /* 호버 시 네온 블루 */
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
}

.card-top {
  display: flex; justify-content: space-between; align-items: center;
}

.category-badge {
  font-size: 11px; font-weight: 700; color: #38bdf8;
  background: rgba(56, 189, 248, 0.1); padding: 4px 8px; border-radius: 4px;
}

.difficulty-badge {
  font-size: 11px; font-weight: 600; padding: 2px 6px; border-radius: 4px; border: 1px solid transparent;
}
.chip-easy { color: #4ade80; border-color: rgba(74,222,128,0.3); }
.chip-medium { color: #fbbf24; border-color: rgba(251,191,36,0.3); }
.chip-hard { color: #f87171; border-color: rgba(248,113,113,0.3); }
.chip-default { color: #9ca3af; border-color: rgba(156,163,175,0.3); }

.card-title {
  margin: 0; font-size: 16px; font-weight: 700; color: #fff;
  line-height: 1.4; height: 46px; overflow: hidden;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
}

.card-meta {
  font-size: 12px; color: #9ca3af; font-family: "JetBrains Mono", monospace;
}

.card-preview {
  flex: 1; margin: 0;
  background: #020617; /* 에디터 배경색 */
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 8px; padding: 12px;
  font-size: 12px; line-height: 1.6; color: #cbd5e1;
  white-space: pre-wrap; overflow: hidden;
  mask-image: linear-gradient(to bottom, black 60%, transparent 100%);
  -webkit-mask-image: linear-gradient(to bottom, black 60%, transparent 100%);
}

.card-action-btn {
  width: 100%; padding: 12px; border-radius: 8px;
  font-size: 14px; font-weight: 700;
  background: #2563eb; color: #fff; border: none;
  cursor: pointer; transition: all 0.2s;
  margin-top: auto;
}
.card-action-btn:hover { background: #1d4ed8; }

.recommend-empty { padding: 40px; text-align: center; color: #6b7280; }

/* Scrollbar */
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #374151; border-radius: 3px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }

/* Animations */
.fade-in-up { opacity: 0; animation: fadeInUp 0.8s ease-out forwards; }
.fade-in { animation: fadeIn 0.4s ease-out; }
.delay-1 { animation-delay: 0.2s; }
.delay-2 { animation-delay: 0.4s; }

@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideUp { from { transform: translateY(30px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }

@media (max-width: 900px) {
  .live-page { padding: 60px 24px; height: auto; overflow-y: auto; }
  .live-hero { grid-template-columns: 1fr; text-align: center; gap: 40px; }
  .hero-text { align-items: center; }
  .title { font-size: 40px; }
  .recommend-grid { grid-template-columns: 1fr; }
  .recommend-card { height: auto; min-height: 300px; }
}
</style>