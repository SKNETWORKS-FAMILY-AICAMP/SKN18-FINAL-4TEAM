<template>
  <div class="mypage">
    <div class="bg-grid"></div>
    <nav class="nav-header">
      <RouterLink to="/" class="brand">JOBTORY</RouterLink>
    </nav>

    <main class="mypage-body">
      <div class="card account-profile-card">
        <div class="top-header">
          <div>
            <h1 class="title">마이페이지</h1>
            <p class="subtitle">계정 정보와 프로필을 한 번에 확인하고 수정할 수 있어요.</p>
          </div>

          <div class="top-actions" v-if="user">
            <RouterLink class="edit-button" :to="{ name: 'profile-edit' }">
              회원정보 수정
            </RouterLink>

            <button class="refresh-btn" @click="fetchUserProfile" :disabled="profileLoading">
              새로고침
            </button>
          </div>
        </div>

        <div v-if="user" class="section">
          <h2 class="section-title">계정</h2>

          <div class="info-grid">
            <div class="info-row">
              <span class="label">아이디</span>
              <span class="value">{{ user.user_id }}</span>
            </div>
            <div class="info-row">
              <span class="label">이름</span>
              <span class="value">{{ user.name }}</span>
            </div>
            <div class="info-row">
              <span class="label">이메일</span>
              <span class="value">{{ user.email }}</span>
            </div>
            <div class="info-row" v-if="user.phone_number">
              <span class="label">전화번호</span>
              <span class="value">{{ user.phone_number }}</span>
            </div>
            <div class="info-row" v-if="user.birthdate">
              <span class="label">생년월일</span>
              <span class="value">{{ user.birthdate }}</span>
            </div>
          </div>
        </div>
        <p class="hint" v-else>로그인을 불러오는 중입니다...</p>

        <div class="section">
          <h2 class="section-title">프로필</h2>
          <p class="profile-subtitle">
            메인페이지 모달에서 입력한 프로필을 여기서도 조회·수정할 수 있어요.
          </p>

          <div v-if="profileLoading" class="status-text">프로필을 불러오는 중...</div>
          <div v-else-if="profileError" class="status-text error">{{ profileError }}</div>

          <div v-else class="profile-grid readonly">
            <div class="profile-field">
              <span class="field-label">최종 학력</span>
              <span class="field-value">{{ profileForm.graduated_school || "-" }}</span>
            </div>
            <div class="profile-field">
              <span class="field-label">학교명</span>
              <span class="field-value">{{ profileForm.university || "-" }}</span>
            </div>
            <div class="profile-field">
              <span class="field-label">전공</span>
              <span class="field-value">{{ profileForm.major || "-" }}</span>
            </div>
            <div class="profile-field">
              <span class="field-label">학적 상태</span>
              <span class="field-value">{{ profileForm.academic_status || "-" }}</span>
            </div>
            <div class="profile-field">
              <span class="field-label">졸업(예정) 연도</span>
              <span class="field-value">{{ profileForm.graduation_year || "-" }}</span>
            </div>

            <div class="profile-field">
              <span class="field-label">경력 레벨</span>
              <span class="field-value">{{ profileForm.career_level || "-" }}</span>
            </div>
            <div class="profile-field">
              <span class="field-label">현재 상태</span>
              <span class="field-value">{{ profileForm.current_status || "-" }}</span>
            </div>
            <div class="profile-field">
              <span class="field-label">희망 근무지</span>
              <span class="field-value">{{ profileForm.region_single || "-" }}</span>
            </div>

            <div class="profile-field full">
              <span class="field-label">기술 스택</span>
              <span class="field-value">{{ formatList(profileForm.tech_stack) }}</span>
            </div>
            <div class="profile-field full">
              <span class="field-label">희망 직무</span>
              <span class="field-value">{{ formatList(profileForm.desired_role) }}</span>
            </div>
            <div class="profile-field full">
              <span class="field-label">세부 희망 직무</span>
              <span class="field-value">{{ formatList(profileForm.detailed_role) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="card reports-card">
        <div class="reports-header">
          <div>
            <h2 class="reports-title">라이브코딩 최종 리포트</h2>
            <p class="reports-subtitle">완료된 세션의 상세 결과와 피드백을 확인하세요.</p>
          </div>
          <button class="refresh-btn" @click="fetchReports" :disabled="listLoading">
            <span v-if="listLoading">...</span>
            <span v-else>새로고침</span>
          </button>
        </div>

        <div v-if="listLoading" class="status-box loading">
          <div class="spinner"></div> 리포트를 불러오는 중...
        </div>
        <div v-else-if="listError" class="status-box error">{{ listError }}</div>
        <div v-else-if="!reports.length" class="status-box empty">
          아직 완료된 라이브코딩 세션이 없습니다.
        </div>

        <div v-else class="report-list-container">
          <div v-for="r in reports" :key="r.session_id" class="report-card-item">
            <div class="report-date-col">
              <div class="date-pill">
                <span class="date-day">{{ formatDay(r.updated_at || r.created_at) }}</span>
                <span class="date-month">{{ formatMonth(r.updated_at || r.created_at) }}</span>
              </div>
            </div>

            <div class="report-info-col">
              <div class="report-title-row">
                <span class="session-id">#{{ r.session_id.slice(0, 8) }}</span>
                <span class="report-time">{{ formatTimeRange(r.updated_at || r.created_at) }}</span>
              </div>
              <div class="report-meta">
                <span class="score-label">최종 점수</span>
                <span class="score-val">{{ r.final_score ?? 0 }}</span>
                <span class="grade-tag" v-if="r.final_grade">{{ r.final_grade }}</span>
                <span v-if="(r.final_score ?? 0) >= 80" class="mini-tag">Excellent</span>
              </div>
            </div>

            <div class="report-action-col">
              <button class="report-btn primary" @click="openReport(r.session_id)">
                결과 보기
              </button>
              <a v-if="r.pdf_path" class="report-btn ghost" :href="r.pdf_path" target="_blank" rel="noopener">
                PDF
              </a>
            </div>
          </div>
        </div>
      </div>

      <div class="card insight-card">
        <div class="insight-header">
          <div>
            <h2 class="insight-title">나의 라이브코딩 성장 리포트</h2>
            <p class="insight-desc">최근 퍼포먼스 추이와 AI 상세 분석을 확인하세요.</p>
          </div>
          <div v-if="payloadLatestAt" class="updated-badge">
            <span class="dot"></span>
            Updated {{ formatDate(payloadLatestAt) }}
          </div>
        </div>

        <div class="dashboard-row" v-if="hasTrend">
          <div class="score-summary">
            <div class="score-label">Latest Score</div>
            <div class="score-big">
              {{ trendStats.current }}
              <span class="score-unit">점</span>
            </div>
            <div class="score-trend" :class="{ up: trendStats.isPositive, down: trendStats.isNegative }">
              <span v-if="trendStats.isPositive">▲</span>
              <span v-if="trendStats.isNegative">▼</span>
              전회 대비 {{ trendStats.label }}
            </div>
          </div>

          <div class="chart-wrapper">
            <svg :viewBox="`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`" class="trend-svg">
              <defs>
                <linearGradient id="chartGradient" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stop-color="#282654" stop-opacity="0.2"/>
                  <stop offset="100%" stop-color="#282654" stop-opacity="0"/>
                </linearGradient>
              </defs>
              <path :d="sparkAreaPath" fill="url(#chartGradient)" stroke="none" />
              <path :d="sparkLinePath" fill="none" stroke="#282654" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <circle 
                v-for="(p, i) in chartPoints" 
                :key="i"
                :cx="p.x" 
                :cy="p.y" 
                r="3" 
                fill="#fff" 
                stroke="#282654" 
                stroke-width="2"
                class="chart-dot"
              />
            </svg>
          </div>
        </div>
        
        <div v-else class="empty-chart-state">
           <p>리포트가 3개 이상 쌓이면 성장 그래프가 나타납니다.</p>
        </div>

        <hr class="divider" />

        <div class="agent-status-msg" v-if="aggregateLoading || aggregateError || (!parsedAggregate && !aggregateOutputText)">
          <span v-if="aggregateLoading">🔄 분석 리포트를 생성하고 있습니다...</span>
          <span v-else-if="aggregateError" class="error-msg">{{ aggregateError }}</span>
          <span v-else>아직 분석 데이터가 충분하지 않습니다.</span>
        </div>

        <div v-if="parsedAggregate" class="analysis-grid">
          <div class="analysis-box strength" v-if="parsedAggregate.strengths?.length">
            <div class="box-header">
              <span class="icon">💪</span> <span class="box-title">강점 (Strengths)</span>
            </div>
            <ul>
              <li v-for="(item, idx) in parsedAggregate.strengths" :key="`s-${idx}`">{{ item }}</li>
            </ul>
          </div>

          <div class="analysis-box weakness" v-if="parsedAggregate.weaknesses?.length">
            <div class="box-header">
              <span class="icon">⚡</span> <span class="box-title">약점 (Weaknesses)</span>
            </div>
            <ul>
              <li v-for="(item, idx) in parsedAggregate.weaknesses" :key="`w-${idx}`">{{ item }}</li>
            </ul>
          </div>

          <div class="analysis-box improvement full-width" v-if="parsedAggregate.improvements?.length">
            <div class="box-header">
              <span class="icon">🚀</span> <span class="box-title">개선 포인트 (Action Plan)</span>
            </div>
            <ul>
              <li v-for="(item, idx) in parsedAggregate.improvements" :key="`i-${idx}`">{{ item }}</li>
            </ul>
          </div>
          
           <div class="analysis-box changes full-width" v-if="parsedAggregate.changes?.length">
             <div class="box-header">
              <span class="icon">🔄</span> <span class="box-title">주요 변화</span>
            </div>
             <ul>
              <li v-for="(item, idx) in parsedAggregate.changes" :key="`c-${idx}`">{{ item }}</li>
            </ul>
          </div>
        </div>

        <div v-else-if="aggregateOutputText" class="agent-output rich">
          {{ aggregateOutputText }}
        </div>
      </div>

      <div v-if="showModal" class="modal-backdrop" @click.self="closeModal">
        <div class="modal">
          <div class="modal-body">
            <iframe
              v-if="selectedSessionId"
              :key="selectedSessionId"
              class="report-frame"
              :src="`${reportPageUrl}?session_id=${encodeURIComponent(selectedSessionId)}`"
              ref="reportFrameRef"
              @load="onReportFrameLoad"
            ></iframe>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref, reactive } from "vue";
import { RouterLink } from "vue-router";
import { useAuth } from "../hooks/useAuth";

const { user, fetchProfile, ensureValidSession, token, BACKEND_BASE } = useAuth();

// 프로필 폼/로딩 상태
const profileForm = reactive({
  graduated_school: "",
  university: "",
  major: "",
  academic_status: "",
  graduation_year: "",
  career_level: "",
  current_status: "",
  tech_stack: [],
  desired_role: [],
  detailed_role: [],
  region: [],
  region_single: "",
});
const profileLoading = ref(false);
const profileError = ref("");

const reports = ref([]);
const listLoading = ref(false);
const listError = ref("");
const showModal = ref(false);
const selectedSessionId = ref("");
const reportPageUrl = "/coding-test/report";
const reportFrameRef = ref(null);

// 누적 딥 에이전트 리포트
const aggregateLoading = ref(false);
const aggregateError = ref("");
const aggregateOutput = ref("");
const payloadUserId = ref("");
const payloadLatestAt = ref("");
const payloadReports = ref([]);
const payloadReportIds = ref([]);
const payloadGrowth = ref(null);
const payloadSelectedReport = ref([]);
const payloadPrevAgentResult = ref("");
const payloadReadyToRun = ref(false);
const payloadRunMode = ref("");
const payloadCachedResult = ref(null);
const latestGrowthContent = ref(""); 
const latestGrowthVersion = ref(null);
const latestGrowthIds = ref([]);
const AGG_TS_KEY = "jobtory_last_aggregate_ts";

// final_score 추세용
const trendLoading = ref(false);
const trendError = ref("");
const trendPoints = ref([]); 

// 차트 관련 상수
const CHART_WIDTH = 300; 
const CHART_HEIGHT = 80;

function handleReportMessage(event) {
  if (event.origin !== window.location.origin) return;
  if (event.data?.type === "close-report-modal") {
    closeModal();
  }
}

onMounted(() => {
  if (!user.value) void fetchProfile();
  void fetchReports();
  void fetchPayloadAndMaybeAggregate();
  void fetchUserProfile();
  void fetchTrend();
  window.addEventListener("message", handleReportMessage);
});

onBeforeUnmount(() => {
  window.removeEventListener("message", handleReportMessage);
});

// --- API Methods ---
const fetchReports = async () => {
  listLoading.value = true;
  listError.value = "";
  try {
    const ok = await ensureValidSession();
    if (!ok) {
      listError.value = "로그인이 필요합니다.";
      reports.value = [];
      return;
    }
    const resp = await fetch(`${BACKEND_BASE}/api/livecoding/reports/`, {
      headers: { Authorization: `Bearer ${token.value}` }
    });
    if (!resp.ok) {
      listError.value = "리포트 목록을 불러오지 못했습니다.";
      return;
    }
    const data = await resp.json();
    reports.value = data.results || [];
  } catch (err) {
    console.error(err);
    listError.value = "리포트 목록을 불러오지 못했습니다.";
  } finally {
    listLoading.value = false;
  }
};

const fetchTrend = async () => {
  trendLoading.value = true;
  trendError.value = "";
  trendPoints.value = [];
  try {
    const ok = await ensureValidSession();
    if (!ok) {
      trendError.value = "로그인이 필요합니다.";
      return;
    }
    const resp = await fetch(`${BACKEND_BASE}/api/livecoding/reports/trend/`, {
      headers: { Authorization: `Bearer ${token.value}` },
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      trendError.value = data?.detail || "점수 추세를 불러오지 못했습니다.";
      return;
    }
    const results = Array.isArray(data.results) ? data.results : [];
    trendPoints.value = results.map((r) => ({
      t: r.created_at,
      score: typeof r.final_score === "number" ? r.final_score : null,
    }));
  } catch (e) {
    console.error(e);
    trendError.value = "점수 추세를 불러오지 못했습니다.";
  } finally {
    trendLoading.value = false;
  }
};

const fetchUserProfile = async () => {
  profileLoading.value = true;
  profileError.value = "";
  try {
    const ok = await ensureValidSession();
    if (!ok) {
      profileError.value = "로그인이 필요합니다.";
      return;
    }
    const res = await fetch(`${BACKEND_BASE}/api/user/profile/detail/`, {
      headers: token.value ? { Authorization: `Bearer ${token.value}` } : {}
    });
    if (!res.ok) throw new Error("프로필을 불러오지 못했습니다.");
    const data = await res.json();
    mapProfileToForm(data);
  } catch (err) {
    console.error(err);
    profileError.value = err?.message || "프로필을 불러오지 못했습니다.";
  } finally {
    profileLoading.value = false;
  }
};

const mapProfileToForm = (data) => {
  profileForm.graduated_school = data.graduated_school || "";
  profileForm.university = data.university || "";
  profileForm.major = data.major || "";
  profileForm.academic_status = data.academic_status || "";
  profileForm.graduation_year = data.graduation_year || "";
  profileForm.career_level = data.career_level || "";
  profileForm.current_status = data.current_status || "";
  profileForm.tech_stack = data.tech_stack || [];
  profileForm.desired_role = data.desired_role || [];
  profileForm.detailed_role = data.detailed_role || [];
  profileForm.region = data.region || [];
  profileForm.region_single = (data.region && data.region[0]) || "";
};

const fetchPayload = async () => {
  const ok = await ensureValidSession();
  if (!ok) {
    aggregateError.value = "로그인이 필요합니다.";
    return false;
  }
  try {
    const resp = await fetch(`${BACKEND_BASE}/api/livecoding/reports/payload/`, {
      headers: { Authorization: `Bearer ${token.value}` },
    });
    const data = await resp.json().catch(() => ({}));
    payloadUserId.value = data.user_id || "";
    const growthAt = data.user_growth_insight?.created_at || "";
    payloadLatestAt.value = growthAt || data.latest_created_at || data.latest_updated_at || "";
    payloadReports.value = data.reports || [];
    payloadReportIds.value = data.report_ids || [];
    payloadGrowth.value = data.user_growth_insight || null;
    payloadSelectedReport.value = data.selected_report || data.selected_reports || [];
    payloadPrevAgentResult.value = data.prev_agent_result || "";
    payloadReadyToRun.value = !!data.ready_to_run;
    payloadRunMode.value = data.run_mode || "";
    payloadCachedResult.value = data.cached_agent_result || null;
    
    if (!resp.ok) {
      aggregateError.value = data?.detail || `HTTP ${resp.status}`;
      return false;
    }

    if (data.run_mode === "blocked") {
      aggregateError.value = "최소 3개의 리포트가 쌓여야 성장 리포트를 실행합니다.";
      payloadReadyToRun.value = false;
      if (data.user_growth_insight?.report_content) {
        latestGrowthContent.value = data.user_growth_insight.report_content;
        latestGrowthVersion.value = data.user_growth_insight.version || null;
        latestGrowthIds.value = data.user_growth_insight.report_ids || [];
      }
      return true;
    }
    
    if (data.user_growth_insight && data.user_growth_insight.report_content) {
      latestGrowthContent.value = data.user_growth_insight.report_content;
      latestGrowthVersion.value = data.user_growth_insight.version || null;
      latestGrowthIds.value = data.user_growth_insight.report_ids || [];
    }
    
    if (!latestGrowthContent.value && payloadPrevAgentResult.value) {
      latestGrowthContent.value = payloadPrevAgentResult.value;
      latestGrowthIds.value = data.user_growth_insight?.report_ids || payloadReportIds.value || [];
      if (!payloadLatestAt.value) {
        payloadLatestAt.value = data.latest_created_at || new Date().toISOString();
      }
    }
    
    if (!payloadReadyToRun.value && data.run_mode === "cached" && data.cached_agent_result) {
      latestGrowthContent.value = data.cached_agent_result;
      latestGrowthIds.value = data.user_growth_insight?.report_ids || [];
    }
    return true;
  } catch (e) {
    console.error(e);
    aggregateError.value = "리포트 페이로드를 불러오지 못했습니다.";
    return false;
  }
};

const runAggregateAgent = async () => {
  aggregateLoading.value = true;
  aggregateError.value = "";
  try {
    const ok = await ensureValidSession();
    if (!ok) {
      aggregateError.value = "로그인이 필요합니다.";
      return;
    }
    if (payloadRunMode.value === "blocked") {
      aggregateError.value = "최소 3개의 리포트가 필요합니다.";
      return;
    }
    if (payloadRunMode.value === "cached") {
      const cached = payloadCachedResult.value || payloadPrevAgentResult.value || payloadGrowth.value?.report_content;
      if (cached) {
        latestGrowthContent.value = cached;
        latestGrowthIds.value = payloadGrowth.value?.report_ids || payloadReportIds.value || [];
      }
      return;
    }
    const reportCount = payloadReportIds.value.length || payloadReports.value.length || payloadSelectedReport.value.length;
    if (!reportCount) {
      aggregateError.value = "리포트가 없습니다.";
      return;
    }
    
    const body = {
      user_id: payloadUserId.value,
      report_ids: payloadReportIds.value,
      run_mode: payloadRunMode.value,
    };
    if (payloadRunMode.value === "initial") {
      body.reports = payloadReports.value;
    } else if (payloadRunMode.value === "incremental") {
      body.selected_reports = payloadSelectedReport.value || [];
      body.prev_agent_result = payloadPrevAgentResult.value || "";
    } else {
      body.reports = payloadReports.value;
    }

    const resp = await fetch(`${BACKEND_BASE}/api/livecoding/reports/aggregate/`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token.value}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      aggregateError.value = data?.detail || `HTTP ${resp.status}`;
      if (data?.block_reason === "need_min_reports" && payloadGrowth.value?.report_content) {
        latestGrowthContent.value = payloadGrowth.value.report_content;
        latestGrowthIds.value = payloadGrowth.value.report_ids || [];
      }
      return;
    }
    
    const agentResult = data.agent_result !== undefined ? data.agent_result : data;
    aggregateOutput.value = agentResult;
    
    if (typeof agentResult === "string") {
      latestGrowthContent.value = agentResult;
    } else if (agentResult && typeof agentResult === "object") {
      latestGrowthContent.value = agentResult.report_content || agentResult.text || JSON.stringify(agentResult);
    }
    
    const usedIds = data.used_report_ids || agentResult?.report_ids || payloadReportIds.value || [];
    latestGrowthIds.value = Array.isArray(usedIds) ? usedIds : [];
    if (data.growth_version !== undefined) {
      latestGrowthVersion.value = data.growth_version;
    }
    
    const ts = data.latest_updated_at || payloadLatestAt.value || new Date().toISOString();
    payloadLatestAt.value = ts;
    try { localStorage.setItem(AGG_TS_KEY, ts); } catch {}
  } catch (e) {
    console.error(e);
    aggregateError.value = "에이전트 실행 중 오류가 발생했습니다.";
  } finally {
    aggregateLoading.value = false;
  }
};

const fetchPayloadAndMaybeAggregate = async () => {
  const fetched = await fetchPayload();
  if (!fetched) return;

  const latest = payloadLatestAt.value || "";
  let lastTs = "";
  try { lastTs = localStorage.getItem(AGG_TS_KEY) || ""; } catch {}

  if (payloadRunMode.value === "blocked") return;
  if (payloadRunMode.value === "cached") {
    const cached = payloadCachedResult.value || payloadPrevAgentResult.value || payloadGrowth.value?.report_content;
    if (cached) {
      latestGrowthContent.value = cached;
      latestGrowthIds.value = payloadGrowth.value?.report_ids || payloadReportIds.value || [];
    }
    return;
  }

  const hasNewReports = payloadReportIds.value.some((id) => !latestGrowthIds.value.includes(id));
  if (hasNewReports || payloadRunMode.value === "initial" || payloadRunMode.value === "incremental" || (latest && latest !== lastTs)) {
    void runAggregateAgent();
    return;
  }
  if ((!latestGrowthContent.value || (latest && latest !== lastTs))) {
    void runAggregateAgent();
  }
};

// --- Helpers ---
const openReport = (sessionId) => {
  selectedSessionId.value = sessionId;
  showModal.value = true;
};

const closeModal = () => {
  showModal.value = false;
};

const onReportFrameLoad = () => {
  const frame = reportFrameRef.value;
  if (!frame || !frame.contentDocument) return;
  try {
    const doc = frame.contentDocument;
    const style = doc.createElement("style");
    style.textContent = `.actions .btn:not(.primary):not(.close) { display: none !important; }`;
    doc.head.appendChild(style);
    const nonPrimary = doc.querySelectorAll(".actions .btn:not(.primary):not(.close)");
    nonPrimary.forEach((el) => (el.style.display = "none"));
  } catch (e) {
    console.warn("[mypage] failed to tweak embedded report buttons", e);
  }
};

const formatDate = (iso) => {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    return d.toLocaleString();
  } catch {
    return iso;
  }
};

