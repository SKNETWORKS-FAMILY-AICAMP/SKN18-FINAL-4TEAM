<template>
  <div class="session-page">
    <AntiCheatAlert
      :visible="antiCheatAlert.visible"
      :state="antiCheatAlert.state"
      :title="antiCheatAlert.title"
      :description="antiCheatAlert.description"
      :level="antiCheatAlert.level"
      :timestamp="antiCheatAlert.timestamp"
      @dismiss="resetAntiCheatState"
    />
    <header class="session-header">
      <h1>JobTory Live Coding</h1>
      <p class="session-subtitle">실전 환경에서 문제를 풀어보세요.</p>
    </header>

    <main class="session-main">
      <div class="left-column">
        <section class="camera-pane">
          <header class="pane-header">
            <span class="pane-title">캠 미리보기</span>
          </header>
          <div class="camera-body">
            <div class="camera-placeholder">
              <video ref="videoRef" autoplay playsinline muted></video>
            </div>
            <p class="camera-message">
              {{ cameraError || "현재 웹캠으로 녹화 중입니다." }}
            </p>
          </div>
        </section>

        <section class="problem-pane">
          <header class="pane-header">
            <span class="pane-title">문제 설명</span>
          </header>
          <div class="problem-body">
            <h2 class="problem-title">유연근무제</h2>
            <p class="problem-text">
              프로그래머스 사이트를 운영하는 그렙에서는 재택근무와 함께 출근 희망 시간을
              자유롭게 정하는 유연근무제를 시행하고 있습니다. 제도 정착을 위해 오늘부터 일
              주일 동안 각자 설정한 출근 희망 시간에 맞춰 늦지 않고 출근한 직원에게 상품을
              주는 이벤트를 진행하려 합니다.
            </p>
            <p class="problem-text">
              직원들은 앞으로 자신이 설정한 출근 희망 시간 ±10분 까지 여유롭게 출근해야
              합니다. 예를 들어 출근 희망 시간이 9시 58분인 직원은 10시 8분까지 출근해야
              합니다. 단, 토요일, 일요일의 출근 시간은 이벤트에 영향을 끼치지 않습니다.
            </p>
            <h3 class="problem-subtitle">입력 형식</h3>
            <ul class="problem-list">
              <li>첫 줄에 직원 수 <code>n</code>이 주어집니다.</li>
              <li>둘째 줄에는 직원별 희망 출근 시간을 나타내는 배열 <code>schedules</code>가 주어집니다.</li>
              <li>셋째 줄에는 실제 출근 기록을 담은 2차원 배열 <code>timelogs</code>가 주어집니다.</li>
            </ul>
          </div>
        </section>
      </div>

      <section class="editor-pane">
        <header class="pane-header editor-header">
          <div class="tab">{{ currentFilename }}</div>
          <div class="editor-options">
            <select v-model="selectedLanguage" class="lang-select">
              <option value="python3">Python3</option>
              <option value="java">Java</option>
              <option value="c">C</option>
              <option value="cpp">C++</option>
            </select>
          </div>
        </header>
        <div class="editor-body">
          <CodeEditor v-model="code" :mode="cmMode" />
        </div>
        <footer class="editor-footer">
          <button type="button" class="run-button">실행하기</button>
          <span class="hint">실행 결과는 추후 연동 예정</span>
          <button
            type="button"
            class="run-button"
            @click="onAskButtonClick"
            :disabled="isSttRunning"
          >
            {{ isSttRunning ? "분석 중..." : (isRecording ? "제출" : "질문하기") }}
          </button>
          <button type="button" class="run-button">답변하기</button>
        </footer>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import AntiCheatAlert from "../components/AntiCheatAlert.vue";
import CodeEditor from "../components/CodeEditor.vue";
import { useAntiCheatStatus } from "../hooks/useAntiCheatStatus";

/* -----------------------------
   🎤 녹음 관련 상태
----------------------------- */
let audioStream = null;
let mediaRecorder = null;
let audioChunks = [];
const audioBlob = ref(null);
const isRecording = ref(false);
//STT 진행 중 여부
const isSttRunning = ref(false);

