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
          <button class="btn" @click="goHome" :disabled="loading">초기 화면</button>
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
        <!-- ✅ PDF로 뽑을 영역 -->
        <div ref="pdfTarget" class="report-wrap">
          <!-- 평가 요약 섹션 -->
          <div class="evaluation-summary">
            <h2 class="section-title">평가 요약</h2>
            
            <div class="grade-section">
              <div class="grade-badge" :data-grade="gradeSafe">
                <div class="grade-letter">{{ gradeSafe }}</div>
              </div>
              <div class="session-id-small">세션 ID: {{ sessionId }}</div>
            </div>

            <div class="score-grid">
              <div class="score-item">
                <div class="score-label">문제 해결 능력</div>
                <div class="score-value">{{ problemSolvingScoreText }}점</div>
              </div>
              <div class="score-item">
                <div class="score-label">코드 품질</div>
                <div class="score-value">{{ codeQualityScoreText }}점</div>
              </div>
              <div class="score-item">
                <div class="score-label">협업 능력</div>
                <div class="score-value">{{ collaborationScoreText }}점</div>
              </div>
              <div class="score-item highlight">
                <div class="score-label">최종 점수</div>
                <div class="score-value">{{ finalScoreText }}점</div>
              </div>
            </div>

            <!-- 강점 -->
            <div class="feedback-box strength">
              <div class="feedback-icon">👍</div>
              <div class="feedback-content">
                <div class="feedback-title">강점</div>
                <div class="feedback-text" v-html="strengthTextHtml2"></div>
              </div>
            </div>

            <!-- 개선점 -->
            <div class="feedback-box improvement">
              <div class="feedback-icon">💡</div>
              <div class="feedback-content">
                <div class="feedback-title">개선점</div>
                <div class="feedback-text" v-html="improvementTextHtml2"></div>
              </div>
            </div>

            <!-- 부정행위 경고 -->
            <div v-if="hasCheatingWarning" class="feedback-box warning">
              <div class="feedback-icon">🔍</div>
              <div class="feedback-content">
                <div class="feedback-title">부정행위 경고</div>
                <div class="feedback-text">{{ cheatingWarningText }}</div>
              </div>
            </div>

            <!-- 부정행위 기록 (점수 반영 없음) -->
            <div v-if="antiCheatSummary" class="feedback-box warning">
              <div class="feedback-icon">📌</div>
              <div class="feedback-content">
                <div class="feedback-title">부정행위 기록</div>
                <div class="feedback-text">
                  {{ formatAntiCheatLine("캠 기반", antiCheatSummary.camera) }}
                </div>
                <div class="feedback-text">
                  {{ formatAntiCheatLine("타이핑/화면 이탈", antiCheatSummary.typing) }}
                </div>
              </div>
            </div>
          </div>

          <!-- 종합 평가 섹션 -->
          <div class="comprehensive-evaluation">
            <h2 class="section-title">종합 평가</h2>
            <div class="evaluation-text">{{ comprehensiveEvaluationText }}</div>
          </div>

          <div class="problem-solving-evaluation">
            <h2 class="section-title">문제 해결 능력 평가</h2>

            <div class="problem-description-box">
              <h3>📋 문제 설명</h3>
              
              <!-- 카테고리/난이도 정보 -->
              <div class="problem-meta">
                <div class="meta-item">
                  <span class="meta-label">카테고리</span>
                  <span class="meta-value">{{ problemCategory }}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-label">난이도</span>
                  <span class="meta-value" :class="difficultyClass">{{ problemDifficulty }}</span>
                </div>
              </div>

              <div class="problem-text">
                  {{ extractProblemDescription(graphOutput.problem_text || '문제 정보를 불러오는 중입니다.') }}
                </div>
              </div>
            
            <!-- 초기 전략 답변 -->
            <div class="ps-section">
              <div class="ps-header">
                <span class="ps-icon">💭</span>
                <h3 class="ps-subtitle">초기 접근 방법</h3>
              </div>
              <div class="ps-content">
                <div class="ps-label">응시자의 전략 답변</div>
                <div class="strategy-answer">{{ initialStrategyAnswer }}</div>
              </div>
            </div>

            <!-- 문제 이해도 평가 -->
            <div class="ps-section">
              <div class="ps-header">
                <span class="ps-icon">🎯</span>
                <h3 class="ps-subtitle">문제 이해도</h3>
              </div>
              <div class="ps-content">
                <div class="understanding-grid">
                  <div class="understanding-item">
                    <div class="understanding-label">문제 이해</div>
                    <div class="understanding-value" :class="problemUnderstandingClass">
                      {{ problemUnderstandingText }}
                    </div>
                  </div>
                  <div class="understanding-item">
                    <div class="understanding-label">접근 방법 적절성</div>
                    <div class="understanding-value" :class="approachValidityClass">
                      {{ approachValidityText }}
                    </div>
                  </div>
                </div>
                <div class="ps-feedback">{{ problemUnderstandingFeedback }}</div>
              </div>
            </div>

            <!-- 실행 일관성 평가 -->
            <div class="ps-section">
              <div class="ps-header">
                <span class="ps-icon">⚙️</span>
                <h3 class="ps-subtitle">전략 실행 일관성</h3>
              </div>
              <div class="ps-content">
                <div class="consistency-status" :class="consistencyClass">
                  <span class="consistency-badge">{{ consistencyBadge }}</span>
                  <span class="consistency-text">{{ consistencyText }}</span>
                </div>
                <div class="ps-feedback">{{ consistencyFeedback }}</div>
              </div>
            </div>

            <!-- 질문/응답 로그 -->
            <div v-if="qaHistory && qaHistory.length > 0" class="ps-section">
              <div class="ps-header">
                <span class="ps-icon">💬</span>
                <h3 class="ps-subtitle">면접 중 질문/응답 내역</h3>
              </div>
              <div class="ps-content">
                <div class="qa-list">
                  <div v-for="(qa, idx) in qaHistory" :key="idx" class="qa-item">
                    <div class="qa-number">Q{{ idx + 1 }}</div>
                    <div class="qa-content">
                      <div class="qa-question">{{ qa.question }}</div>
                      <div class="qa-answer">{{ qa.answer }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 코드 평가 근거 섹션 -->
          <div class="code-evaluation">
            <h2 class="section-title">코드 평가 근거</h2>
            <div class="code-header">
              <span class="code-meta"># 제출 코드에 대한 상세 평가</span>
            </div>
            <pre class="code-with-comments"><code>{{ annotatedCode }}</code></pre>
          </div>
        </div>

        <!-- raw redis data: problem + latest code -->
        <section class="raw-block" v-if="problemText || latestCode">
          <h3>원본 문제/최종 코드 (Redis)</h3>
          <div class="raw-grid">
            <div>
              <div class="raw-label">문제 본문</div>
              <pre class="pre raw-pre">{{ problemText || "-" }}</pre>
            </div>
            <div>
              <div class="raw-label">최종 제출 코드</div>
              <pre class="pre raw-pre">{{ latestCode || "-" }}</pre>
            </div>
          </div>
        </section>

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
const problemText = ref("");
const latestCode = ref("");

// ✅ 세부 점수들
const codeQualityScore = ref(null);
const problemSolvingScore = ref(null);
const collaborationScore = ref(null);

// ✅ 피드백 내용
const strengthText = ref("");
const improvementText = ref("");

// ✅ '-' 기준 줄바꿈(HTML) 적용된 표시용 텍스트
const strengthTextHtml = computed(() => {
  const s = (strengthText.value || "").trim();
  if (!s) return "";
  // "- "로 시작하는 항목들을 줄바꿈으로 분리 (문장 중간 하이픈 오인 최소화)
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

// 만약 한 줄로 쭉 들어오고 "- ... - ..." 형태라면, 항목마다 줄바꿈
const strengthTextHtml2 = computed(() => {
  const s = (strengthText.value || "").trim();
  if (!s) return "";
  // " - " 패턴을 "<br>- "로 (첫 항목 앞에는 br 안 붙이기)
  return s
    .replace(/\s+\-\s+/g, "<br>- ")
    .replace(/^<br>/, "");
});

const improvementTextHtml2 = computed(() => {
  const s = (improvementText.value || "").trim();
  if (!s) return "";
  return s
    .replace(/\s+\-\s+/g, "<br>- ")
    .replace(/^<br>/, "");
});

const cheatingWarningText = ref("");
const comprehensiveEvaluationText = ref("");
const annotatedCode = ref("");
const antiCheatSummary = ref(null);

// ✅ 문제 해결 능력 평가 관련
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
  if (diff.includes("쉬움") || diff.includes("easy")) return "difficulty-easy";
  if (diff.includes("중간") || diff.includes("medium")) return "difficulty-medium";
  if (diff.includes("어려움") || diff.includes("hard")) return "difficulty-hard";
  return "";
});

// ✅ LangGraph 최종 output 전체 저장
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
  return `${label}: ${count}회 (${level})`;
};

