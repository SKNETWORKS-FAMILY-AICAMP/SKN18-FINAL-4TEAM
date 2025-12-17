<template>
  <div class="rendering-page">
    <div class="rendering-card">
      <header class="rendering-header">
        <div class="logo-mark">J</div>
        <div class="title-block">
          <h1>JobTory Live Coding</h1>
          <p>최종 리포트를 생성하고 있습니다.</p>
        </div>
      </header>

      <section class="loader-block">
        <div class="loader-ring" aria-label="loading">
          <div class="loader-core"></div>
        </div>

        <p class="loader-main">잠시만 기다려 주세요</p>

        <p class="loader-sub">
          현재 단계: <strong>{{ statusLabel }}</strong>
          <span v-if="statusText" class="status-chip">· {{ statusText }}</span>
        </p>

        <div class="progress-wrap" v-if="steps.length">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
          </div>
          <div class="progress-meta">
            <span>{{ Math.min(currentStepIndex + 1, steps.length) }} / {{ steps.length }}</span>
            <span v-if="lastPolledAt">마지막 확인: {{ lastPolledAt }}</span>
          </div>
        </div>

        <p v-if="errorMessage" class="loader-error">
          {{ errorMessage }}
        </p>

        <div v-if="debug && lastResponse" class="debug-box">
          <div class="debug-title">DEBUG</div>
          <pre class="debug-pre">{{ lastResponse }}</pre>
        </div>
      </section>

      <ul class="step-list">
        <li
          v-for="(step, idx) in steps"
          :key="step.key"
          :class="[
            'step-item',
            { active: idx === currentStepIndex, done: idx < currentStepIndex }
          ]"
        >
          <div class="step-left">
            <span class="step-dot">
              <span v-if="idx < currentStepIndex">✓</span>
              <span v-else>{{ idx + 1 }}</span>
            </span>
            <div class="step-text">
              <div class="step-title">{{ step.label }}</div>
              <div class="step-desc" v-if="step.desc">{{ step.desc }}</div>
            </div>
          </div>

          <span class="step-state">
            <span v-if="idx < currentStepIndex">완료</span>
            <span v-else-if="idx === currentStepIndex">진행 중</span>
            <span v-else>대기</span>
          </span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

// ✅ 프로젝트에 맞게 가져오거나, 없으면 env로 처리
// const BACKEND_BASE = import.meta.env.VITE_BACKEND_BASE || "http://localhost:8000";
const BACKEND_BASE =
  import.meta.env.VITE_BACKEND_BASE ||
  import.meta.env.VITE_BACKEND_URL ||
  "http://localhost:8000";

const router = useRouter();
const route = useRoute();

const sessionId = String(route.query.session_id || "");
const token = localStorage.getItem("jobtory_access_token");

// ===== UI step 정의 (FinalEvalState.step 과 1:1로 맞춤) =====
const steps = [
  { key: "init", label: "평가 준비", desc: "제출 내용을 확인하고 평가를 시작합니다." },
  { key: "code_collab_eval", label: "코드 품질/협업 평가", desc: "코드 스타일/구조/협업 관점 평가 중입니다." },
  { key: "problem_eval", label: "문제 해결 평가", desc: "문제 접근/정확성/복잡도 관점 평가 중입니다." },
  { key: "report_generate", label: "리포트 생성", desc: "최종 리포트를 작성하고 있습니다." },
  { key: "saved", label: "저장 완료", desc: "리포트가 생성되었습니다. 결과 화면으로 이동합니다." },
];

const currentStepIndex = ref(0);
const statusStep = ref("init");
const statusText = ref(""); // running / done / error
const errorMessage = ref("");
const lastPolledAt = ref("");
const lastResponse = ref(""); // debug용

// 개발 중이면 true로 바꾸면 응답 payload를 화면에 표시
const debug = ref(false);

// ===== 폴링 제어 =====
let pollTimer = null;
let inFlight = false;

// 기본 1초 ~ 최대 8초까지 429/backoff 시 증가
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
  const idx = steps.findIndex((s) => s.key === step);
  return idx === -1 ? 0 : idx;
};

const statusLabel = computed(() => {
  const step = statusStep.value || "init";
  if (step === "error") return "오류 발생";
  return steps.find((s) => s.key === step)?.label ?? "평가 준비";
});

