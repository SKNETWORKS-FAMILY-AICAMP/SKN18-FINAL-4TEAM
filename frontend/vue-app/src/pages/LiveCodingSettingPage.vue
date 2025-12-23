<template>
  <div class="setting-root">
    <div class="setting-card">
      <!-- 왼쪽 사이드바 -->
      <aside class="step-sidebar">
        <h2 class="sidebar-title">시험 안내</h2>
        <ol class="step-list">
          <li
            v-for="item in steps"
            :key="item.id"
            :class="['step-item', stepClass(item.id)]"
          >
            <div class="step-index">{{ item.id }}</div>
            <div class="step-label">{{ item.label }}</div>
            <span v-if="item.id === 2 && cameraPassed" class="pass-badge">통과</span>
            <!-- ✅ 마이크 + 스피커 둘 다 통과해야 3번에 뱃지 표시 -->
            <span v-if="item.id === 3 && micPassed && speakerPassed" class="pass-badge"
              >통과</span
            >
          </li>
        </ol>
      </aside>

      <!-- 오른쪽 컨텐츠 -->
      <section class="step-content">
        <!-- 1. 안내 사항 -->
        <div v-if="currentStep === 1" class="step-panel">
          <h3 class="step-title">테스트 시작 전 안내 사항</h3>
          <p class="step-desc">테스트 시작 전에 아래 내용을 확인해 주세요.</p>
          <ul class="bullet-list">
            <li>테스트는 전체 화면 모드에서만 진행됩니다.</li>
            <li>원활한 감독을 위해 카메라 및 마이크 권한 허용이 필요합니다.</li>
            <li>화면 공유를 통해 코드 작성 화면이 실시간으로 전송됩니다.</li>
            <li>다른 탭/창으로의 잦은 이동 등 부정행위가 감지될 경우 시험이 중단될 수 있습니다.</li>
            <li>안정적인 네트워크 환경에서 참여해 주세요.</li>
            <li>이해하셨다면 ‘다음’을 눌러 진행해주세요!</li>
          </ul>

          <div class="panel-footer">
            <button class="primary-btn" @click="goNext">다음</button>
          </div>
        </div>

        <!-- 2. 웹캠 연결 -->
        <div v-else-if="currentStep === 2" class="step-panel">
          <h3 class="step-title">웹캠 연결</h3>
          <p class="step-desc">
            공정한 평가를 위해 카메라를 활성화해 주세요.<br />
            얼굴이 화면 중앙의 테두리 안에 모두 보이도록 위치를 맞춰 주세요.
          </p>

          <div class="preview-box" :class="[previewBorderClass, cameraActive ? 'preview-active' : '']">
            <video
              ref="videoRef"
              autoplay
              playsinline
              class="video-preview"
              v-show="cameraActive"
            ></video>
            <div
              v-if="cameraActive"
              class="face-target-box"
              :class="{
                'target-success': detectionStatus === 'success',
                'target-fail': detectionStatus === 'fail'
              }"
            ></div>
            <div v-show="!cameraActive" class="preview-placeholder">
              <div class="placeholder-illustration-wrap">
                <img :src="faceDetectImage" alt="카메라 안내" class="placeholder-illustration" />
              </div>
            </div>
          </div>
          <p class="help-text">
            상태:
            <strong>{{ cameraStatusText }}</strong>
          </p>

          <canvas ref="canvasRef" class="hidden-canvas"></canvas>

          <div class="panel-footer">
            <button class="secondary-btn" @click="goPrev">이전</button>
            <button class="primary-btn" @click="startCameraTest" v-if="!cameraActive">
              {{ cameraPassedOnce ? "웹캠 테스트 재시작" : "웹캠 테스트 시작" }}
            </button>
            <button
              class="primary-btn"
              :disabled="!cameraPassed"
              @click="goNext"
            >
              다음
            </button>
          </div>
        </div>

        <!-- 3. 마이크/스피커 연결 -->
        <div v-else-if="currentStep === 3" class="step-panel">
          <h3 class="step-title">마이크 연결</h3>
          <p class="step-desc">
            아래 버튼을 눌러 마이크/스피커 테스트를 진행해 주세요. 말소리가 일정 기준 이상 감지되면 자동으로 통과합니다.
          </p>

          <!-- 🎤 마이크 테스트 -->
          <div class="audio-test-box">
            <label class="audio-label">마이크 입력 레벨</label>
            <div class="audio-bar-wrapper">
              <div class="audio-bar-bg">
                <!-- 실시간 레벨 -->
                <div
                  class="audio-bar-fill"
                  :style="{ width: micLevel + '%' }"
                ></div>
                <!-- ✅ 통과 기준선 표시 -->
                <div
                  class="audio-bar-threshold"
                  :style="{ left: MIC_THRESHOLD_LEVEL + '%' }"
                ></div>
              </div>
              <span class="audio-level-text">
                {{ micLevel }}%
              </span>
            </div>
            <p class="help-text small">
              통과 기준: 바가 <strong>{{ MIC_THRESHOLD_LEVEL }}%</strong> 이상으로 올라가면 자동으로 통과합니다.
            </p>
          </div>

          <!-- 🔊 스피커 테스트 -->
          <div class="speaker-test-box">
            <label class="audio-label">스피커 테스트</label>
            <div class="speaker-actions">
              <button type="button" class="secondary-btn small" @click="playSpeakerTest">
                테스트 음성 재생
              </button>
              <button
                type="button"
                class="secondary-btn small"
                :disabled="!speakerTestPlayed"
                @click="confirmSpeakerHeard"
              >
                소리가 들렸어요
              </button>
            </div>
          </div>

          <p class="help-text">
            상태:
            <strong>
              {{
                micPassed && speakerPassed
                  ? "마이크·스피커 통과 ✅"
                  : micChecking
                  ? "음성 분석 중... 말을 해보세요 🎤"
                  : !micPassed
                  ? "마이크 테스트 필요 ❗"
                  : !speakerPassed
                  ? "스피커 테스트 필요 ❗"
                  : "테스트 필요 ❗"
              }}
            </strong>
          </p>

          <div class="panel-footer">
            <button class="secondary-btn" @click="goPrev">이전</button>
            <button class="primary-btn" @click="startMicTest">
              {{ micChecking ? "테스트 중..." : "마이크/스피커 테스트" }}
            </button>
            <button
              class="primary-btn"
              :disabled="!micPassed || !speakerPassed"
              @click="goNext"
            >
              다음
            </button>
          </div>
        </div>

        <!-- 4. 설정 완료 -->
        <div v-else-if="currentStep === 4" class="step-panel">
          <h3 class="step-title">설정 완료</h3>
          <p class="step-desc">모든 준비가 완료되었습니다.</p>

          <ul class="bullet-list">
            <li>웹캠과 마이크가 정상적으로 작동하는지 다시 한 번 확인해 주세요.</li>
            <li>테스트가 시작되면 제한 시간 내에 문제를 해결해야 합니다.</li>
            <li>테스트 종료 후 결과와 피드백 리포트가 제공됩니다.</li>
            <li>시작 버튼을 누르면 즉시 라이브 코딩 테스트가 시작됩니다.</li>
          </ul>

          <div class="panel-footer">
            <button class="secondary-btn" @click="goPrev">이전</button>
            <button
              class="primary-btn"
              :disabled="!cameraPassed || !micPassed || !speakerPassed || isStarting"
              @click="startTest"
            >
              {{ isStarting ? "시작 중..." : "시작" }}
            </button>
          </div>
        </div>
      </section>
    </div>

  </div>
