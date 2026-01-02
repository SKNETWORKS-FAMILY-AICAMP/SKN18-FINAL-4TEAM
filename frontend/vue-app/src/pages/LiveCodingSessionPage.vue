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
      <!-- 인트로 준비 오버레이 -->
      <div v-if="isIntroPreparing" class="intro-loading-overlay">
        <div class="intro-loading-card">
          <div class="intro-spinner" aria-hidden="true">
            <span v-for="bar in 12" :key="bar" :style="{ '--i': bar }"></span>
          </div>
          <p class="intro-loading-text">면접을 진행할 면접관을 배정 중입니다.</p>
          <p class="intro-loading-sub">잠시만 기다려주세요.</p>
        </div>
      </div>

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
              <h2 class="problem-title">{{ problemData.title || "실전 문제" }}</h2>
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
            :read-only="sessionStage !== 'coding'"
            @editor-keydown="handleEditorKeydown"
            @editor-copy="handleCopy"
          />
        </div>
        <footer class="editor-footer">
          <div class="footer-left">
            <button
              type="button"
              class="hint-button"
              @click="onHintButtonClick"
              :disabled="isSttRunning || isTtsPlaying || isHintDisabled"
            >
              {{
                isHintRecording
                  ? "힌트 설명 중... 다시 눌러 전송"
                  : (isHintLoading ? "힌트 생성 중..." : "힌트 요청")
              }}
            </button>
            <span class="hint-counter">사용한 횟수 {{ hintCount }}/{{ HINT_LIMIT }}</span>
          </div>
          <div class="footer-right">
            <button
              type="button"
              class="run-button"
              @click="onSubmitClick"
              :disabled="isSubmitting || isSttRunning || isTtsPlaying || isRecording || isHintRecording || isHintLoading"
            >
              {{ isSubmitting ? "제출 중..." : "제출하기" }}
            </button>
          </div>
        </footer>
      </section>
    </main>

    <!-- 자동 녹음(전략 답변 등) 중: 중앙 제출 버튼 -->
    <div v-if="showAutoRecordingSubmitOverlay" class="recording-submit-overlay">
      <p class="recording-mic-helper" role="status" aria-live="polite">
        답변이 끝나면 마이크 버튼을 눌러 제출해 주세요
      </p>
      <button
        type="button"
        class="recording-mic-button"
        :class="{ 'is-recording': isRecording }"
        :style="recordingMicStyle"
        @click="onAskButtonClick"
        :disabled="isSttRunning || isTtsPlaying || isMicCooldown"
        aria-label="답변 제출하기"
      >
        <svg viewBox="0 0 24 24" focusable="false" aria-hidden="true">
          <path
            fill="currentColor"
            d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3zm5-3a1 1 0 1 1 2 0 7 7 0 0 1-6 6.93V20h2a1 1 0 1 1 0 2H9a1 1 0 1 1 0-2h2v-2.07A7 7 0 0 1 5 11a1 1 0 1 1 2 0 5 5 0 0 0 10 0z"
          />
        </svg>
      </button>
    </div>

    <!-- STT → LangGraph → TTS 처리 중 오버레이 -->
    <div v-if="isSttRunning" class="processing-overlay">
      <div class="processing-card">
        <div class="processing-spinner"></div>
        <p class="processing-text">응답을 분석하고 있어요...</p>
        <p class="processing-subtext">잠시만 기다려 주세요</p>
      </div>
    </div>

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

    <!-- 새로고침 감지 안내 모달 -->
    <div v-if="showReloadIntroModal" class="refresh-modal-overlay">
      <div class="refresh-modal">
        <h3>새로고침을 감지했어요</h3>
        <p>인트로 음성 재생을 위해 확인 버튼을 눌러 주세요.</p>
        <button type="button" class="primary-btn" @click="confirmReloadIntro">확인</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter, onBeforeRouteLeave, onBeforeRouteUpdate } from "vue-router";
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
   변수 선언
----------------------------- */
const INTRO_AUDIO_KEY = (sessionId) => `jobtory_intro_audio_${sessionId}`;
const INTRO_TEXT_KEY = (sessionId) => `jobtory_intro_text_${sessionId}`;
let audioStream = null;
let mediaRecorder = null;
let audioChunks = [];
const audioBlob = ref(null);
const isRecording = ref(false);
const isSttRunning = ref(false);
const isTtsPlaying = ref(false);
const isMicCooldown = ref(false);
const micLevel = ref(0);
let micLevelRafId = null;
let micAudioContext = null;
let micAnalyser = null;
let micTimeDomainData = null;

const answerCountdown = ref(null);
let answerCountdownTimer = null;
let micCooldownTimer = null;
const ANSWER_COUNTDOWN_SECONDS = 30;
const answerCountdownTotalSeconds = ref(ANSWER_COUNTDOWN_SECONDS);

const isAutoRecording = ref(false);

const HINT_LIMIT = 3;
const hintCount = ref(0);
const isHintLoading = ref(false);
const isHintDisabled = computed(() => isHintLoading.value || hintCount.value >= HINT_LIMIT);
const isHintRecording = ref(false);
const ringRadius = 46;
const ringSize = 140;
const ringCircumference = 2 * Math.PI * ringRadius;
const LAST_PATH_KEY = "jobtory_last_path";
const sessionStage = ref("intro"); // 서버 stage/state를 반영하는 클라이언트 단계

const introPlayBlocked = ref(false);
const showReloadIntroModal = ref(false);
const cameFromReload = ref(false);
let introGestureHandler = null;
const isIntroPreparing = ref(false);
const countdownStarted = ref(false);
const introSecondChanceUsed = ref(false);

/* -----------------------------
   🔥 버튼 클릭 로직
----------------------------- */
const onAskButtonClick = async () => {
  if (isHintRecording.value) return;
  clearAnswerCountdown();
  if (isMicCooldown.value) return;
  if (micCooldownTimer) {
    clearTimeout(micCooldownTimer);
    micCooldownTimer = null;
  }
  isMicCooldown.value = true;
  micCooldownTimer = setTimeout(() => {
    isMicCooldown.value = false;
    micCooldownTimer = null;
  }, 1000);

  if (isSttRunning.value) return;

  if (!isRecording.value) {
    isAutoRecording.value = false;
    // 사용자가 말하기 시작하면 코딩 질문 타이머는 잠시 정지
    stopCodingQuestionTimer();
    // 수동으로 질문하기 버튼을 눌렀을 때 녹음 시작
    await startRecording();
    isRecording.value = true;
    return;
  }

  await stopRecording();
  isRecording.value = false;
  isAutoRecording.value = false;

  isSttRunning.value = true;
  try {
    await runSttClient();
  } finally {
    isSttRunning.value = false;
  }
};

const onAnswerButtonClick = async () => {
  if (isHintRecording.value) return;
  clearAnswerCountdown();
  if (isSttRunning.value || isRecording.value) return;
	 // 자동 답변 타이머로 말하기 시작할 때도 코딩 질문 타이머 정지
  stopCodingQuestionTimer();
  isAutoRecording.value = true;
  try {
    await startRecording();
    isRecording.value = true;
  } catch (e) {
    isAutoRecording.value = false;
    throw e;
  }
};

const startAnswerCountdown = (seconds = 30) => {
  clearAnswerCountdown();
  answerCountdownTotalSeconds.value = seconds;
  answerCountdown.value = seconds;
  answerCountdownTimer = setInterval(() => {
    if (answerCountdown.value === null) return;
    answerCountdown.value -= 1;
    if (answerCountdown.value <= 0) {
      clearAnswerCountdown();
      void onAnswerButtonClick();
    }
  }, 1000);
};

const clearAnswerCountdown = () => {
  if (answerCountdownTimer) {
    clearInterval(answerCountdownTimer);
    answerCountdownTimer = null;
  }
  answerCountdown.value = null;
  answerCountdownTotalSeconds.value = ANSWER_COUNTDOWN_SECONDS;
};

const ringStrokeOffset = computed(() => {
  if (answerCountdown.value === null) return ringCircumference;
  const totalSeconds =
    typeof answerCountdownTotalSeconds.value === "number" && answerCountdownTotalSeconds.value > 0
      ? answerCountdownTotalSeconds.value
      : ANSWER_COUNTDOWN_SECONDS;
  const progress = Math.max(
    0,
    Math.min(1, answerCountdown.value / totalSeconds)
  );
  return ringCircumference * (1 - progress);
});

const showAutoRecordingSubmitOverlay = computed(() => {
  if (!isRecording.value) return false;
  if (!isAutoRecording.value) return false;
  if (isHintRecording.value) return false;
  if (isSttRunning.value || isTtsPlaying.value) return false;
  return true;
});