/* -----------------------------
   🔥 버튼 클릭 로직
   - isRecording = false → 녹음 시작
   - isRecording = true → 녹음 종료 + STT 실행
----------------------------- */
const onAskButtonClick = async () => {
  // STT 처리 중일 땐 아예 무시
  if (isSttRunning.value) return;

  if (!isRecording.value) {
    // 질문하기 → 녹음 시작
    await startRecording();
    isRecording.value = true;
  } else {
    // 제출 → 녹음 종료 + STT 실행
    await stopRecording();
    isRecording.value = false;

    isSttRunning.value = true;      // 🔥 STT 시작
    try {
      await runSttClient();         // STT 끝날 때까지 버튼 비활성화
    } finally {
      isSttRunning.value = false;   // 🔥 STT 종료 후 다시 활성화
    }
  }
};

/* -----------------------------
   🎙️ 녹음 시작
----------------------------- */
const startRecording = async () => {
  try {
    audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(audioStream);
    audioChunks = [];

    mediaRecorder.ondataavailable = (e) => {
      audioChunks.push(e.data);
    };

    mediaRecorder.onstop = () => {
      audioBlob.value = new Blob(audioChunks, { type: "audio/webm" });
      console.log("🎤 녹음 완료:", audioBlob.value);
    };

    mediaRecorder.start();
    console.log("🎙️ 녹음 시작됨");
  } catch (err) {
    console.error("마이크 오류:", err);
    showAntiCheat("micError", "마이크 접근 권한이 필요합니다.");
  }
};

/* -----------------------------
   ⏹녹음 종료
----------------------------- */
const stopRecording = () => {
  return new Promise((resolve) => {
    if (!mediaRecorder || mediaRecorder.state === "inactive") {
      console.log("이미 녹음 중이 아님");
      resolve();
      return;
    }

    // ⬇️ 여기서 onstop에서 Blob 만들고 resolve
    mediaRecorder.onstop = () => {
      audioBlob.value = new Blob(audioChunks, { type: "audio/webm" });
      console.log("🎤 녹음 완료:", audioBlob.value);
      if (audioStream) {
        audioStream.getTracks().forEach((t) => t.stop());
        audioStream = null;
      }
      resolve();
    };

    mediaRecorder.stop();
    console.log("⏹ 녹음 종료 요청");
  });
};

/* -----------------------------
   📤 서버 전송 & STT 실행
----------------------------- */
const runSttClient = async () => {
  if (!audioBlob.value) {
    showAntiCheat("sttError", "녹음된 음성이 없습니다.");
    return;
  }

  try {
    const res = await fetch("http://localhost:8000/api/stt/run/", {
      method: "POST",
      // raw PCM/웹엠 바이트 그대로 보낼 거라 헤더 안 넣는 게 안전
      // headers: { "Content-Type": "application/octet-stream" },
      body: audioBlob.value,
    });

    const data = await res.json();
    console.log("STT 결과:", data);

    if (data.lines) {
      const text = data.lines.map(l => l.text || "").join(" ");
      console.log("최종 텍스트:", text);
    } else {
      showAntiCheat("sttError", "STT 결과가 올바르지 않습니다.");
    }
  } catch (err) {
    console.error("STT 요청 실패:", err);
    showAntiCheat("sttError", "서버 통신 오류");
  }
};


/* -----------------------------
  ✂ 이하 기존 코드 유지
----------------------------- */

const selectedLanguage = ref("c");
const code = ref("");
const languageTemplates = {
  python3: `def solution():\n    answer = 0\n    # TODO\n    return answer\n`,
  java: `class Solution {\n    public int solution() {\n        int answer = 0;\n        return answer;\n    }\n}\n`,
  c: `#include <stdio.h>\nint solution() { return 0; }\n`,
  cpp: `#include <bits/stdc++.h>\nusing namespace std;\nint solution() { return 0; }\n`,
};

watch(selectedLanguage, (lang) => {
  code.value = languageTemplates[lang];
});

const currentFilename = computed(() => {
  switch (selectedLanguage.value) {
    case "python3": return "solution.py";
    case "java": return "Solution.java";
    case "c": return "solution.c";
    case "cpp": return "solution.cpp";
    default: return "solution.txt";
  }
});

const cmMode = computed(() => {
  switch (selectedLanguage.value) {
    case "python3": return "python";
    case "java": return "text/x-java";
    case "c": return "text/x-csrc";
    case "cpp": return "text/x-c++src";
    default: return "text/plain";
  }
});