</template>

<script setup>
import { ref, onBeforeUnmount, nextTick, computed } from "vue";
import { useRouter } from "vue-router";
import { onMounted } from "vue"

const router = useRouter();
const faceDetectImage = new URL("../assets/face_detect_image.png", import.meta.url).href;
const BACKEND_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const DEFAULT_LANGUAGE = "python";

const resetLivecodingCaches = () => {
  sessionStorage.removeItem("jobtory_intro_tts_text");
  sessionStorage.removeItem("jobtory_intro_tts_audio");
  sessionStorage.removeItem("jobtory_livecoding_problem_data");
  localStorage.removeItem("jobtory_livecoding_session_id");
};

/* ----- 공통: 로그인 보장 헬퍼 ----- */
const ensureLoggedIn = () => {
  const token = localStorage.getItem("jobtory_access_token");
  if (!token) {
    window.alert("라이브 코딩을 시작하려면 먼저 로그인해 주세요.");
    router.push({ name: "login" });
    return null;
  }
  return token;
};

/* ----- 마이크 통과 기준 상수 (즉시 통과 버전) ----- */
// rms가 이 값 이상이면 "충분히 크게 말한 것"으로 판단
const RMS_THRESHOLD = 3;

// UI용 퍼센트 기준선 (micLevel 계산 방식과 동일 스케일)
const MIC_THRESHOLD_LEVEL = Math.min(
  100,
  Math.round((RMS_THRESHOLD / 60) * 100)
);