const recordingMicStyle = computed(() => {
  const level = Math.max(0, Math.min(1, micLevel.value || 0));
  const waveOpacity = Math.max(0.15, Math.min(0.6, 0.18 + level * 0.42));
  const waveScale = Math.max(1.7, Math.min(2.8, 1.85 + level * 0.9));
  return {
    "--mic-level": level.toFixed(3),
    "--mic-wave-opacity": waveOpacity.toFixed(3),
    "--mic-wave-scale": waveScale.toFixed(3),
  };
});

const stopMicLevelMeter = () => {
  if (micLevelRafId) {
    cancelAnimationFrame(micLevelRafId);
    micLevelRafId = null;
  }
  micAnalyser = null;
  micTimeDomainData = null;
  if (micAudioContext) {
    try {
      micAudioContext.close();
    } catch {
      // ignore
    }
    micAudioContext = null;
  }
  micLevel.value = 0;
};

const startMicLevelMeter = (stream) => {
  stopMicLevelMeter();
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    micAudioContext = new AudioCtx();
    const source = micAudioContext.createMediaStreamSource(stream);
    micAnalyser = micAudioContext.createAnalyser();
    micAnalyser.fftSize = 2048;
    micTimeDomainData = new Uint8Array(micAnalyser.fftSize);
    source.connect(micAnalyser);

    const tick = () => {
      if (!micAnalyser || !micTimeDomainData) return;
      micAnalyser.getByteTimeDomainData(micTimeDomainData);
      let sumSquares = 0;
      for (let i = 0; i < micTimeDomainData.length; i += 1) {
        const centered = (micTimeDomainData[i] - 128) / 128;
        sumSquares += centered * centered;
      }
      const rms = Math.sqrt(sumSquares / micTimeDomainData.length);
      const normalized = Math.max(0, Math.min(1, (rms - 0.02) / 0.25));
      micLevel.value = normalized;
      micLevelRafId = requestAnimationFrame(tick);
    };
    micLevelRafId = requestAnimationFrame(tick);
  } catch (e) {
    console.warn("mic level meter init failed:", e);
  }
};

/* -----------------------------
  📤 코드 제출 버튼 (렌더링 페이지 이동 예정)
----------------------------- */
const isSubmitting = ref(false);

const onSubmitClick = async () => {
  const sessionId = route.query.session_id;
  const token = localStorage.getItem("jobtory_access_token");

  if (!sessionId) return window.alert("session_id가 없습니다.");
  if (!token) return router.push({ name: "login" });
  if (isSubmitting.value) return;

  isSubmitting.value = true;
  try {
    // (선택) 마지막 코드 저장
    await saveCodeSnapshot(code.value);

    // ✅ step3(langgraph) 시작 트리거
    const resp = await fetch(`${BACKEND_BASE}/api/livecoding/final-eval/start/`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ session_id: sessionId }),
    });

    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      console.warn("final-eval start failed", resp.status, data);
      return window.alert(data?.detail || "최종 평가 시작에 실패했습니다.");
    }

    // ✅ rendering.vue 이동
    router.replace({
      name: "livecoding-rendering",
      query: { session_id: sessionId },
    });
  } catch (e) {
    console.error(e);
    window.alert("제출 처리 중 오류가 발생했습니다.");
  } finally {
    isSubmitting.value = false;
  }
};

// 힌트 버튼: 첫 클릭에서 힌트 설명을 녹음, 두 번째 클릭에서 STT + 힌트 생성
const onHintButtonClick = async () => {
  const token = localStorage.getItem("jobtory_access_token");
  const sessionId = route.query.session_id;

  if (hintCount.value >= HINT_LIMIT) {
    showAntiCheat("sttError", "사용 가능한 힌트가 모두 소진되었습니다.");
    return;
  }
  if (!token || !sessionId) {
    showAntiCheat("sttError", "세션이나 로그인 정보가 없습니다.");
    return;
  }

  // 아직 힌트를 위한 녹음을 시작하지 않은 상태 → 녹음 시작
  if (!isHintRecording.value) {
    if (isSttRunning.value || isTtsPlaying.value || isRecording.value) {
      // 다른 음성 작업이 진행 중이면 무시
      return;
    }
    try {
      await startRecording();
      isRecording.value = true;
      isHintRecording.value = true;
    } catch (err) {
      console.error("힌트 녹음 시작 오류:", err);
      showAntiCheat("micError", "마이크 접근 권한이 필요합니다.");
    }
    return;
  }

  // 이미 힌트 녹음 중인 상태에서 다시 클릭 → 녹음 종료 후 STT + 힌트 요청
  try {
    await stopRecording();
  } catch (err) {
    console.error("힌트 녹음 종료 오류:", err);
  } finally {
    isRecording.value = false;
    isHintRecording.value = false;
  }

  if (!audioBlob.value) {
    showAntiCheat("sttError", "녹음된 음성이 없습니다.");
    return;
  }

  isSttRunning.value = true;
  isHintLoading.value = true;
  try {
    const sttText = await transcribeHintAudio();
    if (!sttText) {
      return;
    }
    await requestHint(sttText);
  } finally {
    isSttRunning.value = false;
    isHintLoading.value = false;
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
    startMicLevelMeter(audioStream);

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
    stopMicLevelMeter();
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

	    mediaRecorder.onstop = () => {
	      audioBlob.value = new Blob(audioChunks, { type: "audio/webm" });
	      console.log("🎤 녹음 완료:", audioBlob.value);
	      stopMicLevelMeter();
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

const endSessionAndReturnToCodingTest = async (reason = "intro_flow_done_without_strategy") => {
  clearCountdown();
  try {
    // 인트로 단계에서 전략이 아닌 답변이 반복되어 세션이 종료되는 경우,
    // 홈 화면으로 이동하기 전에 사용자에게 한 번 안내 메시지를 보여준다.
    if (reason === "intro_flow_done_without_strategy") {
      window.alert("답변이 적절하지 않아 세션을 종료합니다.");
    }

    const token = localStorage.getItem("jobtory_access_token");
    if (token) {
      await fetch(`${BACKEND_BASE}/api/livecoding/session/end/`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ session_id: route.query.session_id, reason }),
      }).catch(() => {});
    }
  } finally {
    localStorage.removeItem("jobtory_livecoding_session_id");
    router.replace({ name: "home", query: { alert: reason } });
  }
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
    showAntiCheat("sttError", "음성에서 유효한 문장을 인식하지 못했습니다. 다시 한번 말해주세요.");
    // 로딩 오버레이를 제거하고 안내 음성을 재생한다.
    isSttRunning.value = false;
    isTtsPlaying.value = true;
    const played = await playInlineTts("음성에서 유효한 문장을 인식하지 못했습니다. 다시 한번 말해주세요.");
    if (!played) void playWarningBeep();
    isTtsPlaying.value = false;
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
    // ✅ strategy로 분류되었고 STT 텍스트가 있다면 저장
    if (eventData.user_answer_class === "strategy" && sttText) {
      try {
        // 1. localStorage에 백업 저장
        const strategyKey = `strategy_answer_${sessionId}`;
        localStorage.setItem(strategyKey, sttText);
        console.log("✅ localStorage 백업:", strategyKey, sttText.substring(0, 30));
        // 백엔드에 명시적으로 전략 답변 저장 요청
        await fetch(`${BACKEND_BASE}/api/livecoding/session/strategy/`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            session_id: sessionId,
            strategy_answer: sttText,
            timestamp: new Date().toISOString(),
          }),
        });
        console.log("✅ 전략 답변 저장 완료:", sttText.substring(0, 30));
      } catch (e) {
        console.error("❌ 전략 답변 저장 실패:", e);
      }
    }

    // 백엔드가 tts_text를 문자열(텍스트)로 줄 수도 있고,
    // 이미 TTS가 적용된 오디오 청크 배열로 줄 수도 있으므로 둘 다 처리한다.
    const rawTts = eventData?.tts_text;
    let replyText = "";
    let replyChunks = [];
    if (Array.isArray(rawTts)) {
      replyChunks = rawTts;
    } else if (typeof rawTts === "string") {
      replyText = rawTts.trim();
    }

    const userAnswerClass = (eventData?.user_answer_class || "").trim();
    const introFlowDone = Boolean(eventData?.intro_flow_done);
    const stageFromServer = (eventData?.stage || "").trim().toLowerCase();
    const codingIntroText = (eventData?.coding_intro_text || "").trim();
    if (stageFromServer) {
      // 서버에서 내려준 stage를 sessionStage/currentStage 모두에 반영
      sessionStage.value = stageFromServer;
      currentStage.value = stageFromServer;
    }

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
      (replyText || replyChunks.length > 0) &&
      userAnswerClass !== "strategy" &&
      (!introFlowDone || isFirstNonStrategy);

    // intro 단계에서 첫 번째 비전략 답변(irrelevant / problem_question)에 대해
    // 피드백 TTS를 들려준 뒤에는, 사용자가 버튼을 다시 누르지 않아도
    // 자동으로 마이크를 열어 재답변을 받을 수 있도록 플래그를 세팅한다.
    const shouldAutoReRecord =
      sessionStage.value === "intro" &&
      isFirstNonStrategy &&
      (userAnswerClass === "irrelevant" || userAnswerClass === "problem_question");

    const autoReRecordIfNeeded = async () => {
      if (!shouldAutoReRecord) return;
      if (isRecording.value || isSttRunning.value || isHintRecording.value) return;
      try {
        isAutoRecording.value = true;
        await startRecording();
        isRecording.value = true;
      } catch (err) {
        isAutoRecording.value = false;
        console.error("인트로 재답변 자동 녹음 시작 실패:", err);
        showAntiCheat(
          "micError",
          "마이크 자동 시작에 실패했습니다. 다시 한 번 버튼을 눌러 주세요."
        );
      }
    };

    // 코딩 스테이지로 막 전환된 경우, 별도의 인트로 멘트를 한 번 재생
    if (stageFromServer === "coding" && codingIntroText) {
      try {
        await fetchAndPlayTts({
          token,
          sessionId,
          text: codingIntroText,
          // 코딩 단계 진입 멘트는 종종 2문장 이상이라 잘리지 않도록 넉넉히 설정
          maxSentences: 10,
          onStart: () => {
            isSttRunning.value = false;
          },
        });
      } catch (err) {
        console.error("코딩 스테이지 인트로 TTS 요청/재생 오류:", err);
      }
    }

    if (allowTts) {
      if (isFirstNonStrategy) {
        introSecondChanceUsed.value = true;
      }
      try {
        // 이미 오디오 청크가 내려온 경우 그대로 재생
        if (replyChunks.length > 0) {
          await playTtsChunks(replyChunks, {
            onStart: () => {
              isSttRunning.value = false;
            },
          });
          await autoReRecordIfNeeded();
        } else if (replyText) {
          // 텍스트만 온 경우에만 TTS API를 호출
          const ok = await fetchAndPlayTts({
            token,
            sessionId,
            text: replyText,
            maxSentences: 2,
            onStart: () => {
              isSttRunning.value = false;
            },
          });
          if (ok) {
            await autoReRecordIfNeeded();
          }
        }
      } catch (err) {
        console.error("응답 TTS 요청/재생 오류:", err);
      }
    }
  } catch (err) {
    console.error("STT 요청 실패:", err);
    showAntiCheat("sttError", "서버 통신 오류");
  }
  // 사용자의 발화/분석이 끝난 뒤, 코딩 단계라면 질문 타이머를 다시 시작
  if (currentStage.value === "coding") {
    startCodingQuestionTimer();
  }
};

