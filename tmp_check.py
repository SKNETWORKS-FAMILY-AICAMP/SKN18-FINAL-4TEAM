
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import AntiCheatAlert from "../components/AntiCheatAlert.vue";
import CodeEditor from "../components/CodeEditor.vue";
import { useAntiCheatStatus } from "../hooks/useAntiCheatStatus";

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
const introText = ref("");
const ttsError = ref("");
const langgraphError = ref("");
const ttsAudioSrc = ref("");
const ttsInlinePlayer = ref(null);
const needManualPlay = ref(false);
const ttsChunks = ref([]);
const currentChunkIdx = ref(0);
let inlineOnEnded = null;
let userInteractListener = null;

const {
  alert: antiCheatAlert,
  setState: setAntiCheatState,
  resetState: resetAntiCheatState
} = useAntiCheatStatus();

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

const tryResumeTts = async () => {
  if (!needManualPlay.value || !ttsAudioSrc.value) return;
  await playTtsInline();
};

const fetchRandomProblem = async () => {
  isLoadingProblem.value = true;
  problemError.value = "";

  try {
    const resp = await fetch(`${BACKEND_BASE}/api/coding-test/session/?language=python`);
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      throw new Error(data?.detail || "세션 데이터를 불러오지 못했습니다.");
    }

    problemData.value = data.problem;
    if (selectedLanguage.value !== "python3") {
      selectedLanguage.value = "python3";
    }
    if (data.problem?.starter_code) {
      code.value = data.problem.starter_code;
    } else if (selectedLanguage.value === "python3") {
      code.value = languageTemplates.python3;
    }

    introText.value = data.langgraph?.current_question_text || "";
    langgraphError.value = data.langgraph?.error || "";
    ttsError.value = data.tts?.error || "";

    const chunkList = Array.isArray(data.tts?.chunks) ? data.tts.chunks : [];
    const audioList = chunkList
      .map((item) => (typeof item === "string" ? item : item?.audio_base64))
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
    problemError.value = err?.message || "세션 데이터를 불러오지 못했습니다.";
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

onMounted(async () => {
  void fetchRandomProblem();
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
  userInteractListener = () => {
    void tryResumeTts();
  };
  document.addEventListener("click", userInteractListener);
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
  if (userInteractListener) {
    document.removeEventListener("click", userInteractListener);
    userInteractListener = null;
  }
  clearAntiCheatTimer();
});
