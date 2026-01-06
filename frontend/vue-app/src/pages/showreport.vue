<template>
  <div class="page">
    <div class="bg-pattern"></div>
    <div class="card">
      <header class="header">
        <div class="header-left">
          <div class="brand">JOBTORY REPORT</div>
          <div class="divider"></div>
          <div class="session-info">SESSION #{{ sessionId.slice(0, 8) }}</div>
        </div>
        <div class="actions">
          <button class="btn ghost" @click="goHome" :disabled="loading">초기 화면</button>
          <button class="btn ghost" @click="reload" :disabled="loading">새로고침</button>
          <button class="btn primary" @click="downloadPdf" :disabled="loading || !reportMarkdown">
            PDF 내보내기
          </button>
        </div>
      </header>

      <section v-if="loading" class="status-container">
        <div class="loader-ring"></div>
        <p class="status-text">분석 결과를 불러오는 중입니다...</p>
      </section>

      <section v-else-if="error" class="status-container error">
        <div class="error-icon">!</div>
        <p class="error-title">리포트 로드 실패</p>
        <p class="error-desc">{{ error }}</p>
        <button class="btn ghost" @click="reload">다시 시도</button>
      </section>

      <section v-else class="content custom-scrollbar">
        <div ref="pdfTarget" class="report-body">
          
          <div class="summary-section">
            <h2 class="section-heading">Evaluation Summary</h2>
            <div class="summary-grid">
              <div class="grade-card" :data-grade="gradeSafe">
                <div class="grade-label">FINAL GRADE</div>
                <div class="grade-value">{{ gradeSafe }}</div>
              </div>
              <div class="score-card total">
                <div class="score-label">Total Score</div>
                <div class="score-value">{{ finalScoreText }}</div>
                <div class="score-bar-bg">
                  <div class="score-bar-fill" :style="{ width: finalScoreText + '%' }"></div>
                </div>
              </div>
              <div class="detail-scores">
                <div class="detail-item">
                  <span class="label">문제 해결</span>
                  <span class="value">{{ problemSolvingScoreText }}</span>
                  <div class="mini-bar"><div class="fill" :style="{ width: problemSolvingScoreText + '%' }"></div></div>
                </div>
                <div class="detail-item">
                  <span class="label">코드 품질</span>
                  <span class="value">{{ codeQualityScoreText }}</span>
                  <div class="mini-bar"><div class="fill" :style="{ width: codeQualityScoreText + '%' }"></div></div>
                </div>
                <div class="detail-item">
                  <span class="label">협업 능력</span>
                  <span class="value">{{ collaborationScoreText }}</span>
                  <div class="mini-bar"><div class="fill" :style="{ width: collaborationScoreText + '%' }"></div></div>
                </div>
              </div>
            </div>
          </div>

          <div class="feedback-section">
            <div class="feedback-grid">
              <div class="feedback-col strength">
                <div class="col-header">Strength</div>
                <div class="col-body" v-html="strengthTextHtml2"></div>
              </div>
              <div class="feedback-col improvement">
                <div class="col-header">Improvement</div>
                <div class="col-body" v-html="improvementTextHtml2"></div>
              </div>
            </div>
          </div>

          <div v-if="hasCheatingWarning || antiCheatSummary" class="alert-section">
            <h3 class="alert-header">Detection Log</h3>
            <div v-if="hasCheatingWarning" class="alert-box warning">
              <div class="alert-title">경고 알림</div>
              <div class="alert-desc">{{ cheatingWarningText }}</div>
            </div>
            <div v-if="antiCheatSummary" class="alert-grid">
              <div class="alert-item">
                <span class="label">Camera Events</span>
                <span class="val">{{ antiCheatSummary.camera?.count || 0 }}</span>
              </div>
              <div class="alert-item">
                <span class="label">Input Events</span>
                <span class="val">{{ antiCheatSummary.typing?.count || 0 }}</span>
              </div>
            </div>
          </div>

          <div class="comment-section">
            <h3 class="sub-heading">Comprehensive Review</h3>
            <div class="text-block">{{ comprehensiveEvaluationText }}</div>
          </div>

          <div class="recommend-section">
            <h3 class="sub-heading">Recommended Problems</h3>
            <p class="recommend-desc">이번 리포트 기준으로 바로 이어서 풀어볼 수 있는 문제입니다.</p>
            <div v-if="!recommendedProblems.length" class="recommend-empty">
              아직 추천 문제가 없습니다.
            </div>
            <div v-else class="recommend-grid">
              <article v-for="item in recommendedProblems" :key="item.problem_id" class="recommend-card">
                <div class="recommend-title">#{{ item.problem_id }} {{ item.problem }}</div>
                <div class="recommend-meta">
                  <span class="recommend-chip">{{ item.category || "미분류" }}</span>
                  <span class="recommend-chip" :class="difficultyChipClass(item.difficulty)">
                    {{ item.difficulty || "미정" }}
                  </span>
                </div>
                <div v-if="item.algorithm && item.algorithm.length" class="recommend-algos">
                  {{ formatAlgoList(item.algorithm) }}
                </div>
              </article>
            </div>
          </div>

          <hr class="divider-line" />

          <div class="analysis-section">
            <h2 class="section-heading">Problem Solving Analysis</h2>
            
            <div class="problem-info-card">
              <div class="info-row">
                <span class="info-label">Problem</span>
                <span class="info-val title">{{ problemData?.title || "Untitled Problem" }}</span>
              </div>
              <div class="info-meta">
                <span class="tag">{{ problemCategory }}</span>
                <span class="tag difficulty" :class="difficultyClass">{{ problemDifficulty }}</span>
              </div>
              <div class="info-desc">
                {{ extractProblemDescription(graphOutput.problem_text || 'Loading problem details...') }}
              </div>
              <div v-if="displayedTestCases.length" class="testcases-mini">
                 <div v-for="tc in displayedTestCases" :key="tc.id" class="tc-row">
                    <code>Input: {{ tc.input }}</code> <span>→</span> <code>Output: {{ tc.output }}</code>
                 </div>
              </div>
            </div>

            <div class="analysis-grid">
              <div class="analysis-card">
                <div class="card-head">Initial Strategy</div>
                <div class="card-body">{{ initialStrategyAnswer }}</div>
              </div>
              <div class="analysis-card">
                <div class="card-head">Evaluation Metrics</div>
                <div class="metrics-list">
                  <div class="metric-row">
                    <span class="m-label">이해도</span>
                    <span class="m-val" :class="problemUnderstandingClass">{{ problemUnderstandingText }}</span>
                  </div>
                  <div class="metric-row">
                    <span class="m-label">접근법</span>
                    <span class="m-val" :class="approachValidityClass">{{ approachValidityText }}</span>
                  </div>
                  <div class="metric-row">
                    <span class="m-label">일관성</span>
                    <span class="m-val" :class="consistencyClass">{{ consistencyText }}</span>
                  </div>
                </div>
                <div class="metric-feedback">{{ problemUnderstandingFeedback }}</div>
              </div>
            </div>

            <div v-if="qaHistory && qaHistory.length > 0" class="qa-section">
              <h3 class="sub-heading">Interview Log</h3>
              <div class="qa-timeline">
                <div v-for="(qa, idx) in qaHistory" :key="idx" class="qa-entry">
                  <div class="qa-q">
                    <span class="marker">Q{{ idx + 1 }}</span>
                    {{ qa.question }}
                  </div>
                  <div class="qa-a">{{ qa.answer }}</div>
                </div>
              </div>
            </div>
          </div>

          <hr class="divider-line" />

          <div class="code-section">
            <h2 class="section-heading">Code Review</h2>
            <div class="code-box">
              <pre><code>{{ annotatedCode }}</code></pre>
            </div>
          </div>

        </div> 
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import html2pdf from "html2pdf.js";