// 문제 이해도 클래스
const problemUnderstandingClass = computed(() => {
  const text = problemUnderstandingText.value.toLowerCase();
  if (text.includes("우수") || text.includes("정확")) return "status-excellent";
  if (text.includes("양호") || text.includes("적절")) return "status-good";
  if (text.includes("부족") || text.includes("미흡")) return "status-poor";
  return "";
});

const approachValidityClass = computed(() => {
  const text = approachValidityText.value.toLowerCase();
  if (text.includes("우수") || text.includes("적절")) return "status-excellent";
  if (text.includes("양호") || text.includes("보통")) return "status-good";
  if (text.includes("부적절") || text.includes("부족")) return "status-poor";
  return "";
});

// 일관성 상태
const consistencyClass = computed(() => {
  const text = consistencyText.value.toLowerCase();
  if (text.includes("불일치") || text.includes("변경")) return "consistency-mismatch";
  if (text.includes("개선") || text.includes("발전")) return "consistency-improved";
  if (text.includes("일치") || text.includes("동일")) return "consistency-match";
  return "";
});

const consistencyBadge = computed(() => {
  const text = consistencyText.value.toLowerCase();
  if (text.includes("불일치") || text.includes("변경")) return "≠ 불일치";
  if (text.includes("개선") || text.includes("발전")) return "↑ 개선";
  if (text.includes("일치") || text.includes("동일")) return "✓ 일치";
  return "?";
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

    const data = await resp.json().catch(() => ({}));  // ✅ 여기서 선언됨!

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

    const output = data.graph_output || {};

    problemText.value = data.problem_text || output.problem_text || "";
    latestCode.value =
      data.submitted_code ||
      output.submitted_code ||
      (data.latest_code && (data.latest_code.code || data.latest_code.value)) ||
      "";

    // ✅ 최종 output에서 세부 정보 추출
    graphOutput.value = output;
    
    // ✅ 점수 추출 (수정됨)
    codeQualityScore.value = output.code_quality_score ?? null;  // 100점 환산
    problemSolvingScore.value = output.problem_solving_score ?? null;  // 100점 환산
    collaborationScore.value = output.collaboration_score ?? null;  // 100점 환산
    
    // 피드백 추출
    strengthText.value = output.strength || "데이터를 불러오는 중 문제가 발생했습니다.";
    improvementText.value = output.improvement || "데이터를 불러오는 중 문제가 발생했습니다.";
    cheatingWarningText.value = output.cheating_warning || "";
    comprehensiveEvaluationText.value = output.comprehensive_evaluation || "종합 평가 데이터를 불러오는 중입니다.";
    annotatedCode.value = output.annotated_code || latestCode.value || "# 코드를 불러올 수 없습니다.";
    antiCheatSummary.value = output.anti_cheat_summary || null;
    
    // ✅ 카테고리/난이도 추출 (output에서!)
    problemCategory.value = output.problem_category || "미분류";
    problemDifficulty.value = output.problem_difficulty || "미정";
    
    const normalizeEvalLabel = (value) => {
      if (!value) return "평가 중";
      if (value.includes("우수")) return "우수";
      if (value.includes("양호")) return "양호";
      if (value.includes("부족")) return "부족";
      return value;
    };

    // ✅ 문제 해결 능력 평가 데이터 추출
    const psEval = output.problem_solving_evaluation || {};
    initialStrategyAnswer.value = psEval.initial_strategy || "초기 전략 답변이 기록되지 않았습니다.";
    problemUnderstandingText.value = normalizeEvalLabel(psEval.problem_understanding);
    problemUnderstandingFeedback.value = psEval.understanding_feedback || "";
    approachValidityText.value = normalizeEvalLabel(psEval.approach_validity);
    consistencyText.value = psEval.consistency_status || "분석 중";
    consistencyFeedback.value = psEval.consistency_feedback || "";
    qaHistory.value = psEval.qa_history || [];
    
  } catch (e) {
    error.value = "서버와 통신 중 오류가 발생했습니다.";
    console.error(e);
  } finally {
    loading.value = false;
  }
};