/* ----- 단계 ----- */
const currentStep = ref(1);
const steps = [
  { id: 1, label: "안내 사항" },
  { id: 2, label: "웹캠 연결" },
  { id: 3, label: "마이크 연결" },
  { id: 4, label: "설정 완료" },
];

const stepClass = (id) => {
  if (id === currentStep.value) return "is-active";
  if (id < currentStep.value) return "is-done";
  return "is-upcoming";
};

const goNext = () => {
  const prevStep = currentStep.value;
  if (prevStep === 2) {
    stopCamera();
    if (cameraPassed.value) {
      cameraPassedOnce.value = true;
    }
  }
  if (currentStep.value < 4) currentStep.value += 1;
};

const goPrev = () => {
  const prevStep = currentStep.value;
  if (prevStep === 2) {
    stopCamera();
    cameraPassed.value = false;
    detectionStatus.value = "idle";
    cameraPassedOnce.value = false;
  }
  if (currentStep.value > 1) currentStep.value -= 1;
};

/* ----- 웹캠 체크 ----- */
const videoRef = ref(null);
const canvasRef = ref(null);
const cameraActive = ref(false);
const cameraPassed = ref(false);
const cameraPassedOnce = ref(false);
const cameraChecking = ref(false);
let cameraStream = null;
let mediapipeInterval = null;
const detectionStatus = ref("idle"); // idle | success | fail

const previewBorderClass = computed(() => {
  if (!cameraActive.value) return "border-idle";
  if (detectionStatus.value === "success") return "border-success";
  if (detectionStatus.value === "fail") return "border-fail";
  return "border-idle";
});

const cameraStatusText = computed(() => {
  if (cameraActive.value) {
    if (detectionStatus.value === "success") return "얼굴 인식 성공! ✅";
    if (cameraChecking.value) return "얼굴 감지 중...";
    if (detectionStatus.value === "fail") return "얼굴이 인식되지 않았습니다.";
    return "얼굴 감지 중...";
  }
  return cameraPassed.value ? "얼굴 인식 성공! ✅" : "테스트 필요 ❗";
});

const stopFaceDetection = () => {
  if (mediapipeInterval) {
    clearInterval(mediapipeInterval);
    mediapipeInterval = null;
  }
};

const sendFrameForMediapipe = async () => {
  const video = videoRef.value;
  if (!video || video.readyState < 2) return;

  const canvas = document.createElement("canvas");
  // 경량화를 위해 해상도 축소
  canvas.width = 192;
  canvas.height = 108;
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
      // 설정 페이지는 얼굴 존재만 확인하는 경량 엔드포인트 사용
      const resp = await fetch(
        `${BACKEND_BASE}/mediapipe/presence/`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) {
        detectionStatus.value = "fail";
        cameraPassed.value = false;
        return;
      }

      const faceCount = Number(data.face_count ?? 0);
      const hasFace = faceCount >= 1;
      detectionStatus.value = hasFace ? "success" : "fail";
      cameraPassed.value = hasFace;
      // 한 번 성공하면 추가 요청을 중단해 부하를 줄입니다.
      if (hasFace) {
        stopFaceDetection();
      }
    } catch (err) {
      detectionStatus.value = "fail";
      cameraPassed.value = false;
    }
  }, "image/jpeg", 0.35);
};

const startCameraTest = async () => {
  cameraPassed.value = false;
  cameraChecking.value = true;
  detectionStatus.value = "idle";

  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: true });

    cameraActive.value = true;
    await nextTick();

    if (videoRef.value) {
      videoRef.value.srcObject = cameraStream;
    }

    setTimeout(() => {
      checkCameraBrightness();
      stopFaceDetection();
      mediapipeInterval = setInterval(() => {
        void sendFrameForMediapipe();
      }, 1000);
    }, 800);
  } catch (e) {
    cameraChecking.value = false;
    alert("웹캠 접근이 거부되었습니다. 브라우저 권한 설정을 확인해 주세요.");
  }
};

