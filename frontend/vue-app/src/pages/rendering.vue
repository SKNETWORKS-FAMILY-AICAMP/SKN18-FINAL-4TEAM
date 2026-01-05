<template>
  <div class="rendering-page">
    <div class="bg-grid"></div>
    <div class="bg-glow"></div>

    <div class="rendering-card fade-in-up">
      <header class="rendering-header">
        <div class="brand">
          <span class="logo-icon">⚡</span>
          <span class="logo-text">JOBTORY AI</span>
        </div>
        <div class="session-info">
          <span class="badge">SESSION ENDED</span>
        </div>
      </header>

      <section class="loader-block">
        <div class="visual-area">
          <div class="pulse-ring"></div>
          <div class="icon-box">
            <div class="loader-spinner"></div>
          </div>
        </div>

        <h1 class="status-title">
          {{ statusLabel }}
          <span class="dots">...</span>
        </h1>
        <p class="status-desc">{{ getStepDescription(statusStep) }}</p>

        <div class="progress-container" v-if="steps.length">
          <div class="progress-bar-bg">
            <div class="progress-bar-fill" :style="{ width: progressPercent + '%' }">
              <div class="progress-glow"></div>
            </div>
          </div>
          <div class="progress-info">
            <span class="percentage">{{ progressPercent }}% Completed</span>
            <span class="step-count">Step {{ Math.min(currentStepIndex + 1, steps.length) }} of {{ steps.length }}</span>
          </div>
        </div>

        <p v-if="errorMessage" class="error-msg">
          ⚠️ {{ errorMessage }}
        </p>
      </section>

      <div class="timeline-area">
        <ul class="step-list">
          <li
            v-for="(step, idx) in steps"
            :key="step.key"
            :class="[
              'step-item',
              { 
                'active': idx === currentStepIndex, 
                'done': idx < currentStepIndex,
                'pending': idx > currentStepIndex
              }
            ]"
          >
            <div class="step-marker">
              <div class="line" v-if="idx !== steps.length - 1"></div>
              <div class="dot">
                <span v-if="idx < currentStepIndex" class="check-icon">✔</span>
                <span v-else-if="idx === currentStepIndex" class="loading-dot"></span>
              </div>
            </div>
            <div class="step-content">
              <div class="step-head">
                <span class="step-label">{{ step.label }}</span>
                <span class="step-status-text">
                  {{ idx < currentStepIndex ? '완료' : (idx === currentStepIndex ? '처리 중...' : '대기') }}
                </span>
              </div>
            </div>
          </li>
        </ul>
      </div>

      <div v-if="debug && lastResponse" class="terminal-box">
        <div class="terminal-header">
          <span class="dot red"></span>
          <span class="dot yellow"></span>
          <span class="dot green"></span>
          <span class="terminal-title">Debug Console</span>
        </div>
        <pre class="terminal-body">{{ lastResponse }}</pre>
        <div class="terminal-footer">Last polled: {{ lastPolledAt }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

// ✅ 기존 로직 100% 유지
const BACKEND_BASE =
  import.meta.env.VITE_BACKEND_BASE ||
  import.meta.env.VITE_BACKEND_URL ||
  "http://localhost:8000";

const router = useRouter();
const route = useRoute();

const sessionId = String(route.query.session_id || "");
const token = localStorage.getItem("jobtory_access_token");

const steps = [
  { key: "init", label: "데이터 수집", desc: "제출된 코드와 면접 데이터를 취합하고 있습니다." },
  { key: "code_collab_eval", label: "코드 품질 분석", desc: "코드 스타일, 구조, 효율성을 AI가 분석 중입니다." },
  { key: "problem_eval", label: "문제 해결력 평가", desc: "알고리즘 정확도와 문제 접근 방식을 평가합니다." },
  { key: "report_generate", label: "리포트 생성", desc: "종합 분석 결과를 리포트 형태로 변환합니다." },
  { key: "saved", label: "저장 완료", desc: "모든 분석이 완료되었습니다. 결과 페이지로 이동합니다." },
];

const currentStepIndex = ref(0);
const statusStep = ref("init");
const statusText = ref(""); 
const errorMessage = ref("");
const lastPolledAt = ref("");
const lastResponse = ref(""); 

const debug = ref(false); // 필요시 true로 변경

let pollTimer = null;
let inFlight = false;
const baseIntervalMs = 1000;
const maxIntervalMs = 8000;
const intervalMs = ref(baseIntervalMs);

const mapStepToIndex = (step) => {
    const alias = {
    create_report: "report_generate",
    create_report_node: "report_generate",
    report: "report_generate",
  };
  const normalized = alias[step] || step;
  const idx = steps.findIndex((s) => s.key === normalized); // normalized 사용 수정
  return idx === -1 ? 0 : idx;
};

const statusLabel = computed(() => {
  const step = statusStep.value || "init";
  if (step === "error") return "오류 발생";
  return steps.find((s) => s.key === step)?.label ?? "데이터 분석 중";
});

// 현재 단계의 설명을 가져오는 헬퍼
const getStepDescription = (stepKey) => {
  const step = steps.find(s => s.key === stepKey);
  return step ? step.desc : "잠시만 기다려 주세요.";
};

const progressPercent = computed(() => {
  if (!steps.length) return 0;
  // 저장 완료(saved) 상태면 100% 강제
  if (statusStep.value === 'saved') return 100;
  
  const idx = Math.min(currentStepIndex.value, steps.length);
  // 조금 더 부드러운 진행바를 위해 기본값 + 난수(Fake progress) 대신 정직한 단계별 % 사용
  return Math.round(((idx) / (steps.length - 1)) * 100);
});

const formatTime = (d) => {
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  const ss = String(d.getSeconds()).padStart(2, "0");
  return `${hh}:${mm}:${ss}`;
};

const stopPolling = () => {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = null;
};

const schedulePolling = () => {
  stopPolling();
  pollTimer = setInterval(() => {
    pollStatus();
  }, intervalMs.value);
};

const goToReport = () => {
  setTimeout(() => {
    router.replace({
      name: "livecoding-report",
      query: { session_id: sessionId },
    });
  }, 1000); // 1초 뒤 이동 (100% 바를 보여주기 위함)
};

const pollStatus = async () => {
  if (!sessionId) {
    errorMessage.value = "session_id가 없습니다.";
    return;
  }
  if (!token) {
    return router.replace({ name: "login" });
  }
  if (inFlight) return;
  inFlight = true;

  try {
    const url = `${BACKEND_BASE}/api/livecoding/final-eval/status/?session_id=${encodeURIComponent(
      sessionId
    )}`;

    const resp = await fetch(url, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
    });

    if (resp.status === 429) {
      intervalMs.value = Math.min(intervalMs.value * 2, maxIntervalMs);
      schedulePolling();
      return;
    }

    const data = await resp.json().catch(() => ({}));
    if (debug.value) lastResponse.value = JSON.stringify(data, null, 2);

    if (resp.status === 401) {
      return router.replace({ name: "login" });
    }

    if (!resp.ok) {
      errorMessage.value = data?.detail || `상태 조회 실패 (HTTP ${resp.status})`;
      return;
    }

    errorMessage.value = "";
    lastPolledAt.value = formatTime(new Date());

    const step = data.step || "init";
    const st = data.status || (step === "saved" ? "done" : "running");

    statusStep.value = step;
    statusText.value = st;

    const idx = mapStepToIndex(step);
    currentStepIndex.value = Math.max(currentStepIndex.value, idx);

    if (intervalMs.value !== baseIntervalMs) {
      intervalMs.value = baseIntervalMs;
      schedulePolling();
    }

    if (step === "saved" && (data.final_report_markdown || data.final_score != null)) {
      currentStepIndex.value = steps.length - 1; // 마지막 단계로
      stopPolling();
      return goToReport();
    }

    if (st === "error" || step === "error") {
      errorMessage.value = data.error || "최종 평가 중 오류가 발생했습니다.";
      stopPolling();
      return;
    }
  } catch (e) {
    errorMessage.value = "서버와 통신 중 오류가 발생했습니다.";
  } finally {
    inFlight = false;
  }
};