const reload = () => fetchReport();

// PDF 다운로드
const pdfTarget = ref(null);
const downloadPdf = async () => {
  if (!pdfTarget.value) return;

  // ✅ PDF 생성 시점에만 다크모드 강제
  const el = pdfTarget.value;
  el.classList.add("pdf-dark");

  // ✅ html2canvas가 배경을 투명으로 두면 PDF 기본 흰색이 비치므로,
  //    다크 배경을 제대로 굳히려면 backgroundColor를 명시하는 게 안전함.
  const opt = {
    margin: 10,
    filename: `JobTory_Report_${sessionId}.pdf`,
    image: { type: "jpeg", quality: 0.98 },
    html2canvas: {
      scale: 2,
      useCORS: true,
      backgroundColor: "#0b0f14", // ✅ 다크 배경 강제
    },
    jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
  };

  try {
    await html2pdf().set(opt).from(el).save();
  } finally {
    // ✅ 끝나면 원복
    el.classList.remove("pdf-dark");
  }
};


onMounted(() => {
  fetchReport();
});

const extractProblemDescription = (fullText) => {
  if (!fullText) return '';
  
  // "제한사항" 이전까지만 추출
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

.report-wrap {
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255, 255, 255, 0.02);
  overflow: hidden;
}

/* 평가 요약 섹션 */
.evaluation-summary {
  padding: 24px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.section-title {
  font-size: 18px;
  font-weight: 700;
  margin: 0 0 20px 0;
  color: #e9e9ea;
}

.grade-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.grade-badge {
  width: 80px;
  height: 80px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, rgba(74, 222, 128, 0.15), rgba(34, 197, 94, 0.15));
  border: 2px solid rgba(74, 222, 128, 0.3);
}