const checkCameraBrightness = () => {
  try {
    const video = videoRef.value;
    const canvas = canvasRef.value;
    if (!video || !canvas) {
      cameraChecking.value = false;
      return;
    }

    const width = 160;
    const height = 90;
    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, width, height);
    const frame = ctx.getImageData(0, 0, width, height);
    const data = frame.data;

    let total = 0;
    for (let i = 0; i < data.length; i += 4) {
      total += (data[i] + data[i + 1] + data[i + 2]) / 3;
    }
    // 밝기 값은 참고용으로만 사용 (통과/실패 판정은 서버 Mediapipe 결과에 따름)
  } catch (e) {
    cameraPassed.value = false;
  } finally {
    cameraChecking.value = false;
  }
};

const stopCamera = () => {
  stopFaceDetection();
  if (cameraStream) {
    cameraStream.getTracks().forEach((t) => t.stop());
    cameraStream = null;
  }
  cameraActive.value = false;
};

/* ----- 마이크 체크 (기준선 넘는 순간 통과) ----- */
const micLevel = ref(0);
const micPassed = ref(false);
const micChecking = ref(false);

let micStream = null;
let audioCtx = null;
let analyser = null;
let micAnimationId = null;
let micCheckTimeout = null;

const startMicTest = async () => {
  micPassed.value = false;
  micChecking.value = true;

  stopMic();

  try {
    micStream = await navigator.mediaDevices.getUserMedia({ audio: true });

    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioCtx.createMediaStreamSource(micStream);
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 2048;

    source.connect(analyser);

    const dataArray = new Uint8Array(analyser.fftSize);
    let maxVolume = 0;

    const updateLevel = () => {
      if (!analyser) return;
      analyser.getByteTimeDomainData(dataArray);

      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) {
        const v = dataArray[i] - 128;
        sum += v * v;
      }
      const rms = Math.sqrt(sum / dataArray.length);

      maxVolume = Math.max(maxVolume, rms);

      // UI용 퍼센트 레벨
      micLevel.value = Math.min(100, Math.round((rms / 60) * 100));

      // ✅ 기준선 넘는 순간 통과 처리
      if (rms >= RMS_THRESHOLD) {
        console.log("Mic passed with rms:", rms);
        micPassed.value = true;
        micChecking.value = false;
        stopMic(false); // 스트림/타이머 정리 (레벨은 유지)
        return;
      }

      micAnimationId = requestAnimationFrame(updateLevel);
    };

    updateLevel();

    // 최대 5초까지만 기다리고, 그 안에 통과 못 하면 실패
    micCheckTimeout = setTimeout(() => {
      if (!micPassed.value) {
        micChecking.value = false;
        console.log("Mic test failed, maxVolume:", maxVolume);
        stopMic(false);
      }
    }, 5000);
  } catch (e) {
    micChecking.value = false;
    alert("마이크 접근이 거부되었습니다. 브라우저 권한 설정을 확인해 주세요.");
  }
};

const stopMic = (resetLevel = true) => {
  if (micAnimationId) {
    cancelAnimationFrame(micAnimationId);
    micAnimationId = null;
  }
  if (micCheckTimeout) {
    clearTimeout(micCheckTimeout);
    micCheckTimeout = null;
  }
  if (micStream) {
    micStream.getTracks().forEach((t) => t.stop());
    micStream = null;
  }
  if (audioCtx) {
    audioCtx.close();
    audioCtx = null;
  }
  if (resetLevel) {
    micLevel.value = 0;
  }
};

/* ----- 스피커 체크 ----- */
const speakerPassed = ref(false);
const speakerTestPlayed = ref(false);

const playSpeakerTest = () => {
  speakerTestPlayed.value = true;

  const ctx = new (window.AudioContext || window.webkitAudioContext)();
  const osc = ctx.createOscillator();
  osc.type = "sine";
  osc.frequency.value = 880;

  osc.connect(ctx.destination);
  osc.start();

  setTimeout(() => {
    osc.stop();
    ctx.close();
  }, 1000);
};

const confirmSpeakerHeard = () => {
  speakerPassed.value = true;
};


/* ----- 마지막: 테스트 시작 ----- */
const isStarting = ref(false);

