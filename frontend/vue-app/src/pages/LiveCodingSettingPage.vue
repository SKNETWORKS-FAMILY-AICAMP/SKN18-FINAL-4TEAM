<template>
  <div class="setting-root">
    <div class="setting-card">
      
      <aside class="step-sidebar">
        <h2 class="sidebar-title">Environment Setup</h2>
        <div class="step-progress">
          <div 
            v-for="(item, index) in steps" 
            :key="item.id" 
            class="step-item"
            :class="stepClass(item.id)"
          >
            <div class="step-indicator">
              <span v-if="isStepCompleted(item.id)" class="check-icon">✔</span>
              <span v-else>{{ index + 1 }}</span>
            </div>
            <div class="step-info">
              <span class="step-label">{{ item.label }}</span>
              <span class="step-status" v-if="currentStep === item.id">Current Step</span>
            </div>
          </div>
          <div class="progress-line-bg"></div>
          <div class="progress-line-fill" :style="{ height: `${((currentStep - 1) / (steps.length - 1)) * 100}%` }"></div>
        </div>
      </aside>

      <section class="step-content">
        
        <div v-if="currentStep === 1" class="step-panel fade-in">
          <div class="panel-header">
            <h3>Before You Start</h3>
            <p>안정적인 테스트 환경을 위해 다음 사항을 확인해주세요.</p>
          </div>
          
          <div class="info-grid">
            <div class="info-card">
              <span class="icon">🖥️</span>
              <h4>전체 화면</h4>
              <p>부정행위 방지를 위해</p>
              <p>전체 화면 모드로 진행됩니다.</p>
            </div>
            <div class="info-card">
              <span class="icon">📷</span>
              <h4>웹캠 & 마이크</h4>
              <p>실시간 감독을 위해</p>
              <p>장치 권한 허용이 필요합니다.</p>
            </div>
            <div class="info-card">
              <span class="icon">📡</span>
              <h4>네트워크</h4>
              <p>끊김 없는 테스트를 위해</p>
              <p>안정적인 인터넷을 사용하세요.</p>
            </div>
          </div>

          <ul class="bullet-list">
              <li>작성된 코드는 화면 공유를 통해 실시간으로 전송됩니다.</li>
              <li>다른 탭/창으로의 잦은 이동 등 부정행위가 감지되었을 경우
              시험이 중단될 수 있습니다.</li>
            </ul>

          <div class="panel-footer">
            <button class="btn-primary" @click="goNext">확인했습니다.</button>
          </div>
        </div>

        <div v-else-if="currentStep === 2" class="step-panel fade-in">
          <div class="panel-header">
            <h3>📷 Camera Check</h3>
            <p>얼굴이 화면 중앙 프레임 안에 잘 들어오는지 확인해주세요.</p>
          </div>

          <div class="preview-container" :class="detectionStatus">
            <video ref="videoRef" autoplay playsinline class="video-preview" v-show="cameraActive"></video>
            
            <div v-if="cameraActive" class="face-guide-box" :class="detectionStatus">
              <div class="guide-corner top-left"></div>
              <div class="guide-corner top-right"></div>
              <div class="guide-corner bottom-left"></div>
              <div class="guide-corner bottom-right"></div>
            </div>

            <div v-show="!cameraActive" class="placeholder-box">
              <div class="placeholder-icon">ⓘ</div>
              <p>카메라 연결이 필요합니다.</p>
            </div>
          </div>

          <div class="status-message">
            <span class="status-dot" :class="detectionStatus"></span>
            {{ cameraStatusText }}
          </div>
          
          <canvas ref="canvasRef" class="hidden"></canvas>

          <div class="panel-footer">
            <button class="btn-secondary" @click="goPrev">이전</button>
            <button v-if="!cameraActive" class="btn-action" @click="startCameraTest">
              {{ cameraPassedOnce ? "다시 테스트하기" : "카메라 켜기" }}
            </button>
            <button class="btn-primary" :disabled="!cameraPassed" @click="goNext">다음</button>
          </div>
        </div>

        <div v-else-if="currentStep === 3" class="step-panel fade-in">
          <div class="panel-header">
            <h3>🎙️ Audio Check</h3>
            <p>마이크 입력과 스피커 출력이 정상인지 확인해주세요.</p>
          </div>

          <div class="test-module">
            <div class="module-label">
              <span>Microphone</span>
              <span class="status-badge" :class="{ 'pass': micPassed }">{{ micPassed ? 'PASS' : 'CHECKING' }}</span>
            </div>
            
            <div class="audio-visualizer">
              <div class="bar-container">
                <div class="bar-fill" :style="{ width: micLevel + '%' }"></div>
                <div class="threshold-line" :style="{ left: MIC_THRESHOLD_LEVEL + '%' }" title="통과 기준선"></div>
              </div>
              <span class="level-text">{{ micLevel }}%</span>
            </div>
            <p class="module-desc">큰 소리로 말해서 게이지가 기준선({{ MIC_THRESHOLD_LEVEL }}%)을 넘기면 통과됩니다.</p>
          </div>

          <div class="test-module">
            <div class="module-label">
              <span>Speaker</span>
              <span class="status-badge" :class="{ 'pass': speakerPassed }">{{ speakerPassed ? 'PASS' : 'PENDING' }}</span>
            </div>
            <div class="speaker-controls">
              <button class="btn-small" @click="playSpeakerTest">🔊 테스트음 재생</button>
              <button class="btn-small outline" :disabled="!speakerTestPlayed" @click="confirmSpeakerHeard">
                {{ speakerPassed ? '확인 완료' : '잘 들려요 👌' }}
              </button>
            </div>
          </div>

          <div class="panel-footer">
            <button class="btn-secondary" @click="goPrev">이전</button>
            <button class="btn-action" @click="startMicTest" v-if="!micChecking && !micPassed">
              마이크 테스트 시작
            </button>
            <button class="btn-primary" :disabled="!micPassed || !speakerPassed" @click="goNext">다음</button>
          </div>
        </div>

        <div v-else-if="currentStep === 4" class="step-panel fade-in">
          <div class="panel-header center">
            <div class="success-icon">🎉</div>
            <h3>All Set!</h3>
            <p>모든 준비가 완료되었습니다.</p>
          </div>

          <div class="final-check-list">
            <div class="check-item">
              <span class="check">✔</span> 웹캠 연결 확인됨
            </div>
            <div class="check-item">
              <span class="check">✔</span> 오디오 장치 확인됨
            </div>
            <div class="check-item">
              <span class="check">✔</span> 네트워크 상태 양호
            </div>
          </div>

          <ul class="bullet-list">
            <li>테스트가 시작되면 제한 시간 내에 문제를 해결해야 합니다.</li>
            <li>AI면접관이 작성된 코드를 바탕으로 질문하게 됩니다.</li>
            <li>사용자는 하단의 [힌트 버튼]을 누르면 질문하실 수 있습니다.</li>
            <li>테스트 종료 후에는 결과와 피드백 리포트가 제공됩니다.</li>
            <li>시작 버튼을 누르면 즉시 라이브 코딩 테스트가 시작됩니다.</li>
          </ul>

          <div class="panel-footer center">
            <button class="btn-secondary" @click="goPrev">이전</button>
            <button class="btn-primary large" :disabled="isStarting" @click="startTest">
              {{ isStarting ? "시험장 입장 중..." : "시험 시작" }}
            </button>
          </div>
        </div>

      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onBeforeUnmount, nextTick, computed, onMounted } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const BACKEND_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const DEFAULT_LANGUAGE = "python";

