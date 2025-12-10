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
      <div class="session-title-block">
        <h1>JobTory Live Coding</h1>
        <p class="session-subtitle">실전 환경에서 문제를 풀어보세요.</p>
      </div>
      <div class="timer-chip">
        남은 시간
        <span class="timer-value">{{ formattedRemainingTime }}</span>
      </div>
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
          <CodeEditor
            v-model="code"
            :mode="cmMode"
            @editor-keydown="handleEditorKeydown"
            @editor-copy="handleCopy"
          />
        </div>
        <footer class="editor-footer">
          <div class="footer-left">
            <button
              type="button"
              class="mic-button"
              @click="onAskButtonClick"
            :disabled="isSttRunning"
            :class="{ 'is-active': isRecording }"
          >
            <span class="mic-label">
              {{ isSttRunning ? "분석 중..." : (isRecording ? "제출하기" : "음성입력") }}
            </span>
          </button>
            <button type="button" class="hint-button" @click="requestHint">힌트요청</button>
            <span class="hint-counter">힌트 3/3</span>
            <span v-if="answerCountdown !== null" class="hint countdown-inline">
              {{ answerCountdown }}초 후 자동 답변 시작
            </span>
          </div>
          <div class="footer-right">
            <button type="button" class="run-button">실행하기</button>
            <span class="hint">실행 결과는 추후 연동 예정</span>
          </div>
        </footer>
      </section>
    </main>

    <!-- 30초 카운트다운 오버레이 -->
    <div v-if="answerCountdown !== null" class="countdown-overlay">
      <div class="countdown-ring">
        <svg :width="ringSize" :height="ringSize">
          <circle
            class="ring-bg"
            :r="ringRadius"
            :cx="ringSize / 2"
            :cy="ringSize / 2"
          />
          <circle
            class="ring-progress"
            :r="ringRadius"
            :cx="ringSize / 2"
            :cy="ringSize / 2"
            :stroke-dasharray="ringCircumference"
            :stroke-dashoffset="ringStrokeOffset"
          />
        </svg>
        <div class="countdown-text">{{ answerCountdown }}</div>
      </div>
      <p class="countdown-helper">곧 답변 녹음이 자동으로 시작됩니다</p>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import AntiCheatAlert from "../components/AntiCheatAlert.vue";
import CodeEditor from "../components/CodeEditor.vue";
import { useAntiCheatStatus } from "../hooks/useAntiCheatStatus";

const BACKEND_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const route = useRoute();
const router = useRouter();

const {
  alert: antiCheatAlert,
  setState: setAntiCheatState,
  resetState: resetAntiCheatState,
} = useAntiCheatStatus();


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
const isTtsPlaying = ref(false);
const answerCountdown = ref(null);
let answerCountdownTimer = null;
const ANSWER_COUNTDOWN_SECONDS = 30;
const ringRadius = 46;
const ringSize = 140;
const ringCircumference = 2 * Math.PI * ringRadius;
const hasPlayedIntroTts = ref(false);
const introSecondChanceUsed = ref(false);

/* -----------------------------
   🔥 버튼 클릭 로직
   - isRecording = false → 녹음 시작
   - isRecording = true → 녹음 종료 + STT 실행
----------------------------- */
const onAskButtonClick = async () => {
  // STT 처리 중이면 무시
  if (isSttRunning.value) return;

  if (!isRecording.value) {
    // 수동으로 질문하기 버튼을 눌렀을 때 녹음 시작
    await startRecording();
    isRecording.value = true;
    return;
  }

  // 녹음 중일 때만 제출 → 녹음 종료 + STT 실행
  await stopRecording();
  isRecording.value = false;

  isSttRunning.value = true;
  try {
    await runSttClient();
  } finally {
    isSttRunning.value = false;
  }
};

const onAnswerButtonClick = async () => {
  clearAnswerCountdown();
  if (isSttRunning.value || isRecording.value) return;
  await startRecording();
  isRecording.value = true;
};

