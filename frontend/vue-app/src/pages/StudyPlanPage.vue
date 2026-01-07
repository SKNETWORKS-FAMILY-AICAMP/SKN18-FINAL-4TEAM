<script setup>
import { ref, reactive, onMounted, computed } from 'vue';
import FullCalendar from '@fullcalendar/vue3';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
import axios from 'axios';
import { useRouter } from 'vue-router';
import { useAuth } from '../hooks/useAuth';

// --- 상태 관리 (State) ---
const duration = ref(7); // 1주(7일)로 고정
const loading = ref(false);
const { token, ensureValidSession, BACKEND_BASE } = useAuth();
const router = useRouter();

const redirectToLogin = () => {
  const redirect = router.currentRoute?.value?.fullPath || "/login";
  router.push({ name: "login", query: { redirect } });
};

function getEventClassNames(arg) {
  const status = (arg?.event?.extendedProps?.is_completed || '').toString().toUpperCase();
  if (status === 'COMPLETE') return ['is-completed'];
  return ['is-pending'];
}

// FullCalendar 설정 및 데이터 관리
const calendarOptions = reactive({
  plugins: [ dayGridPlugin, interactionPlugin ],
  initialView: 'dayGridMonth',
  headerToolbar: {
    left: 'prev,next today',
    center: 'title',
    right: 'dayGridMonth'
  },
  events: [], 
  eventClassNames: getEventClassNames,
  eventClick: handleEventClick,
  height: 'auto', // 달력 높이는 내용에 맞게 자동 조절
  dayMaxEvents: true
});

// Todo List Data (날짜순 정렬)
const todoList = computed(() => {
  return [...calendarOptions.events].sort((a, b) => new Date(a.start) - new Date(b.start));
});

const isVideoOpen = ref(false);
const activeVideo = ref(null);
const lectureNote = ref('');
const reflectionSaving = ref(false);

const statusLabel = computed(() => {
  const raw = (activeVideo.value?.extendedProps?.is_completed || '').toString().toUpperCase();
  if (raw === 'COMPLETE') return '완료';
  if (raw === 'NEEDS_WORK') return '미흡';
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

// Helper for Todo List Item Styling
function getTodoStatusClass(event) {
  const status = (event.extendedProps?.is_completed || '').toUpperCase();
  if (status === 'COMPLETE') return 'todo-done';
  if (status === 'NEEDS_WORK') return 'todo-pending'; 
  return 'todo-pending';
}

function getTodoStatusLabel(event) {
  const status = (event.extendedProps?.is_completed || '').toUpperCase();
  if (status === 'COMPLETE') return '완료';
  if (status === 'NEEDS_WORK') return '미흡';
  if (status === 'POLISH') return '수정 필요';
  return '미진행';
}

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
  } catch (err) { /* ignore */ }
  return '';
}

function openVideoModal(event) {
  activeVideo.value = event;
  lectureNote.value = event?.extendedProps?.lecture_note ?? '';
  isVideoOpen.value = true;
}

function openVideoModalFromTodo(eventData) {
  activeVideo.value = eventData; 
  lectureNote.value = eventData.extendedProps?.lecture_note ?? '';
  isVideoOpen.value = true;
}

function closeVideoModal() {
  isVideoOpen.value = false;
  activeVideo.value = null;
}

async function saveReflection() {
  if (!activeVideo.value) return;

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
        headers: { Authorization: `Bearer ${token.value}` }
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
      if(!activeVideo.value.extendedProps) activeVideo.value.extendedProps = {};
      activeVideo.value.extendedProps.lecture_note = updatedComment;
      activeVideo.value.extendedProps.is_completed = updatedCompleted;
      if (coachOutput) activeVideo.value.extendedProps.coach_output = coachOutput;
    }
    
    const itemInList = calendarOptions.events.find(e => e.extendedProps?.task_id === taskId);
    if(itemInList) {
        itemInList.extendedProps.lecture_note = updatedComment;
        itemInList.extendedProps.is_completed = updatedCompleted;
    }

  } catch (error) {
    console.error(error);
    const message = error?.response?.data?.error || error?.response?.data?.detail || "회고 저장에 실패했습니다.";
    alert(message);
  } finally {
    reflectionSaving.value = false;
  }
}

function handleEventClick(info) {
  info.jsEvent.preventDefault();
  openVideoModal(info.event);
}