const formatDay = (iso) => {
  if (!iso) return "--";
  try {
    const d = new Date(iso);
    return String(d.getDate()).padStart(2, "0");
  } catch {
    return "--";
  }
};

const formatMonth = (iso) => {
  if (!iso) return "NA";
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  try {
    const d = new Date(iso);
    return months[d.getMonth()] || "NA";
  } catch {
    return "NA";
  }
};

const formatTimeRange = (iso) => {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    const time = d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    return `${time}`;
  } catch {
    return "";
  }
};

const formatList = (arr) => {
  if (!arr || !arr.length) return "-";
  return arr.join(", ");
};

const getGradeClass = (grade) => {
  if (!grade) return "grade-none";
  const g = grade.toUpperCase();
  if (['S', 'A+', 'A'].includes(g)) return "grade-high";
  if (['B+', 'B'].includes(g)) return "grade-mid";
  if (['C+', 'C', 'F'].includes(g)) return "grade-low";
  return "grade-none";
};

// --- Computed Properties ---
const aggregateOutputText = computed(() => {
  if (aggregateLoading.value) return "";
  const val = latestGrowthContent.value || aggregateOutput.value;
  if (!val) return "";
  if (typeof val === "string") return val;
  if (val.text) return val.text;
  if (val.agent_result && val.agent_result.text) return val.agent_result.text;
  try { return JSON.stringify(val, null, 2); } catch { return String(val); }
});