watch(isRecording, (recording) => {
  if (!recording) {
    isAutoRecording.value = false;
    stopMicLevelMeter();
  }
});

// 힌트용 STT: 현재 녹음된 음성을 텍스트로만 변환
const transcribeHintAudio = async () => {
  if (!audioBlob.value) {
    showAntiCheat("sttError", "녹음된 음성이 없습니다.");
    return "";
  }

  const sessionId = route.query.session_id;
  if (!sessionId) {
    showAntiCheat("sttError", "session_id가 없습니다. 세션을 다시 시작해 주세요.");
    return "";
  }

  try {
    const sttResp = await fetch(
      `${BACKEND_BASE}/api/stt/transcribe/?session_id=${encodeURIComponent(
        sessionId
      )}`,
      {
        method: "POST",
        body: audioBlob.value,
      }
    );

    const sttData = await sttResp.json().catch(() => ({}));
    if (!sttResp.ok) {
      console.warn("STT(힌트) 요청 실패", sttResp.status, sttData);
      showAntiCheat("sttError", sttData?.error || "음성을 인식하지 못했습니다.");
      return "";
    }

    const sttText = (sttData?.stt_text || "").trim();
    console.log("STT(힌트) 결과:", sttData);

    if (!sttText) {
      showAntiCheat(
        "sttError",
        "음성에서 유효한 문장을 인식하지 못했습니다. 다시 한번 말해주세요."
      );
      return "";
    }

    return sttText;
  } catch (err) {
    console.error("STT(힌트) 요청 실패:", err);
    showAntiCheat("sttError", "서버 통신 오류");
    return "";
  }
};

/* -----------------------------
  🔊 TTS
------------------------------ */
// 코딩 세션 페이지가 아닐 때는 어떤 TTS도 재생하지 않는다.
const isCodingSessionRouteActive = () => router.currentRoute.value?.name === "coding-session";

// 현재 재생 중인 TTS 오디오들을 추적해서 화면을 떠날 때 모두 중단할 수 있도록 한다.
const activeTtsAudios = new Set();
// 진행 중인 TTS 요청(스트리밍 fetch)을 중단하기 위한 AbortController들
const activeTtsControllers = new Set();
// stopAllTts() 호출 이후에는 이전 TTS 작업이 더 이상 오디오를 재생하지 않도록 하는 세대 토큰
let ttsStopGeneration = 0;
const TTS_STREAM_ENDPOINT = `${BACKEND_BASE}/api/tts/intro/stream/`;
const TTS_BATCH_ENDPOINT = `${BACKEND_BASE}/api/tts/intro/`;

const stopAllTts = () => {
  // 이후에 실행 중이던 TTS 작업들이 새로운 오디오를 재생하지 못하도록 한다.
  ttsStopGeneration += 1;

  // 진행 중인 스트리밍 요청이 있다면 즉시 중단한다.
  try {
    activeTtsControllers.forEach((controller) => {
      try {
        controller.abort();
      } catch {
        // ignore
      }
    });
    activeTtsControllers.clear();
  } catch {
    // ignore
  }

  // 브라우저 Audio 요소로 재생 중인 TTS 정지
  try {
    activeTtsAudios.forEach((audio) => {
      try {
        audio.pause();
        // 재생 대기/진행 중인 Promise가 onended/onerror만 기다리며 남아있지 않도록 정리한다.
        if (typeof audio.onended === "function") {
          try {
            audio.onended();
          } catch {
            // ignore
          }
        }
        audio.src = "";
      } catch {
        // ignore
      }
    });
    activeTtsAudios.clear();
  } catch {
    // ignore
  }

  // Web Speech API로 재생 중인 inline TTS도 정지
  if (typeof window !== "undefined" && "speechSynthesis" in window) {
    try {
      window.speechSynthesis.cancel();
    } catch {
      // ignore
    }
  }
};

const playSingleTtsChunk = async (chunk) => {
  if (!chunk?.audio) return true;
  const myGeneration = ttsStopGeneration;
  if (!isCodingSessionRouteActive()) return false;
  const audio = new Audio(`data:audio/mp3;base64,${chunk.audio}`);
  try {
    if (myGeneration !== ttsStopGeneration || !isCodingSessionRouteActive()) return false;
    activeTtsAudios.add(audio);
    await audio.play();
  } catch (err) {
    console.error("TTS 재생 실패:", err);
    try {
      activeTtsAudios.delete(audio);
    } catch {
      // ignore
    }
    // 자동재생 차단(NotAllowedError)은 상위에서 기존 로직대로 처리할 수 있게 던진다.
    if (err && err.name === "NotAllowedError") {
      throw err;
    }
    return false;
  }

  return await new Promise((resolve) => {
    const cleanup = () => {
      audio.onended = null;
      audio.onerror = null;
      activeTtsAudios.delete(audio);
    };
    audio.onended = () => {
      cleanup();
      resolve(true);
    };
    audio.onerror = () => {
      cleanup();
      resolve(false);
    };
  });
};

const fetchTtsChunksBatch = async ({ token, sessionId, text, maxSentences }) => {
  const ttsText = typeof text === "string" ? text.trim() : "";
  if (!ttsText) return [];
  if (!isCodingSessionRouteActive()) return [];
  const url = `${TTS_BATCH_ENDPOINT}?session_id=${encodeURIComponent(sessionId)}`;
  const controller = new AbortController();
  activeTtsControllers.add(controller);
  try {
    const resp = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(
        maxSentences ? { tts_text: ttsText, max_sentences: maxSentences } : { tts_text: ttsText }
      ),
      signal: controller.signal,
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      console.warn("TTS batch 요청 실패", resp.status, data);
      return [];
    }
    if (!isCodingSessionRouteActive()) return [];
    return normalizeTtsChunks(data?.tts_text);
  } catch (err) {
    if (err?.name === "AbortError") return [];
    throw err;
  } finally {
    activeTtsControllers.delete(controller);
  }
};

