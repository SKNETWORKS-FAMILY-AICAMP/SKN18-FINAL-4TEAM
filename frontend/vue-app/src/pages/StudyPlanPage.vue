<script setup>
import { ref, reactive, onMounted, computed, nextTick } from 'vue';
import FullCalendar from '@fullcalendar/vue3';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
import axios from 'axios';
import { useRouter } from 'vue-router';
import { useAuth } from '../hooks/useAuth';

// --- 상태 관리 (State) ---
const duration = ref(7); // 기본 7일
const loading = ref(false);
const { token, ensureValidSession, BACKEND_BASE } = useAuth();
const router = useRouter();
const calendarRef = ref(null);
const redirectToLogin = () => {
  const redirect = router.currentRoute?.value?.fullPath || "/login";
  router.push({ name: "login", query: { redirect } });
};

// FullCalendar 설정 및 데이터 관리
const calendarOptions = reactive({
  plugins: [ dayGridPlugin, interactionPlugin ],
  initialView: 'dayGridMonth',
  headerToolbar: {
    left: 'prev,next today',
    center: 'title',
    right: 'dayGridMonth'
  },
  events: [], // 여기에 API 데이터가 들어갑니다
  eventClick: handleEventClick,
  height: 'auto'
});

const isVideoOpen = ref(false);
const activeVideo = ref(null);
const lectureNote = ref('');
const reflectionSaving = ref(false);
const statusLabel = computed(() => {
  const raw = (activeVideo.value?.extendedProps?.is_completed || '').toString().toUpperCase();
  if (raw === 'COMPLETE') return '완료';
  if (raw === 'NEEDS_WORK' || raw === 'NEEDS_WORK') return '미흡';
  if (raw === 'POLISH') return '수정 필요';
  return '미진행';
});
const statusClass = computed(() => {
  const label = statusLabel.value;
  if (label === '완료') return 'status-badge--done';
  if (label === '수정 필요') return 'status-badge--doing';
  if (label === '미흡') return 'status-badge--todo';
  return 'status-badge--todo';
});
const statusStyle = computed(() => {
  const label = statusLabel.value;
  if (label === '완료') return { background: '#e7f5ff', color: '#1f6f54', border: '1px solid #86efac' };
  if (label === '수정 필요') return { background: '#eef2ff', color: '#312e81', border: '1px solid #c7d2fe' };
  if (label === '미흡') return { background: '#fff0e5', color: '#9a3412', border: '1px solid #fdba74' };
  return { background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1' };
});

function getYouTubeEmbedUrl(url) {
  if (!url) return '';
  try {
    const parsed = new URL(url);
    if (parsed.hostname.includes('youtu.be')) {
      const id = parsed.pathname.replace('/', '');
      return id ? `https://www.youtube.com/embed/${id}` : '';
    }
    if (parsed.hostname.includes('youtube.com')) {
      const id = parsed.searchParams.get('v');
      return id ? `https://www.youtube.com/embed/${id}` : '';
    }
  } catch (err) { /* ignore malformed urls */ }
  return '';
}

function openVideoModal(event) {
  activeVideo.value = event;
  lectureNote.value = event?.extendedProps?.lecture_note ?? '';
  isVideoOpen.value = true;
}

function closeVideoModal() {
  isVideoOpen.value = false;
  activeVideo.value = null;
}

async function saveReflection() {
  if (!activeVideo.value) {
    return;
  }

  const trimmedNote = (lectureNote.value || "").trim();
  if (trimmedNote.length < 30) {
    alert("회고는 30자 이상 작성해주세요.");
    return;
  }

  const ok = await ensureValidSession();
  if (!ok) {
    alert("로그인이 필요합니다.");
    return;
  }

  const taskId = activeVideo.value?.extendedProps?.task_id;
  if (!taskId) {
    alert("저장할 수 있는 작업이 없습니다.");
    return;
  }

  reflectionSaving.value = true;
  try {
    const response = await axios.patch(
      `${BACKEND_BASE}/api/tasks/reflection/`,
      {
        task_id: taskId,
        lecture_note: trimmedNote
      },
      {
        headers: {
          Authorization: `Bearer ${token.value}`
        }
      }
    );

    const updatedComment = response.data?.lecture_note ?? trimmedNote;
    const updatedCompleted = response.data?.is_completed ?? statusLabel.value;
    const coachOutput = response.data?.coach_output ?? '';
    if (typeof activeVideo.value.setExtendedProp === 'function') {
      activeVideo.value.setExtendedProp('lecture_note', updatedComment);
      activeVideo.value.setExtendedProp('is_completed', updatedCompleted);
      if (coachOutput) activeVideo.value.setExtendedProp('coach_output', coachOutput);
    } else {
      activeVideo.value.extendedProps = {
        ...(activeVideo.value.extendedProps || {}),
        lecture_note: updatedComment,
        is_completed: updatedCompleted,
        ...(coachOutput ? { coach_output: coachOutput } : {}),
      };
    }
  } catch (error) {
    console.error(error);
    const message =
      error?.response?.data?.error ||
      error?.response?.data?.detail ||
      "회고 저장에 실패했습니다.";
    alert(message);
  } finally {
    reflectionSaving.value = false;
  }
}

// --- 함수 구현 ---

// 1. 이벤트 클릭 핸들러 (영상 링크 이동)
function handleEventClick(info) {
  info.jsEvent.preventDefault();
  openVideoModal(info.event);
}

// 2. 계획 생성 요청 (API 호출)
async function loadLatestPlan() {
  const ok = await ensureValidSession();
  if (!ok) {
    alert("로그인이 필요합니다.");
    redirectToLogin();
    return;
  }

  try {
    const response = await axios.get(`${BACKEND_BASE}/api/plans/latest/`, {
      headers: {
        Authorization: `Bearer ${token.value}`
      }
    });
    if (response.data?.events) {
      calendarOptions.events = response.data.events;
    }
  } catch (error) {
    if (error?.response?.status !== 404) {
      console.error(error);
    }
  }
}

async function generatePlan() {
  loading.value = true;
  
  try {
    const ok = await ensureValidSession();
    if (!ok) {
      alert("로그인이 필요합니다.");
      redirectToLogin();
      return;
    }

    // Django API 호출 (CORS 설정 필수)
    const response = await axios.post(
      `${BACKEND_BASE}/api/generate-plan/`,
      {
        duration: duration.value
      },
      {
        headers: {
          Authorization: `Bearer ${token.value}`
        }
      }
    );

    // 받은 데이터를 캘린더 옵션에 주입 (반응형으로 즉시 업데이트됨)
    calendarOptions.events = Array.isArray(response.data.events)
      ? [...response.data.events]
      : [];
    await nextTick();
    const calendarApi = calendarRef.value?.getApi?.();
    if (calendarApi) {
      calendarApi.removeAllEvents();
      calendarApi.addEventSource(calendarOptions.events);
      calendarApi.render();
    }
    
    alert("커리큘럼 생성이 완료되었습니다!");

  } catch (error) {
    console.error(error);
    const detail = error?.response?.data?.detail;
    const code = error?.response?.data?.code;
    if (code === "need_min_livecoding") {
      alert(detail || "라이브 코딩 테스트를 최소 3회 완료해야 합니다.");
      router.push({ name: "home" });
      return;
    }
    if (error?.response?.status === 401) {
      alert(detail || "로그인이 필요합니다.");
      redirectToLogin();
      return;
    }

    const fallback = detail || error?.response?.data?.error;
    alert(fallback || "에러가 발생했습니다. 백엔드 서버가 켜져있는지 확인해주세요.");
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void loadLatestPlan();
});
</script>

<template>
  <div class="app-container">
    <header class="header">
      <h1>AI 학습 코치</h1>
    </header>

    <div class="input-section">
      <div class="input-textblock">
        <div class="input-label">사용자 맞춤형 7일 플랜</div>
        <div class="input-helper">라이브 코딩 테스트 결과를 바탕으로 보완이 필요한 부분에 맞춘 커리큘럼을 제공합니다.</div>
      </div>
      <button 
        @click="generatePlan" 
        :disabled="loading" 
        class="btn-generate"
      >
        {{ loading ? "Deep Agent 생각 중..." : "학습계획 생성" }}
      </button>
    </div>

    <div class="calendar-wrapper">
      <FullCalendar ref="calendarRef" :options="calendarOptions" />
    </div>
    <Teleport to="body">
      <div v-if="isVideoOpen" class="video-modal" role="dialog" aria-modal="true">
        <div class="video-backdrop"></div>
        <div class="video-sheet">
        <div class="video-header">
          <div class="video-title">
            세부 계획<span v-if="activeVideo?.extendedProps?.day_number"> · {{ activeVideo.extendedProps.day_number }}일차</span>
          </div>
          <button type="button" class="video-close" @click="closeVideoModal">닫기</button>
        </div>
        <div class="video-status">
          <span :class="['status-badge', statusClass]" :style="statusStyle">
            {{ statusLabel }}
          </span>
        </div>
        <div class="video-meta">{{ activeVideo?.title || "학습 일정" }}</div>
        <div class="video-frame">
            <iframe
              v-if="getYouTubeEmbedUrl(activeVideo?.url)"
              :src="getYouTubeEmbedUrl(activeVideo?.url)"
              title="YouTube video"
              frameborder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
              allowfullscreen
            ></iframe>
            <div v-else class="video-empty">유효한 유튜브 링크가 없습니다.</div>
          </div>
        <div class="reflection-block">
          <div class="reflection-fields">
            <label class="reflection-label">
              공부한 내용
              <textarea
                v-model="lectureNote"
                class="reflection-input"
                rows="3"
                placeholder="오늘 배운 내용을 적어주세요. 추후 AI코치가 피드백을 제공해드립니다."
              ></textarea>
            </label>
          </div>
          <div class="reflection-actions">
            <button type="button" class="reflection-save" :disabled="reflectionSaving" @click="saveReflection">
              {{ reflectionSaving ? "저장 중..." : "학습내용 저장" }}
            </button>
          </div>
        </div>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<style scoped>
/* 기본 배경색 */
:global(body) {
  background: #f8f4eb;
}

/* 전체 레이아웃 */
.app-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 40px 20px;
  font-family: "SF Pro", sans-serif;
  color: #333;
}