const startAnswerCountdown = (seconds = 30) => {
  clearAnswerCountdown();
  answerCountdown.value = seconds;
  answerCountdownTimer = setInterval(() => {
    if (answerCountdown.value === null) return;
    answerCountdown.value -= 1;
    if (answerCountdown.value <= 0) {
      clearAnswerCountdown();
      void onAnswerButtonClick(); // 자동으로 녹음 시작 (제출은 수동)
    }
  }, 1000);
};

const clearAnswerCountdown = () => {
  if (answerCountdownTimer) {
    clearInterval(answerCountdownTimer);
    answerCountdownTimer = null;
  }
  answerCountdown.value = null;
};

const ringStrokeOffset = computed(() => {
  if (answerCountdown.value === null) return ringCircumference;
  const progress = Math.max(
    0,
    Math.min(1, answerCountdown.value / ANSWER_COUNTDOWN_SECONDS)
  );
  return ringCircumference * (1 - progress);
});

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

  const sessionId = route.query.session_id;
  if (!sessionId) {
    showAntiCheat("sttError", "session_id가 없습니다. 세션을 다시 시작해 주세요.");
    return;
  }

  const token = localStorage.getItem("jobtory_access_token");

  try {
    // 1단계: STT 전용 엔드포인트로 음성 → 텍스트 변환
    const sttResp = await fetch(
      `${BACKEND_BASE}/api/stt/transcribe/?session_id=${encodeURIComponent(
        sessionId
      )}`,
      {
        method: "POST",
        // raw webm 바이트 그대로 전송
        body: audioBlob.value,
      }
    );

    const sttData = await sttResp.json().catch(() => ({}));
    if (!sttResp.ok) {
      console.warn("STT 요청 실패", sttResp.status, sttData);
      showAntiCheat("sttError", sttData?.error || "음성을 인식하지 못했습니다.");
      return;
    }

    const sttText = (sttData?.stt_text || "").trim();
    console.log("STT 결과:", sttData);

    if (!sttText) {
      showAntiCheat("sttError", "음성에서 유효한 문장을 인식하지 못했습니다.");
      return;
    }

    // 2단계: STT 텍스트를 LangGraph 이벤트 API에 전달
    const eventResp = await fetch(`${BACKEND_BASE}/api/interview/event/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        session_id: sessionId,
        stt_text: sttText,
      }),
    });
    const eventData = await eventResp.json().catch(() => ({}));
    console.log("Interview event 결과:", eventData);

    if (!eventResp.ok) {
      console.warn("Interview event 호출 실패", eventResp.status, eventData);
      showAntiCheat("sttError", eventData?.detail || "응답을 생성하지 못했습니다.");
      return;
    }

    const replyText = (eventData?.tts_text || "").trim();
    const userAnswerClass = (eventData?.user_answer_class || "").trim();
    const introFlowDone = Boolean(eventData?.intro_flow_done);

    const isFirstNonStrategy =
      introFlowDone && userAnswerClass !== "strategy" && !introSecondChanceUsed.value;
    const shouldEndIntro =
      introFlowDone && userAnswerClass !== "strategy" && !isFirstNonStrategy;

    // intro_flow_done인데 이미 한 번 기회를 준 뒤에도 strategy가 아니면 종료
    if (shouldEndIntro) {
      await endSessionAndReturnToCodingTest("intro_flow_done_without_strategy");
      return;
    }

    const allowTts =
      replyText &&
      userAnswerClass !== "strategy" &&
      (!introFlowDone || isFirstNonStrategy);

    if (allowTts) {
      if (isFirstNonStrategy) {
        introSecondChanceUsed.value = true;
      }
      try {
        const ttsResp = await fetch(
          `${BACKEND_BASE}/api/tts/intro/?session_id=${encodeURIComponent(
            sessionId
          )}`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            // 답변/피드백은 너무 길게 읽지 않도록 최대 문장 수를 제한
            body: JSON.stringify({ tts_text: replyText, max_sentences: 2 }),
          }
        );
        const ttsData = await ttsResp.json().catch(() => ({}));
        if (!ttsResp.ok) {
          console.warn("응답 TTS 생성 실패", ttsResp.status, ttsData);
          return;
        }
        const chunks = Array.isArray(ttsData?.tts_text) ? ttsData.tts_text : [];
        if (chunks.length) {
          await playTtsChunks(chunks);
        }
      } catch (err) {
        console.error("응답 TTS 요청/재생 오류:", err);
      }
    }
  } catch (err) {
    console.error("STT 요청 실패:", err);
    showAntiCheat("sttError", "서버 통신 오류");
  }
};

/* -----------------------------
  🔊 TTS: 문제 안내 자동 재생
------------------------------ */
const playTtsChunks = async (chunks = []) => {
  for (const chunk of chunks) {
    if (!chunk?.audio) continue;
    const audio = new Audio(`data:audio/mp3;base64,${chunk.audio}`);
    try {
      await audio.play();
    } catch (err) {
      console.error("TTS 재생 실패:", err);
      break;
    }
    await new Promise((resolve) => {
      audio.onended = resolve;
      audio.onerror = resolve;
    });
  }
};

const requestAndPlayTts = async (problemPayload) => {
  if (!problemPayload || isTtsPlaying.value || hasPlayedIntroTts.value) return;
  const token = localStorage.getItem("jobtory_access_token");
  const sessionId = route.query.session_id;
  if (!token) {
    console.warn("TTS 요청을 위해 로그인 토큰이 필요합니다.");
    return;
  }
  if (!sessionId) {
    console.warn("TTS 요청에 session_id가 필요합니다.");
    return;
  }
  isTtsPlaying.value = true;
  try {
    // 1단계: 문제 + 인트로 텍스트만 LangGraph에서 받아오기
    const initResp = await fetch(
      `${BACKEND_BASE}/api/coding-problems/session/init/?session_id=${encodeURIComponent(
        sessionId
      )}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(problemPayload),
      }
    );
    const initData = await initResp.json().catch(() => ({}));
    if (!initResp.ok) {
      console.error("TTS 인트로 텍스트 요청 실패:", initData);
      // TTS 재생이 실패해도 카운트다운은 진행
      hasPlayedIntroTts.value = true;
      startAnswerCountdown(ANSWER_COUNTDOWN_SECONDS);
      return;
    }

    const introText = (initData && initData.tts_text) || "";
    if (!introText) {
      // 인트로 텍스트가 없어도 타이머는 시작
      hasPlayedIntroTts.value = true;
      startAnswerCountdown(ANSWER_COUNTDOWN_SECONDS);
      return;
    }

    // 2단계: 인트로 텍스트를 TTS 전용 API에 보내어 오디오만 생성
    const ttsResp = await fetch(
      `${BACKEND_BASE}/api/tts/intro/?session_id=${encodeURIComponent(
        sessionId
      )}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        // 인트로 안내도 너무 길지 않게 2문장 정도만 읽도록 제한해
        // 첫 오디오가 나오는 시간을 줄입니다.
        body: JSON.stringify({ tts_text: introText, max_sentences: 2 }),
      }
    );
    const ttsData = await ttsResp.json().catch(() => ({}));
    if (!ttsResp.ok) {
      console.error("TTS 오디오 생성 요청 실패:", ttsData);
      hasPlayedIntroTts.value = true;
      startAnswerCountdown(ANSWER_COUNTDOWN_SECONDS);
      return;
    }

    const chunks = Array.isArray(ttsData?.tts_text) ? ttsData.tts_text : [];
    if (chunks.length) {
      await playTtsChunks(chunks);
      hasPlayedIntroTts.value = true;
      startAnswerCountdown(ANSWER_COUNTDOWN_SECONDS);
    } else {
      // 오디오 청크가 없어도 타이머는 시작
      hasPlayedIntroTts.value = true;
      startAnswerCountdown(ANSWER_COUNTDOWN_SECONDS);
    }
  } catch (err) {
    console.error("TTS 요청/재생 오류:", err);
  } finally {
    isTtsPlaying.value = false;
  }
};

/* -----------------------------
  ✂ 이하 기존 코드 유지
----------------------------- */
const languageTemplates = {
  python3: `def solution():\n    answer = 0\n    # TODO: 코드를 작성하세요.\n    return answer\n`,
  java: `class Solution {\n    public int solution() {\n        int answer = 0;\n        // TODO: 코드를 작성하세요.\n        return answer;\n    }\n}\n`,
  c: `#include <stdio.h>\n\nint solution() {\n    int answer = 0;\n    // TODO: 코드를 작성하세요.\n    return answer;\n}\n`,
  cpp: `#include <bits/stdc++.h>\nusing namespace std;\n\nint solution() {\n    int answer = 0;\n    // TODO: 코드를 작성하세요.\n    return answer;\n}\n`
}
const selectedLanguage = ref("python3");
const code = ref(languageTemplates[selectedLanguage.value]);
const problemData = ref(null);
const isLoadingProblem = ref(false);
const problemError = ref("");
const timeLimitSeconds = ref(40 * 60);
const remainingSeconds = ref(null);
let countdownTimer = null;
let hasAutoEnded = false;