async function* parseNdjsonStream(stream) {
  if (!stream) return;
  const reader = stream.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      try {
        yield JSON.parse(trimmed);
      } catch (e) {
        console.warn("NDJSON 파싱 실패:", e, trimmed.slice(0, 120));
      }
    }
  }
  const tail = buffer.trim();
  if (tail) {
    try {
      yield JSON.parse(tail);
    } catch (e) {
      console.warn("NDJSON tail 파싱 실패:", e, tail.slice(0, 120));
    }
  }
}

const fetchAndPlayTtsStream = async ({
  token,
  sessionId,
  text,
  maxSentences,
  onStart,
  collectChunks,
}) => {
  const myGeneration = ttsStopGeneration;
  const ttsText = typeof text === "string" ? text.trim() : "";
  if (!ttsText) return false;
  if (!isCodingSessionRouteActive()) return false;

  const url = `${TTS_STREAM_ENDPOINT}?session_id=${encodeURIComponent(sessionId)}`;
  const controller = new AbortController();
  activeTtsControllers.add(controller);
  let resp;
  try {
    resp = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(
        maxSentences ? { tts_text: ttsText, max_sentences: maxSentences } : { tts_text: ttsText }
      ),
      signal: controller.signal,
    });
  } catch (err) {
    // 화면 이탈/정지 처리로 abort 된 경우는 조용히 중단한다.
    if (myGeneration !== ttsStopGeneration || err?.name === "AbortError") return false;
    throw err;
  }

  if (myGeneration !== ttsStopGeneration) return false;

  if (!resp.ok) {
    const errBody = await resp.json().catch(() => ({}));
    console.warn("TTS stream 요청 실패", resp.status, errBody);
    try {
      activeTtsControllers.delete(controller);
    } catch {
      // ignore
    }
    return false;
  }
  if (!resp.body) {
    // 브라우저/프록시 환경에 따라 stream body가 없을 수 있음(Safari 등)
    try {
      activeTtsControllers.delete(controller);
    } catch {
      // ignore
    }
    return false;
  }

  let started = false;
  let overallOk = true;
  let chain = Promise.resolve(true);
  let gotAnyAudio = false;
  let canceled = false;

  try {
    for await (const msg of parseNdjsonStream(resp.body)) {
      if (myGeneration !== ttsStopGeneration || !isCodingSessionRouteActive()) {
        canceled = true;
        break;
      }
      if (msg?.error) {
        console.warn("TTS stream error chunk:", msg.error);
        continue;
      }
      if (!msg?.audio) continue;
      gotAnyAudio = true;
      const chunk = { text: msg.text || "", audio: msg.audio };
      if (typeof collectChunks === "function") {
        try {
          collectChunks(chunk);
        } catch {
          // ignore
        }
      }
      chain = chain.then(async () => {
        if (myGeneration !== ttsStopGeneration || !isCodingSessionRouteActive()) {
          canceled = true;
          return false;
        }
        if (!started && typeof onStart === "function") {
          started = true;
          onStart();
        }
        const ok = await playSingleTtsChunk(chunk);
        if (!ok) overallOk = false;
        return ok;
      });
    }
  } catch (err) {
    if (myGeneration !== ttsStopGeneration || err?.name === "AbortError") {
      canceled = true;
    } else {
      throw err;
    }
  } finally {
    activeTtsControllers.delete(controller);
  }

  try {
    const tailOk = await chain;
    if (canceled) return false;
    return gotAnyAudio && overallOk && tailOk;
  } catch (err) {
    // NotAllowedError(자동재생 차단) 등은 상위에서 처리하도록 전달
    throw err;
  }
};

const playTtsChunks = async (chunks = [], opts = { throwOnError: false, onStart: null }) => {
  const myGeneration = ttsStopGeneration;
  if (!isCodingSessionRouteActive()) return false;
  let started = false;
  for (const chunk of chunks) {
    if (myGeneration !== ttsStopGeneration || !isCodingSessionRouteActive()) return false;
    if (!chunk?.audio) continue;
    const audio = new Audio(`data:audio/mp3;base64,${chunk.audio}`);
    try {
      activeTtsAudios.add(audio);
      if (!started && typeof opts.onStart === "function") {
        started = true;
        opts.onStart();
      }
      await audio.play();
    } catch (err) {
      console.error("TTS 재생 실패:", err);
      try {
        activeTtsAudios.delete(audio);
      } catch {
        // ignore
      }
      if (err && err.name === "NotAllowedError") {
        throw err;
      }
      if (opts?.throwOnError) throw err;
      return false;
    }

    const finished = await new Promise((resolve) => {
      const cleanup = () => {
        audio.onended = null;
        audio.onerror = null;
        activeTtsAudios.delete(audio);
      };
      audio.onended = () => {
        cleanup();
        resolve(true);
      };
      audio.onerror = () => {
        cleanup();
        resolve(false);
      };
    });

    if (!finished) return false;
  }
  return true;
};

const fetchAndPlayTts = async ({
  token,
  sessionId,
  text,
  maxSentences,
  onStart,
  collectChunks,
}) => {
  const myGeneration = ttsStopGeneration;
  if (!isCodingSessionRouteActive()) return false;
  try {
    const ok = await fetchAndPlayTtsStream({
      token,
      sessionId,
      text,
      maxSentences,
      onStart,
      collectChunks,
    });
    if (myGeneration !== ttsStopGeneration) return false;
    if (ok) return true;
  } catch (err) {
    if (err && err.name === "NotAllowedError") throw err;
    console.warn("TTS stream 재생 실패, batch로 fallback:", err);
  }

  if (myGeneration !== ttsStopGeneration) return false;
  const chunks = await fetchTtsChunksBatch({ token, sessionId, text, maxSentences });
  if (myGeneration !== ttsStopGeneration) return false;
  if (chunks.length && typeof collectChunks === "function") {
    try {
      chunks.forEach((c) => collectChunks(c));
    } catch {
      // ignore
    }
  }
  if (!chunks.length) return false;
  if (myGeneration !== ttsStopGeneration) return false;
  return await playTtsChunks(chunks, { onStart });
};
const playWarningBeep = async (durationMs = 400, freq = 880) => {
  try {
    const Ctor = window.AudioContext || window.webkitAudioContext;
    if (!Ctor) return false;
    const ctx = new Ctor();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.value = freq;
    gain.gain.setValueAtTime(0.18, ctx.currentTime);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + durationMs / 1000);
    return await new Promise((resolve) => {
      osc.onended = () => {
        ctx.close().catch(() => {});
        resolve(true);
      };
    });
  } catch (err) {
    console.warn("warning beep failed:", err);
    return false;
  }
};

const playInlineTts = async (text = "") => {
  const trimmed = text.trim();
  if (!trimmed || typeof window === "undefined") return false;
  if (!isCodingSessionRouteActive()) return false;
  try {
    if (!("speechSynthesis" in window)) return false;
    const synth = window.speechSynthesis;
    synth.cancel();
    const utter = new SpeechSynthesisUtterance(trimmed);
    const ok = await new Promise((resolve) => {
      utter.onend = () => resolve(true);
      utter.onerror = () => resolve(false);
      synth.speak(utter);
    });
    return Boolean(ok);
  } catch (err) {
    console.warn("inline TTS 재생 실패:", err);
    return false;
  }
};

const normalizeTtsChunks = (payload) => {
  if (Array.isArray(payload)) {
    return payload
      .map((c) => {
        if (!c) return null;
        if (typeof c === "string") return { audio: c, text: "" };
        if (
          typeof c === "object" &&
          (("audio" in c && c.audio) || ("audio_base64" in c && c.audio_base64) || "text" in c)
        ) {
          const obj = c;
          const audio = obj.audio || obj.audio_base64 || "";
          const text = obj.text || "";
          if (audio || text) return { audio, text };
        }
        return null;
      })
      .filter((v) => v && (v.audio || v.text));
  }
  if (typeof payload === "string" && payload.trim()) {
    return [{ audio: payload.trim(), text: "" }];
  }
  return [];
};