.grade-badge[data-grade="A+"],
.grade-badge[data-grade="A"] {
  background: linear-gradient(135deg, rgba(74, 222, 128, 0.15), rgba(34, 197, 94, 0.15));
  border-color: rgba(74, 222, 128, 0.3);
}

.grade-badge[data-grade="B+"],
.grade-badge[data-grade="B"] {
  background: linear-gradient(135deg, rgba(96, 165, 250, 0.15), rgba(59, 130, 246, 0.15));
  border-color: rgba(96, 165, 250, 0.3);
}

.grade-badge[data-grade="C+"],
.grade-badge[data-grade="C"] {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.15), rgba(245, 158, 11, 0.15));
  border-color: rgba(251, 191, 36, 0.3);
}

.grade-badge[data-grade="D"],
.grade-badge[data-grade="F"] {
  background: linear-gradient(135deg, rgba(248, 113, 113, 0.15), rgba(239, 68, 68, 0.15));
  border-color: rgba(248, 113, 113, 0.3);
}

.grade-letter {
  font-size: 42px;
  font-weight: 900;
  line-height: 1;
}

.session-id-small {
  font-size: 12px;
  opacity: 0.6;
  font-family: ui-monospace, monospace;
}

.score-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.score-item {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 14px;
  text-align: center;
}

.score-item.highlight {
  background: rgba(30, 41, 59, 0.5);
  border-color: rgba(255,255,255,0.12);
}

.score-label {
  font-size: 12px;
  opacity: 0.7;
  margin-bottom: 6px;
}

.score-value {
  font-size: 20px;
  font-weight: 700;
}

.feedback-box {
  display: flex;
  gap: 12px;
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 12px;
  border: 1px solid rgba(255,255,255,0.08);
}

.feedback-box.strength {
  background: rgba(74, 222, 128, 0.05);
  border-color: rgba(74, 222, 128, 0.2);
}

.feedback-box.improvement {
  background: rgba(251, 191, 36, 0.05);
  border-color: rgba(251, 191, 36, 0.2);
}

.feedback-box.warning {
  background: rgba(248, 113, 113, 0.05);
  border-color: rgba(248, 113, 113, 0.2);
}

.feedback-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.feedback-content {
  flex: 1;
}

.feedback-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 6px;
}

.feedback-text {
  font-size: 14px;
  line-height: 1.6;
  opacity: 0.9;
}