const BACKEND_BASE =
  import.meta.env.VITE_BACKEND_BASE ||
  import.meta.env.VITE_BACKEND_URL ||
  "http://localhost:8000";

const route = useRoute();
const router = useRouter();

const goHome = () => {
  router.replace({ path: "/" });
};

const sessionId = String(route.query.session_id || "");
const token = localStorage.getItem("jobtory_access_token");

const loading = ref(false);
const error = ref("");

const status = ref("");
const step = ref("");
const reportMarkdown = ref("");
const finalScore = ref(null);
const finalGrade = ref(null);
const problemData = ref(null);
const problemText = ref("");
const latestCode = ref("");
const recommendedProblems = ref([]);

const codeQualityScore = ref(null);
const problemSolvingScore = ref(null);
const collaborationScore = ref(null);

const strengthText = ref("");
const improvementText = ref("");

const displayedTestCases = computed(() => {
  if (!problemData.value?.test_cases?.length) return [];
  return problemData.value.test_cases.slice(0, 2);
});

const strengthTextHtml = computed(() => {
  const s = (strengthText.value || "").trim();
  if (!s) return "";
  return s.replace(/(^|\n)\s*-\s*/g, "$1- ").replace(/\n/g, "<br>");
});

const improvementTextHtml = computed(() => {
  const s = (improvementText.value || "").trim();
  if (!s) return "";
  return s.replace(/(^|\n)\s*-\s*/g, "$1- ").replace(/\n/g, "<br>");
});