const formattedRemainingTime = computed(() => {
  if (remainingSeconds.value === null || remainingSeconds.value === undefined) {
    return "--:--";
  }
  const sec = Math.max(0, remainingSeconds.value);
  const mm = String(Math.floor(sec / 60)).padStart(2, "0");
  const ss = String(sec % 60).padStart(2, "0");
  return `${mm}:${ss}`;
});


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
const loadSavedCodeIfExists = async (sessionId, token, language) => {
  try {
    const params = new URLSearchParams({
      session_id: String(sessionId),
      language: String(language || ""),
    });
    const resp = await fetch(
      `${BACKEND_BASE}/api/livecoding/session/code/?${params.toString()}`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    if (!resp.ok) {
      // 404는 "저장된 스냅샷 없음" 상황이므로 조용히 반환
      if (resp.status !== 404) {
        const errBody = await resp.json().catch(() => ({}));
        console.warn("failed to load code snapshot", resp.status, errBody);
      }
      return;
    }

    const data = await resp.json().catch(() => ({}));
    if (data && typeof data.code === "string") {
      code.value = data.code;
    }
  } catch (err) {
    console.error("failed to load saved code snapshot", err);
  }
};

const fetchRandomProblem = async () => {
  isLoadingProblem.value = true;
  problemError.value = "";
  hasAutoEnded = false;
  clearCountdown();

  try {
    const sessionId = route.query.session_id;
    const token = localStorage.getItem("jobtory_access_token");

    if (!sessionId) {
      throw new Error("세션 ID가 없습니다. 라이브 코딩을 다시 시작해 주세요.");
    }
    if (!token) {
      throw new Error("로그인이 필요합니다. 다시 로그인해 주세요.");
    }

    const resp = await fetch(
      `${BACKEND_BASE}/api/livecoding/session/?session_id=${encodeURIComponent(
        sessionId
      )}`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    );

    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      throw new Error(data?.detail || "세션 정보를 불러오지 못했습니다.");
    }

    problemData.value = data;
    hasPlayedIntroTts.value = false;
    introSecondChanceUsed.value = false;
    clearAnswerCountdown();
    isRecording.value = false;
    timeLimitSeconds.value = Number(data?.time_limit_seconds || 40 * 60);
    remainingSeconds.value =
      data?.remaining_seconds !== undefined && data?.remaining_seconds !== null
        ? Number(data.remaining_seconds)
        : timeLimitSeconds.value;

    if (remainingSeconds.value <= 0) {
      await endSessionDueToTimeout();
      return;
    }

    startCountdown();

    // 항상 python3 기준으로 시작 코드 설정
    if (selectedLanguage.value !== "python3") {
      selectedLanguage.value = "python3";
    }
    if (problemData.value?.starter_code) {
      code.value = problemData.value.starter_code;
    } else if (selectedLanguage.value === "python3") {
      code.value = languageTemplates.python3;
    }

    // 세션/언어별로 저장된 코드가 있다면 불러와서 이어서 작성할 수 있도록 합니다.
    await loadSavedCodeIfExists(sessionId, token, selectedLanguage.value);
    // 문제 안내 음성 자동 재생 (TTS 응답이 느려도 UI 로딩을 막지 않도록 fire-and-forget)
    void requestAndPlayTts(problemData.value);
  } catch (err) {
    console.error(err);
    problemError.value = err?.message || "문제를 불러오지 못했습니다.";
  } finally {
    isLoadingProblem.value = false;
  }
};