// 인트로용 고정 인사 멘트들
const INTRO_GREETINGS = [
  "안녕하세요 오늘 라이브 코딩 테스트를 함께 진행할 면접관입니다. 지금 화면에 보이는 문제를 천천히 살펴보시고, 곧 핵심 내용을 간단히 정리해서 안내해 드리겠습니다.",
  "안녕하세요 저는 이번 라이브 코딩 세션을 맡은 면접관입니다. 화면의 문제를 먼저 훑어봐 주시면, 잠시 후 어떤 내용을 요구하는지 핵심만 콕 집어서 설명해 드리겠습니다.",
  "안녕하세요 라이브 코딩 테스트를 진행할 면접관입니다. 우선 화면에 보이는 문제를 한 번 읽어보시고, 이 문제의 중요한 부분을 곧 요약해서 설명해 드리겠습니다.",
  "안녕하세요 오늘 코딩 테스트를 도와드릴 면접관입니다. 화면의 문제를 편하게 읽어보시고 계시면, 조금 뒤에 문제의 목적과 핵심 포인트를 짧게 정리해 드리겠습니다.",
  "안녕하세요 지금부터 라이브 코딩 테스트를 함께 할 면접관입니다. 우선 화면에 나온 문제를 눈으로 익혀 두시고, 곧 어떤 문제인지 한 번에 이해하실 수 있도록 핵심만 추려서 안내해 드리겠습니다."
];

const getRandomIntroGreeting = () => {
  if (!INTRO_GREETINGS.length) return "";
  const idx = Math.floor(Math.random() * INTRO_GREETINGS.length);
  return INTRO_GREETINGS[idx] || "";
};