const codeQualityScoreText = computed(() => {
  if (codeQualityScore.value === null || codeQualityScore.value === undefined) return "-";
  const n = Number(codeQualityScore.value);
  if (Number.isNaN(n)) return String(codeQualityScore.value);
  return n.toFixed(0);
});

const strengthTextHtml2 = computed(() => {
  const s = (strengthText.value || "").trim();
  if (!s) return "";
  return s.replace(/\s+\-\s+/g, "<br>• ").replace(/^<br>/, "");
});

const improvementTextHtml2 = computed(() => {
  const s = (improvementText.value || "").trim();
  if (!s) return "";
  return s.replace(/\s+\-\s+/g, "<br>• ").replace(/^<br>/, "");
});

const cheatingWarningText = ref("");
const comprehensiveEvaluationText = ref("");
const annotatedCode = ref("");
const antiCheatSummary = ref(null);

const initialStrategyAnswer = ref("");
const problemUnderstandingText = ref("");
const problemUnderstandingFeedback = ref("");
const approachValidityText = ref("");
const consistencyText = ref("");
const consistencyFeedback = ref("");
const qaHistory = ref([]);

const problemCategory = ref("");
const problemDifficulty = ref("");

const difficultyClass = computed(() => {
  const diff = problemDifficulty.value.toLowerCase();
  if (diff.includes("쉬움") || diff.includes("easy")) return "easy";
  if (diff.includes("중간") || diff.includes("medium")) return "medium";
  if (diff.includes("어려움") || diff.includes("hard")) return "hard";
  return "";
});

const graphOutput = ref({});

const gradeSafe = computed(() => String(finalGrade.value || "-"));

const finalScoreText = computed(() => {
  if (finalScore.value === null || finalScore.value === undefined) return "-";
  const n = Number(finalScore.value);
  if (Number.isNaN(n)) return String(finalScore.value);
  return n.toFixed(0);
});

const problemSolvingScoreText = computed(() => {
  if (problemSolvingScore.value === null || problemSolvingScore.value === undefined) return "-";
  const n = Number(problemSolvingScore.value);
  if (Number.isNaN(n)) return String(problemSolvingScore.value);
  return n.toFixed(0);
});

const collaborationScoreText = computed(() => {
  if (collaborationScore.value === null || collaborationScore.value === undefined) return "-";
  const n = Number(collaborationScore.value);
  if (Number.isNaN(n)) return String(collaborationScore.value);
  return n.toFixed(0);
});

const hasCheatingWarning = computed(() => {
  return cheatingWarningText.value && cheatingWarningText.value.trim().length > 0;
});

const formatAntiCheatLine = (label, payload) => {
  if (!payload) return `${label}: -`;
  const count = Number(payload.count || 0);
  const level = payload.level || "-";
  return `${label}: ${count} (${level})`;
};

const problemUnderstandingClass = computed(() => {
  const text = problemUnderstandingText.value.toLowerCase();
  if (text.includes("우수") || text.includes("정확")) return "high";
  if (text.includes("양호") || text.includes("적절")) return "mid";
  if (text.includes("부족") || text.includes("미흡")) return "low";
  return "";
});

const approachValidityClass = computed(() => {
  const text = approachValidityText.value.toLowerCase();
  if (text.includes("우수") || text.includes("적절")) return "high";
  if (text.includes("양호") || text.includes("보통")) return "mid";
  if (text.includes("부적절") || text.includes("부족")) return "low";
  return "";
});

const consistencyClass = computed(() => {
  const text = consistencyText.value.toLowerCase();
  if (text.includes("불일치") || text.includes("변경")) return "mismatch";
  if (text.includes("개선") || text.includes("발전")) return "improved";
  if (text.includes("일치") || text.includes("동일")) return "match";
  return "";
});