// 힌트 요청: session_id, code, language, 문제 정보 함께 전달
const requestHint = async () => {
  const token = localStorage.getItem("jobtory_access_token");
  const sessionId = route.query.session_id;
  if (!token || !sessionId) {
    showAntiCheat("sttError", "세션이나 로그인 정보가 없습니다.");
    return;
  }

  try {
    const resp = await fetch(`${BACKEND_BASE}/api/livecoding/session/hint/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        session_id: sessionId,
        language: selectedLanguage.value,
        code: code.value,
        problem_description: problemData.value?.problem || "",
        problem_algorithm_category: problemData.value?.category || "",
      }),
    });

    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      console.warn("hint request failed", data);
      showAntiCheat("sttError", data.detail || "힌트를 가져오지 못했습니다.");
      return;
    }

    console.log("hint result", data);

    // 힌트가 TTS 오디오로 내려오면 바로 재생
    const ttsChunks = Array.isArray(data?.tts_audio) ? data.tts_audio : [];
    if (ttsChunks.length) {
      try {
        await playTtsChunks(ttsChunks);
      } catch (err) {
        console.error("failed to play hint TTS", err);
      }
    }
  } catch (err) {
    console.error("hint request error", err);
    showAntiCheat("sttError", "힌트 요청 중 오류가 발생했습니다.");
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

let saveCodeTimer = null;

const saveCodeSnapshot = async (content) => {
  const sessionId = route.query.session_id;
  const token = localStorage.getItem("jobtory_access_token");
  if (!sessionId || !token) return;

  try {
    await fetch(`${BACKEND_BASE}/api/livecoding/session/code/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        session_id: sessionId,
        language: selectedLanguage.value,
        code: content ?? "",
      }),
    });
  } catch (err) {
    console.error("failed to save code snapshot", err);
  }
};