async function loadLatestPlan() {
  const ok = await ensureValidSession();
  if (!ok) {
    alert("로그인이 필요합니다.");
    redirectToLogin();
    return;
  }

  try {
    const response = await axios.get(`${BACKEND_BASE}/api/plans/latest/`, {
      headers: { Authorization: `Bearer ${token.value}` }
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

    const response = await axios.post(
      `${BACKEND_BASE}/api/generate-plan/`,
      { duration: duration.value },
      { headers: { Authorization: `Bearer ${token.value}` } }
    );

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
    <div class="bg-grid"></div>

    <header class="header">
      <nav class="nav-header">
        <RouterLink to="/" class="brand">JOBTORY</RouterLink>
      </nav>
      <div class="header-content">
        <h1>AI 학습 코치</h1>
      </div>
    </header>

    <div class="input-section">
      <div class="input-label">약점 보완을 위해 라이브코딩 성장리포트 기반 맞춤형 커리큘럼을 생성합니다.</div>
      <div class="fixed-duration-badge">1주 완성</div>
      <button 
        @click="generatePlan" 
        :disabled="loading" 
        class="btn-generate"
      >
        {{ loading ? "Deep Agent 생각 중..." : "학습계획 생성" }}
      </button>
    </div>

    <div class="content-row">
      <div class="calendar-wrapper">
        <FullCalendar :options="calendarOptions" />
      </div>

      <div class="todo-wrapper">
        <div class="todo-header">
          <h3>TodoList</h3>
          <span class="todo-count">{{ todoList.length }} Tasks</span>
        </div>
        <div class="todo-list custom-scrollbar">
          <div v-if="todoList.length === 0" class="todo-empty">
            아직 계획이 없습니다.<br>학습계획을 생성해보세요!
          </div>
          <div 
            v-else
            v-for="(item, index) in todoList" 
            :key="index" 
            class="todo-item"
            @click="openVideoModalFromTodo(item)"
          >
            <div class="todo-date-badge">
              <span class="day">Day</span>
              <span class="num">{{ item.extendedProps?.day_number || (index + 1) }}</span>
            </div>
            <div class="todo-content">
              <div class="todo-title">{{ item.title }}</div>
              <div class="todo-tags">
                <span class="todo-date">{{ item.start }}</span>
                <span :class="['todo-status', getTodoStatusClass(item)]">
                  {{ getTodoStatusLabel(item) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="isVideoOpen" class="video-modal" role="dialog" aria-modal="true">
        <div class="video-backdrop" @click="closeVideoModal"></div>
        <div class="video-sheet">
          <div class="video-header">
            <div class="video-title">
              세부 계획<span v-if="activeVideo?.extendedProps?.day_number"> · {{ activeVideo.extendedProps.day_number }}일차</span>
            </div>
            <button type="button" class="video-close" @click="closeVideoModal"></button>
          </div>
          <div class="video-body">
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
                  공부한 내용 (회고)
                  <textarea
                    v-model="lectureNote"
                    class="reflection-input"
                    rows="3"
                    placeholder="오늘 배운 내용을 적어주세요. AI 코치가 피드백을 제공해드립니다."
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
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
/* 기본 배경색 */
:global(body) {
  background: #f8f4eb;
  margin: 0;
  font-family: "Inter", sans-serif;
  overflow-x: hidden
}

.bg-grid {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  z-index: -1;
  pointer-events: none;
  background-image: 
    linear-gradient(rgba(0, 0, 0, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 0, 0, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
}

/* 전체 레이아웃 */
.app-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 8px 20px;
  color: #333;
}

/* 헤더 */
.header {
  text-align: center;
  margin-bottom: 40px;
  padding-top: 40px;
}

.header-content h1 {
  font-size: 3.0rem;
  color: #2c3e50;
  margin-bottom: 10px;
}

.nav-header {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  padding: 32px 40px;
  z-index: 100;
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

/* 입력 섹션 */
.input-section {
  display: flex;
  gap: 15px;
  align-items: center;
  justify-content: center;
  margin-bottom: 30px;
  background: #fff;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  border: 1px solid #eee;
}


.fixed-duration-badge {
  padding: 12px 20px;
  background-color: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  color: #2c3e50;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 100px;
}

.btn-generate {
  padding: 12px 24px;
  background-color: #1f2933; 
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.2s;
  height: 100%;
}

.btn-generate:hover {
  background-color: #64748b;
}

.btn-generate:disabled {
  background-color: #8ab0ca;
  cursor: not-allowed;
}

/* --- [수정된 부분] 컨텐츠 레이아웃 --- */
.content-row {
  display: flex;
  gap: 24px;
  align-items: flex-start; /* 높이를 서로 맞추지 않고 본연의 높이 유지 */
}

/* 달력 섹션 */
.calendar-wrapper {
  flex: 2;
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  min-width: 0;
  border: 1px solid #f0f0f0;
  /* height: auto; (기본값) -> 달력은 내용에 따라 늘어남 */
}

/* --- 투두 리스트 섹션 --- */
.todo-wrapper {
  flex: 1;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  border: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  
  /* 고정 높이 설정 (스크롤을 위해 필수) */
  height: 588px; 
  overflow: hidden;
}

.todo-header {
  padding: 20px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
}

.todo-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 800;
  color: #1e293b;
}

.todo-count {
  font-size: 0.85rem;
  font-weight: 600;
  color: #64748b;
  background: #f1f5f9;
  padding: 4px 8px;
  border-radius: 99px;
}

.todo-list {
  flex: 1;
  overflow-y: auto; /* 내용이 많으면 스크롤 */
  padding: 16px;
  background: #f9fafb;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.todo-empty {
  text-align: center;
  color: #94a3b8;
  padding: 40px 0;
  font-size: 0.95rem;
  line-height: 1.5;
}

.todo-item {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  gap: 16px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.todo-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  border-color: #cbd5e1;
}

.todo-date-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #f9fafb;
  color: #1e293b;
  width: 50px;
  height: 50px;
  border-radius: 10px;
  flex-shrink: 0;
}

.todo-date-badge .day { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; }
.todo-date-badge .num { font-size: 1.2rem; font-weight: 800; line-height: 1; }

.todo-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
  min-width: 0;
}

.todo-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.todo-tags {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.todo-date {
  font-size: 0.8rem;
  color: #94a3b8;
}

.todo-status {
  font-size: 0.75rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
}

.todo-done { color: #15803d; background: #dcfce7; }
.todo-pending { color: #9a3412; background: #ffedd5; }

/* Custom Scrollbar */
.custom-scrollbar::-webkit-scrollbar,
:global(.video-body::-webkit-scrollbar) { width: 1px; }
.custom-scrollbar::-webkit-scrollbar-thumb,
:global(.video-body::-webkit-scrollbar-thumb) { background: #cbd5e1; border-radius: 3px; }
.custom-scrollbar::-webkit-scrollbar-track,
:global(.video-body::-webkit-scrollbar-track) { background: transparent; }


/* =========================================
   [모달 디자인]
   ========================================= */

:global(.video-modal) {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  box-sizing: border-box;
}

:global(.video-backdrop) {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  animation: fadeIn 0.2s ease-out;
}

:global(.video-sheet) {
  position: relative;
  z-index: 10;
  width: min(680px, 100%);
  background: #ffffff;
  border-radius: 20px;
  box-shadow: 0 20px 50px -12px rgba(0, 0, 0, 0.25);
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 60px);
  overflow: hidden;
  animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

:global(.video-header) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #f1f5f9;
  background: #fff;
  flex-shrink: 0;
}

:global(.video-title) {
  font-size: 1.2rem;
  font-weight: 700;
  color: #1e293b;
}

:global(.video-close) {
  background: transparent;
  border: none;
  font-size: 24px;
  color: #94a3b8;
  cursor: pointer;
  padding: 4px;
  border-radius: 50%;
  line-height: 1;
  transition: all 0.2s;
}
:global(.video-close:hover) {
  background: #f1f5f9;
  color: #1e293b;
}
:global(.video-close::before) { content: "×"; }

:global(.video-body) {
  padding: 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

:global(.video-status) {
  display: flex;
}

:global(.video-meta) {
  font-size: 1.5rem;
  font-weight: 800;
  color: #0f172a;
  line-height: 1.3;
}

:global(.video-frame) {
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #000;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  flex-shrink: 0;
}

:global(.video-frame iframe) {
  width: 100%;
  height: 100%;
  border: none;
}

:global(.video-empty) {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  font-size: 0.95rem;
}

:global(.reflection-block) {
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

:global(.reflection-label) {
  font-size: 0.9rem;
  font-weight: 700;
  color: #475569;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

:global(.reflection-input) {
  width: 100%;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 12px;
  font-size: 0.95rem;
  font-family: "Inter", sans-serif;
  resize: vertical;
  background: #fff;
  transition: border-color 0.2s;
  box-sizing: border-box;
}
:global(.reflection-input:focus) {
  outline: none;
  border-color: #94a3b8;
  
}

:global(.reflection-actions) {
  display: flex;
  justify-content: flex-end;
}

:global(.reflection-save) {
  background: #1f2933;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}
:global(.reflection-save:hover) {
  background: #94a3b8;
}
:global(.reflection-save:disabled) {
  background: #94a3b8;
  cursor: not-allowed;
}

/* 애니메이션 */
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }

/* 상태 배지 스타일 */
.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 0.9rem;
  font-weight: 700;
  letter-spacing: -0.01em;
}
.status-badge--todo { background: #fff0e5; color: #9a3412; border: 1px solid #fdba74; }
.status-badge--doing { background: #eef2ff; color: #312e81; border: 1px solid #c7d2fe; }
.status-badge--done { background: #e6f7ec; color: #14532d; border: 1px solid #86efac; }

/* FullCalendar Custom */
:deep(.fc-event) {
  cursor: pointer;
  border: none;
  border-left: 4px solid transparent;
  padding: 4px;
  font-weight: 600;
}
:deep(.fc-event.is-pending) { background-color: #6abaff; color: #fff; border-left-color: #4291b8; }
:deep(.fc-event.is-pending:hover) { background-color: #9bc7e6; }
:deep(.fc-event.is-completed) { background-color: #78808bff; color: #78808bff; border-left-color: #78808bff; }
:deep(.fc-event.is-completed:hover) { background-color: #78808bff; }
:deep(.fc-day-today) { background-color: #fff9db !important; }

/* Responsive */
@media (max-width: 900px) {
  .content-row {
    flex-direction: column;
  }
  .todo-wrapper {
    height: 400px;
  }
}
</style>