const prettyGraphOutput = computed(() => {
  try {
    return JSON.stringify(graphOutput.value || {}, null, 2);
  } catch {
    return String(graphOutput.value || "");
  }
});

const difficultyChipClass = (value) => {
  const diff = String(value || "").toLowerCase();
  if (diff.includes("easy") || diff.includes("쉬움")) return "chip-easy";
  if (diff.includes("medium") || diff.includes("중간") || diff.includes("normal")) return "chip-medium";
  if (diff.includes("hard") || diff.includes("어려움")) return "chip-hard";
  return "chip-default";
};

const formatAlgoList = (algos) => {
  if (!algos) return "";
  if (Array.isArray(algos)) return algos.filter(Boolean).join(", ");
  return String(algos);
};

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

    if (data.problem_data) {
        problemData.value = data.problem_data;
    } else {
        problemData.value = { title: "Coding Test Problem", test_cases: [] };
    }

    reportMarkdown.value = data.final_report_markdown || "";
    finalScore.value = data.final_score ?? null;
    finalGrade.value = data.final_grade ?? null;

    const output = data.graph_output || {};

    problemText.value = data.problem_text || output.problem_text || "";
    latestCode.value =
      data.submitted_code ||
      output.submitted_code ||
      (data.latest_code && (data.latest_code.code || data.latest_code.value)) ||
      "";

    graphOutput.value = output;
    if (Array.isArray(output.recommended_problems)) {
      recommendedProblems.value = output.recommended_problems.slice(0, 3);
    } else {
      recommendedProblems.value = [];
    }
    
    codeQualityScore.value = output.code_quality_score ?? null;
    problemSolvingScore.value = output.problem_solving_score ?? null;
    collaborationScore.value = output.collaboration_score ?? null;
    
    strengthText.value = output.strength || "데이터 없음";
    improvementText.value = output.improvement || "데이터 없음";
    cheatingWarningText.value = output.cheating_warning || "";
    comprehensiveEvaluationText.value = output.comprehensive_evaluation || "평가 중...";
    annotatedCode.value = output.annotated_code || latestCode.value || "// 코드 없음";
    antiCheatSummary.value = output.anti_cheat_summary || null;
    
    problemCategory.value = output.problem_category || "General";
    problemDifficulty.value = output.problem_difficulty || "Normal";
    
    const normalizeEvalLabel = (value) => {
      if (!value) return "-";
      if (value.includes("우수")) return "우수";
      if (value.includes("양호")) return "양호";
      if (value.includes("부족")) return "부족";
      return value;
    };

    const psEval = output.problem_solving_evaluation || {};
    initialStrategyAnswer.value = psEval.initial_strategy || "기록 없음";
    problemUnderstandingText.value = normalizeEvalLabel(psEval.problem_understanding);
    problemUnderstandingFeedback.value = psEval.understanding_feedback || "";
    approachValidityText.value = normalizeEvalLabel(psEval.approach_validity);
    consistencyText.value = psEval.consistency_status || "-";
    consistencyFeedback.value = psEval.consistency_feedback || "";
    qaHistory.value = psEval.qa_history || [];
    
  } catch (e) {
    error.value = "서버 통신 오류";
    console.error(e);
  } finally {
    loading.value = false;
  }
};

const reload = () => fetchReport();

const pdfTarget = ref(null);
const downloadPdf = async () => {
  if (!pdfTarget.value) return;

  const el = pdfTarget.value;
  el.classList.add("pdf-mode");

  const opt = {
    margin: 10,
    filename: `JobTory_Report_${sessionId}.pdf`,
    image: { type: "jpeg", quality: 0.98 },
    html2canvas: {
      scale: 2,
      useCORS: true,
      backgroundColor: "#ffffff",
    },
    jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
  };

  try {
    await html2pdf().set(opt).from(el).save();
  } finally {
    el.classList.remove("pdf-mode");
  }
};

onMounted(() => {
  fetchReport();
});

const extractProblemDescription = (fullText) => {
  if (!fullText) return '';
  const constraints = fullText.indexOf('제한사항');
  const testCases = fullText.indexOf('입출력 예');
  const examples = fullText.indexOf('예제');
  let endIndex = fullText.length;
  if (constraints > 0) endIndex = Math.min(endIndex, constraints);
  if (testCases > 0) endIndex = Math.min(endIndex, testCases);
  if (examples > 0) endIndex = Math.min(endIndex, examples);
  return fullText.substring(0, endIndex).trim();
};
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap");
@import url("https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap");