/* 헤더 */
.header {
  text-align: center;
  margin-bottom: 28px;
}

.header h1 {
  font-size: 2.8rem;
  color: #1f2f3f;
  margin-bottom: 10px;
  letter-spacing: -0.02em;
}

.header p {
  color: #5d6674;
  font-size: 1.15rem;
}

/* 입력 섹션 */
.input-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 28px;
  flex-wrap: wrap;
  margin: 28px 0 40px;
  background: linear-gradient(135deg, #f9fbff, #f6f7fa);
  padding: 24px 30px;
  border-radius: 16px;
  border: 1px solid #e6ebf3;
  box-shadow: 0 10px 28px rgba(31, 45, 79, 0.08);
}

.input-textblock {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1 1 auto;
  min-width: 0;
}

.input-label {
  font-size: 1.15rem;
  font-weight: 800;
  color: #1f2f3f;
}

.input-helper {
  color: #5d6674;
  font-size: 1rem;
}

.btn-generate {
  padding: 15px 30px;
  background-color: #1f2933; 
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1.1rem;
  font-weight: 800;
  margin-left: auto;
  min-width: 180px;
  cursor: pointer;
  transition: background 0.2s, transform 0.15s ease, box-shadow 0.2s ease;
  box-shadow: 0 12px 24px rgba(31, 41, 51, 0.2);
}