watch(
  () => code.value,
  (newCode) => {
    // 사용자가 입력할 때마다 일정 시간(debounce) 후 서버에 스냅샷을 저장합니다.
    if (saveCodeTimer) {
      clearTimeout(saveCodeTimer);
      saveCodeTimer = null;
    }
    saveCodeTimer = setTimeout(() => {
      void saveCodeSnapshot(newCode);
    }, 1500);
  }
);

const clearCountdown = () => {
  if (countdownTimer) {
    clearInterval(countdownTimer);
    countdownTimer = null;
  }
};

const endSessionDueToTimeout = async () => {
  if (hasAutoEnded) return;
  hasAutoEnded = true;
  clearCountdown();

  try {
    const token = localStorage.getItem("jobtory_access_token");
    if (token) {
      await fetch(`${BACKEND_BASE}/api/livecoding/session/end/`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ reason: "timeout" })
      }).catch(() => {});
    }
  } finally {
    localStorage.removeItem("jobtory_livecoding_session_id");
    router.replace({ name: "home", query: { alert: "session_timeout" } });
  }
};

const endSessionAndReturnToCodingTest = async (reason = "") => {
  const showTerminationNotice = () => {
    if (reason === "intro_flow_done_without_strategy") {
      window.alert(
        "코딩 테스트가 정상적으로 진행되지 않아 세션을 종료합니다.\n\n" +
          "문제 풀이 전략을 두 차례 요청드렸으나,\n" +
          "해당 단계에서 요구되는 답변을 확인할 수 없었습니다.\n\n" +
          "다시 테스트를 시작하시려면 메인 화면으로 이동해 주세요."
      );
    }
  };

  try {
    const token = localStorage.getItem("jobtory_access_token");
    const sessionId = route.query.session_id;
    if (token && sessionId) {
      await fetch(`${BACKEND_BASE}/api/livecoding/session/end/`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ session_id: sessionId, reason })
      }).catch(() => {});
    }
  } finally {
    showTerminationNotice();
    localStorage.removeItem("jobtory_livecoding_session_id");
    router.replace({ name: "coding-test" });
  }
};