const startTest = async () => {
  if (isStarting.value) return;
  const token = ensureLoggedIn();
  if (!token) return;
  isStarting.value = true;

  try {
    // 기본 준비(warmup + 문제 프리로드)가 되어 있는지 확인
    if (!problemData.value) {
      const ok = await runInitialSetup();
      if (!ok) {
        window.alert("환경 준비에 실패했습니다. 다시 시도해 주세요.");
        return;
      }
    }

    const resp = await fetch(`${BACKEND_BASE}/api/livecoding/start/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        problem_data: problemData.value,
      }),
    });

    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      window.alert(data.detail || "라이브 코딩 세션을 시작하지 못했습니다.");
      return;
    }
    if (!data.session_id) {
      window.alert("세션 ID를 받지 못했습니다. 다시 시도해 주세요.");
      return;
    }
    localStorage.setItem("jobtory_livecoding_session_id", data.session_id);

 
    router.replace({
      name: "coding-session",
      query: {
        session_id: data.session_id,
      },
    });
  } catch (err) {
    console.error(err);
    window.alert(
      "라이브 코딩 세션을 시작하지 못했습니다. 잠시 후 다시 시도해 주세요."
    );
  } finally {
    isStarting.value = false;
  }
};

/* -----------------------------------------
   LangGraph / 문제
-------------------------------------------- */
const problemData = ref(null);
const hasInitRun = ref(false);
const isWarmed = ref(false);
const isPreloading = ref(false);
const warmupLanggraph = async () => {
  if (isWarmed.value) return true;
  try {
    const token = ensureLoggedIn();
    if (!token) return false;

    const resp = await fetch(`${BACKEND_BASE}/api/warmup/langgraph/`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    const data = await resp.json().catch(() => ({}));
    if (resp.ok && data?.status === "warmed") {
      isWarmed.value = true;
      return true;
    }
  } catch (err) {
    console.warn("warmup failed", err);
  }
  return false;
};

const preloadProblem = async () => {
  if (problemData.value) return true; // 이미 문제를 받아두었으면 다시 랜덤 요청하지 않음
  if (isPreloading.value) return !!problemData.value;
  isPreloading.value = true;
  try {
    const token = ensureLoggedIn();
    if (!token) return false;

    const resp = await fetch(`${BACKEND_BASE}/api/livecoding/preload/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        language: DEFAULT_LANGUAGE,
      }),
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      window.alert(data?.detail || "문제 준비 중 오류가 발생했습니다.");
      return false;
    }
    if (!data?.problem_id) {
      window.alert("문제 정보를 받지 못했습니다. 다시 시도해 주세요.");
      return false;
    }
    console.log("[livecoding][preload] problem loaded", {
      problem_id: data.problem_id,
    });
    problemData.value = data;
    return true;
  } catch (err) {
    console.error(err);
    window.alert("문제 준비 중 오류가 발생했습니다. 다시 시도해 주세요.");
    return false;
  } finally {
    isPreloading.value = false;
  }
};

/* ----- 초기 자동 셋업: warmup + 문제 프리로드만 ----- */
const runInitialSetup = async () => {
  if (hasInitRun.value) return true;
  try {
    const [warmOk, preloaded] = await Promise.all([warmupLanggraph(), preloadProblem()]);
    if (!warmOk || !preloaded) return false;

    hasInitRun.value = true;
    return true;
  } catch (e) {
    console.error("runInitialSetup 실패:", e);
    return false;
  }
};

/* ----- 컴포넌트 언마운트 시 정리 ----- */
onBeforeUnmount(() => {
  stopCamera();
  stopMic();
});

onMounted(() => {
  const token = ensureLoggedIn();
  if (!token) return;          // 로그인 페이지로 보내고 초기화 중단
  void runInitialSetup();      // warmup + preload 실행
});
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap");

.setting-root {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: #262728;
  font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.setting-card {
  display: grid;
  grid-template-columns: 260px minmax(520px, 720px);
  background: #e5e7eb;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.4);
  width: 100%;
  max-width: 1200px;
  min-height: 80vh;
}

/* 사이드바 */
.step-sidebar {
  background: #e5e7eb;
  padding: 24px 20px;
  border-right: 1px solid #d1d5db;
}

.sidebar-title {
  font-size: 18px;
  font-weight: 800;
  margin-bottom: 16px;
  color: #111827;
}

.step-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 4px;
  border-radius: 8px;
  font-size: 14px;
  position: relative;
}