.btn-generate:hover {
  background-color: #2d7a56;
  transform: translateY(-1px);
  box-shadow: 0 16px 32px rgba(45, 122, 86, 0.25);
}

.btn-generate:disabled {
  background-color: #8ab0caff;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* 캘린더 스타일 커스텀 */
.calendar-wrapper {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
:global(.video-modal) {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 30;
}

:global(.video-backdrop) {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
}

:global(.video-sheet) {
  position: relative;
  width: min(720px, 92vw);
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 28px 60px rgba(15, 23, 42, 0.28);
  display: flex;
  flex-direction: column;
  gap: 12px;
  font-family: "SF Pro", sans-serif;
}

:global(.video-header) {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

:global(.video-title) {
  font-size: 1.35rem;
  font-weight: 800;
  color: #1f2933;
}

:global(.video-close) {
  background: none;
  border: none;
  color: #6b7280;
  font-weight: 700;
  cursor: pointer;
}

:global(.video-meta) {
  color: #6b4f3f;
  font-size: 2.5rem;
  font-weight: 700;
}

:global(.video-frame) {
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #f1f5f9;
  border-radius: 12px;
  overflow: hidden;
}

:global(.video-frame iframe) {
  width: 100%;
  height: 100%;
  border: none;
}

:global(.reflection-block) {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

:global(.reflection-title) {
  font-size: 1.1rem;
  font-weight: 800;
  color: #2c3e50;
}

:global(.reflection-fields) {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

:global(.reflection-label) {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 0.95rem;
  font-weight: 700;
  color: #2f2a1f;
}

:global(.reflection-input) {
  border: 1px solid #d2d6dc;
  border-radius: 12px;
  padding: 12px 14px;
  font-size: 1rem;
  resize: vertical;
  font-family: "SF Pro", sans-serif;
}

:global(.reflection-actions) {
  display: flex;
  justify-content: flex-end;
}

:global(.reflection-save) {
  border: none;
  background: #1f6f54;
  color: #fff;
  font-weight: 700;
  border-radius: 10px;
  padding: 10px 16px;
  cursor: pointer;
}

:global(.reflection-save:disabled) {
  background: #94a3b8;
  cursor: not-allowed;
}

:global(.video-empty) {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8a6f56;
  font-size: 0.95rem;
}


/* Vue Style Deep Selector (::v-deep) for Child Components */
:deep(.fc-event) {
  cursor: pointer;
  border: none;
  border-left: 4px solid transparent;
  padding: 4px;
  font-weight: 600;
}

:deep(.fc-event.is-pending) {
  background-color: #6abaffff;
  color: #f8fafc;
  border-left-color: #4291b8ff;
}

:deep(.fc-event.is-pending:hover) {
  background-color: #9bc7e6ff;
}

:deep(.fc-event.is-completed) {
  background-color: #cad4dcff;
  color: #2c3e50;
  border-left-color: #4291b8ff;
}

:deep(.fc-event.is-completed:hover) {
  background-color: #cfe9ff;
}

:deep(.fc-day-today) {
  background-color: #fff9db !important;
}
</style>
:global(.video-status) {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 0.95rem;
  font-weight: 800;
  letter-spacing: -0.01em;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.status-badge--todo {
  background: #fff0e5;
  color: #9a3412;
  border: 1px solid #fdba74;
}
.status-badge--doing {
  background: #eef2ff;
  color: #312e81;
  border: 1px solid #c7d2fe;
}
.status-badge--done {
  background: #e6f7ec;
  color: #14532d;
  border: 1px solid #86efac;
}
