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
            <div v-if="isLoadingProblem" class="problem-status">문제를 불러오는 중입니다.</div>
            <div v-else-if="problemError" class="problem-status error">
              <p>{{ problemError }}</p>
              <button type="button" class="retry-button" @click="fetchRandomProblem">다시 시도</button>
            </div>
            <div v-else-if="problemData" class="problem-content">
              <h2 class="problem-title">실전 문제</h2>
              <p v-for="(para, idx) in problemParagraphs" :key="idx" class="problem-text">
                {{ para }}
              </p>

              <div v-if="displayedTestCases.length" class="testcase-block">
                <h3 class="problem-subtitle">예시 테스트 케이스</h3>
                <ul class="testcase-list">
                  <li v-for="tc in displayedTestCases" :key="tc.id" class="testcase-item">
                    <div class="testcase-label">입력</div>
                    <pre>{{ tc.input }}</pre>
                    <div class="testcase-label">출력</div>
                    <pre>{{ tc.output }}</pre>
                  </li>
                </ul>
              </div>
            </div>
            <div v-else class="problem-status">표시할 문제가 없습니다.</div>
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

<<<<<<< HEAD
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
=======
const BACKEND_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

const languageTemplates = {
  python3: `def solution():\n    answer = 0\n    # TODO: 코드를 작성하세요.\n    return answer\n`,
  java: `class Solution {\n    public int solution() {\n        int answer = 0;\n        // TODO: 코드를 작성하세요.\n        return answer;\n    }\n}\n`,
  c: `#include <stdio.h>\n\nint solution() {\n    int answer = 0;\n    // TODO: 코드를 작성하세요.\n    return answer;\n}\n`,
  cpp: `#include <bits/stdc++.h>\nusing namespace std;\n\nint solution() {\n    int answer = 0;\n    // TODO: 코드를 작성하세요.\n    return answer;\n}\n`
};

const selectedLanguage = ref("python3");
const code = ref(languageTemplates[selectedLanguage.value]);
const problemData = ref(null);
const isLoadingProblem = ref(false);
const problemError = ref("");
>>>>>>> cd7d63074ca89914ae1dbe3bff73314c77846e6b

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
  if (lang === "python3" && problemData.value?.starter_code) {
    code.value = problemData.value.starter_code;
    return;
  }
  code.value = languageTemplates[lang] || languageTemplates.python3;
});

const problemParagraphs = computed(() => {
  if (!problemData.value?.problem) return [];
  return problemData.value.problem
    .replace(/\r\n?/g, "\n")
    .split(/\n{2,}/)         
    .map((p) => p.replace(/\n/g, " ").trim())
    .filter(Boolean);
});

const displayedTestCases = computed(() => {
  if (!problemData.value?.test_cases?.length) return [];
  return problemData.value.test_cases.slice(0, 3);
});

const fetchRandomProblem = async () => {
  isLoadingProblem.value = true;
  problemError.value = "";

  try {
    const resp = await fetch(`${BACKEND_BASE}/api/coding-problems/random/?language=python`);
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      throw new Error(data?.detail || "문제를 불러오지 못했습니다.");
    }

    problemData.value = data;
    if (selectedLanguage.value !== "python3") {
      selectedLanguage.value = "python3";
    }
    if (data.starter_code) {
      code.value = data.starter_code;
    } else if (selectedLanguage.value === "python3") {
      code.value = languageTemplates.python3;
    }
  } catch (err) {
    console.error(err);
    problemError.value = err?.message || "문제를 불러오지 못했습니다.";
  } finally {
    isLoadingProblem.value = false;
  }
};

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
<<<<<<< HEAD
let mediaStreamVideo = null;
=======
let mediaStream = null;
let antiCheatTimer = null;
let webcamMonitor = null;
let mediapipeInterval = null;
let keyTimestamps = [];
let lastAbnormalAlert = 0;
let lastCopyAlert = 0;
let lastCameraStatus = "ok";

const KEY_WINDOW_MS = 2000;
const KEY_THRESHOLD = 12;
const ABNORMAL_COOLDOWN_MS = 8000;
const COPY_COOLDOWN_MS = 4000;

const clearAntiCheatTimer = () => {
  if (antiCheatTimer) {
    clearTimeout(antiCheatTimer);
    antiCheatTimer = null;
  }
};

const showAntiCheat = (stateKey, detail) => {
  clearAntiCheatTimer();
  setAntiCheatState(stateKey, { detail, timestamp: Date.now() });
  antiCheatTimer = setTimeout(() => {
    resetAntiCheatState();
    antiCheatTimer = null;
  }, 7000);
};

const handleVisibilityChange = () => {
  if (document.visibilityState === "hidden") {
    showAntiCheat("tabSwitch", "시험 화면을 벗어났습니다.");
  }
};

const handleWindowBlur = () => {
  showAntiCheat("windowBlur", "다른 창으로 이동이 감지되었습니다.");
};

const handlePaste = () => {
  showAntiCheat("pasteDetected", "외부 붙여넣기 시도가 감지되었습니다.");
};

const handleCopy = () => {
  const now = Date.now();
  if (now - lastCopyAlert < COPY_COOLDOWN_MS) return;
  lastCopyAlert = now;
  showAntiCheat("copyDetected", "코드 편집기에서 복사 동작이 감지되었습니다.");
};