onMounted(() => {
  pollStatus();
  schedulePolling();
});

onBeforeUnmount(() => {
  stopPolling();
});
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap");
@import url("https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap");

/* --- Layout & Background --- */
.rendering-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0B1120; /* Deep Dark Navy */
  color: #f1f5f9;
  font-family: "Inter", sans-serif;
  position: relative;
  overflow: hidden;
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
}

.bg-glow {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 600px; height: 600px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
  filter: blur(80px);
  pointer-events: none;
}

/* --- Main Card --- */
.rendering-card {
  width: 100%;
  max-width: 600px;
  background: rgba(30, 41, 59, 0.6); /* Glassmorphism */
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 0;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

/* --- Header --- */
.rendering-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 32px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  background: rgba(0, 0, 0, 0.2);
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
}
.logo-icon { font-size: 20px; }
.logo-text { font-family: "JetBrains Mono", monospace; font-weight: 800; font-size: 14px; letter-spacing: 0.05em; color: #fff; }

.badge {
  font-size: 11px;
  font-weight: 700;
  color: #94a3b8;
  background: rgba(255, 255, 255, 0.1);
  padding: 4px 10px;
  border-radius: 99px;
}

/* --- Loader & Status Section --- */
.loader-block {
  padding: 48px 32px 32px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.visual-area {
  position: relative;
  width: 80px; height: 80px;
  margin-bottom: 24px;
  display: flex; align-items: center; justify-content: center;
}

.pulse-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 2px solid rgba(99, 102, 241, 0.3);
  animation: ripple 2s infinite;
}

.icon-box {
  width: 64px; height: 64px;
  background: #1e293b;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  border: 1px solid rgba(99, 102, 241, 0.3);
  box-shadow: 0 0 20px rgba(99, 102, 241, 0.2);
}

.loader-spinner {
  width: 32px; height: 32px;
  border: 3px solid transparent;
  border-top-color: #818cf8;
  border-right-color: #818cf8;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.status-title {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 800;
  color: #fff;
}
.dots { animation: blink 1.5s infinite; }

.status-desc {
  margin: 0 0 32px;
  font-size: 15px;
  color: #94a3b8;
}

/* Progress Bar */
.progress-container { width: 100%; max-width: 400px; }
.progress-bar-bg {
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 99px;
  overflow: hidden;
  margin-bottom: 8px;
}
.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #a855f7);
  border-radius: 99px;
  position: relative;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}