const startCountdown = () => {
  clearCountdown();
  countdownTimer = setInterval(() => {
    if (remainingSeconds.value === null || remainingSeconds.value === undefined) return;
    const next = Math.max(0, Number(remainingSeconds.value) - 1);
    remainingSeconds.value = next;
    if (next <= 0) {
      void endSessionDueToTimeout();
    }
  }, 1000);
};

const cmMode = computed(() => {
  switch (selectedLanguage.value) {
    case "python3": return "python";
    case "java": return "text/x-java";
    case "c": return "text/x-csrc";
    case "cpp": return "text/x-c++src";
    default: return "text/plain";
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
const offscreenCount = ref(0);
const isForceEnding = ref(false);
let lastOffscreenAlert = 0;

const KEY_WINDOW_MS = 2000;
const KEY_THRESHOLD = 12;
const ABNORMAL_COOLDOWN_MS = 8000;
const COPY_COOLDOWN_MS = 4000;
const OFFSCREEN_LIMIT = 3000;
const OFFSCREEN_COOLDOWN_MS = 1500; // blur/visibility/mouseleave가 연달아 올 때 중복 카운트 방지

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

const registerOffscreenInfraction = (stateKey, baseDetail) => {
  const now = Date.now();
  // 같은 전환으로 blur/visibility/mouseleave가 연달아 올 때 한 번만 카운트
  if (now - lastOffscreenAlert < OFFSCREEN_COOLDOWN_MS) {
    return;
  }
  lastOffscreenAlert = now;

  offscreenCount.value += 1;
  const withCount = `${baseDetail} (누적 ${offscreenCount.value}/${OFFSCREEN_LIMIT})`;
  showAntiCheat(stateKey, withCount);

  if (offscreenCount.value >= OFFSCREEN_LIMIT) {
    void forceEndSession("anti-cheat: offscreen threshold exceeded");
  }
};

const forceEndSession = async (reason = "") => {
  if (isForceEnding.value) return;
  isForceEnding.value = true;
  clearCountdown();

  try {
    const token = localStorage.getItem("jobtory_access_token");
    const sessionId = route.query.session_id;
    if (token) {
      await fetch(`${BACKEND_BASE}/api/livecoding/session/end/`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ session_id: sessionId, reason })
      }).catch(() => {});
    }
  } finally {
    localStorage.removeItem("jobtory_livecoding_session_id");
    router.replace({ name: "home", query: { alert: "anti-cheat" } });
  }
};

const handleVisibilityChange = () => {
  if (document.visibilityState === "hidden") {
    registerOffscreenInfraction("tabSwitch", "시험 화면을 벗어났습니다.");
  }
};

const handleWindowBlur = () => {
  registerOffscreenInfraction("windowBlur", "다른 창으로 이동이 감지되었습니다.");
};

const handlePaste = () => {
  showAntiCheat("pasteDetected", "외부 붙여넣기 시도가 차단되었습니다.");
};

