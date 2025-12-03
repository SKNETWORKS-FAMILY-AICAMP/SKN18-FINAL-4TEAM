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
            <span v-if="isLoading" class="small-label">불러오는 중...</span>
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
          <CodeEditor
            v-model="code"
            :mode="cmMode"
            @editor-keydown="handleEditorKeydown"
            @editor-copy="handleCopy"
          />
        </div>
        <footer class="editor-footer">
          <button type="button" class="run-button">실행하기</button>
          <span class="hint">실행 결과는 추후 연동 예정</span>
        </footer>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import AntiCheatAlert from "../components/AntiCheatAlert.vue";
import CodeEditor from "../components/CodeEditor.vue";
import { useAntiCheatStatus } from "../hooks/useAntiCheatStatus";

<<<<<<< HEAD
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
=======
const BACKEND_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
>>>>>>> origin/dev

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

const {
  alert: antiCheatAlert,
  setState: setAntiCheatState,
  resetState: resetAntiCheatState
} = useAntiCheatStatus();

const isLoading = ref(true);
const loadError = ref("");
const problem = ref(null);
const introText = ref("");
const ttsAudioSrc = ref("");
const ttsError = ref("");
const langgraphError = ref("");
const ttsAudioRef = ref(null);
const ttsInlinePlayer = ref(null);
const needManualPlay = ref(false);
const ttsChunks = ref([]);
const currentChunkIdx = ref(0);
let inlineOnEnded = null;

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
    case "python3":
      return "solution.py";
    case "java":
      return "Solution.java";
    case "c":
      return "solution.c";
    case "cpp":
      return "solution.cpp";
    default:
      return "solution.txt";
  }
});

const cmMode = computed(() => {
  switch (selectedLanguage.value) {
    case "python3":
      return "python";
    case "java":
      return "text/x-java";
    case "c":
      return "text/x-csrc";
    case "cpp":
      return "text/x-c++src";
    default:
      return "text/plain";
  }
});

const videoRef = ref(null);
const cameraError = ref("");
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

const playTts = async () => {
  if (!ttsAudioRef.value) return;
  try {
    needManualPlay.value = false;
    await ttsAudioRef.value.play();
  } catch (err) {
    // 브라우저 오토플레이 차단 시 수동 재생 유도
    needManualPlay.value = true;
    console.warn("TTS auto-play blocked:", err);
  }
};

const playTtsInline = async () => {
  if (!ttsAudioSrc.value) return;
  if (!ttsInlinePlayer.value) {
    ttsInlinePlayer.value = new Audio();
    ttsInlinePlayer.value.playsInline = true;
    ttsInlinePlayer.value.autoplay = true;
    ttsInlinePlayer.value.loop = false;
    inlineOnEnded = async () => {
      const nextIdx = currentChunkIdx.value + 1;
      if (nextIdx >= ttsChunks.value.length) return;
      currentChunkIdx.value = nextIdx;
      await setAudioByIndex(nextIdx);
    };
    ttsInlinePlayer.value.addEventListener("ended", () => {
      void inlineOnEnded?.();
    });
  }
  try {
    ttsInlinePlayer.value.src = ttsAudioSrc.value;
    needManualPlay.value = false;
    await ttsInlinePlayer.value.play();
  } catch (err) {
    needManualPlay.value = true;
    console.warn("Inline TTS auto-play blocked:", err);
  }
};

const setAudioByIndex = async (idx) => {
  const chunk = ttsChunks.value[idx];
  if (!chunk) return false;
  ttsAudioSrc.value = `data:audio/mp3;base64,${chunk}`;
  await nextTick();
  await playTtsInline();
  return true;
};

const loadSession = async () => {
  isLoading.value = true;
  loadError.value = "";
  try {
    const resp = await fetch(`${API_BASE}/api/coding-test/session/`);
    const data = await resp.json();
    if (!resp.ok) {
      throw new Error(data.detail || "세션 데이터를 불러오지 못했습니다.");
    }

    problem.value = data.problem;
    introText.value = data.langgraph?.current_question_text || "";
    langgraphError.value = data.langgraph?.error || "";
    ttsError.value = data.tts?.error || "";

    const chunkList = Array.isArray(data.tts?.chunks) ? data.tts.chunks : [];
    const audioList = chunkList
      .map((item) => item?.audio_base64)
      .filter(Boolean);
    ttsChunks.value = audioList;
    currentChunkIdx.value = 0;

    if (audioList.length > 0) {
      await setAudioByIndex(0);
    } else {
      ttsAudioSrc.value = "";
    }
  } catch (err) {
    console.error(err);
    loadError.value = err.message || "세션 데이터를 불러오지 못했습니다.";
  } finally {
    isLoading.value = false;
  }
};

onMounted(async () => {
<<<<<<< HEAD
  await loadSession();
=======
  void fetchRandomProblem();
>>>>>>> origin/dev
  try {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      cameraError.value = "이 브라우저에서는 웹캠을 사용할 수 없습니다.";
      showAntiCheat("cameraBlocked", cameraError.value);
      return;
    }
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 360 },
      audio: false
    });

    mediaStream.getVideoTracks().forEach((track) => {
      track.onended = () => {
        cameraError.value = "웹캠 연결이 중단되었습니다.";
        showAntiCheat("cameraBlocked", cameraError.value);
        lastCameraStatus = "blocked";
      };
    });

    if (videoRef.value) {
      videoRef.value.srcObject = mediaStream;
      await videoRef.value.play();
    }
    startWebcamMonitor();
    mediapipeInterval = setInterval(() => {
      void sendFrameForMediapipe();
    }, 5000);
  } catch (err) {
    cameraError.value = "웹캠 권한을 허용해 주세요.";
    showAntiCheat("cameraBlocked", cameraError.value);
    console.error(err);
  }

  window.addEventListener("blur", handleWindowBlur);
  document.addEventListener("visibilitychange", handleVisibilityChange);
  document.addEventListener("paste", handlePaste);
  document.addEventListener("copy", handleCopy);
});

onBeforeUnmount(() => {
  if (mediaStream) {
    mediaStream.getTracks().forEach((t) => t.stop());
    mediaStream = null;
  }
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

<<<<<<< HEAD
.small-label {
  font-size: 12px;
  color: #9ca3af;
}

.error-text {
  color: #fca5a5;
  font-size: 13px;
  margin: 0 0 8px;
}

.tts-block {
  margin-top: 16px;
}

.tts-audio {
  margin-top: 8px;
  width: 100%;
=======
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
>>>>>>> origin/dev
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