const parsedAggregate = computed(() => {
  if (aggregateLoading.value) return null;
  const val = latestGrowthContent.value || aggregateOutput.value;
  let obj = null;
  if (typeof val === "string") {
    try { obj = JSON.parse(val); } catch { obj = null; }
  } else if (val && typeof val === "object") {
    obj = val.agent_result || val;
    if (typeof obj === "string") {
      try { obj = JSON.parse(obj); } catch { obj = null; }
    }
  }
  if (obj && typeof obj === "object") {
    return {
      strengths: obj.strengths || [],
      weaknesses: obj.weaknesses || [],
      improvements: obj.improvements || [],
      changes: obj.changes || [],
    };
  }
  return null;
});

const trendStats = computed(() => {
  const pts = trendPoints.value;
  if (!pts.length) return { current: 0, delta: 0, label: '-' };
  const current = pts[pts.length - 1].score ?? 0;
  let delta = 0;
  if (pts.length >= 2) {
    const prev = pts[pts.length - 2].score ?? 0;
    delta = current - prev;
  }
  const sign = delta > 0 ? '+' : '';
  return {
    current,
    delta,
    label: delta === 0 ? '-' : `${sign}${delta}`,
    isPositive: delta > 0,
    isNegative: delta < 0
  };
});

const computedChartData = computed(() => {
  const pts = trendPoints.value;
  if (pts.length < 2) return null;
  const scores = pts.map((p) => (p.score == null ? 0 : p.score));
  const min = Math.min(...scores, 0); 
  const max = Math.max(...scores, 100); 
  const range = max - min || 1; 
  const gapX = CHART_WIDTH / (pts.length - 1);
  return pts.map((p, i) => {
    const x = i * gapX;
    const normalizedScore = (p.score ?? 0);
    const y = CHART_HEIGHT - ((normalizedScore - min) / range) * (CHART_HEIGHT - 20) - 10; 
    return { x, y, score: p.score, date: p.t };
  });
});