const progressPercent = computed(() => {
  if (!steps.length) return 0;
  const idx = Math.min(currentStepIndex.value, steps.length - 1);
  return Math.round(((idx + 1) / steps.length) * 100);
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
  // 네 라우터 이름에 맞게 수정 가능
  router.replace({
    name: "livecoding-report",
    query: { session_id: sessionId },
  });
};

const pollStatus = async () => {
  if (!sessionId) {
    errorMessage.value = "session_id가 없습니다.";
    return;
  }
  if (!token) {
    // 토큰 없으면 로그인으로
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

    // ✅ 429 대응: 폴링 간격을 늘림 (최대 maxIntervalMs)
    if (resp.status === 429) {
      intervalMs.value = Math.min(intervalMs.value * 2, maxIntervalMs);
      schedulePolling();
      return;
    }

    const data = await resp.json().catch(() => ({}));
    if (debug.value) lastResponse.value = JSON.stringify(data, null, 2);

    // 인증 만료/오류
    if (resp.status === 401) {
      return router.replace({ name: "login" });
    }

    if (!resp.ok) {
      // 일시적인 서버 오류면 메시지 노출만 하고 계속 폴링
      errorMessage.value =
        data?.detail || `상태 조회 실패 (HTTP ${resp.status})`;
      return;
    }

    errorMessage.value = "";
    lastPolledAt.value = formatTime(new Date());

    // ===== 상태 반영 =====
    const step = data.step || "init";
    const st = data.status || (step === "saved" ? "done" : "running");

    statusStep.value = step;
    statusText.value = st;

    // 진행 인덱스: 뒤로 가지 않게
    const idx = mapStepToIndex(step);
    currentStepIndex.value = Math.max(currentStepIndex.value, idx);

    // backoff 했다가 정상 응답 오면 다시 기본으로 복귀
    if (intervalMs.value !== baseIntervalMs) {
      intervalMs.value = baseIntervalMs;
      schedulePolling();
    }

    // ===== 종료 조건 =====
    if (step === "saved" && (data.final_report_markdown || data.final_score != null)) {
      currentStepIndex.value = steps.length - 1;
      stopPolling();
      return goToReport();
    }

    // ===== 에러 조건 =====
    if (st === "error" || step === "error") {
      errorMessage.value = data.error || "최종 평가 중 오류가 발생했습니다.";
      stopPolling();
      return;
    }
  } catch (e) {
    // 네트워크 오류 등: 폴링 유지하되 메시지는 보여줌
    errorMessage.value = "서버와 통신 중 오류가 발생했습니다.";
  } finally {
    inFlight = false;
  }
};

onMounted(() => {
  // 최초 1회 즉시 실행 후 폴링 시작
  pollStatus();
  schedulePolling();
});

onBeforeUnmount(() => {
  stopPolling();
});
</script>

<style scoped>
.rendering-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: #0f1115;
  color: #e9e9ea;
}

.rendering-card {
  width: min(860px, 94vw);
  background: rgba(24, 26, 31, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 18px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.45);
  overflow: hidden;
}

.rendering-header {
  display: flex;
  gap: 14px;
  align-items: center;
  padding: 22px 22px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.logo-mark {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-weight: 800;
  background: rgba(255, 255, 255, 0.08);
}

.title-block h1 {
  margin: 0;
  font-size: 18px;
  letter-spacing: -0.2px;
}

.title-block p {
  margin: 4px 0 0;
  font-size: 13px;
  opacity: 0.75;
}

.loader-block {
  padding: 20px 22px 8px;
  text-align: center;
}

.loader-ring {
  width: 64px;
  height: 64px;
  margin: 8px auto 14px;
  border-radius: 999px;
  border: 4px solid rgba(255, 255, 255, 0.12);
  border-top-color: rgba(255, 255, 255, 0.6);
  animation: spin 1s linear infinite;
  position: relative;
}

.loader-core {
  position: absolute;
  inset: 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loader-main {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
}

.loader-sub {
  margin: 8px 0 0;
  font-size: 13px;
  opacity: 0.85;
}

.status-chip {
  display: inline-block;
  margin-left: 8px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  background: rgba(255, 255, 255, 0.08);
  opacity: 0.95;
}

.progress-wrap {
  margin: 14px auto 0;
  width: min(520px, 92%);
}

.progress-bar {
  height: 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: rgba(255, 255, 255, 0.45);
  width: 0%;
  transition: width 240ms ease;
}

.progress-meta {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  opacity: 0.7;
}

.loader-error {
  margin: 14px auto 0;
  max-width: 560px;
  font-size: 13px;
  color: #ffb4b4;
  background: rgba(255, 60, 60, 0.08);
  border: 1px solid rgba(255, 60, 60, 0.18);
  padding: 10px 12px;
  border-radius: 12px;
}

.step-list {
  list-style: none;
  margin: 10px 0 20px;
  padding: 0 22px 22px;
  display: grid;
  gap: 10px;
}

.step-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 14px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.03);
}

.step-item.active {
  border-color: rgba(255, 255, 255, 0.18);
  background: rgba(255, 255, 255, 0.055);
}

.step-item.done {
  opacity: 0.92;
}

.step-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.step-dot {
  width: 28px;
  height: 28px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 800;
  background: rgba(255, 255, 255, 0.08);
  flex: 0 0 auto;
}

.step-text {
  min-width: 0;
  text-align: left;
}

.step-title {
  font-size: 14px;
  font-weight: 750;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.step-desc {
  margin-top: 2px;
  font-size: 12px;
  opacity: 0.68;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.step-state {
  font-size: 12px;
  opacity: 0.7;
  flex: 0 0 auto;
}

.debug-box {
  margin: 16px auto 0;
  width: min(720px, 94%);
  text-align: left;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(0, 0, 0, 0.25);
  border-radius: 12px;
  overflow: hidden;
}

.debug-title {
  padding: 8px 10px;
  font-size: 12px;
  opacity: 0.75;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.debug-pre {
  margin: 0;
  padding: 10px;
  font-size: 12px;
  line-height: 1.4;
  opacity: 0.9;
  overflow: auto;
  max-height: 220px;
}
</style>
