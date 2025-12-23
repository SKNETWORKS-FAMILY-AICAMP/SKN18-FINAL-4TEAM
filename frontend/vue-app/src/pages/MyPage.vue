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
              <button class="delete-btn" @click="deleteReport(r.session_id)" :disabled="listLoading">삭제</button>
            </div>
          </div>
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
import { onMounted, ref } from "vue";
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

onMounted(() => {
  if (!user.value) {
    void fetchProfile();
  }
  void fetchReports();
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

const deleteReport = async (sessionId) => {
  const confirmed = window.confirm("Delete this report?");
  if (!confirmed) return;
  try {
    const resp = await fetch(`${BACKEND_BASE}/api/livecoding/reports/${encodeURIComponent(sessionId)}/`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token.value}`,
      },
    });
    if (!resp.ok && resp.status !== 404) {
      alert("Failed to delete report.");
      return;
    }
    await fetchReports();
    if (selectedSessionId.value === sessionId) {
      closeModal();
    }
  } catch (err) {
    console.error(err);
    alert("Error occurred while deleting report.");
  }
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
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap");

.mypage {
  min-height: 100vh;
  background: #f8f4eb;
  font-family: "Nunito", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
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
}

.reports-subtitle {
  margin: 4px 0 0;
  color: #4b5563;
  font-size: 14px;
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

.delete-btn {
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid #ef4444;
  background: #fef2f2;
  color: #b91c1c;
  cursor: pointer;
}
.delete-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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
</style>