// --- Helpers ---
const ensureLoggedIn = () => {
  const token = localStorage.getItem("jobtory_access_token");
  if (!token) {
    window.alert("라이브 코딩을 시작하려면 먼저 로그인해 주세요.");
    router.push({ name: "login" });
    return null;
  }
  return token;
};

// --- Constants ---
const RMS_THRESHOLD = 3;
const MIC_THRESHOLD_LEVEL = Math.min(100, Math.round((RMS_THRESHOLD / 60) * 100));

// --- State ---
const currentStep = ref(1);
const steps = [
  { id: 1, label: "Notice" },
  { id: 2, label: "Camera" },
  { id: 3, label: "Audio" },
  { id: 4, label: "Ready" },
];

const cameraPassedOnce = ref(false);

const isStepCompleted = (id) => {
  if (id < currentStep.value) return true;
  if (id === 2 && cameraPassed.value) return true;
  if (id === 3 && micPassed.value && speakerPassed.value) return true;
  return false;
};

const stepClass = (id) => {
  if (id === currentStep.value) return "active";
  if (id < currentStep.value) return "completed";
  return "";
};

const goNext = () => {
  const prevStep = currentStep.value;
  if (prevStep === 2) {
    stopCamera();
    if (cameraPassed.value) cameraPassedOnce.value = true;
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

// --- Camera Logic (API Included) ---
const videoRef = ref(null);
const canvasRef = ref(null);
const cameraActive = ref(false);
const cameraPassed = ref(false);
const cameraChecking = ref(false);
let cameraStream = null;
let mediapipeInterval = null;
const detectionStatus = ref("idle"); // idle | success | fail

const cameraStatusText = computed(() => {
  if (cameraActive.value) {
    if (detectionStatus.value === "success") return "Face Detected";
    if (detectionStatus.value === "fail") return "Face Not Found";
    return "Detecting...";
  }
  return cameraPassed.value ? "Check Passed" : "Camera Required";
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
  canvas.width = 192; canvas.height = 108;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  canvas.toBlob(async (blob) => {
    if (!blob) return;
    const formData = new FormData();
    formData.append("image", blob, "frame.jpg");

    try {
      const resp = await fetch(`${BACKEND_BASE}/mediapipe/presence/`, {
        method: "POST",
        body: formData,
      });

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
      stopFaceDetection();
      mediapipeInterval = setInterval(() => void sendFrameForMediapipe(), 1000);
    }, 800);
  } catch (e) {
    cameraChecking.value = false;
    alert("웹캠 접근이 거부되었습니다. 권한을 확인해주세요.");
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

// --- Audio Logic ---
const micLevel = ref(0);
const micPassed = ref(false);
const micChecking = ref(false);
const speakerPassed = ref(false);
const speakerTestPlayed = ref(false);
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

    const update = () => {
      if (!analyser) return;
      analyser.getByteTimeDomainData(dataArray);
      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) {
        const v = dataArray[i] - 128;
        sum += v * v;
      }
      const rms = Math.sqrt(sum / dataArray.length);
      maxVolume = Math.max(maxVolume, rms);
      
      micLevel.value = Math.min(100, Math.round((rms / 60) * 100));

      if (rms >= RMS_THRESHOLD) {
        micPassed.value = true;
        micChecking.value = false;
        stopMic(false);
        return;
      }
      micAnimationId = requestAnimationFrame(update);
    };
    update();

    micCheckTimeout = setTimeout(() => {
      if (!micPassed.value) {
        micChecking.value = false;
        stopMic(false);
        console.log("Mic test failed", maxVolume);
      }
    }, 5000);
  } catch (e) {
    micChecking.value = false;
    alert("마이크 접근이 거부되었습니다.");
  }
};

const stopMic = (reset = true) => {
  if (micAnimationId) cancelAnimationFrame(micAnimationId);
  if (micCheckTimeout) clearTimeout(micCheckTimeout);
  if (micStream) {
    micStream.getTracks().forEach((t) => t.stop());
    micStream = null;
  }
  if (audioCtx) {
    audioCtx.close();
    audioCtx = null;
  }
  if (reset) micLevel.value = 0;
};

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

// --- Test Start Logic (API Included) ---
const isStarting = ref(false);
const problemData = ref(null);
const hasInitRun = ref(false);
const isWarmed = ref(false);
const isPreloading = ref(false);

const loadSelectedProblem = () => {
  if (problemData.value) return;
  const raw = sessionStorage.getItem("jobtory_livecoding_problem_data");
  if (!raw) return;
  try {
    const parsed = JSON.parse(raw);
    if (parsed && parsed.problem_id) {
      problemData.value = parsed;
    }
  } catch {}
};

const warmupLanggraph = async () => {
  if (isWarmed.value) return true;
  try {
    const token = ensureLoggedIn();
    if (!token) return false;
    const resp = await fetch(`${BACKEND_BASE}/api/warmup/langgraph/`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
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
  if (problemData.value) return true;
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
      body: JSON.stringify({ language: DEFAULT_LANGUAGE }),
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok || !data?.problem_id) return false;
    
    problemData.value = data;
    return true;
  } catch (err) {
    console.error(err);
    return false;
  } finally {
    isPreloading.value = false;
  }
};

const runInitialSetup = async () => {
  if (hasInitRun.value) return true;
  try {
    loadSelectedProblem();
    const [warmOk, preloaded] = await Promise.all([warmupLanggraph(), preloadProblem()]);
    if (!warmOk || !preloaded) return false;
    hasInitRun.value = true;
    return true;
  } catch {
    return false;
  }
};

const startTest = async () => {
  if (isStarting.value) return;
  const token = ensureLoggedIn();
  if (!token) return;
  isStarting.value = true;

  try {
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
      body: JSON.stringify({ problem_data: problemData.value }),
    });

    const data = await resp.json().catch(() => ({}));
    if (!resp.ok || !data.session_id) {
      window.alert(data.detail || "세션을 시작하지 못했습니다.");
      return;
    }
    
    localStorage.setItem("jobtory_livecoding_session_id", data.session_id);
    sessionStorage.removeItem("jobtory_livecoding_problem_data");

    router.replace({
      name: "coding-session",
      query: { session_id: data.session_id },
    });
  } catch (err) {
    console.error(err);
    window.alert("오류가 발생했습니다.");
  } finally {
    isStarting.value = false;
  }
};

