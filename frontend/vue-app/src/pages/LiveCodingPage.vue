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

    <div v-if="showRecommendationModal" class="recommend-modal-overlay" @click.self="closeRecommendationModal">
      <div class="recommend-modal">
        <div class="recommend-modal-header">
          <h3>이번 리포트 추천 문제</h3>
          <button type="button" class="recommend-close" @click="closeRecommendationModal">닫기</button>
        </div>
        <div v-if="recommendedCandidates.length" class="recommend-body">
          <p class="recommend-desc">
            최신 리포트 기반으로 이어서 풀기 좋은 문제입니다. 상위 3개 추천만 노출됩니다.
          </p>
          <div class="recommend-grid">
            <article
              v-for="item in recommendedCandidates"
              :key="item.problem_id"
              class="recommend-card"
            >
              <div class="recommend-title">
                #{{ item.problem_id }} {{ truncateText(item.title || item.problem, 10) }}
              </div>
              <div class="recommend-meta">
                <span class="recommend-chip">{{ item.category || "미분류" }}</span>
                <span class="recommend-chip" :class="difficultyChipClass(item.difficulty)">
                  {{ item.difficulty || "미정" }}
                </span>
              </div>
              <div v-if="item.algorithm && item.algorithm.length" class="recommend-algo">
                {{ formatAlgoList(item.algorithm) }}
              </div>
              <pre class="recommend-snippet">{{ getProblemPreview(item) }}</pre>
              <button
                type="button"
                class="recommend-btn primary"
                @click="startWithRecommendation(item)"
              >
                추천 문제 풀이하기
              </button>
            </article>
          </div>
        </div>
        <div v-else class="recommend-empty">추천 문제를 불러오는 중입니다.</div>
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

/* ----- Session Logic (기존 유지) ----- */
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
  const preview = raw.replace(/\s+/g, " ").trim().slice(0, 200);
  return preview + (raw.length > 200 ? "..." : "");
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

/* 추천 모달 */
.recommend-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(3, 7, 18, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
  padding: 24px;
}

.recommend-modal {
  width: min(980px, 94vw);
  background: #111827;
  color: #e5e7eb;
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: 0 20px 40px rgba(0,0,0,0.4);
  padding: 20px;
  max-height: min(78vh, 720px);
  display: flex;
  flex-direction: column;
}

.recommend-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.recommend-modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
}

.recommend-close {
  background: transparent;
  border: 1px solid rgba(255,255,255,0.15);
  color: #cbd5f5;
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 12px;
  cursor: pointer;
}

.recommend-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-y: auto;
  padding-right: 6px;
}

.recommend-title {
  font-size: 16px;
  font-weight: 600;
}

.recommend-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.recommend-card {
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: 320px;
}

.recommend-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.recommend-algo {
  font-size: 12px;
  color: #a5b4fc;
}

.recommend-snippet {
  margin: 0;
  white-space: normal;
  font-size: 12px;
  line-height: 1.5;
  color: #94a3b8;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 8px;
  padding: 8px 10px;
  flex: 1;
  min-height: 120px;
  max-height: 160px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 8;
  -webkit-box-orient: vertical;
}

.recommend-chip {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 999px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.12);
  color: #cbd5e1;
}

.recommend-chip.chip-easy { color: #4ade80; border-color: rgba(74,222,128,0.4); }
.recommend-chip.chip-medium { color: #facc15; border-color: rgba(250,204,21,0.4); }
.recommend-chip.chip-hard { color: #f87171; border-color: rgba(248,113,113,0.4); }
.recommend-chip.chip-default { color: #cbd5e1; }

.recommend-desc {
  margin: 4px 0 0;
  font-size: 13px;
  color: #9ca3af;
  line-height: 1.5;
}

.recommend-empty {
  font-size: 13px;
  color: #9ca3af;
  padding: 8px 0;
}

.recommend-actions {
  margin-top: 16px;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.recommend-btn {
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 13px;
  border: 1px solid transparent;
  cursor: pointer;
}

.recommend-btn.primary {
  background: #6366f1;
  color: #fff;
}

.recommend-card .recommend-btn.primary {
  align-self: flex-end;
  margin-top: auto;
}

.recommend-btn.ghost {
  background: transparent;
  border-color: rgba(255,255,255,0.2);
  color: #cbd5e1;
}

@media (max-width: 900px) {
  .recommend-grid {
    grid-template-columns: 1fr;
  }
}
</style>
