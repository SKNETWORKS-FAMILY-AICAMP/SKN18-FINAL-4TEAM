<template>
  <div class="mypage">
    <header class="mypage-header">
      <RouterLink to="/" class="brand">JOBTORY</RouterLink>
    </header>

    <main class="mypage-body">
      <div class="card">
        <h1 class="title">마이페이지</h1>
        <p class="subtitle">계정 정보를 확인하고 서비스를 계속 이용하세요.</p>
        <div class="info-grid" v-if="user">
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
        <p class="hint" v-else>프로필을 불러오는 중입니다...</p>
        <div class="actions" v-if="user">
          <RouterLink to="/profile/edit" class="edit-button">
            회원정보 수정
          </RouterLink>
        </div>
      </div>

      <!-- 라이브코딩 리포트 목록 -->
      <div class="card reports-card">
        <div class="reports-header">
          <div>
            <h2 class="reports-title">라이브코딩 최종 리포트</h2>
            <p class="reports-subtitle">완료된 세션을 모달로 열어 보고 PDF로 저장하세요.</p>
          </div>
          <button class="refresh-btn" @click="fetchReports" :disabled="listLoading">새로고침</button>
        </div>

        <div v-if="listLoading" class="status-text">리포트 목록을 불러오는 중...</div>
        <div v-else-if="listError" class="status-text error">{{ listError }}</div>
        <div v-else-if="!reports.length" class="status-text">저장된 리포트가 없습니다.</div>

        <div v-else class="report-list">
          <div v-for="r in reports" :key="r.session_id" class="report-item">
            <div class="report-meta">
              <div class="report-session">세션 ID: {{ r.session_id }}</div>
              <div class="report-grade" v-if="r.final_grade">등급 {{ r.final_grade }}</div>
              <div class="report-score" v-if="r.final_score">점수 {{ r.final_score }}</div>
              <div class="report-date" v-if="r.updated_at">갱신 {{ formatDate(r.updated_at) }}</div>
            </div>
            <div class="report-actions">
              <button class="view-btn" @click="openReport(r.session_id)">보기</button>
              <a v-if="r.pdf_path" class="pdf-link" :href="r.pdf_path" target="_blank" rel="noopener">저장된 PDF</a>
            </div>
          </div>
        </div>
      </div>

      <!-- 성장 리포트 안내 카드 -->
      <div class="card insight-card">
        <div class="insight-header">
          <div>
            <h2 class="insight-title">나의 라이브코딩 성장 리포트</h2>
            <p class="insight-desc">라이브코딩 결과를 바탕으로 강점과 개선 포인트를 한눈에 정리해드립니다.</p>
          </div>
        </div> 
        <div class="agent-row">
          <div class="agent-status" :class="{ error: !!aggregateError }">
            <span v-if="aggregateLoading">성장 리포트 갱신 중입니다...</span>
            <span
              v-else-if="
                aggregateError && !latestGrowthContent && !aggregateOutputText
              "
            >
              {{ aggregateError }}
            </span>
            <span
              v-else-if="
                !payloadLatestAt && !latestGrowthContent && !aggregateOutputText
              "
            >
              아직 성장 리포트가 없습니다. 리포트가 3개 이상 쌓이면 자동 생성됩니다.
            </span>
          </div>
          <div v-if="payloadLatestAt" class="agent-updated">
            최근 갱신 시점: {{ formatDate(payloadLatestAt) }}
          </div>
        </div>
        <div v-if="parsedAggregate" class="agent-output rich">
          <div v-if="parsedAggregate.strengths?.length" class="agg-section">
            <div class="agg-title">💪 강점</div>
            <ul class="agg-list">
              <li v-for="(item, idx) in parsedAggregate.strengths" :key="`s-${idx}`">{{ item }}</li>
            </ul>
          </div>
          <div v-if="parsedAggregate.weaknesses?.length" class="agg-section">
            <div class="agg-title">⚠️ 약점</div>
            <ul class="agg-list">
              <li v-for="(item, idx) in parsedAggregate.weaknesses" :key="`w-${idx}`">{{ item }}</li>
            </ul>
          </div>
          <div v-if="parsedAggregate.improvements?.length" class="agg-section">
            <div class="agg-title">🔧 개선 포인트</div>
            <ul class="agg-list">
              <li v-for="(item, idx) in parsedAggregate.improvements" :key="`i-${idx}`">{{ item }}</li>
            </ul>
          </div>
          <div v-if="parsedAggregate.changes?.length" class="agg-section">
            <div class="agg-title">🔄 변화</div>
            <ul class="agg-list">
              <li v-for="(item, idx) in parsedAggregate.changes" :key="`c-${idx}`">{{ item }}</li>
            </ul>
          </div>
        </div>
        <div v-else-if="aggregateOutputText" class="agent-output rich">
          {{ aggregateOutputText }}
        </div>
        <div
          v-else-if="!aggregateLoading && !aggregateError"
          class="agent-output"
        >
          성장 리포트가 아직 생성되지 않았습니다. 리포트가 3개 이상 쌓이면 자동으로 생성돼요.
        </div>
      </div>

      <!-- 리포트 모달: showreport 라우트를 iframe으로 재사용 -->
      <div v-if="showModal" class="modal-backdrop" @click.self="closeModal">
        <div class="modal">
          <div class="modal-header">
            <div>
              <div class="modal-title">리포트 미리보기</div>
              <div class="modal-subtitle">세션 ID: {{ selectedSessionId }}</div>
            </div>
            <button class="close-btn" @click="closeModal">닫기</button>
          </div>
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
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import { useAuth } from "../hooks/useAuth";