const fetchIntroTtsText = async () => {
  const token = localStorage.getItem("jobtory_access_token");
  const sessionId = route.query.session_id;
  if (!token || !sessionId || !problemData?.value) return null;

  const textKey = INTRO_TEXT_KEY(sessionId);

  const cachedText = sessionStorage.getItem(textKey);
  if (cachedText && cachedText.trim()) return cachedText.trim();

  try {
    const initResp = await fetch(`${BACKEND_BASE}/api/coding-problems/session/init/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        ...problemData.value,
        session_id: sessionId,
      }),
    });
    const initData = await initResp.json().catch(() => ({}));
    if (!initResp.ok) {
      console.warn("intro TTS 데이터를 가져오지 못했습니다.", initData);
      return null;
    }

    const refreshedText = typeof initData.tts_text === "string" ? initData.tts_text.trim() : "";
    if (refreshedText) {
      sessionStorage.setItem(textKey, refreshedText);
      // 기존 로직에서 audioKey를 쓰던 곳이 있어, text-only로 전환 시에도
      // 이전 캐시가 남아있다면 그대로 사용 가능하도록 삭제하지는 않는다.
      return refreshedText;
    }

    console.warn("intro TTS 텍스트를 다시 준비하지 못했습니다.", initData);
  } catch (err) {
    console.error("intro TTS 텍스트 재요청 실패:", err);
  }
  return null;
};

const setupIntroGestureResume = () => {
  if (introGestureHandler) return;
  const handler = () => {
    introGestureHandler = null;
    window.removeEventListener("click", handler, true);
    window.removeEventListener("keydown", handler, true);
    window.removeEventListener("touchstart", handler, true);
    introPlayBlocked.value = false;
    // intro는 서버 stage 기준으로 항상 재생 시도하므로 로컬 재생 플래그는 사용하지 않음
    void playIntroTtsFromSession();
  };
  introGestureHandler = handler;
  window.addEventListener("click", handler, true);
  window.addEventListener("keydown", handler, true);
  window.addEventListener("touchstart", handler, true);
};

const clearIntroGestureHandler = () => {
  if (introGestureHandler) {
    window.removeEventListener("click", introGestureHandler, true);
    window.removeEventListener("keydown", introGestureHandler, true);
    window.removeEventListener("touchstart", introGestureHandler, true);
    introGestureHandler = null;
  }
};

const isReloadNavigation = () => {
  try {
    const navEntries = performance.getEntriesByType("navigation");
    if (navEntries && navEntries[0]) {
      return navEntries[0].type === "reload";
    }
    // fallback for older browsers
    // @ts-ignore
    return performance.navigation?.type === performance.navigation.TYPE_RELOAD;
  } catch (e) {
    return false;
  }
};

const confirmReloadIntro = async () => {
  showReloadIntroModal.value = false;
  introPlayBlocked.value = false;
  // intro는 서버 stage 기준으로 항상 재생 시도하므로 로컬 재생 플래그는 사용하지 않음
  clearIntroGestureHandler();
  sessionStorage.setItem(LAST_PATH_KEY, window.location.pathname);
  await playIntroTtsFromSession();
};

const playIntroTtsFromSession = async () => {
  const myGeneration = ttsStopGeneration;
  if (isTtsPlaying.value) {
    return;
  }
  if (sessionStage.value !== "intro") {
    return;
  }
  if (!isCodingSessionRouteActive()) return;

  // 인트로용 고정 인사 TTS가 준비되기 전까지 로딩 오버레이를 유지한다.
  isIntroPreparing.value = true;

  const sessionId = route.query.session_id;
  const token = localStorage.getItem("jobtory_access_token");

  // 메인 인트로 오디오를 가져오는 작업을 미리 시작해 두고,
  // 그 사이에 고정 인사 멘트를 먼저 재생한다.
  const loadCachedIntroChunks = () => {
    // stage가 intro이면 이전 재생 여부와 관계없이 항상 재생을 시도한다.
    const audioKey = sessionId ? INTRO_AUDIO_KEY(sessionId) : null;
    const audio = audioKey ? sessionStorage.getItem(audioKey) : null;

    let chunks;
    if (audio) {
      try {
        chunks = JSON.parse(audio);
      } catch (e) {
        console.error("intro TTS audio JSON 파싱 실패:", e);
        chunks = null;
      }
    }

    chunks = normalizeTtsChunks(chunks);
    return chunks;
  };

  const cachedIntroChunks = loadCachedIntroChunks();
  const introTextPromise = cachedIntroChunks.length ? null : fetchIntroTtsText();

  introPlayBlocked.value = false;
  isTtsPlaying.value = true;

  try {
    // 1) 짧은 인사 멘트를 먼저 TTS로 재생 (체감 레이턴시 감소)
    const greetingText = getRandomIntroGreeting();
    if (greetingText && token && sessionId) {
      try {
        const ok = await fetchAndPlayTts({
          token,
          sessionId,
          text: greetingText,
          maxSentences: 5,
          onStart: () => {
            
            isIntroPreparing.value = false;
            startCountdownOnce();
          },
        });
        if (myGeneration !== ttsStopGeneration || !isCodingSessionRouteActive()) return;
        if (!ok) {
          isIntroPreparing.value = false;
        }
      } catch (e) {
        console.warn("intro greeting TTS 재생 실패:", e);
        isIntroPreparing.value = false;
      }
    } else {
      // 인사 멘트를 재생하지 못하는 경우에도 오버레이를 제거
      isIntroPreparing.value = false;
    }

    if (myGeneration !== ttsStopGeneration || !isCodingSessionRouteActive()) return;

    // 2) 메인 인트로 오디오가 준비될 때까지 대기 후 재생
    let completed = false;
    if (cachedIntroChunks.length) {
      completed = await playTtsChunks(cachedIntroChunks, { throwOnError: true });
    } else {
      const introText = await introTextPromise;
      if (myGeneration !== ttsStopGeneration || !isCodingSessionRouteActive()) return;
      if (!introText) {
        window.alert("인트로 오디오가 준비되지 않았습니다. 다시 시작해 주세요.");
        return;
      }
      const collected = [];
      completed = await fetchAndPlayTts({
        token,
        sessionId,
        text: introText,
        // 서버 환경변수(TTS_MAX_SENTENCES)가 너무 낮게 설정되어 있어도
        // 메인 인트로가 잘리지 않도록 충분히 큰 값으로 명시한다.
        maxSentences: 30,
        collectChunks: (c) => collected.push(c),
      });
      if (myGeneration !== ttsStopGeneration || !isCodingSessionRouteActive()) return;
      if (completed && collected.length && sessionId) {
        try {
          sessionStorage.setItem(INTRO_AUDIO_KEY(sessionId), JSON.stringify(collected));
        } catch (e) {
          console.warn("intro 오디오 캐시 저장 실패:", e);
        }
      }
    }
    if (completed && sessionStage.value === "intro") {
      startAnswerCountdown(ANSWER_COUNTDOWN_SECONDS);
      showReloadIntroModal.value = false;
    }
  } catch (err) {
    console.error("인트로 TTS 재생 오류:", err);
    if (err && err.name === "NotAllowedError") {
      introPlayBlocked.value = true;
      if (cameFromReload.value) {
        showReloadIntroModal.value = true;
      } else {
        setupIntroGestureResume();
      }
    }
  } finally {
    isTtsPlaying.value = false;
  }
};

/* -----------------------------
  ⏱ 코딩 단계: 2분마다 코드 기반 질문 요청
------------------------------ */
const currentStage = ref("intro");
const CODING_QUESTION_INTERVAL_MS = 120000; // 2분
const CODING_ANSWER_AUTOSTART_DELAY_SECONDS = 5;
let codingQuestionTimer = null;
const isQuestionPolling = ref(false);

const requestCodingQuestion = async () => {
  // 아직 코딩 스테이지가 아니거나, 사용자가 말하는 중이면 아무 것도 하지 않음
  if (currentStage.value !== "coding") return;
  if (isRecording.value || isSttRunning.value) return;
  if (isQuestionPolling.value) return;
  const myGeneration = ttsStopGeneration;
  if (!isCodingSessionRouteActive()) return;

  const token = localStorage.getItem("jobtory_access_token");
  const sessionId = route.query.session_id;
  if (!token || !sessionId) return;

  isQuestionPolling.value = true;
  try {
    const resp = await fetch(
      `${BACKEND_BASE}/api/livecoding/session/question/`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ session_id: sessionId }),
      }
    );
    const data = await resp.json().catch(() => ({}));
    if (myGeneration !== ttsStopGeneration || !isCodingSessionRouteActive()) return;

    if (!resp.ok || data.skipped) {
      // 질문을 건너뛴 경우 조용히 반환
      return;
    }

    // 서버에서 이미 TTS 오디오까지 내려온 경우
    const preserveTtsPlaying = isTtsPlaying.value;
    let ttsOk = false;
    if (Array.isArray(data.tts_audio) && data.tts_audio.length) {
      try {
        if (!preserveTtsPlaying) isTtsPlaying.value = true;
        ttsOk = await playTtsChunks(data.tts_audio);
      } catch (err) {
        console.error("coding question TTS 재생 실패:", err);
      } finally {
        if (!preserveTtsPlaying) isTtsPlaying.value = false;
      }
    } else {
      const questionText = (data.question || "").trim();
      if (!questionText) return;

      // 텍스트만 온 경우, 인트로 TTS API를 통해 읽어준다.
      try {
        if (!preserveTtsPlaying) isTtsPlaying.value = true;
        ttsOk = await fetchAndPlayTts({
          token,
          sessionId,
          text: questionText,
          maxSentences: 10,
        });
      } catch (err) {
        console.error("coding question TTS 요청 실패:", err);
      } finally {
        if (!preserveTtsPlaying) isTtsPlaying.value = false;
      }
    }

    if (ttsOk) {
      if (myGeneration !== ttsStopGeneration || !isCodingSessionRouteActive()) return;
      if (currentStage.value !== "coding") return;
      if (isRecording.value || isSttRunning.value || isHintRecording.value) return;
      startAnswerCountdown(CODING_ANSWER_AUTOSTART_DELAY_SECONDS);
    }
  } catch (err) {
    console.error("coding question 요청 실패:", err);
  } finally {
    isQuestionPolling.value = false;
  }
};

const startCodingQuestionTimer = () => {
  if (codingQuestionTimer) return;
  codingQuestionTimer = setInterval(() => {
    void requestCodingQuestion();
  }, CODING_QUESTION_INTERVAL_MS);
};

const stopCodingQuestionTimer = () => {
  if (codingQuestionTimer) {
    clearInterval(codingQuestionTimer);
    codingQuestionTimer = null;
  }
};

/* -----------------------------
  ✂ 이하 기존 코드 유지
----------------------------- */
const languageTemplates = {
  python3: `def solution():\n    answer = 0\n    # TODO: 코드를 작성하세요.\n    return answer\n`,
  java: `class Solution {\n    public int solution() {\n        int answer = 0;\n        // TODO: 코드를 작성하세요.\n        return answer;\n    }\n}\n`,
  c: `#include <stdio.h>\n\nint solution() {\n    int answer = 0;\n    // TODO: 코드를 작성하세요.\n    return answer;\n}\n`,
  cpp: `#include <bits/stdc++.h>\nusing namespace std;\n\nint solution() {\n    int answer = 0;\n    // TODO: 코드를 작성하세요.\n    return answer;\n}\n`,
};
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
  const problemLang = (problemData.value?.language || "").toLowerCase();
  const mapped = mapProblemLanguage(problemLang);
  if (problemData.value?.starter_code && mapped === lang) {
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
    // 서버 메타에 저장된 힌트 사용 횟수를 복원 (이어하기 시 초기화 방지)
    if (typeof data.hint_count === "number") {
      hintCount.value = Math.min(HINT_LIMIT, Math.max(0, data.hint_count));
    } else {
      hintCount.value = 0;
    }
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

    // 코딩 단계 질문용 타이머 시작 (stage는 intro→coding 전환 시점에만 실제 동작)
    startCodingQuestionTimer();
  } catch (err) {
    console.error(err);
    problemError.value = err?.message || "문제를 불러오지 못했습니다.";
  } finally {
    isLoadingProblem.value = false;
  }
};

// 힌트 요청: session_id, code, language, 문제 정보 + 사용자의 힌트 요청 발화 함께 전달
const requestHint = async (hintRequestText = "") => {
  const token = localStorage.getItem("jobtory_access_token");
  const sessionId = route.query.session_id;
  if (hintCount.value >= HINT_LIMIT) {
    showAntiCheat("sttError", "사용 가능한 힌트가 모두 소진되었습니다.");
    return;
  }
  if (!token || !sessionId) {
    showAntiCheat("sttError", "세션이나 로그인 정보가 없습니다.");
    return;
  }

  try {
    isHintLoading.value = true;
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
        hint_count: hintCount.value,
        hint_request_text: hintRequestText,
      }),
    });

    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      console.warn("hint request failed", data);
      showAntiCheat("sttError", data.detail || "힌트를 가져오지 못했습니다.");
      return;
    }

    console.log("hint result", data);

    // 힌트 사용 횟수 반영 (백엔드 응답 우선, 없으면 +1)
    if (data && typeof data.hint_count === "number") {
      hintCount.value = Math.min(HINT_LIMIT, Math.max(0, data.hint_count));
    } else {
      hintCount.value = Math.min(HINT_LIMIT, hintCount.value + 1);
    }

    // 힌트 텍스트가 내려오면 TTS API를 통해 오디오를 생성해 재생
    const hintText = (data && typeof data.hint_text === "string") ? data.hint_text : "";
    if (hintText) {
      try {
        await fetchAndPlayTts({
          token,
          sessionId,
          text: hintText,
          maxSentences: 10,
          onStart: () => {
            // 힌트 TTS가 실제로 재생되기 시작하는 시점에
            // STT 로딩 오버레이를 제거해 코딩 화면이 보이도록 한다.
            isSttRunning.value = false;
          },
        });
      } catch (err) {
        console.error("failed to play hint TTS", err);
      }
    }
  } catch (err) {
    console.error("hint request error", err);
    showAntiCheat("sttError", "힌트 요청 중 오류가 발생했습니다.");
  } finally {
    isHintLoading.value = false;
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
  // 타임아웃 시에는 세션을 바로 종료하지 않고
  // 현재 코드를 기준으로 자동 제출 및 리포트 생성을 시작한다.
  stopCodingQuestionTimer();

  const sessionId = route.query.session_id;
  const token = localStorage.getItem("jobtory_access_token");

  if (!sessionId || !token) {
    // 세션이나 토큰 정보가 없으면 기존 동작대로 세션만 종료
    try {
      if (token) {
        await fetch(`${BACKEND_BASE}/api/livecoding/session/end/`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ reason: "timeout" }),
        }).catch(() => {});
      }
    } finally {
      localStorage.removeItem("jobtory_livecoding_session_id");
      router.replace({ name: "home", query: { alert: "session_timeout" } });
    }
    return;
  }

  try {
    // 타임아웃 직전에 현재 코드를 한 번 더 저장
    await saveCodeSnapshot(code.value);

    const resp = await fetch(`${BACKEND_BASE}/api/livecoding/final-eval/start/`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ session_id: sessionId }),
    });

    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      console.warn("final-eval start failed on timeout", resp.status, data);
      window.alert(
        data?.detail ||
          "제한 시간이 만료되어 세션이 종료되었습니다. 리포트 생성에 실패했습니다."
      );
      localStorage.removeItem("jobtory_livecoding_session_id");
      router.replace({ name: "home", query: { alert: "session_timeout" } });
      return;
    }

    // 자동 제출이 시작되면 렌더링 화면으로 이동하여 리포트 생성을 기다린다.
    router.replace({
      name: "livecoding-rendering",
      query: { session_id: sessionId, timeout: "1" },
    });
  } catch (e) {
    console.error("failed to start final eval on timeout", e);
    window.alert(
      "제한 시간이 만료되어 세션이 종료되었습니다. 리포트 생성 중 오류가 발생했습니다."
    );
    localStorage.removeItem("jobtory_livecoding_session_id");
    router.replace({ name: "home", query: { alert: "session_timeout" } });
  }
};