const sparkLinePath = computed(() => {
  const points = computedChartData.value;
  if (!points) return "";
  return `M ${points.map(p => `${p.x},${p.y}`).join(" L ")}`;
});

const sparkAreaPath = computed(() => {
  const points = computedChartData.value;
  if (!points) return "";
  const line = points.map(p => `${p.x},${p.y}`).join(" L ");
  return `M ${points[0].x},${CHART_HEIGHT} L ${line} L ${points[points.length-1].x},${CHART_HEIGHT} Z`;
});

const chartPoints = computed(() => computedChartData.value || []);
const hasTrend = computed(() => trendPoints.value.length >= 3);
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap");

/* 1. 레이아웃 */
.mypage {
  position: relative;
  width: 100vw;
  height: 100vh;
  background: #f8f4eb;
  font-family: "Inter", sans-serif;
  color: #111827;
  overflow: hidden;
}

.bg-grid {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  z-index: 0;
  background-size: 40px 40px;
  background-image:
    linear-gradient(to right, rgba(0, 0, 0, 0.05) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(0, 0, 0, 0.05) 1px, transparent 1px);
  mask-image: linear-gradient(to bottom, black 40%, transparent 100%);
  pointer-events: none;
}

.nav-header {
  position: absolute;
  top: 0; left: 0;
  width: 100%;
  padding: 24px 40px;
  z-index: 2;
  display: flex;
  align-items: center;
}