.progress-glow {
  position: absolute; top: 0; right: 0; bottom: 0; width: 100px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
  animation: shimmer 1.5s infinite;
}
.progress-info {
  display: flex; justify-content: space-between;
  font-size: 12px; color: #94a3b8; font-family: "JetBrains Mono", monospace;
}

.error-msg {
  margin-top: 20px;
  color: #f87171;
  font-size: 14px;
  background: rgba(239, 68, 68, 0.1);
  padding: 10px 16px;
  border-radius: 8px;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

/* --- Timeline Area --- */
.timeline-area {
  background: rgba(0, 0, 0, 0.2);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  padding: 24px 40px;
}
.step-list {
  list-style: none; padding: 0; margin: 0;
  display: flex; flex-direction: column; gap: 0; /* gap은 marker line으로 처리 */
}
.step-item {
  display: flex; gap: 20px;
  position: relative;
  padding-bottom: 24px;
}
.step-item:last-child { padding-bottom: 0; }

/* Marker Line */
.step-marker {
  display: flex; flex-direction: column; align-items: center; width: 24px;
}
.line {
  position: absolute; top: 24px; bottom: 0; left: 11px; /* dot center */
  width: 2px; background: rgba(255, 255, 255, 0.1);
}
.step-item.done .line { background: #6366f1; } /* 완료된 라인 색상 */
.step-item:last-child .line { display: none; }

.dot {
  width: 24px; height: 24px; border-radius: 50%;
  background: #1e293b; border: 2px solid rgba(255, 255, 255, 0.2);
  display: flex; align-items: center; justify-content: center;
  z-index: 2; transition: all 0.3s;
}
.step-item.active .dot {
  border-color: #818cf8;
  background: rgba(99, 102, 241, 0.2);
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
}
.step-item.done .dot {
  background: #6366f1; border-color: #6366f1;
}

.check-icon { font-size: 12px; color: #fff; }
.loading-dot {
  width: 8px; height: 8px; background: #818cf8; border-radius: 50%;
  animation: pulse 1.5s infinite;
}

.step-content { flex: 1; padding-top: 2px; }
.step-head { display: flex; justify-content: space-between; align-items: center; }
.step-label { font-size: 14px; font-weight: 600; color: #64748b; transition: color 0.3s; }
.step-item.active .step-label { color: #fff; }
.step-item.done .step-label { color: #cbd5e1; }

.step-status-text {
  font-size: 12px; font-weight: 500; color: #64748b;
}
.step-item.active .step-status-text { color: #818cf8; }
.step-item.done .step-status-text { color: #10b981; }

/* --- Debug Terminal --- */
.terminal-box {
  margin: 20px 32px 32px;
  background: #0f0f12;
  border: 1px solid #333;
  border-radius: 8px;
  font-family: "JetBrains Mono", monospace;
  overflow: hidden;
}
.terminal-header {
  background: #1a1a1d; padding: 8px 12px; display: flex; align-items: center; gap: 6px;
}
.dot { width: 10px; height: 10px; border-radius: 50%; }
.dot.red { background: #ef4444; }
.dot.yellow { background: #f59e0b; }
.dot.green { background: #10b981; }
.terminal-title { margin-left: 8px; font-size: 12px; color: #666; }
.terminal-body {
  padding: 12px; margin: 0; font-size: 11px; color: #22c55e;
  overflow-x: auto; max-height: 150px;
}
.terminal-footer {
  padding: 4px 12px; border-top: 1px solid #222; font-size: 10px; color: #555; text-align: right;
}

/* Animations */
.fade-in-up { animation: fadeInUp 0.6s ease-out; }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
@keyframes spin { to { transform: rotate(360deg); } }
@keyframes shimmer { 0% { transform: translateX(-100%); } 100% { transform: translateX(400%); } }
@keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.5; transform: scale(0.8); } }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
@keyframes ripple { 0% { transform: scale(0.8); opacity: 1; } 100% { transform: scale(1.5); opacity: 0; } }

</style>