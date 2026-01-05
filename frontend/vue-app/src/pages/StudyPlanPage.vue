<script setup>
import { ref, reactive, onMounted } from 'vue';
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
const completionLevel = ref('완료');
const reflectionSaving = ref(false);

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
  completionLevel.value = event?.extendedProps?.is_completed ?? '완료';
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
        lecture_note: lectureNote.value,
        completion_level: completionLevel.value
      },
      {
        headers: {
          Authorization: `Bearer ${token.value}`
        }
      }
    );

    const updatedComment = response.data?.lecture_note ?? lectureNote.value;
    const updatedCompleted = response.data?.is_completed ?? completionLevel.value;
    if (typeof activeVideo.value.setExtendedProp === 'function') {
      activeVideo.value.setExtendedProp('lecture_note', updatedComment);
      activeVideo.value.setExtendedProp('is_completed', updatedCompleted);
    } else {
      activeVideo.value.extendedProps = {
        ...(activeVideo.value.extendedProps || {}),
        lecture_note: updatedComment,
        is_completed: updatedCompleted
      };
    }
  } catch (error) {
    console.error(error);
    alert("회고 저장에 실패했습니다.");
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
    calendarOptions.events = response.data.events;
    
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
      <h1> AI 학습 코치</h1>
      <p>약점 보완을 위해 AI코치가 맞춤형 커리큘럼을 짜드립니다.</p>
    </header>

    <div class="input-section">
      <div class="input-label">라이브코딩 성장 리포트 기반 커리큘럼을 생성합니다.</div>
      <select v-model="duration" class="input-select">
        <option :value="7">1주 완성</option>
        <option :value="30">4주 완성</option>
      </select>

      <button 
        @click="generatePlan" 
        :disabled="loading" 
        class="btn-generate"
      >
        {{ loading ? "Deep Agent 생각 중..." : "학습계획 생성" }}
      </button>
    </div>

    <div class="calendar-wrapper">
      <FullCalendar :options="calendarOptions" />
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
              완료 상태
              <select v-model="completionLevel" class="reflection-select" aria-label="완료 상태 선택">
                <option value="미진행">미진행</option>
                <option value="진행중">진행중</option>
                <option value="완료">완료</option>
              </select>
            </label>
            <label class="reflection-label">
              공부한 내용
              <textarea
                v-model="lectureNote"
                class="reflection-input"
                rows="3"
                maxlength="200"
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
  margin-bottom: 40px;
}

.header h1 {
  font-size: 2.5rem;
  color: #2c3e50;
  margin-bottom: 10px;
}

.header p {
  color: #7f8c8d;
  font-size: 1.1rem;
}

/* 입력 섹션 */
.input-section {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-bottom: 40px;
  background: #f8f9fa;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.05);
}

.input-text {
  width: 400px;
  padding: 12px 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
}

.input-select {
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
}

.btn-generate {
  padding: 1px 20px;
  background-color: #1f2933; 
  color: white;
  border: none;
  border-radius: 5px;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-generate:hover {
  background-color: #33a06f;
}

.btn-generate:disabled {
  background-color: #8ab0caff;
  cursor: not-allowed;
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

:global(.reflection-select),
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