const {
  alert: antiCheatAlert,
  setState: setAntiCheatState,
  resetState: resetAntiCheatState
} = useAntiCheatStatus();

const showAntiCheat = (key, detail) => {
  setAntiCheatState(key, { detail, timestamp: Date.now() });
  setTimeout(() => resetAntiCheatState(), 7000);
};

const videoRef = ref(null);
const cameraError = ref("");
let mediaStreamVideo = null;

onMounted(async () => {
  try {
    mediaStreamVideo = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 360 },
      audio: false,
    });
    if (videoRef.value) {
      videoRef.value.srcObject = mediaStreamVideo;
      await videoRef.value.play();
    }
  } catch (err) {
    cameraError.value = "웹캠 권한을 허용해 주세요.";
  }
});

onBeforeUnmount(() => {
  if (mediaStreamVideo) {
    mediaStreamVideo.getTracks().forEach((t) => t.stop());
  }
});
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap");

.session-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #111827;
  color: #e5e7eb;
  font-family: "Nunito", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.session-header {
  padding: 14px 28px;
  border-bottom: 1px solid #1f2937;
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.session-header h1 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
}

.session-subtitle {
  margin: 0;
  font-size: 13px;
  color: #9ca3af;
}

.session-main {
  flex: 1;
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 1.6fr);
  gap: 1px;
  background: #030712;
}

.left-column {
  display: flex;
  flex-direction: column;
}

.camera-pane,
.problem-pane,
.editor-pane {
  display: flex;
  flex-direction: column;
  background: #020617;
}

.pane-header {
  padding: 10px 18px;
  border-bottom: 1px solid #1e293b;
  font-size: 13px;
  color: #9ca3af;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.pane-title {
  font-weight: 600;
}

.problem-body {
  padding: 16px 20px 20px;
  overflow-y: auto;
}

.camera-body {
  flex: 0 0 auto;
  padding: 12px 18px 8px;
  display: flex;
  justify-content: center;
  flex-direction: column;
  align-items: center;
}

.camera-placeholder {
  width: auto;
  height: auto;
  border-radius: 16px;
  border: 1px solid #374151;
  overflow: hidden;
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle at 0 0, #020617, #020617 40%, #020617);
}

.camera-placeholder video {
  width: 260px;
  aspect-ratio: 16 / 9;
  border-radius: 14px;
  object-fit: cover;
  box-shadow: 0 10px 25px rgba(15, 23, 42, 0.7);
}

.camera-placeholder .camera-message {
  font-size: 5px;
  color: #e5e7eb;
  background: rgba(15, 23, 42, 0.6);
  padding: 4px 5px;
  border-radius: 999px;
  margin-top: 6px;
}

.problem-title {
  margin: 0 0 12px;
  font-size: 18px;
  color: #f9fafb;
}

.problem-subtitle {
  margin: 16px 0 6px;
  font-size: 14px;
  color: #e5e7eb;
}

.problem-text {
  margin: 0 0 10px;
  font-size: 13px;
  line-height: 1.6;
  color: #d1d5db;
}

.problem-list {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  color: #d1d5db;
}

.editor-header {
  justify-content: space-between;
}

.tab {
  padding: 4px 10px;
  border-radius: 999px;
  background: #0f172a;
  font-size: 12px;
  color: #e5e7eb;
}

.editor-options {
  font-size: 12px;
  color: #9ca3af;
}

.lang-select {
  background: transparent;
  border: none;
  color: #9ca3af;
  font-size: 12px;
  padding: 2px 4px;
  outline: none;
}

.lang-select option {
  color: #0f172a;
}

.editor-body {
  flex: 1;
  padding: 12px 16px 0;
  background: #020617;
}

.editor-footer {
  padding: 8px 18px 12px;
  border-top: 1px solid #1f2937;
  display: flex;
  align-items: center;
  gap: 12px;
}

.run-button {
  padding: 6px 14px;
  border-radius: 999px;
  border: none;
  background: #22c55e;
  color: #022c22;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.hint {
  font-size: 12px;
  color: #9ca3af;
}

@media (max-width: 900px) {
  .session-main {
    grid-template-columns: 1fr;
  }

  .code-editor {
    height: 260px;
  }
}
</style>