const sendFrameForMediapipe = async () => {
  const video = videoRef.value;
  if (!video || video.readyState < 2) return;

  const canvas = document.createElement("canvas");
  canvas.width = 320;
  canvas.height = 180;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const vw = video.videoWidth || 640;
  const vh = video.videoHeight || 360;
  const scale = Math.min(canvas.width / vw, canvas.height / vh);
  const dw = vw * scale;
  const dh = vh * scale;
  const dx = (canvas.width - dw) / 2;
  const dy = (canvas.height - dh) / 2;

  ctx.drawImage(video, dx, dy, dw, dh);

  canvas.toBlob(async (blob) => {
    if (!blob) return;

    const formData = new FormData();
    formData.append("image", blob, "frame.jpg");

    try {
      const resp = await fetch(`${BACKEND_BASE}/mediapipe/analyze/`, {
        method: "POST",
        body: formData
      });

      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) {
        console.error("mediapipe analyze error:", data);
        return;
      }

      if (data.is_cheating) {
        const detail =
          data.reason || "카메라 분석 결과 의심스러운 행동이 감지되었습니다.";
        showAntiCheat("mediapipeCheat", detail);
      }
    } catch (err) {
      console.error("mediapipe analyze request failed:", err);
    }
  }, "image/jpeg", 0.6);
};

const handleEditorKeydown = (event) => {
  const now = Date.now();
  if ((event.ctrlKey || event.metaKey) && event.key?.toLowerCase() === "c") {
    handleCopy();
    return;
  }

  keyTimestamps.push(now);
  keyTimestamps = keyTimestamps.filter((ts) => now - ts <= KEY_WINDOW_MS);

  if (
    keyTimestamps.length >= KEY_THRESHOLD &&
    now - lastAbnormalAlert >= ABNORMAL_COOLDOWN_MS
  ) {
    lastAbnormalAlert = now;
    showAntiCheat(
      "abnormalInput",
      `최근 ${KEY_WINDOW_MS / 1000}초간 ${keyTimestamps.length}회의 빠른 키 입력이 감지되었습니다.`
    );
  }
};

const startWebcamMonitor = () => {
  if (webcamMonitor) {
    clearInterval(webcamMonitor);
    webcamMonitor = null;
  }
  webcamMonitor = setInterval(() => {
    const hasLiveTrack =
      mediaStream &&
      mediaStream.getVideoTracks().some((track) => track.readyState === "live");

    if (!hasLiveTrack) {
      cameraError.value = "웹캠 연결이 중단되었습니다.";
      if (lastCameraStatus !== "blocked") {
        showAntiCheat("cameraBlocked", cameraError.value);
        lastCameraStatus = "blocked";
      }
    } else {
      lastCameraStatus = "ok";
    }
  }, 5000);
};

const stopWebcamMonitor = () => {
  if (webcamMonitor) {
    clearInterval(webcamMonitor);
    webcamMonitor = null;
  }
};
>>>>>>> cd7d63074ca89914ae1dbe3bff73314c77846e6b

onMounted(async () => {
  void fetchRandomProblem();
  try {
    mediaStreamVideo = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 360 },
      audio: false,
    });
    if (videoRef.value) {
      videoRef.value.srcObject = mediaStreamVideo;
      await videoRef.value.play();
    }
<<<<<<< HEAD
=======
    startWebcamMonitor();
    mediapipeInterval = setInterval(() => {
      void sendFrameForMediapipe();
    }, 5000);
>>>>>>> cd7d63074ca89914ae1dbe3bff73314c77846e6b
  } catch (err) {
    cameraError.value = "웹캠 권한을 허용해 주세요.";
  }
});

onBeforeUnmount(() => {
  if (mediaStreamVideo) {
    mediaStreamVideo.getTracks().forEach((t) => t.stop());
  }
<<<<<<< HEAD
=======
  stopWebcamMonitor();
  if (mediapipeInterval) {
    clearInterval(mediapipeInterval);
    mediapipeInterval = null;
  }
  window.removeEventListener("blur", handleWindowBlur);
  document.removeEventListener("visibilitychange", handleVisibilityChange);
  document.removeEventListener("paste", handlePaste);
  document.removeEventListener("copy", handleCopy);
  clearAntiCheatTimer();
>>>>>>> cd7d63074ca89914ae1dbe3bff73314c77846e6b
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

.retry-button {
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid #1f2937;
  background: #0f172a;
  color: #e5e7eb;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.15s ease, transform 0.15s ease;
}

.retry-button:hover {
  background: #111827;
  transform: translateY(-1px);
}

.problem-status {
  border: 1px solid #1e293b;
  background: #0b1220;
  color: #cbd5e1;
  padding: 12px;
  border-radius: 12px;
  font-size: 13px;
  text-align: center;
}

.problem-status.error {
  border-color: #4b2835;
  color: #fca5a5;
  background: #190c11;
}

.problem-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
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

.testcase-block {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #1f2937;
}

.testcase-list {
  list-style: none;
  padding: 0;
  margin: 8px 0 0;
  display: grid;
  gap: 10px;
}

.testcase-item {
  border: 1px solid #1f2937;
  background: #0c1221;
  border-radius: 12px;
  padding: 10px;
}

.testcase-label {
  font-size: 11px;
  color: #9ca3af;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  margin-bottom: 4px;
}

.testcase-item pre {
  background: #0f172a;
  border-radius: 10px;
  padding: 8px;
  color: #e5e7eb;
  font-size: 12px;
  white-space: pre-wrap;
  margin: 0 0 8px;
  overflow-x: auto;
}

.testcase-item pre:last-of-type {
  margin-bottom: 0;
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