const startCountdown = () => {
  clearCountdown();
  countdownTimer = setInterval(() => {
    if (remainingSeconds.value === null || remainingSeconds.value === undefined)
      return;
    const next = Math.max(0, Number(remainingSeconds.value) - 1);
    remainingSeconds.value = next;
    if (next <= 0) {
      void endSessionDueToTimeout();
    }
  }, 1000);
};

const startCountdownOnce = () => {
  if (countdownStarted.value) return;
  countdownStarted.value = true;
  startCountdown();
};

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

const mapProblemLanguage = (lang = "") => {
  switch (lang.toLowerCase()) {
    case "python":
    case "python3":
      return "python3";
    case "java":
      return "java";
    case "c":
      return "c";
    case "cpp":
    case "c++":
      return "cpp";
    default:
      return "python3";
  }
};

/* -----------------------------
   👀 안티치트 / 웹캠 감시
----------------------------- */
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
const isAntiCheatReady = computed(() => !isIntroPreparing.value);

const KEY_WINDOW_MS = 2000;
const KEY_THRESHOLD = 12;
const ABNORMAL_COOLDOWN_MS = 8000;
const COPY_COOLDOWN_MS = 4000;
const OFFSCREEN_LIMIT = 3000;
const OFFSCREEN_COOLDOWN_MS = 1500;

const clearAntiCheatTimer = () => {
  if (antiCheatTimer) {
    clearTimeout(antiCheatTimer);
    antiCheatTimer = null;
  }
};

const showAntiCheat = (stateKey, detail) => {
  if (!isAntiCheatReady.value) return;
  clearAntiCheatTimer();
  setAntiCheatState(stateKey, { detail, timestamp: Date.now() });
  antiCheatTimer = setTimeout(() => {
    resetAntiCheatState();
    antiCheatTimer = null;
  }, 7000);
};

const sendAntiCheatEvent = async (eventType) => {
  const sessionId = route.query.session_id;
  const token = localStorage.getItem("jobtory_access_token");
  if (!sessionId || !token) return;
  try {
    await fetch(`${BACKEND_BASE}/api/livecoding/anti-cheat/event/`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ session_id: sessionId, event_type: eventType }),
    });
  } catch (err) {
    console.error("anti-cheat event failed", err);
  }
};

const registerOffscreenInfraction = (stateKey, baseDetail) => {
  if (!isAntiCheatReady.value) return;
  const now = Date.now();
  if (now - lastOffscreenAlert < OFFSCREEN_COOLDOWN_MS) {
    return;
  }
  lastOffscreenAlert = now;

  offscreenCount.value += 1;
  const withCount = `${baseDetail} (누적 ${offscreenCount.value}/${OFFSCREEN_LIMIT})`;
  showAntiCheat(stateKey, withCount);
  void sendAntiCheatEvent("typing_offscreen");

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
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ session_id: sessionId, reason }),
      }).catch(() => {});
    }
  } finally {
    localStorage.removeItem("jobtory_livecoding_session_id");
    router.replace({ name: "home", query: { alert: "anti-cheat" } });
  }
};

const handleVisibilityChange = () => {
  if (document.visibilityState === "hidden") {
    if (!isAntiCheatReady.value) return;
    registerOffscreenInfraction("tabSwitch", "시험 화면을 벗어났습니다.");
  }
};

const handleWindowBlur = () => {
  if (!isAntiCheatReady.value) return;
  registerOffscreenInfraction("windowBlur", "다른 창으로 이동이 감지되었습니다.");
};

const handlePaste = () => {
  if (!isAntiCheatReady.value) return;
  showAntiCheat("pasteDetected", "외부 붙여넣기 시도가 차단되었습니다.");
  void sendAntiCheatEvent("typing_paste");
};

const handleCopy = () => {
  if (!isAntiCheatReady.value) return;
  const now = Date.now();
  if (now - lastCopyAlert < COPY_COOLDOWN_MS) return;
  lastCopyAlert = now;
  showAntiCheat("copyDetected", "복사 동작이 차단되었습니다.");
  void sendAntiCheatEvent("typing_copy");
};

