<script setup>
import { ref, reactive } from 'vue';
import FullCalendar from '@fullcalendar/vue3';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
import axios from 'axios';

// --- 상태 관리 (State) ---
const weakness = ref('');
const duration = ref(7); // 기본 7일
const loading = ref(false);

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

// --- 함수 구현 ---

// 1. 이벤트 클릭 핸들러 (영상 링크 이동)
function handleEventClick(info) {
  info.jsEvent.preventDefault(); // 브라우저 기본 동작 막기

  if (info.event.url) {
    window.open(info.event.url, "_blank");
  } else {
    alert("이 일정에는 연결된 영상이 없습니다.");
  }
}

// 2. 계획 생성 요청 (API 호출)
async function generatePlan() {
  if (!weakness.value) {
    alert("약점을 입력해주세요!");
    return;
  }

  loading.value = true;
  
  try {
    // Django API 호출 (CORS 설정 필수)
    const response = await axios.post('http://127.0.0.1:8000/api/generate-plan/', {
      weakness: weakness.value,
      duration: duration.value
    });

    // 받은 데이터를 캘린더 옵션에 주입 (반응형으로 즉시 업데이트됨)
    calendarOptions.events = response.data.events;
    
    alert("커리큘럼 생성이 완료되었습니다! 📅");

  } catch (error) {
    console.error(error);
    alert("에러가 발생했습니다. 백엔드 서버가 켜져있는지 확인해주세요.");
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="app-container">
    <header class="header">
      <h1>🎓 AI Deep Agent 학습 플래너</h1>
      <p>당신의 약점을 입력하면 맞춤형 커리큘럼을 짜드립니다.</p>
    </header>

    <div class="input-section">
      <input 
        type="text" 
        v-model="weakness"
        placeholder="예: Django DRF ViewSet이 너무 어려워" 
        class="input-text"
        @keyup.enter="generatePlan"
      />
      
      <select v-model="duration" class="input-select">
        <option :value="7">7일 완성 (1주)</option>
        <option :value="30">한달 완성 (4주)</option>
      </select>

      <button 
        @click="generatePlan" 
        :disabled="loading" 
        class="btn-generate"
      >
        {{ loading ? "Deep Agent 생각 중... 🤖" : "커리큘럼 생성하기 ✨" }}
      </button>
    </div>

    <div class="calendar-wrapper">
      <FullCalendar :options="calendarOptions" />
    </div>
  </div>
</template>

<style scoped>
/* 전체 레이아웃 */
.app-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 40px 20px;
  font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
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
  padding: 12px 24px;
  background-color: #42b883; /* Vue Green Color */
  color: white;
  border: none;
  border-radius: 8px;
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

/* Vue Style Deep Selector (::v-deep) for Child Components */
:deep(.fc-event) {
  cursor: pointer;
  background-color: #e7f5ff;
  border: none;
  border-left: 4px solid #42b883;
  padding: 4px;
  color: #2c3e50;
  font-weight: 500;
}

:deep(.fc-event:hover) {
  background-color: #0091ffff;
}

:deep(.fc-day-today) {
  background-color: #fff9db !important;
}
</style>