.brand {
  font-family: "Inter", sans-serif;
  font-size: 24px;
  font-weight: 900;
  color: #111827;
  text-decoration: none;
  letter-spacing: -0.02em;
  cursor: pointer;
}

.mypage-body {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  padding-top: 100px;
  padding-bottom: 120px;
  padding-left: 16px;
  padding-right: 16px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.mypage-body::-webkit-scrollbar {
  display: none;
}

/* 2. 카드 공통 스타일 */
.card {
  width: min(960px, 100%);
  background: #ffffff;
  border-radius: 18px;
  padding: 32px 28px;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.12);
  border: 1px solid #e5e7eb;
  text-align: left;
  flex-shrink: 0; 
}

/* 3. 계정/프로필 섹션 스타일 */
.title {
  margin: 0 0 8px;
  font-size: 32px;
  font-weight: 800;
}
.subtitle {
  margin: 0 0 14px;
  font-size: 16px;
  color: #4b5563;
}
.hint {
  margin: 0;
  font-size: 14px;
  color: #6b7280;
}
.top-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
}
.top-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}
.section {
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid #e5e7eb;
}
.section-title {
  margin: 0 0 12px;
  font-size: 16px;
  font-weight: 800;
  color: #111827;
}

/* Info Grid (Original Style) */
.info-grid {
  margin-top: 14px;
  display: grid;
  gap: 12px;
}
.info-row {
  display: flex;
  justify-content: space-between;
  border: 1px solid #e5e7eb;
  padding: 10px 12px;
  border-radius: 10px;
  background: #f9fafb;
}
.label {
  font-weight: 700;
  color: #374151;
}
.value {
  color: #111827;
}

