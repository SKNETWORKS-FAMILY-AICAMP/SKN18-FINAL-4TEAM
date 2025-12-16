<template>
  <div class="page">
    <div class="card">
      <header class="header">
        <div class="logo">J</div>
        <div class="title">
          <h1>JobTory Live Coding</h1>
          <p>최종 리포트</p>
        </div>

        <div class="actions">
          <button class="btn" @click="reload" :disabled="loading">새로고침</button>
          <button class="btn primary" @click="downloadPdf" :disabled="loading || !reportMarkdown">
            PDF 다운로드
          </button>
        </div>
      </header>

      <section v-if="loading" class="status">
        <div class="spinner" aria-label="loading"></div>
        <p>리포트를 불러오는 중입니다…</p>
      </section>

      <section v-else-if="error" class="status error">
        <p class="error-title">리포트를 불러오지 못했습니다.</p>
        <p class="error-msg">{{ error }}</p>
      </section>

      <section v-else class="content">
        <div class="summary">
          <div class="badge" :data-grade="gradeSafe">
            <div class="badge-grade">{{ gradeSafe }}</div>
            <div class="badge-label">GRADE</div>
          </div>

          <div class="metrics">
            <div class="metric">
              <div class="k">점수</div>
              <div class="v">{{ scoreText }}</div>
            </div>
            <div class="metric">
              <div class="k">세션</div>
              <div class="v mono">{{ sessionId }}</div>
            </div>
            <div class="metric">
              <div class="k">상태</div>
              <div class="v">{{ statusText }}</div>
            </div>
            <div class="metric">
              <div class="k">단계</div>
              <div class="v">{{ stepText }}</div>
            </div>
          </div>
        </div>

        <!-- ✅ PDF로 뽑을 영역 -->
        <div ref="pdfTarget" class="report-wrap">
          <article class="report" v-html="reportHtml"></article>
        </div>

        <!-- ✅ LangGraph 최종 output 전체 출력 -->
        <details class="debug" open>
          <summary>LangGraph 최종 Output (graph_output)</summary>
          <pre class="pre">{{ prettyGraphOutput }}</pre>
        </details>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import MarkdownIt from "markdown-it";
import html2pdf from "html2pdf.js";

const BACKEND_BASE =
  import.meta.env.VITE_BACKEND_BASE ||
  import.meta.env.VITE_BACKEND_URL ||
  "http://localhost:8000";

const route = useRoute();
const router = useRouter();

const sessionId = String(route.query.session_id || "");
const token = localStorage.getItem("jobtory_access_token");

const loading = ref(false);
const error = ref("");

const status = ref("");
const step = ref("");
const reportMarkdown = ref("");
const finalScore = ref(null);
const finalGrade = ref(null);

// ✅ LangGraph 최종 output 전체 저장
const graphOutput = ref({});

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
});

const gradeSafe = computed(() => String(finalGrade.value || "-"));
const scoreText = computed(() => {
  if (finalScore.value === null || finalScore.value === undefined) return "-";
  const n = Number(finalScore.value);
  if (Number.isNaN(n)) return String(finalScore.value);
  return n.toFixed(2);
});

const statusText = computed(() => status.value || "-");
const stepText = computed(() => step.value || "-");

const reportHtml = computed(() => {
  const src = reportMarkdown.value || "";
  if (!src.trim()) {
    return `<p style="opacity:.75">리포트 본문이 비어있습니다.</p>`;
  }
  return md.render(src);
});

const prettyGraphOutput = computed(() => {
  try {
    return JSON.stringify(graphOutput.value || {}, null, 2);
  } catch {
    return String(graphOutput.value || "");
  }
});

const fetchReport = async () => {
  if (!sessionId) {
    error.value = "session_id가 없습니다.";
    return;
  }
  if (!token) {
    router.replace({ name: "login" });
    return;
  }

  loading.value = true;
  error.value = "";

  try {
    const url = `${BACKEND_BASE}/api/livecoding/final-eval/report/?session_id=${encodeURIComponent(sessionId)}`;
    const resp = await fetch(url, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
    });

    const data = await resp.json().catch(() => ({}));

    if (resp.status === 401) {
      router.replace({ name: "login" });
      return;
    }
    if (!resp.ok) {
      error.value = data?.detail || `HTTP ${resp.status}`;
      return;
    }

    status.value = data.status || "";
    step.value = data.step || "";

    reportMarkdown.value = data.final_report_markdown || "";
    finalScore.value = data.final_score ?? null;
    finalGrade.value = data.final_grade ?? null;

    // ✅ 최종 output 전체
    graphOutput.value = data.graph_output || {};
  } catch (e) {
    error.value = "서버와 통신 중 오류가 발생했습니다.";
  } finally {
    loading.value = false;
  }
};