/* 문제 설명 박스 */
.problem-description-box {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.problem-description-box h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.problem-text {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  padding: 16px;
  line-height: 1.8;
  white-space: pre-wrap;
  font-size: 15px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

/* 종합 평가 섹션 */
.comprehensive-evaluation {
  padding: 24px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.evaluation-text {
  font-size: 14px;
  line-height: 1.8;
  opacity: 0.9;
  white-space: pre-wrap;
}

/* ✅ 문제 해결 능력 평가 섹션 */
.problem-solving-evaluation {
  padding: 24px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  background: rgba(139, 92, 246, 0.02);
}

.ps-section {
  margin-bottom: 20px;
  padding: 16px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px;
}

.ps-section:last-child {
  margin-bottom: 0;
}

.ps-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.ps-icon {
  font-size: 20px;
}

.ps-subtitle {
  font-size: 15px;
  font-weight: 600;
  margin: 0;
  color: #e9e9ea;
}

.ps-content {
  padding-left: 30px;
}

.ps-label {
  font-size: 12px;
  opacity: 0.65;
  margin-bottom: 8px;
}

.strategy-answer {
  font-size: 14px;
  line-height: 1.6;
  padding: 12px;
  background: rgba(255,255,255,0.03);
  border-left: 3px solid rgba(139, 92, 246, 0.5);
  border-radius: 6px;
  opacity: 0.9;
}

.understanding-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 12px;
}

.understanding-item {
  padding: 10px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 8px;
  text-align: center;
}

.understanding-label {
  font-size: 11px;
  opacity: 0.65;
  margin-bottom: 6px;
}

.understanding-value {
  font-size: 14px;
  font-weight: 600;
}

.understanding-value.status-excellent {
  color: #4ade80;
}

.understanding-value.status-good {
  color: #60a5fa;
}

.understanding-value.status-poor {
  color: #f87171;
}

.ps-feedback {
  font-size: 13px;
  line-height: 1.6;
  padding: 10px;
  background: rgba(255,255,255,0.02);
  border-radius: 6px;
  opacity: 0.85;
}

.consistency-status {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: rgba(255,255,255,0.03);
  border-radius: 8px;
  margin-bottom: 12px;
}

.consistency-badge {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  background: rgba(255,255,255,0.1);
}

.consistency-status.consistency-match .consistency-badge {
  background: rgba(74, 222, 128, 0.2);
  color: #4ade80;
}

.consistency-status.consistency-improved .consistency-badge {
  background: rgba(96, 165, 250, 0.2);
  color: #60a5fa;
}

.consistency-status.consistency-mismatch .consistency-badge {
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
}

.consistency-text {
  font-size: 13px;
  flex: 1;
}

.qa-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.qa-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 8px;
}

.qa-number {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  background: rgba(139, 92, 246, 0.15);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #c4b5fd;
}

.qa-content {
  flex: 1;
}

.qa-question {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 6px;
  color: #c4b5fd;
}

.qa-answer {
  font-size: 13px;
  line-height: 1.5;
  opacity: 0.85;
}

/* 코드 평가 근거 섹션 */
.code-evaluation {
  padding: 24px;
}

.code-header {
  margin-bottom: 12px;
}

.code-meta {
  font-size: 13px;
  opacity: 0.7;
  font-family: ui-monospace, monospace;
}

.code-with-comments {
  background: rgba(0,0,0,0.4);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 16px;
  overflow-x: auto;
  margin: 0;
}

.code-with-comments code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #e9e9ea;
  white-space: pre;
}

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
.raw-block {
  margin-top: 16px;
  padding: 12px;
  border-radius: 14px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(0,0,0,0.22);
}
.raw-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.raw-label {
  font-size: 12px;
  opacity: 0.75;
  margin-bottom: 6px;
}
.raw-pre {
  max-height: 220px;
  white-space: pre-wrap;
}

/* ✅ PDF 캡처용 다크모드 강제 */
.pdf-dark {
  background: #0b0f14 !important;
  color: #e6edf3 !important;
}

.pdf-dark .report-page,
.pdf-dark .container,
.pdf-dark .content,
.pdf-dark .report-container {
  background: #0b0f14 !important;
  color: #e6edf3 !important;
}

.pdf-dark .card,
.pdf-dark .panel,
.pdf-dark .section,
.pdf-dark .feedback-box,
.pdf-dark .score-box,
.pdf-dark .block,
.pdf-dark .box {
  background: #111827 !important;
  border-color: rgba(255, 255, 255, 0.08) !important;
  color: #e6edf3 !important;
}

.pdf-dark .feedback-title,
.pdf-dark .title,
.pdf-dark h1,
.pdf-dark h2,
.pdf-dark h3 {
  color: #f8fafc !important;
}

.pdf-dark .muted,
.pdf-dark .sub,
.pdf-dark .desc,
.pdf-dark .label {
  color: rgba(230, 237, 243, 0.75) !important;
}

/* 문제 메타 정보 */
.problem-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  backdrop-filter: blur(10px);
}

.meta-label {
  font-size: 12px;
  opacity: 0.8;
}

.meta-value {
  font-size: 14px;
  font-weight: 600;
}

.meta-value.difficulty-easy {
  color: #4ade80;
}

.meta-value.difficulty-medium {
  color: #fbbf24;
}

.meta-value.difficulty-hard {
  color: #f87171;
}
</style>