.edit-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 18px;
  border-radius: 9999px;
  background: #111827;
  color: #f9fafb;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  border: none;
  cursor: pointer;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.18);
  transition: background 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease;
}
.edit-button:hover {
  background: #020617;
  transform: translateY(-1px);
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.22);
}
.edit-button:active {
  transform: translateY(0);
  box-shadow: 0 6px 14px rgba(15, 23, 42, 0.2);
}

.profile-subtitle {
  margin: 4px 0 0;
  color: #4b5563;
  font-size: 14px;
}
.profile-grid {
  margin-top: 14px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px 16px;
}
.profile-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 14px;
}
.profile-field.full {
  grid-column: 1 / -1;
}
.profile-grid.readonly .field-label {
  font-weight: 700;
  color: #374151;
}
.profile-grid.readonly .field-value {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 10px 12px;
  background: #f9fafb;
  min-height: 38px;
  display: inline-flex;
  align-items: center;
}

/* 4. 리포트 카드 (수정된 디자인: info-row 스타일 계승) */
.reports-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.reports-title {
  margin: 0;
  font-size: 22px;
  font-weight: 800;
  color: #111827;
}
.reports-subtitle {
  margin: 6px 0 0;
  color: #4b5563;
  font-size: 14px;
}

.refresh-btn {
  padding: 8px 14px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  background: #fff;
  color: #374151;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.refresh-btn:hover {
  background: #f9fafb;
}