const reload = () => fetchReport();

// PDF 다운로드
const pdfTarget = ref(null);
const downloadPdf = async () => {
  if (!pdfTarget.value) return;

  const opt = {
    margin: 10,
    filename: `JobTory_Report_${sessionId}.pdf`,
    image: { type: "jpeg", quality: 0.98 },
    html2canvas: { scale: 2, useCORS: true },
    jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
  };

  await html2pdf().set(opt).from(pdfTarget.value).save();
};

onMounted(() => {
  fetchReport();
});
</script>

<style scoped>
.page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: #0f1115;
  color: #e9e9ea;
}
.card {
  width: min(980px, 96vw);
  background: rgba(24, 26, 31, 0.92);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 18px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.45);
  overflow: hidden;
}
.header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.logo {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-weight: 800;
  background: rgba(255,255,255,0.08);
}
.title h1 {
  margin: 0;
  font-size: 18px;
  letter-spacing: -0.2px;
}
.title p {
  margin: 4px 0 0;
  font-size: 13px;
  opacity: 0.75;
}
.actions {
  margin-left: auto;
  display: flex;
  gap: 10px;
}
.btn {
  border: 1px solid rgba(255,255,255,0.14);
  background: rgba(255,255,255,0.06);
  color: #e9e9ea;
  padding: 8px 12px;
  border-radius: 12px;
  cursor: pointer;
  font-size: 13px;
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn.primary {
  background: rgba(255,255,255,0.16);
  border-color: rgba(255,255,255,0.24);
}

.status {
  padding: 30px 20px;
  text-align: center;
}
.status.error {
  color: #ffb4b4;
}
.spinner {
  width: 48px;
  height: 48px;
  margin: 0 auto 12px;
  border-radius: 999px;
  border: 4px solid rgba(255,255,255,0.12);
  border-top-color: rgba(255,255,255,0.6);
  animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.content {
  padding: 18px 20px 24px;
}
.summary {
  display: grid;
  grid-template-columns: 130px 1fr;
  gap: 14px;
  align-items: center;
  margin-bottom: 14px;
}
.badge {
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.05);
  padding: 14px 12px;
  text-align: center;
}
.badge-grade {
  font-size: 36px;
  font-weight: 900;
  line-height: 1;
}
.badge-label {
  margin-top: 6px;
  font-size: 12px;
  opacity: 0.7;
  letter-spacing: 0.12em;
}
.metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}
.metric {
  border: 1px solid rgba(255,255,255,0.06);
  background: rgba(255,255,255,0.03);
  border-radius: 14px;
  padding: 10px 12px;
}
.metric .k {
  font-size: 12px;
  opacity: 0.7;
}
.metric .v {
  margin-top: 4px;
  font-size: 14px;
  font-weight: 700;
}
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }

.report-wrap {
  margin-top: 12px;
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(0,0,0,0.20);
  overflow: hidden;
}
.report {
  padding: 18px 18px;
  line-height: 1.7;
  font-size: 14px;
}
.report :deep(h1) { font-size: 22px; margin: 0 0 10px; }
.report :deep(h2) { font-size: 18px; margin: 18px 0 8px; }
.report :deep(h3) { font-size: 16px; margin: 14px 0 8px; }
.report :deep(code) {
  background: rgba(255,255,255,0.08);
  padding: 2px 6px;
  border-radius: 8px;
}
.report :deep(pre) {
  background: rgba(0,0,0,0.35);
  padding: 12px;
  border-radius: 14px;
  overflow: auto;
}
.report :deep(a) { color: inherit; opacity: .95; text-decoration: underline; }

.debug {
  margin-top: 14px;
  border-radius: 14px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(0,0,0,0.22);
  overflow: hidden;
}
.debug summary {
  cursor: pointer;
  padding: 10px 12px;
  font-size: 13px;
  opacity: 0.85;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.pre {
  margin: 0;
  padding: 12px;
  font-size: 12px;
  line-height: 1.45;
  max-height: 320px;
  overflow: auto;
  opacity: 0.92;
}
</style>
