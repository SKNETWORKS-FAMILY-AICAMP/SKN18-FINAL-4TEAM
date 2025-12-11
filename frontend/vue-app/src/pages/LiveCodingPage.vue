<template>
  <div class="live-page">
    <div class="live-hero">
      <div class="hero-text">
        <p class="eyebrow">JobTory Live Coding</p>
        <h1 class="title">
          Let's Start
          <br />
          Live Coding Test!
        </h1>
        <button type="button" class="start-btn" @click="handleStartClick">테스트 시작</button>
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
        <img :src="typingLogo" alt="Live coding illustration" class="hero-image" />
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
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { RouterLink } from "vue-router";

const router = useRouter();
const typingLogo = new URL("../assets/mainpage_image2.png", import.meta.url).href;
const BACKEND_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

const activeSessionId = ref(null);
const showSessionChoice = ref(false);
const isCheckingActiveSession = ref(false);
const hasCheckedActiveSession = ref(false);

const hasActiveSession = computed(() => !!activeSessionId.value);

const resetLivecodingCaches = () => {
  sessionStorage.removeItem("jobtory_intro_tts_text");
  sessionStorage.removeItem("jobtory_intro_tts_audio");
  sessionStorage.removeItem("jobtory_livecoding_problem_data");
  localStorage.removeItem("jobtory_livecoding_session_id");
  localStorage.removeItem("jobtory_langgraph_id");
};

const loadActiveSession = async (token) => {
  if (isCheckingActiveSession.value || hasCheckedActiveSession.value) return;
  isCheckingActiveSession.value = true;
  try {
    const resp = await fetch(`${BACKEND_BASE}/api/livecoding/session/active/`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    if (!resp.ok) {
      // 서버 기준으로는 진행 중인 세션이 없으므로
      // 로컬에 남아 있는 세션 정보도 정리합니다.
      activeSessionId.value = null;
      localStorage.removeItem("jobtory_livecoding_session_id");
      return;
    }

    const data = await resp.json().catch(() => ({}));
    if (data && data.session_id) {
      activeSessionId.value = data.session_id;
      localStorage.setItem("jobtory_livecoding_session_id", data.session_id);
    } else {
      // 정상 응답이지만 session_id가 없으면 역시
      // 유효한 진행 중 세션이 없다고 보고 정리합니다.
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

  // 아직 진행 중 세션 여부를 체크하지 않았으면 한 번 확인하고 시작합니다.
  if (!hasCheckedActiveSession.value) {
    await loadActiveSession(token);
  }

  // 이미 진행 중인 세션이 있으면 이어하기/새로하기 선택 UI를 보여줍니다.
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
  router.push({ name: "coding-session", query: { session_id: activeSessionId.value } });
};

const handleStartNewSession = async () => {
  const token = localStorage.getItem("jobtory_access_token");
  if (!token) {
    window.alert("라이브 코딩을 시작하려면 먼저 로그인해 주세요.");
    router.push({ name: "login" });
    return;
  }

  try {
    // 기존 진행 중인 세션이 있으면 종료 요청
    if (hasActiveSession.value) {
      await fetch(`${BACKEND_BASE}/api/livecoding/session/end/`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`
        }
      }).catch(() => {});
      activeSessionId.value = null;
      resetLivecodingCaches();
    }

    // 혹시 남아 있는 캐시를 정리하고 완전 새로 시작
    resetLivecodingCaches();

    router.push({ name: "coding-settings" });
  } catch (err) {
    console.error(err);
    window.alert("새로운 라이브 코딩 세션을 시작하는 중 오류가 발생했습니다.");
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
}

.live-hero {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  align-items: center;
  gap: 32px;
}

.hero-text {
  display: flex;
  flex-direction: column;
  gap: 18px;
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

.start-btn {
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
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.18);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.start-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 32px rgba(0, 0, 0, 0.22);
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
}

.feature-grid {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 18px;
}

.feature-card {
  border-radius: 20px;
  padding: 60px 20px;
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 12px;
  align-items: center;
  box-shadow: 0 14px 30px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(0, 0, 0, 0.06);
  color: #111827;
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

.feature-one {
  background: #f6c7d9;
}

.feature-two {
  background: #f8d46f;
}

.feature-three {
  background: #c5b3f5;
}

.session-choice {
  margin-top: 16px;
  padding: 14px 18px;
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.85);
  color: #f9fafb;
  display: inline-flex;
  flex-direction: column;
  gap: 8px;
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

@media (max-width: 640px) {
  .live-page {
    padding: 56px 20px 80px;
  }

  .title {
    font-size: 38px;
  }

  .start-btn {
    width: fit-content;
  }
}

.tts-test-footer {
  margin-top: 16px;
  padding: 24px 0 40px;
  border-top: 1px dashed rgba(248, 250, 252, 0.25); /* 연한 흰색 점선 */
  display: flex;
  justify-content: center;
}

.tts-test-button {
  padding: 8px 18px;
  border-radius: 999px;
  border: 1px solid rgba(248, 250, 252, 0.6);
  background: transparent;
  color: #f8fafc;
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
}

.tts-test-button:hover {
  background: #f8fafc;
  color: #111827;
}
</style>