.status-box {
  padding: 40px;
  text-align: center;
  background: #f9fafb;
  border-radius: 12px;
  color: #6b7280;
  font-size: 14px;
  border: 1px dashed #e5e7eb;
}
.status-box.error { color: #dc2626; background: #fef2f2; border-color: #fecaca; }


.report-list-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.report-card-item {
  display: flex;
  align-items: center;
  gap: 16px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 14px 16px;
  transition: border-color 0.2s, background 0.2s, box-shadow 0.2s;
}
.report-card-item:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
  box-shadow: 0 6px 14px rgba(15, 23, 42, 0.08);
}

.report-date-col {
  display: flex;
  align-items: center;
}
.date-pill {
  width: 60px;
  border-left: 4px solid #6b7280;
  padding-left: 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.date-day {
  font-size: 22px;
  font-weight: 800;
  color: #111827;
  line-height: 1;
}
.date-month {
  font-size: 12px;
  font-weight: 700;
  color: #111827;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.report-info-col {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
  min-width: 0;
}
.report-title-row {
  display: flex;
  align-items: baseline;
  gap: 10px;
  flex-wrap: wrap;
}
.report-title {
  font-size: 15px;
  font-weight: 800;
  color: #111827;
}
.report-time {
  font-size: 12px;
  color: #6b7280;
  font-weight: 600;
}
.report-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  font-size: 12px;
  color: #6b7280;
}
.divider-dot { font-weight: 700; color: #d1d5db; }

.session-id {
  font-family: "Inter", sans-serif;
  color: #111827;
  font-weight: 700;
}

.score-label {
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
}
.score-val {
  font-size: 14px;
  font-weight: 800;
  color: #111827;
}
.grade-tag {
  font-size: 11px;
  font-weight: 800;
  color: #1e293b;
  background: #e2e8f0;
  border-radius: 6px;
  padding: 2px 6px;
  line-height: 1;
}
.mini-tag {
  font-size: 10px;
  font-weight: 700;
  color: #059669;
  background: rgba(5, 150, 105, 0.12);
  padding: 2px 6px;
  border-radius: 999px;
}

.report-action-col {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
.report-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
  text-decoration: none;
}
.report-btn.primary { background: #5c5c63ff; color: #fff; }
.report-btn.primary:hover { background: #c1c0d0ff; }
.report-btn.ghost { background: transparent; color: #94a3b8; border-color: rgba(148, 163, 184, 0.4); }
.report-btn.ghost:hover { background: rgba(15, 23, 42, 0.05); color: #1f2937; }
/* 5. 성장 리포트 (Insight) - 대시보드 스타일 */
.insight-card {
  width: min(960px, 100%);
  background: #ffffff;
  border-radius: 20px;
  box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.08), 0 0 1px rgba(0,0,0,0.1); 
  border: 1px solid #f1f5f9;
  display: flex;
  flex-direction: column;
  padding: 32px;
  gap: 24px;
}
.insight-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}
.insight-title {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  color: #1e293b;
}
.insight-desc {
  margin: 4px 0 0;
  color: #64748b;
  font-size: 14px;
}

.updated-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #64748b;
  background: #f1f5f9;
  padding: 4px 10px;
  border-radius: 99px;
  font-weight: 500;
}
.updated-badge .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #22c55e;
}

.dashboard-row {
  display: flex;
  align-items: center;
  gap: 40px;
  background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%);
  border-radius: 16px;
  padding: 24px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.08);
}
.score-summary {
  min-width: 120px;
  background: #ffffff;
  border-radius: 14px;
  padding: 16px 18px;
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.2);
}
.score-label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
  font-weight: 700;
  margin-bottom: 4px;
}
.score-big {
  font-size: 42px;
  font-weight: 900;
  color: #0f172a;
  line-height: 1;
}
.score-unit {
  font-size: 16px;
  font-weight: 600;
  color: #94a3b8;
}
.score-trend {
  margin-top: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.score-trend.up { color: #22c55e; }
.score-trend.down { color: #ef4444; }

.chart-wrapper {
  flex: 1;
  height: 120px;
  position: relative;
  border-radius: 14px;
  background: #f8fafc;
  padding: 16px 16px 12px;
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.2);
}
.chart-wrapper::before {
  content: "";
  position: absolute;
  inset: 10px 12px 10px;
  border-radius: 10px;
  background-image:
    linear-gradient(rgba(148, 163, 184, 0.22) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.22) 1px, transparent 1px);
  background-size: 24px 24px;
  pointer-events: none;
}
.trend-svg {
  width: 100%;
  height: 100%;
  overflow: visible;
  position: relative;
  z-index: 1;
}
.chart-dot {
  transition: r 0.2s ease, stroke-width 0.2s ease, fill 0.2s ease;
}
.chart-dot:hover {
  r: 5;
  stroke-width: 3;
  cursor: pointer;
  fill: #c7d2fe;
}
.empty-chart-state {
  text-align: center;
  padding: 30px;
  color: #94a3b8;
  font-size: 14px;
  background: #f8fafc;
  border-radius: 12px;
}
.divider {
  border: none;
  height: 1px;
  background: #e2e8f0;
  margin: 0;
}

/* AI 분석 그리드 */
.analysis-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.full-width {
  grid-column: 1 / -1;
}
.analysis-box {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.analysis-box:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(0,0,0,0.05);
}
.analysis-box.strength { border-left: 4px solid #3b82f6; }
.analysis-box.weakness { border-left: 4px solid #f59e0b; }
.analysis-box.improvement { border-left: 4px solid #10b981; }
.analysis-box.changes { border-left: 4px solid #8b5cf6; }

.box-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.box-title {
  font-size: 15px;
  font-weight: 700;
  color: #1e293b;
}
.icon { font-size: 18px; }
.analysis-box ul {
  margin: 0;
  padding-left: 20px;
  font-size: 14px;
  line-height: 1.6;
  color: #334155;
}
.analysis-box li {
  margin-bottom: 4px;
}

.agent-status-msg {
  text-align: center;
  font-size: 14px;
  color: #64748b;
  padding: 20px;
}
.error-msg { color: #ef4444; }
.agent-output {
  margin-top: 8px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  background: #fff;
  padding: 12px;
  white-space: pre-line;
  font-size: 14px;
  line-height: 1.5;
  color: #0f172a;
}

/* 6. 모달 & 미디어쿼리 */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: #0B1120;
  display: grid;
  place-items: center;
  padding: 0px;
  z-index: 2000;
}

.modal {
  width: min(950px, 100%);
  height: min(95vh, 900px);
  background: #0B1120;
  color: #e9e9ea;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  border: none;
  box-shadow: none;
  position: relative;
  padding: 0px;
}

.modal-body {
  flex: 1;
  background: #0B1120;
}

.report-frame {
  width: 100%;
  height: 100%;
  border: none;
  background: #0B1120;
}

@media (max-width: 900px) {
  .nav-header {
    padding: 20px;
    justify-content: center;
  }
  .top-grid {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 640px) {
  .dashboard-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
  }
  .chart-wrapper { width: 100%; }
  .analysis-grid { grid-template-columns: 1fr; }
  .report-card-item {
    flex-direction: column;
    align-items: flex-start;
  }
  .report-action-col {
    width: 100%;
    margin-top: 8px;
    justify-content: flex-start;
  }
}
</style>