.page {
  /* [핵심] 화면 고정 & 전체 스크롤 제거 */
  height: 100vh;
  width: 100vw;
  overflow: hidden; 

  display: flex;
  justify-content: center;
  align-items: center; /* 카드 중앙 정렬 */
  padding: 24px;
  background: #0B1120;
  color: #f1f5f9;
  font-family: "Inter", sans-serif;
  position: relative;
  box-sizing: border-box;
}

.bg-pattern {
  position: absolute; inset: 0; pointer-events: none;
  background-image: radial-gradient(rgba(255,255,255,0.03) 1px, transparent 1px);
  background-size: 24px 24px;
}

.card {
  width: 100%; 
  max-width: 900px;
  
  /* [핵심] 카드 높이 제한 및 내부 스크롤 구조 */
  height: 90vh; 
  max-height: 900px;
  
  background: rgba(17, 24, 39, 0.95);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
  
  display: flex; 
  flex-direction: column; /* 헤더는 고정, 콘텐츠는 아래로 */
  z-index: 1; 
  overflow: hidden; 
}

/* 헤더 (고정) */
.header {
  flex: 0 0 auto; /* 크기 고정 */
  display: flex; align-items: center; justify-content: space-between;
  padding: 20px 32px; border-bottom: 1px solid rgba(255,255,255,0.06);
  background: rgba(17, 24, 39, 1);
}
.header-left { display: flex; align-items: center; gap: 12px; }
.brand { font-weight: 800; font-size: 16px; letter-spacing: -0.5px; color: #fff; }
.divider { width: 1px; height: 16px; background: rgba(255,255,255,0.2); }
.session-info { font-family: "JetBrains Mono", monospace; font-size: 12px; color: #94a3b8; }
.actions { display: flex; gap: 8px; }

.btn {
  padding: 8px 16px; border-radius: 6px; font-size: 13px; font-weight: 500;
  cursor: pointer; transition: all 0.2s; border: 1px solid transparent;
}
.btn.ghost { background: transparent; color: #94a3b8; border-color: rgba(255,255,255,0.1); }
.btn.ghost:hover { background: rgba(255,255,255,0.05); color: #fff; }
.btn.primary { background: #6366f1; color: white; }
.btn.primary:hover { background: #4f46e5; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* 상태 메시지 (중앙 정렬) */
.status-container { 
  flex: 1; 
  padding: 0 20px; 
  display: flex; flex-direction: column; align-items: center; justify-content: center; 
  gap: 16px; 
}
.loader-ring {
  width: 40px; height: 40px; border: 3px solid rgba(255,255,255,0.1);
  border-top-color: #6366f1; border-radius: 50%; animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.status-text { color: #94a3b8; font-size: 14px; }
.status-container.error .error-icon {
  width: 48px; height: 48px; background: rgba(239,68,68,0.1); color: #ef4444;
  border-radius: 50%; display: grid; place-items: center; font-size: 24px; font-weight: 700;
}
.error-title { font-size: 16px; font-weight: 600; margin: 0; }
.error-desc { color: #94a3b8; font-size: 14px; margin: 0; }

/* [핵심] 리포트 본문 (스크롤 영역) */
.content {
  flex: 1; /* 남은 높이 모두 차지 */
  overflow-y: auto; /* 내용 넘치면 스크롤 생성 */
  padding: 32px 40px; 
}

.report-body { display: flex; flex-direction: column; gap: 40px; }

/* 섹션 공통 */
.section-heading {
  font-size: 18px; font-weight: 700; margin: 0 0 20px;
  color: #fff; letter-spacing: -0.5px; border-left: 3px solid #6366f1; padding-left: 12px;
}
.sub-heading {
  font-size: 15px; font-weight: 600; margin: 24px 0 12px; color: #cbd5e1;
}

/* 1. 요약 섹션 */
.summary-grid { display: grid; grid-template-columns: 180px 240px 1fr; gap: 20px; align-items: stretch; }

/* 등급 카드 */
.grade-card {
  background: #1e293b; border: 1px solid rgba(255,255,255,0.1); border-radius: 12px;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 20px; text-align: center;
}
.grade-label { font-size: 11px; font-weight: 600; color: #94a3b8; margin-bottom: 4px; }
.grade-value { font-size: 48px; font-weight: 800; line-height: 1; background: linear-gradient(135deg, #a78bfa, #6366f1); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

/* 점수 카드 */
.score-card {
  background: #1e293b; border: 1px solid rgba(255,255,255,0.1); border-radius: 12px;
  padding: 20px; display: flex; flex-direction: column; justify-content: center;
}
.score-card .score-label { font-size: 12px; color: #94a3b8; margin-bottom: 8px; }
.score-card .score-value { font-size: 32px; font-weight: 700; margin-bottom: 12px; }
.score-bar-bg { height: 6px; background: rgba(255,255,255,0.1); border-radius: 99px; overflow: hidden; }
.score-bar-fill { height: 100%; background: #6366f1; border-radius: 99px; }

/* 세부 점수 */
.detail-scores {
  display: flex; flex-direction: column; justify-content: space-between; gap: 10px;
}
.detail-item {
  display: flex; align-items: center; gap: 12px; padding: 10px;
  background: rgba(255,255,255,0.03); border-radius: 8px;
}
.detail-item .label { font-size: 12px; color: #94a3b8; width: 60px; }
.detail-item .value { font-size: 14px; font-weight: 700; width: 30px; text-align: right; }
.mini-bar { flex: 1; height: 4px; background: rgba(255,255,255,0.1); border-radius: 99px; overflow: hidden; }
.mini-bar .fill { height: 100%; background: #94a3b8; border-radius: 99px; }

/* 2. 피드백 섹션 */
.feedback-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.feedback-col {
  background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px; padding: 20px;
}
.col-header {
  font-size: 13px; font-weight: 700; text-transform: uppercase; margin-bottom: 12px;
  padding-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.06);
}
.strength .col-header { color: #4ade80; border-color: rgba(74,222,128,0.2); }
.improvement .col-header { color: #facc15; border-color: rgba(250,204,21,0.2); }
.col-body { font-size: 14px; line-height: 1.6; color: #d1d5db; }

/* 부정행위 알림 */
.alert-section { margin-top: 10px; }
.alert-header { font-size: 14px; font-weight: 600; color: #ef4444; margin-bottom: 10px; }
.alert-box { background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.2); padding: 12px; border-radius: 8px; margin-bottom: 10px; }
.alert-title { font-size: 13px; font-weight: 700; color: #f87171; margin-bottom: 4px; }
.alert-desc { font-size: 13px; color: #fca5a5; }
.alert-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.alert-item { background: #1e1e1e; padding: 8px 12px; border-radius: 6px; display: flex; justify-content: space-between; font-size: 12px; color: #94a3b8; }
.alert-item .val { font-weight: 700; color: #ef4444; }

/* 3. 종합 코멘트 */
.text-block { font-size: 14px; line-height: 1.7; color: #e5e7eb; white-space: pre-wrap; }

/* 3-1. 추천 문제 */
.recommend-section { margin-top: 16px; }
.recommend-desc { font-size: 12px; color: #94a3b8; margin: -6px 0 12px; }
.recommend-empty { font-size: 12px; color: #94a3b8; }
.recommend-grid { display: grid; gap: 12px; }
.recommend-card {
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px;
  padding: 12px;
}
.recommend-title { font-size: 13px; font-weight: 600; color: #e5e7eb; }
.recommend-meta { display: flex; gap: 8px; margin-top: 8px; flex-wrap: wrap; }
.recommend-chip {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.12);
  color: #cbd5e1;
}
.recommend-chip.chip-easy { color: #4ade80; border-color: rgba(74,222,128,0.4); }
.recommend-chip.chip-medium { color: #facc15; border-color: rgba(250,204,21,0.4); }
.recommend-chip.chip-hard { color: #f87171; border-color: rgba(248,113,113,0.4); }
.recommend-chip.chip-default { color: #cbd5e1; }
.recommend-algos { margin-top: 6px; font-size: 12px; color: #9ca3af; }

.divider-line { height: 1px; background: rgba(255,255,255,0.08); border: none; margin: 0; }

/* 4. 문제 분석 */
.problem-info-card {
  background: #1f2937; padding: 20px; border-radius: 12px; margin-bottom: 20px;
}
.info-row { display: flex; align-items: baseline; gap: 12px; margin-bottom: 12px; }
.info-label { font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; width: 60px; }
.info-val.title { font-size: 16px; font-weight: 700; color: #fff; }
.info-meta { display: flex; gap: 8px; margin-left: 72px; margin-bottom: 12px; }
.tag { font-size: 11px; padding: 2px 8px; background: rgba(255,255,255,0.1); border-radius: 4px; color: #cbd5e1; }
.tag.difficulty.easy { color: #4ade80; background: rgba(74,222,128,0.1); }
.tag.difficulty.medium { color: #facc15; background: rgba(250,204,21,0.1); }
.tag.difficulty.hard { color: #f87171; background: rgba(248,113,113,0.1); }
.info-desc { margin-left: 72px; font-size: 13px; color: #9ca3af; line-height: 1.5; }
.testcases-mini {
    margin-left: 72px; margin-top: 12px;
    background: rgba(0,0,0,0.3); padding: 8px 12px; border-radius: 6px;
    font-size: 12px; color: #cbd5e1;
}
.tc-row { margin-bottom: 4px; font-family: "JetBrains Mono", monospace; }

.analysis-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.analysis-card { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; overflow: hidden; }
.card-head { background: rgba(255,255,255,0.05); padding: 10px 16px; font-size: 12px; font-weight: 700; color: #cbd5e1; }
.card-body { padding: 16px; font-size: 13px; line-height: 1.6; color: #d1d5db; }

.metrics-list { padding: 16px; display: flex; flex-direction: column; gap: 8px; }
.metric-row { display: flex; justify-content: space-between; font-size: 13px; }
.m-label { color: #94a3b8; }
.m-val { font-weight: 600; }
.m-val.high { color: #4ade80; }
.m-val.mid { color: #60a5fa; }
.m-val.low { color: #f87171; }
.m-val.mismatch { color: #f87171; }
.m-val.improved { color: #60a5fa; }
.m-val.match { color: #4ade80; }
.metric-feedback { padding: 0 16px 16px; font-size: 12px; color: #9ca3af; line-height: 1.5; }

.qa-timeline { border-left: 2px solid rgba(255,255,255,0.1); margin-left: 8px; padding-left: 20px; display: flex; flex-direction: column; gap: 20px; }
.qa-entry { position: relative; }
.qa-entry .marker {
  position: absolute; left: -29px; top: 0;
  width: 16px; height: 16px; background: #3730a3; color: #a5b4fc;
  font-size: 10px; font-weight: 700; border-radius: 4px;
  display: grid; place-items: center;
}
.qa-q { font-size: 13px; font-weight: 600; color: #a5b4fc; margin-bottom: 4px; }
.qa-a { font-size: 13px; color: #d1d5db; line-height: 1.5; }

/* 5. 코드 섹션 */
.code-box {
  background: #0d1117; border: 1px solid rgba(255,255,255,0.08); border-radius: 8px;
  padding: 16px; overflow-x: auto;
}
.code-box pre { margin: 0; font-family: "JetBrains Mono", monospace; font-size: 12px; line-height: 1.6; color: #e6edf3; }

/* PDF 모드 */
.pdf-mode { background: #fff !important; color: #111 !important; padding: 40px !important; }
.pdf-mode .card { box-shadow: none; border: none; background: #fff; width: 100%; max-width: none; }
.pdf-mode .header, .pdf-mode .btn, .pdf-mode .status-container { display: none; }
.pdf-mode .grade-card, .pdf-mode .score-card, .pdf-mode .detail-item, .pdf-mode .problem-info-card, .pdf-mode .analysis-card, .pdf-mode .feedback-col {
  background: #f8fafc; border-color: #e2e8f0; color: #0f172a;
}
.pdf-mode h2, .pdf-mode h3 { color: #0f172a; border-color: #6366f1; }
.pdf-mode .text-block, .pdf-mode .info-desc, .pdf-mode .card-body, .pdf-mode .qa-a, .pdf-mode .col-body { color: #334155; }
.pdf-mode .code-box { background: #f1f5f9; border-color: #e2e8f0; }
.pdf-mode .code-box pre { color: #0f172a; }

/* 스크롤바 */
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }

@media (max-width: 768px) {
  .summary-grid { grid-template-columns: 1fr; }
  .feedback-grid { grid-template-columns: 1fr; }
  .analysis-grid { grid-template-columns: 1fr; }
  .card { width: 100%; border-radius: 0; height: 100vh; }
  .content { max-height: calc(100vh - 70px); }
}
</style>