onMounted(() => {
  const token = ensureLoggedIn();
  if (!token) return;
  void runInitialSetup();
});

onBeforeUnmount(() => {
  stopCamera();
  stopMic();
});
</script>

<style scoped>


.setting-root {
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #111827; /* Deep Dark */
  font-family: "Inter", sans-serif;
  color: #f3f4f6;
  overflow: hidden;
}

.setting-card {
  display: grid;
  grid-template-columns: 280px 1fr;
  width: min(1000px, 95vw);
  height: min(700px, 85vh);
  background: #1f2937;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

/* Sidebar */
.step-sidebar {
  background: #18202f;
  padding: 32px 24px;
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  flex-direction: column;
  position: relative;
}

.sidebar-title {
  font-size: 16px;
  font-weight: 700;
  color: #9ca3af;
  margin-bottom: 32px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.step-progress {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.progress-line-bg {
  position: absolute;
  top: 15px; left: 15px; bottom: 15px;
  width: 2px;
  background: #374151;
  z-index: 0;
}

.progress-line-fill {
  position: absolute;
  top: 15px; left: 15px;
  width: 2px;
  background: #6366f1; /* Indigo */
  z-index: 0;
  transition: height 0.4s ease;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
  z-index: 1;
  opacity: 0.5;
  transition: opacity 0.3s;
}

.step-item.active,
.step-item.completed {
  opacity: 1;
}

.step-indicator {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #1f2937;
  border: 2px solid #4b5563;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  color: #9ca3af;
  transition: all 0.3s;
}

.step-item.active .step-indicator {
  border-color: #6366f1;
  color: #fff;
  background: #6366f1;
  box-shadow: 0 0 15px rgba(99, 102, 241, 0.4);
}

.step-item.completed .step-indicator {
  border-color: #6366f1;
  color: #6366f1;
  background: #1f2937;
}

.check-icon { font-size: 12px; }

.step-info { display: flex; flex-direction: column; }
.step-label { font-weight: 600; font-size: 15px; color: #f3f4f6; }
.step-status { font-size: 11px; color: #6366f1; margin-top: 2px; }

/* Main Content */
.step-content {
  padding: 40px;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  background: #1f2937;
}

.step-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  animation: fadeIn 0.4s ease-out;
}

.panel-header h3 {
  font-size: 24px;
  font-weight: 800;
  margin: 0 0 8px;
  color: #fff;
}
.panel-header p { color: #9ca3af; font-size: 14px; }
.panel-header.center { text-align: center; }

.bullet-list {
  margin: 0;
  list-style: none; /* 기본 점 제거 */
  display: flex;
  flex-direction: column;
  gap: 10px; /* 항목 간 간격 */
  border-radius: 8px;
  padding: 50px 135px;
}

.bullet-list li {
  position: relative;
  padding-left: 20px; /* 불릿 공간 확보 */
  font-size: 14px;
  line-height: 1.6;
  color: #c9d1d9; /* 눈이 편안한 밝은 회색 */
  letter-spacing: -0.01em;
}

/* 커스텀 불릿 포인트 */
.bullet-list li::before {
  content: "";
  position: absolute;
  left: 6px;
  top: 10px; /* 텍스트 높이에 맞춰 중앙 정렬 */
  width: 4px;
  height: 4px;
  background-color: #58a6ff; /* IDE 포인트 컬러 (블루) */
  border-radius: 50%;
}

/* Info Cards (Step 1) */
.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 32px;
}

.info-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}
.info-card .icon { font-size: 28px; display: block; margin-bottom: 12px; }
.info-card h4 { margin: 0 0 6px; font-size: 14px; font-weight: 700; color: #e5e7eb; }
.info-card p { margin: 0; font-size: 12px; color: #9ca3af; line-height: 1.5; }

/* Camera Preview (Step 2) */
.preview-container {
  margin-top: 24px;
  width: 100%;
  height: 320px;
  background: #111827;
  border-radius: 16px;
  border: 2px dashed #4b5563;
  position: relative;
  overflow: hidden;
  transition: border-color 0.3s;
}

.preview-container.success { border-color: #10b981; border-style: solid; }
.preview-container.fail { border-color: #ef4444; border-style: solid; }

.video-preview { width: 100%; height: 100%; object-fit: cover; transform: scaleX(-1); }

.face-guide-box {
  position: absolute; top: 15%; left: 25%; right: 25%; bottom: 15%;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  transition: border-color 0.3s;
}
.face-guide-box.success { border-color: #10b981; box-shadow: 0 0 20px rgba(16, 185, 129, 0.2); }
.face-guide-box.fail { border-color: #ef4444; }

.placeholder-box {
  display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;
  color: #6b7280;
}
.placeholder-icon { font-size: 40px; margin-bottom: 12px; opacity: 0.5; }

.status-message {
  margin-top: 16px;
  display: flex; align-items: center; justify-content: center; gap: 8px;
  font-size: 14px; font-weight: 600; color: #d1d5db;
}
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: #6b7280; }
.status-dot.success { background: #10b981; }
.status-dot.fail { background: #ef4444; }

/* Audio Module (Step 3) */
.test-module {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 20px;
  margin-top: 20px;
}

.module-label { display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 14px; font-weight: 600; }
.status-badge { font-size: 11px; padding: 2px 8px; border-radius: 4px; background: #374151; color: #9ca3af; }
.status-badge.pass { background: rgba(16, 185, 129, 0.2); color: #10b981; }

.audio-visualizer { display: flex; align-items: center; gap: 12px; }
.bar-container { flex: 1; height: 8px; background: #374151; border-radius: 99px; position: relative; overflow: hidden; }
.bar-fill { height: 100%; background: #6366f1; border-radius: 99px; transition: width 0.1s; }
.threshold-line { position: absolute; top: 0; bottom: 0; width: 2px; background: #ef4444; z-index: 2; }
.level-text { font-family: "JetBrains Mono"; font-size: 12px; color: #9ca3af; width: 36px; text-align: right; }
.module-desc { font-size: 12px; color: #6b7280; margin-top: 8px; }

.speaker-controls { display: flex; gap: 10px; }

/* Final Step */
.final-check-list {
  border-radius: 10px;
  padding-top: 20px;
  padding-left: 100px;
  display: flex; flex-direction: row; gap: 20px;
}
.check-item { font-size: 15px; font-weight: 600; color: #d1d5db; display: flex; align-items: center; gap: 15px; }
.check { color: #10b981; }
.success-icon { font-size: 48px; margin-bottom: 16px; }

/* Buttons */
.panel-footer {
  margin-top: auto; padding-top: 32px;
  display: flex; justify-content: flex-end; gap: 12px;
}
.panel-footer.center { justify-content: center; }

button { cursor: pointer; transition: all 0.2s; border: none; font-family: inherit; }

.btn-primary {
  padding: 10px 24px;
  background: #6366f1; color: white;
  border-radius: 8px; font-weight: 600; font-size: 14px;
}
.btn-primary:hover { background: #4f46e5; transform: translateY(-1px); }
.btn-primary:disabled { background: #374151; color: #9ca3af; cursor: not-allowed; transform: none; }

.btn-primary.large { padding: 14px 40px; font-size: 16px; }

.btn-secondary {
  padding: 10px 20px;
  background: transparent; color: #9ca3af;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px; font-weight: 500; font-size: 14px;
}
.btn-secondary:hover { border-color: #6366f1; color: #fff; }

.btn-action {
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.1); color: #fff;
  border-radius: 8px; font-size: 14px; font-weight: 600;
}
.btn-action:hover { background: rgba(255, 255, 255, 0.2); }

.btn-small {
  padding: 6px 12px; border-radius: 6px; font-size: 12px; background: #374151; color: #e5e7eb;
}
.btn-small.outline { background: transparent; border: 1px solid #374151; }
.btn-small:hover:not(:disabled) { background: #4b5563; }

.hidden { display: none; }

/* Animations */
.fade-in { animation: fadeIn 0.4s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

/* Scrollbar */
.step-content::-webkit-scrollbar { width: 6px; }
.step-content::-webkit-scrollbar-thumb { background: #374151; border-radius: 3px; }

@media (max-width: 900px) {
  .setting-card { grid-template-columns: 1fr; height: auto; min-height: 100vh; border-radius: 0; }
  .step-sidebar { display: none; } /* 모바일에서는 사이드바 숨김 */
  .info-grid { grid-template-columns: 1fr; }
}
</style>