const sendFrameForMediapipe = async () => {
  if (!isAntiCheatReady.value) return;
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
        body: formData,
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
        void sendAntiCheatEvent("camera_mediapipe");
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
    if (!isAntiCheatReady.value) return;
    const hasLiveTrack =
      mediaStream &&
      mediaStream.getVideoTracks().some((track) => track.readyState === "live");

    if (!hasLiveTrack) {
      cameraError.value = "웹캠 연결이 중단되었습니다.";
      if (lastCameraStatus !== "blocked") {
        showAntiCheat("cameraBlocked", cameraError.value);
        lastCameraStatus = "blocked";
        void sendAntiCheatEvent("camera_blocked");
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

const loadSessionFromApi = async () => {
  const sessionId = route.query.session_id;
  if (!sessionId) {
    problemError.value = "session_id가 없습니다. 설정을 다시 진행해 주세요.";
    return false;
  }

  const token = localStorage.getItem("jobtory_access_token");
  if (!token) {
    problemError.value = "로그인이 필요합니다.";
    router.push({ name: "login" });
    return false;
  }

  isLoadingProblem.value = true;
  problemError.value = "";

  try {
    const resp = await fetch(
      `${BACKEND_BASE}/api/livecoding/session/?session_id=${encodeURIComponent(
        sessionId
      )}`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      problemError.value =
        data?.detail || "세션 정보를 불러오지 못했습니다. 설정을 다시 진행해 주세요.";
      return false;
    }

    problemData.value = data;

    // 서버 메타에 저장된 힌트 사용 횟수를 복원 (이어하기 시 초기화 방지)
    if (typeof data.hint_count === "number") {
      hintCount.value = Math.min(HINT_LIMIT, Math.max(0, data.hint_count));
    } else {
      hintCount.value = 0;
    }

    // 서버 stage/state에 맞춰 단계 설정 (sessionStorage 단계 값은 사용하지 않음)
    const serverStage = String(data.stage || data.state || "intro").toLowerCase();
    sessionStage.value = serverStage;
    // 이어하기 진입 시에도 코딩 스테이지 질문 타이머와 상태가 정상 동작하도록
    // LangGraph 기반 현재 단계(currentStage)도 서버 단계와 동기화한다.
    currentStage.value = serverStage;
    introSecondChanceUsed.value = false;
    clearAnswerCountdown();
    isRecording.value = false;

    timeLimitSeconds.value = Number(data.time_limit_seconds || 40 * 60);
    remainingSeconds.value =
      data.remaining_seconds !== undefined && data.remaining_seconds !== null
        ? Number(data.remaining_seconds)
        : timeLimitSeconds.value;

    // intro 단계에서는 안내 음성 재생 시점에 타이머를 시작하고,
    // 그 외 단계(이어하기 등)는 바로 카운트다운과 코딩 질문 타이머를 시작한다.
    if (sessionStage.value !== "intro") {
      startCountdownOnce();
      if (sessionStage.value === "coding") {
        startCodingQuestionTimer();
      }
    }

    // 언어 & starter code 세팅
    const mappedLang = mapProblemLanguage((data.language || "").toLowerCase());
    selectedLanguage.value = mappedLang;
    if (data.starter_code) {
      code.value = data.starter_code;
    } else {
      code.value = languageTemplates[mappedLang] || languageTemplates.python3;
    }

    await loadSavedCodeIfExists(sessionId, token, mappedLang);

    return true;
  } catch (err) {
    console.error("[LiveCoding] 세션 정보 로드 실패:", err);
    problemError.value = "세션 정보를 불러오는 중 오류가 발생했습니다.";
    return false;
  } finally {
    isLoadingProblem.value = false;
  }
};

onMounted(async () => {
  const loaded = await loadSessionFromApi();
  if (loaded) {
    isIntroPreparing.value = sessionStage.value === "intro";
    const lastPath = sessionStorage.getItem(LAST_PATH_KEY) || "";
    const currentPath = window.location.pathname;
    const isReload = isReloadNavigation() && lastPath === currentPath;
    cameFromReload.value = isReload && sessionStage.value === "intro";
    // 새로고침이라도 intro이면 재생 시도 (자동재생 차단 시 모달/gesture로 처리)
    if (sessionStage.value === "intro" && isReload) {
      showReloadIntroModal.value = true;
      introPlayBlocked.value = true;
    }
    if (sessionStage.value === "intro") {
      playIntroTtsFromSession();
    }
    sessionStorage.setItem(LAST_PATH_KEY, currentPath);
  }
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 360 },
      audio: false,
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
  }

  window.addEventListener("blur", handleWindowBlur);
  document.addEventListener("visibilitychange", handleVisibilityChange);
  document.addEventListener("paste", pasteListener, { capture: true });
  document.addEventListener("copy", copyListener, { capture: true });
  document.addEventListener("mouseleave", handleMouseLeave);
  // 브라우저 탭을 완전히 닫거나 새로고침할 때도
  // 재생 중인 TTS가 남지 않도록 전역 훅을 단다.
  window.addEventListener("beforeunload", stopAllTts);
  // 뒤로가기/외부 이동/bfcache 진입 등 "페이지를 떠나는" 이벤트에서도 TTS를 정리한다.
  window.addEventListener("pagehide", stopAllTts);
  window.addEventListener("unload", stopAllTts);
});

onBeforeUnmount(() => {
  // 코딩 세션 화면을 떠나는 모든 경우(라우트 이동, 새로고침 등)에서
  // 현재 재생 중인 TTS를 가장 먼저 정리한다.
  stopAllTts();

  void saveCodeSnapshot(code.value);
  // 현재 남은 시간을 백엔드에 저장하여,
  // 문제 풀이 화면을 떠났다가 이어하기로 돌아올 때
  // 이 값부터 다시 카운트다운을 시작할 수 있도록 한다.
  try {
    const token = localStorage.getItem("jobtory_access_token");
    const sessionId =
      route.query.session_id || localStorage.getItem("jobtory_livecoding_session_id");
    if (token && sessionId && remainingSeconds.value !== null && remainingSeconds.value !== undefined) {
      void fetch(`${BACKEND_BASE}/api/livecoding/session/timer/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          session_id: sessionId,
          remaining_seconds: Number(remainingSeconds.value) || 0,
        }),
      }).catch(() => {});
    }
  } catch {
    // 타이머 저장 실패는 치명적이지 않으므로 무시
  }
  clearCountdown();
  clearIntroGestureHandler();
  if (micCooldownTimer) {
    clearTimeout(micCooldownTimer);
    micCooldownTimer = null;
  }

  if (mediaStream) {
    mediaStream.getTracks().forEach((t) => t.stop());
  }
  stopWebcamMonitor();
  if (mediapipeInterval) {
    clearInterval(mediapipeInterval);
    mediapipeInterval = null;
  }
  window.removeEventListener("blur", handleWindowBlur);
  window.removeEventListener("beforeunload", stopAllTts);
  window.removeEventListener("pagehide", stopAllTts);
  window.removeEventListener("unload", stopAllTts);
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
  stopCodingQuestionTimer();
});

// 라우트 전환(뒤로가기 / 다른 페이지 이동) 시
// 재생 중인 모든 TTS를 정리해 화면을 떠난 뒤에는 음성이 남지 않도록 한다.
onBeforeRouteLeave(() => {
  stopAllTts();
});

// 같은 컴포넌트가 유지된 채로 라우트만 바뀌는 경우에도(예: query 변경)
// 화면을 떠나는 동작에서 TTS가 남지 않도록 정리한다.
onBeforeRouteUpdate(() => {
  stopAllTts();
});
</script>

<style scoped>
@import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css");

.session-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #111827;
  color: #e5e7eb;
  font-family: "Pretendard", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
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
  position: relative;
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

.hint-counter {
  font-size: 12px;
  color: #9ca3af;
}

.mic-label {
  font-size: 13px;
  font-weight: 700;
  color: inherit;
  white-space: nowrap;
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

.intro-loading-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0b1220;
  z-index: 1200;
  pointer-events: all;
}

.intro-loading-card {
  background: #0b1220;
  border: none;
  border-radius: 14px;
  padding: 24px 28px;
  min-width: 280px;
  text-align: center;
  box-shadow: 0 18px 36px rgba(0, 0, 0, 0.35);
}

.intro-spinner {
  position: relative;
  width: 132px;
  height: 132px;
  margin: 0 auto 18px;
}

.intro-spinner span {
  position: absolute;
  inset: 0;
  transform-origin: 50% 50%;
  --count: 12;
  --deg-step: calc(360deg / var(--count));
  --delay-step: calc(1s / var(--count));
  transform: rotate(calc((var(--i) - 1) * var(--deg-step)));
}

.intro-spinner span::before {
  content: "";
  position: absolute;
  top: 14px;
  left: 50%;
  width: 9px;
  height: 36px;
  margin-left: -4.5px;
  border-radius: 10px;
  background: #e5e7eb;
  opacity: 0.18;
  animation: intro-spinner-fade 1s linear infinite;
  animation-delay: calc(-1s + var(--i) * var(--delay-step));
}


.intro-loading-text {
  margin: 0 0 6px;
  font-weight: 700;
  font-size: 17px;
  color: #f9fafb;
}

.intro-loading-sub {
  margin: 0;
  font-size: 15px;
  color: #9ca3af;
}

.refresh-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1001;
}

.refresh-modal {
  background: #0b1220;
  color: #e5e7eb;
  padding: 20px 24px;
  border-radius: 12px;
  border: 1px solid #1f2937;
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.45);
  min-width: 260px;
  text-align: center;
}

.refresh-modal h3 {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 700;
}

.refresh-modal p {
  margin: 0 0 14px;
  font-size: 13px;
  color: #cbd5e1;
}

.processing-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}

.processing-card {
  background: #0b1220;
  padding: 22px 26px;
  border-radius: 14px;
  border: 1px solid #1f2937;
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.45);
  text-align: center;
  color: #e5e7eb;
  min-width: 260px;
}

.processing-spinner {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 5px solid rgba(255, 255, 255, 0.2);
  border-top-color: #38bdf8;
  margin: 0 auto 12px;
  animation: spin 0.85s linear infinite;
}

.processing-text {
  margin: 0 0 4px;
  font-weight: 700;
  font-size: 15px;
  color: #f9fafb;
}

.processing-subtext {
  margin: 0;
  font-size: 13px;
  color: #9ca3af;
}

.recording-submit-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
  align-items: center;
  justify-content: center;
  z-index: 998;
  pointer-events: none;
}

.recording-mic-helper {
  pointer-events: none;
  margin: 0;
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(148, 163, 184, 0.22);
  color: #f9fafb;
  font-size: 13px;
  font-weight: 700;
  text-align: center;
  backdrop-filter: blur(6px);
  box-shadow: 0 16px 34px rgba(0, 0, 0, 0.45);
}

.recording-mic-button {
  pointer-events: auto;
  width: 104px;
  height: 104px;
  border-radius: 999px;
  border: 2px solid rgba(255, 255, 255, 0.38);
  background: radial-gradient(circle at 30% 20%, rgba(255, 255, 255, 0.18), rgba(255, 255, 255, 0.08)),
    linear-gradient(135deg, rgba(167, 139, 250, 0.6), rgba(99, 102, 241, 0.55));
  color: #0b1220;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  position: relative;
  overflow: visible;
  transition: transform 0.12s ease, filter 0.12s ease, opacity 0.12s ease, box-shadow 0.12s ease;
  box-shadow: 0 22px 46px rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(6px);
  animation: recording-mic-breathe 1.8s ease-in-out infinite;
}

.recording-mic-button.is-recording::before,
.recording-mic-button.is-recording::after {
  content: "";
  position: absolute;
  inset: -10px;
  border-radius: 999px;
  border: 2px solid rgba(255, 255, 255, 0.38);
  opacity: var(--mic-wave-opacity, 0.22);
  transform: scale(1);
  animation: recording-mic-wave 1.35s ease-out infinite;
  pointer-events: none;
}

.recording-mic-button.is-recording::after {
  animation-delay: 0.65s;
}

.recording-mic-button svg {
  width: 28px;
  height: 28px;
  display: block;
  color: #0b1220;
}

.recording-mic-button:hover {
  transform: translateY(-1px);
  filter: brightness(1.03);
}

.recording-mic-button:active {
  transform: translateY(0);
}

.recording-mic-button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  transform: none;
  filter: none;
  box-shadow: none;
  animation: none;
}

@keyframes recording-mic-breathe {
  0% {
    box-shadow: 0 22px 46px rgba(0, 0, 0, 0.55), 0 0 0 0 rgba(167, 139, 250, 0.22);
  }
  50% {
    box-shadow: 0 22px 46px rgba(0, 0, 0, 0.55), 0 0 0 14px rgba(167, 139, 250, 0.06);
  }
  100% {
    box-shadow: 0 22px 46px rgba(0, 0, 0, 0.55), 0 0 0 0 rgba(167, 139, 250, 0.22);
  }
}

@keyframes recording-mic-wave {
  0% {
    transform: scale(1);
    opacity: var(--mic-wave-opacity, 0.22);
  }
  100% {
    transform: scale(var(--mic-wave-scale, 2.2));
    opacity: 0;
  }
}

@keyframes intro-spinner-fade {
  0% {
    opacity: 1;
  }
  100% {
    opacity: 0;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
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