.step-index {
  width: 24px;
  height: 24px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

.step-label {
  font-weight: 600;
}

.pass-badge {
  position: absolute;
  right: 4px;
  top: 7px;
  font-size: 11px;
  background: #10b981;
  color: #f9fafb;
  padding: 2px 6px;
  border-radius: 999px;
}

/* 상태별 스타일 */
.step-item.is-active {
  background: #d1d5db;
}

.step-item.is-active .step-index {
  background: #111827;
  color: #f9fafb;
}

.step-item.is-done .step-index {
  background: #10b981;
  color: #f9fafb;
}

.step-item.is-upcoming .step-index {
  background: #f9fafb;
  color: #4b5563;
}

/* 오른쪽 패널 */
.step-content {
  background: #f3f4f6;
  padding: 28px 32px;
}

.step-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.step-title {
  font-size: 20px;
  font-weight: 800;
  margin-bottom: 8px;
  color: #111827;
}

.step-desc {
  font-size: 14px;
  color: #4b5563;
  margin-bottom: 18px;
}

.bullet-list {
  margin: 0;
  padding-left: 18px;
  font-size: 14px;
  color: #111827;
}

.bullet-list li + li {
  margin-top: 6px;
}

/* 웹캠 프리뷰 */
.preview-box {
  margin-top: 18px;
  flex: 0 0 auto;
  border-radius: 10px;
  border: 3px dashed #9ca3af;
  background: #f1f3f5;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  width: 100%;
  height: 320px;
  overflow: hidden;
}

.preview-active {
  width: 60%;
  margin-left: auto;
  margin-right: auto;
  transition: width 0.2s ease;
}

.border-idle {
  border-style: dashed;
  border-color: #9ca3af;
}

.border-success {
  border-style: dashed;
  border-color: #9ca3af;
}

.border-fail {
  border-style: dashed;
  border-color: #9ca3af;
}

.video-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 9px;
}

.face-target-box {
  position: absolute;
  inset: 10%;
  border: 4px solid #4b5563;
  border-radius: 16px;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.06);
  pointer-events: none;
  transition: border-color 0.2s ease;
}

.target-success {
  border-color: #10b981;
}

.target-fail {
  border-color: #ef4444;
}

.preview-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #1f2937;
  text-align: center;
  padding: 16px;
}

.placeholder-illustration {
  width: 176px;
  height: auto;
  border-radius: 12px;
  opacity: 0.3;
}

.placeholder-illustration-wrap {
  background: transparent;
  border-radius: 0;
  padding: 0;
  box-shadow: none;
}

.camera-guidance {
  margin-top: 14px;
  font-size: 14px;
  line-height: 1.6;
  color: #1f2937;
  text-align: center;
}

.test-running-text {
  font-size: 14px;
  color: #4b5563;
  font-weight: 600;
}

/* 마이크 테스트 */
.audio-test-box {
  margin-top: 18px;
}

.audio-label {
  font-size: 13px;
  color: #4b5563;
  margin-bottom: 6px;
  display: block;
}

.audio-bar-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
}

.audio-bar-bg {
  flex: 1;
  height: 10px;
  border-radius: 999px;
  background: #e5e7eb;
  overflow: hidden;
  position: relative; /* 기준선 absolute 포지셔닝용 */
}

.audio-bar-fill {
  height: 100%;
  border-radius: 999px;
  background: #10b981;
  transition: width 0.12s ease-out;
}

/* ✅ 통과 기준선 */
.audio-bar-threshold {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #ef4444; /* 빨간 기준선 */
  transform: translateX(-50%);
  opacity: 0.9;
}

.audio-level-text {
  font-size: 12px;
  color: #4b5563;
}

/* 스피커 테스트 */
.speaker-test-box {
  margin-top: 16px;
}

.speaker-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.secondary-btn.small {
  padding: 6px 12px;
  font-size: 12px;
}

/* 공통 */
.help-text {
  margin-top: 10px;
  font-size: 13px;
  color: #4b5563;
}

.help-text.small {
  font-size: 12px;
  color: #6b7280;
}

/* 푸터 버튼 */
.panel-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: auto;
  padding-top: 24px;
  flex-wrap: wrap;
}

.primary-btn,
.secondary-btn {
  min-width: 96px;
  padding: 8px 18px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
}

.primary-btn {
  background: #111827;
  color: #f9fafb;
}

.primary-btn:hover {
  filter: brightness(1.05);
}

.primary-btn:disabled {
  background: #6b7280;
  cursor: not-allowed;
}

.secondary-btn {
  background: #e5e7eb;
  color: #111827;
}

.secondary-btn:hover {
  filter: brightness(0.98);
}

/* 숨김 캔버스 */
.hidden-canvas {
  display: none;
}

@media (max-width: 900px) {
  .setting-root {
    padding: 20px;
  }

  .setting-card {
    grid-template-columns: 1fr;
  }

  .step-sidebar {
    border-right: none;
    border-bottom: 1px solid #d1d5db;
  }
}
</style>