const { user, fetchProfile, ensureValidSession, token, BACKEND_BASE } = useAuth();

const reports = ref([]);
const listLoading = ref(false);
const listError = ref("");
const showModal = ref(false);
const selectedSessionId = ref("");
const reportPageUrl = "/coding-test/report";
const reportFrameRef = ref(null);

// 누적 딥 에이전트 리포트 (DB에 저장된 최신 growth insight를 사용)
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
const latestGrowthContent = ref(""); // 서버에서 받은 growth_insight.report_content
const latestGrowthVersion = ref(null);
const latestGrowthIds = ref([]);
const AGG_TS_KEY = "jobtory_last_aggregate_ts";

onMounted(() => {
  if (!user.value) {
    void fetchProfile();
  }
  void fetchReports();
  void fetchPayloadAndMaybeAggregate();
});

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
      headers: {
        Authorization: `Bearer ${token.value}`,
      },
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

const openReport = (sessionId) => {
  selectedSessionId.value = sessionId;
  showModal.value = true;
};

const closeModal = () => {
  showModal.value = false;
};

// 모달에서만 초기화면/새로고침 버튼을 숨기기 위해 iframe 로드 후 스타일 주입
const onReportFrameLoad = () => {
  const frame = reportFrameRef.value;
  if (!frame || !frame.contentDocument) return;
  try {
    const doc = frame.contentDocument;
    const style = doc.createElement("style");
    style.textContent = `.actions .btn:not(.primary) { display: none !important; }`;
    doc.head.appendChild(style);
    const nonPrimary = doc.querySelectorAll(".actions .btn:not(.primary)");
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

const aggregateOutputText = computed(() => {
  // 로딩 중에는 기존 growth를 잠시 숨긴다
  if (aggregateLoading.value) return "";
  const val = latestGrowthContent.value || aggregateOutput.value;
  if (!val) return "";
  if (typeof val === "string") return val;
  if (val.text) return val.text;
  if (val.agent_result && val.agent_result.text) return val.agent_result.text;
  try {
    return JSON.stringify(val, null, 2);
  } catch {
    return String(val);
  }
});

const parsedAggregate = computed(() => {
  if (aggregateLoading.value) return null;
  const val = latestGrowthContent.value || aggregateOutput.value;
  let obj = null;
  if (typeof val === "string") {
    try {
      obj = JSON.parse(val);
    } catch {
      obj = null;
    }
  } else if (val && typeof val === "object") {
    obj = val.agent_result || val;
    if (typeof obj === "string") {
      try {
        obj = JSON.parse(obj);
      } catch {
        obj = null;
      }
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

const runAggregateAgent = async () => {
  aggregateLoading.value = true;
  aggregateError.value = "";
  try {
    const ok = await ensureValidSession();
    if (!ok) {
      aggregateError.value = "로그인이 필요합니다.";
      return;
    }

    // 프론트 강제 호출 시에도 run_mode별 가드 유지
    if (payloadRunMode.value === "blocked") {
      aggregateError.value = "최소 3개의 리포트가 필요합니다.";
      return;
    }

    if (payloadRunMode.value === "cached") {
      const cached =
        payloadCachedResult.value ||
        payloadPrevAgentResult.value ||
        payloadGrowth.value?.report_content;
      if (cached) {
        latestGrowthContent.value = cached;
        latestGrowthIds.value =
          payloadGrowth.value?.report_ids || payloadReportIds.value || [];
      }
      return;
    }

    const reportCount =
      payloadReportIds.value.length ||
      payloadReports.value.length ||
      payloadSelectedReport.value.length;
    if (!reportCount) {
      aggregateError.value = "리포트가 없습니다.";
      return;
    }
    if (!payloadGrowth.value && reportCount < 3) {
      aggregateError.value = "최소 3개의 리포트가 필요합니다.";
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

    const resp = await fetch(
      `${BACKEND_BASE}/api/livecoding/reports/aggregate/`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token.value}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      }
    );
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      aggregateError.value = data?.detail || `HTTP ${resp.status}`;
      // 3개 미만 블록이면 기존 성장 리포트를 그대로 노출
      if (
        data?.block_reason === "need_min_reports" &&
        payloadGrowth.value?.report_content
      ) {
        latestGrowthContent.value = payloadGrowth.value.report_content;
        latestGrowthIds.value = payloadGrowth.value.report_ids || [];
      }
      return;
    }
    // agent_result_raw가 있으면 디버깅용으로 콘솔에 남김
    if (data.agent_result_raw !== undefined) {
      console.debug("[aggregate] raw response", data.agent_result_raw);
    }
    const agentResult =
      data.agent_result !== undefined ? data.agent_result : data;
    aggregateOutput.value = agentResult;
    // 최신 growth insight 저장 (문자열이면 그대로, 객체면 report_content 우선)
    if (typeof agentResult === "string") {
      latestGrowthContent.value = agentResult;
    } else if (agentResult && typeof agentResult === "object") {
      latestGrowthContent.value =
        agentResult.report_content ||
        agentResult.text ||
        JSON.stringify(agentResult);
    }
    const usedIds =
      data.used_report_ids ||
      agentResult?.report_ids ||
      payloadReportIds.value ||
      [];
    latestGrowthIds.value = Array.isArray(usedIds) ? usedIds : [];
    if (data.growth_version !== undefined) {
      latestGrowthVersion.value = data.growth_version;
    }
    // 페이로드 최신 ts 로컬 저장
    const ts =
      data.latest_updated_at ||
      payloadLatestAt.value ||
      new Date().toISOString();
    payloadLatestAt.value = ts;
    try {
      localStorage.setItem(AGG_TS_KEY, ts);
    } catch {}
  } catch (e) {
    console.error(e);
    aggregateError.value = "에이전트 실행 중 오류가 발생했습니다.";
  } finally {
    aggregateLoading.value = false;
  }
};

const fetchPayload = async () => {
  const ok = await ensureValidSession();
  if (!ok) {
    aggregateError.value = "로그인이 필요합니다.";
    return false;
  }
  try {
    const resp = await fetch(`${BACKEND_BASE}/api/livecoding/reports/payload/`, {
      headers: {
        Authorization: `Bearer ${token.value}`,
      },
    });
    const data = await resp.json().catch(() => ({}));
    payloadUserId.value = data.user_id || "";
    // 성장 리포트 최신 시점: deepagent가 만든 성장 리포트(created_at) 우선
    const growthAt = data.user_growth_insight?.created_at || "";
    payloadLatestAt.value =
      growthAt || data.latest_created_at || data.latest_updated_at || "";
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
    // 3개 미만 등으로 실행 차단된 경우 (성장 리포트 영역에만 안내)
    if (data.run_mode === "blocked") {
      const msg = "최소 3개의 리포트가 쌓여야 성장 리포트를 실행합니다.";
      aggregateError.value = msg;
      payloadReadyToRun.value = false;
      // 기존 성장 리포트가 있으면 그대로 표시
      if (data.user_growth_insight?.report_content) {
        latestGrowthContent.value = data.user_growth_insight.report_content;
        latestGrowthVersion.value = data.user_growth_insight.version || null;
        latestGrowthIds.value = data.user_growth_insight.report_ids || [];
      }
      return true; // 페이로드는 읽었으나 실행은 안 함
    }
    // 최신 growth insight가 있으면 바로 채워서 표시
    if (data.user_growth_insight && data.user_growth_insight.report_content) {
      latestGrowthContent.value = data.user_growth_insight.report_content;
      latestGrowthVersion.value = data.user_growth_insight.version || null;
      latestGrowthIds.value = data.user_growth_insight.report_ids || [];
    }
    // incremental/cached 등의 이전 결과가 있으면 즉시 표출
    if (!latestGrowthContent.value && payloadPrevAgentResult.value) {
      latestGrowthContent.value = payloadPrevAgentResult.value;
      latestGrowthIds.value =
        data.user_growth_insight?.report_ids || payloadReportIds.value || [];
      if (!payloadLatestAt.value) {
        payloadLatestAt.value =
          data.latest_created_at ||
          data.latest_updated_at ||
          data.user_growth_insight?.created_at ||
          new Date().toISOString();
      }
    }
    // 백엔드가 cached라고 알려준 경우 바로 표시
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

const fetchPayloadAndMaybeAggregate = async () => {
  const fetched = await fetchPayload();
  if (!fetched) return;

  const latest = payloadLatestAt.value || "";
  let lastTs = "";
  try {
    lastTs = localStorage.getItem(AGG_TS_KEY) || "";
  } catch {}

  // blocked는 실행하지 않고 안내만 유지
  if (payloadRunMode.value === "blocked") {
    return;
  }

  // cached라면 기존 결과만 표시
  if (payloadRunMode.value === "cached") {
    const cached =
      payloadCachedResult.value ||
      payloadPrevAgentResult.value ||
      payloadGrowth.value?.report_content;
    if (cached) {
      latestGrowthContent.value = cached;
      latestGrowthIds.value =
        payloadGrowth.value?.report_ids || payloadReportIds.value || [];
    }
    return;
  }

  // 새 리포트가 있으면 바로 갱신 실행
  const hasNewReports =
    payloadReportIds.value.some((id) => !latestGrowthIds.value.includes(id));
  if (
    hasNewReports ||
    payloadRunMode.value === "initial" ||
    payloadRunMode.value === "incremental" ||
    (latest && latest !== lastTs)
  ) {
    void runAggregateAgent();
    return;
  }

  // 최신 growth insight가 없거나, latest ts가 바뀌었으면 실행 시도
  if ((!latestGrowthContent.value || (latest && latest !== lastTs))) {
    void runAggregateAgent();
  }
};
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap");

.mypage {
  min-height: 100vh;
  background: #f8f4eb;
  font-family: "Inter", sans-serif;
  color: #111827;
}

.mypage-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 32px;
}

.brand {
  font-weight: 800;
  letter-spacing: 0.14em;
  color: #0f172a;
  text-decoration: none;
  font-size: 22px;
}

.mypage-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  padding: 60px 16px;
}

.card {
  width: min(960px, 100%);
  background: #ffffff;
  border-radius: 18px;
  padding: 32px 28px;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.12);
  border: 1px solid #e5e7eb;
  text-align: left;
}

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

.info-grid {
  margin-top: 20px;
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

.actions {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
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
  transition: background 0.15s ease, transform 0.15s ease,
    box-shadow 0.15s ease;
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

.reports-card {
  width: min(960px, 100%);
}

.reports-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.reports-title {
  margin: 0;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.01em;
  line-height: 1.2;
}

.reports-subtitle {
  margin: 6px 0 0;
  color: #4b5563;
  font-size: 14px;
  letter-spacing: -0.01em;
  line-height: 1.6;
}

.refresh-btn {
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  cursor: pointer;
}

.report-list {
  margin-top: 16px;
  display: grid;
  gap: 12px;
}

.report-item {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 12px;
  background: #f9fafb;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.report-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  font-size: 14px;
  color: #374151;
}

.report-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.view-btn {
  padding: 8px 12px;
  border-radius: 8px;
  border: none;
  background: #111827;
  color: #f9fafb;
  cursor: pointer;
}

.pdf-link {
  color: #2563eb;
  text-decoration: none;
  font-size: 14px;
}

.status-text {
  margin-top: 14px;
  color: #4b5563;
  font-size: 14px;
}

.status-text.error {
  color: #dc2626;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: grid;
  place-items: center;
  padding: 16px;
  z-index: 2000;
}

.modal {
  width: min(1100px, 100%);
  height: min(90vh, 900px);
  background: #0f1115;
  color: #e9e9ea;
  border-radius: 14px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.04);
}

.modal-title {
  font-weight: 700;
}

.modal-subtitle {
  font-size: 13px;
  color: #cbd5e1;
}

.close-btn {
  border: none;
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
}

.modal-body {
  flex: 1;
  background: #0f1115;
}

.report-frame {
  width: 100%;
  height: 100%;
  border: none;
  background: #0f1115;
}

.insight-card {
  width: min(960px, 100%);
  border: 1px dashed #d4d4d8;
  background: linear-gradient(135deg, #fbfbfe 0%, #f4f6ff 100%);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.insight-title {
  margin: 0;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.01em;
  line-height: 1.2;
}

.insight-desc {
  margin: 6px 0 0;
  color: #4b5563;
  font-size: 14px;
  letter-spacing: -0.01em;
  line-height: 1.6;
}


.agent-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  align-items: center;
}

.agent-status {
  font-size: 13px;
  color: #475569;
}

.agent-status.error {
  color: #dc2626;
}

.agent-updated {
  justify-self: end;
  font-size: 13px;
  color: #4b5563;
}

.agent-output {
  margin-top: 8px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  background: #fff;
  padding: 12px;
  white-space: pre-line;
  font-family: "Nunito", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 14px;
  line-height: 1.5;
  color: #0f172a;
}

.agg-section {
  margin-bottom: 10px;
}

.agg-title {
  font-weight: 800;
  margin-bottom: 6px;
}

.agg-list {
  margin: 0;
  padding-left: 18px;
  color: #1f2937;
}
</style>