const handleCopy = () => {
  const now = Date.now();
  if (now - lastCopyAlert < COPY_COOLDOWN_MS) return;
  lastCopyAlert = now;
  showAntiCheat("copyDetected", "복사 동작이 차단되었습니다.");
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
      const sessionId = route.query.session_id;
      const url = sessionId
        ? `${BACKEND_BASE}/mediapipe/analyze/?session_id=${encodeURIComponent(
            sessionId
          )}`
        : `${BACKEND_BASE}/mediapipe/analyze/`;

      const resp = await fetch(url, {
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
    event.preventDefault();
    handleCopy();
    return;
  }
  if ((event.ctrlKey || event.metaKey) && event.key?.toLowerCase() === "v") {
    event.preventDefault();
    handlePaste();
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

const handleMouseLeave = (event) => {
  if (!event.relatedTarget) {
    registerOffscreenInfraction("windowBlur", "마우스가 시험 화면 밖으로 이동했습니다.");
  }
};

const pasteListener = (e) => {
  e.preventDefault();
  handlePaste();
};

const copyListener = (e) => {
  e.preventDefault();
  handleCopy();
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
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 360 },
      audio: false,
    });
    if (videoRef.value) {
      videoRef.value.srcObject = mediaStream ;
      await videoRef.value.play();
    }
    startWebcamMonitor();
    mediapipeInterval = setInterval(() => {
      void sendFrameForMediapipe();
    }, 5000);
  } catch (err) {
    cameraError.value = "웹캠 권한을 허용해 주세요.";
  }

  window.addEventListener("blur", handleWindowBlur);
  document.addEventListener("visibilitychange", handleVisibilityChange);
  document.addEventListener("paste", pasteListener, { capture: true });
  document.addEventListener("copy", copyListener, { capture: true });
  document.addEventListener("mouseleave", handleMouseLeave);
});

onBeforeUnmount(() => {
  // 페이지를 떠날 때 마지막 코드 스냅샷을 한 번 더 저장해 이어하기 진입 시 최대한 최근 코드가 복원되도록 합니다.
  void saveCodeSnapshot(code.value);
  clearCountdown();

  if (mediaStream) {
    mediaStream.getTracks().forEach((t) => t.stop());
  }
  stopWebcamMonitor();
  if (mediapipeInterval) {
    clearInterval(mediapipeInterval);
    mediapipeInterval = null;
  }
  window.removeEventListener("blur", handleWindowBlur);
  document.removeEventListener("visibilitychange", handleVisibilityChange);
  document.removeEventListener("paste", pasteListener, { capture: true });
  document.removeEventListener("copy", copyListener, { capture: true });
  document.removeEventListener("mouseleave", handleMouseLeave);
  clearAntiCheatTimer();
  if (saveCodeTimer) {
    clearTimeout(saveCodeTimer);
    saveCodeTimer = null;
  }
  clearAnswerCountdown();
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
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.session-title-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
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

.timer-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 999px;
  background: #0f172a;
  color: #e5e7eb;
  font-size: 13px;
  border: 1px solid #1f2937;
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.25);
}

.timer-value {
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  color: #38bdf8;
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
  justify-content: space-between;
  gap: 12px;
}

.footer-left,
.footer-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.mic-button,
.hint-button,
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

.mic-button:disabled,
.hint-button:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.mic-button:hover:not(:disabled),
.hint-button:hover:not(:disabled) {
  background: #1fb154;
  transform: translateY(-1px);
}

.mic-button.is-active {
  background: linear-gradient(135deg, #16a34a, #22c55e);
  color: #0b1a13;
}

.mic-label {
  font-size: 13px;
  font-weight: 700;
  color: inherit;
  white-space: nowrap;
}

.hint-counter {
  font-size: 12px;
  color: #9ca3af;
}

.countdown-inline {
  color: #9ca3af;
}

.run-button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.disabled-answer {
  background: #4b5563;
  color: #e5e7eb;
}

.hint {
  font-size: 12px;
  color: #9ca3af;
}

.countdown-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.65);
  z-index: 999;
}

.countdown-ring {
  position: relative;
  width: 180px;
  height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ring-bg {
  fill: none;
  stroke: rgba(255, 255, 255, 0.2);
  stroke-width: 10;
  transform: rotate(-90deg);
  transform-origin: 50% 50%;
}

.ring-progress {
  fill: none;
  stroke: #ec4899;
  stroke-width: 10;
  transform: rotate(-90deg);
  transform-origin: 50% 50%;
  transition: stroke-dashoffset 0.2s ease;
}

.countdown-text {
  position: absolute;
  color: #fff;
  font-size: 48px;
  font-weight: 800;
}

.countdown-helper {
  margin-top: 10px;
  color: #f3f4f6;
  font-size: 14px;
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
