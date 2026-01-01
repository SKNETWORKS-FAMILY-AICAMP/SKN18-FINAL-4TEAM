<template>
  <div class="setting-root">
    <div class="bg-grid"></div>

    <div class="setting-card">
      <aside class="step-sidebar">
        <div class="sidebar-header">
          <span class="brand-logo">JOBTORY</span>
          <h2 class="sidebar-title">환경 설정</h2>
        </div>
        
        <ol class="step-list">
          <li
            v-for="item in steps"
            :key="item.id"
            :class="['step-item', stepClass(item.id)]"
          >
            <div class="step-indicator">
              <span v-if="isStepPassed(item.id)" class="check-icon">✓</span>
              <span v-else class="step-num">{{ item.id }}</span>
            </div>
            <div class="step-info">
              <span class="step-label">{{ item.label }}</span>
              <span v-if="isStepPassed(item.id)" class="step-status">완료</span>
            </div>
          </li>
        </ol>
        
        <div class="sidebar-footer">
          <p>설정이 완료되면<br/>테스트가 시작됩니다.</p>
        </div>
      </aside>

      <section class="step-content">
        <div v-if="currentStep === 1" class="step-panel fade-in">
          <div class="panel-header">
            <span class="step-tag">Step 1</span>
            <h3 class="step-title">테스트 안내</h3>
          </div>
          
          <div class="panel-body">
            <div class="info-box">
              <div class="info-item">
                <span class="icon">🖥️</span>
                <p>전체 화면 모드로만 진행됩니다.</p>
              </div>
              <div class="info-item">
                <span class="icon">📹</span>
                <p>카메라 및 마이크 권한 허용이 필수입니다.</p>
              </div>
              <div class="info-item">
                <span class="icon">📡</span>
                <p>화면 공유를 통해 코딩 과정이 녹화됩니다.</p>
              </div>
              <div class="info-item warning">
                <span class="icon">⚠️</span>
                <p>탭 이동 등 부정행위 감지 시 시험이 중단됩니다.</p>
              </div>
            </div>
          </div>

          <div class="panel-footer">
            <button class="primary-btn full-width" @click="goNext">
              동의하고 시작하기
              <svg class="arrow-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 12h14M12 5l7 7-7 7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </button>
          </div>
        </div>

        <div v-else-if="currentStep === 2" class="step-panel fade-in">
          <div class="panel-header">
            <span class="step-tag">Step 2</span>
            <h3 class="step-title">웹캠 확인</h3>
          </div>

          <div class="panel-body centered">
            <div class="camera-frame" :class="{ 'is-active': cameraActive, 'is-success': detectionStatus === 'success', 'is-fail': detectionStatus === 'fail' }">
              <video
                ref="videoRef"
                autoplay
                playsinline
                class="video-preview"
                v-show="cameraActive"
              ></video>
              
              <div class="guide-overlay" v-if="cameraActive">
                <div class="face-guide"></div>
                <div class="scan-line" v-if="detectionStatus !== 'success'"></div>
              </div>

              <div v-show="!cameraActive" class="camera-placeholder">
                <div class="placeholder-icon">📷</div>
                <p>카메라 권한을 허용해주세요</p>
              </div>
              
              <div class="status-badge" :class="detectionStatus">
                {{ cameraStatusText }}
              </div>
            </div>
          </div>

          <canvas ref="canvasRef" class="hidden-canvas"></canvas>

          <div class="panel-footer">
            <button class="secondary-btn" @click="goPrev">이전</button>
            <button class="action-btn" @click="startCameraTest" v-if="!cameraActive">
              카메라 켜기
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

        <div v-else-if="currentStep === 3" class="step-panel fade-in">
          <div class="panel-header">
            <span class="step-tag">Step 3</span>
            <h3 class="step-title">오디오 확인</h3>
          </div>

          <div class="panel-body">
            <div class="audio-check-grid">
              <div class="check-card" :class="{ 'passed': micPassed }">
                <div class="card-head">
                  <span class="icon">🎤</span>
                  <h4>마이크</h4>
                </div>
                
                <div class="meter-container">
                  <div class="meter-bar">
                    <div class="meter-fill" :style="{ width: micLevel + '%' }"></div>
                    <div class="threshold-line" :style="{ left: MIC_THRESHOLD_LEVEL + '%' }"></div>
                  </div>
                  <div class="meter-labels">
                    <span>0%</span>
                    <span class="threshold-label">통과 기준</span>
                    <span>100%</span>
                  </div>
                </div>
                
                <button class="test-btn" @click="startMicTest" :disabled="micPassed || micChecking">
                  {{ micPassed ? "확인 완료 ✅" : micChecking ? "목소리를 내세요..." : "마이크 테스트 시작" }}
                </button>
              </div>

              <div class="check-card" :class="{ 'passed': speakerPassed }">
                <div class="card-head">
                  <span class="icon">🔊</span>
                  <h4>스피커</h4>
                </div>
                <p class="card-desc">테스트 음성을 확인하세요.</p>
                
                <div class="btn-group">
                  <button class="test-btn outline" @click="playSpeakerTest">
                    ▶ 재생
                  </button>
                  <button 
                    class="test-btn" 
                    :disabled="!speakerTestPlayed || speakerPassed"
                    @click="confirmSpeakerHeard"
                  >
                    {{ speakerPassed ? "확인 완료 ✅" : "잘 들립니다" }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div class="panel-footer">
            <button class="secondary-btn" @click="goPrev">이전</button>
            <button
              class="primary-btn"
              :disabled="!micPassed || !speakerPassed"
              @click="goNext"
            >
              다음
            </button>
          </div>
        </div>

        <div v-else-if="currentStep === 4" class="step-panel fade-in">
          <div class="panel-header center">
            <div class="success-icon">🎉</div>
            <h3 class="step-title">준비 완료!</h3>
          </div>

          <div class="panel-body centered">
            <div class="final-checklist">
              <div class="check-item"><span class="check">✓</span> 웹캠 연결 확인</div>
              <div class="check-item"><span class="check">✓</span> 마이크 입력 확인</div>
              <div class="check-item"><span class="check">✓</span> 스피커 출력 확인</div>
            </div>
          </div>

          <div class="panel-footer center">
            <button
              class="primary-btn large full-width"
              :disabled="!cameraPassed || !micPassed || !speakerPassed || isStarting"
              @click="startTest"
            >
              {{ isStarting ? "입장 중..." : "테스트 시작하기" }}
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

/* 헬퍼 함수 */
const isStepPassed = (stepId) => {
  if (stepId === 1 && currentStep.value > 1) return true;
  if (stepId === 2 && cameraPassed.value) return true;
  if (stepId === 3 && micPassed.value && speakerPassed.value) return true;
  return false;
};

const ensureLoggedIn = () => {
  const token = localStorage.getItem("jobtory_access_token");
  if (!token) {
    window.alert("로그인이 필요합니다.");
    router.push({ name: "login" });
    return null;
  }
  return token;
};

const RMS_THRESHOLD = 3;
const MIC_THRESHOLD_LEVEL = Math.min(100, Math.round((RMS_THRESHOLD / 60) * 100));

const currentStep = ref(1);
const steps = [
  { id: 1, label: "안내" },
  { id: 2, label: "웹캠" },
  { id: 3, label: "오디오" },
  { id: 4, label: "완료" },
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

/* Camera Logic */
const videoRef = ref(null);
const canvasRef = ref(null);
const cameraActive = ref(false);
const cameraPassed = ref(false);
const cameraPassedOnce = ref(false);
const cameraChecking = ref(false);
let cameraStream = null;
let mediapipeInterval = null;
const detectionStatus = ref("idle");

const cameraStatusText = computed(() => {
  if (detectionStatus.value === 'success') return '인식 완료';
  if (detectionStatus.value === 'fail') return '인식 실패';
  return '인식 중...';
});

const stopFaceDetection = () => {
  if (mediapipeInterval) { clearInterval(mediapipeInterval); mediapipeInterval = null; }
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
      const resp = await fetch(`${BACKEND_BASE}/mediapipe/presence/`, { method: "POST", body: formData });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) { detectionStatus.value = "fail"; cameraPassed.value = false; return; }
      const hasFace = Number(data.face_count ?? 0) >= 1;
      detectionStatus.value = hasFace ? "success" : "fail";
      cameraPassed.value = hasFace;
      if (hasFace) stopFaceDetection();
    } catch (err) { detectionStatus.value = "fail"; cameraPassed.value = false; }
  }, "image/jpeg", 0.35);
};

const startCameraTest = async () => {
  cameraPassed.value = false; cameraChecking.value = true; detectionStatus.value = "idle";
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: true });
    cameraActive.value = true;
    await nextTick();
    if (videoRef.value) videoRef.value.srcObject = cameraStream;
    setTimeout(() => {
      stopFaceDetection();
      mediapipeInterval = setInterval(() => void sendFrameForMediapipe(), 1000);
    }, 800);
  } catch (e) { cameraChecking.value = false; alert("웹캠 권한을 확인해주세요."); }
};

const stopCamera = () => {
  stopFaceDetection();
  if (cameraStream) { cameraStream.getTracks().forEach(t => t.stop()); cameraStream = null; }
  cameraActive.value = false;
};

/* Audio Logic */
const micLevel = ref(0);
const micPassed = ref(false);
const micChecking = ref(false);
let micStream = null; let audioCtx = null; let analyser = null; let micAnimationId = null;

const startMicTest = async () => {
  micPassed.value = false; micChecking.value = true; stopMic();
  try {
    micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioCtx.createMediaStreamSource(micStream);
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 2048;
    source.connect(analyser);
    const dataArray = new Uint8Array(analyser.fftSize);
    
    const updateLevel = () => {
      if (!analyser) return;
      analyser.getByteTimeDomainData(dataArray);
      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) { const v = dataArray[i] - 128; sum += v * v; }
      const rms = Math.sqrt(sum / dataArray.length);
      micLevel.value = Math.min(100, Math.round((rms / 60) * 100));
      if (rms >= RMS_THRESHOLD) { micPassed.value = true; micChecking.value = false; stopMic(false); return; }
      micAnimationId = requestAnimationFrame(updateLevel);
    };
    updateLevel();
    setTimeout(() => { if (!micPassed.value) { micChecking.value = false; stopMic(false); } }, 5000);
  } catch (e) { micChecking.value = false; alert("마이크 권한을 확인해주세요."); }
};

const stopMic = (reset = true) => {
  if (micAnimationId) cancelAnimationFrame(micAnimationId);
  if (micStream) { micStream.getTracks().forEach(t => t.stop()); micStream = null; }
  if (audioCtx) { audioCtx.close(); audioCtx = null; }
  if (reset) micLevel.value = 0;
};

const speakerPassed = ref(false);
const speakerTestPlayed = ref(false);
const playSpeakerTest = () => {
  speakerTestPlayed.value = true;
  const ctx = new (window.AudioContext || window.webkitAudioContext)();
  const osc = ctx.createOscillator();
  osc.type = "sine"; osc.frequency.value = 880;
  osc.connect(ctx.destination);
  osc.start();
  setTimeout(() => { osc.stop(); ctx.close(); }, 1000);
};
const confirmSpeakerHeard = () => { speakerPassed.value = true; };

/* Start Test Logic */
const isStarting = ref(false);
const problemData = ref(null);

const startTest = async () => {
  if (isStarting.value) return;
  const token = ensureLoggedIn(); if (!token) return;
  isStarting.value = true;
  try {
    if (!problemData.value) await runInitialSetup();
    const resp = await fetch(`${BACKEND_BASE}/api/livecoding/start/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ problem_data: problemData.value }),
    });
    const data = await resp.json();
    if (resp.ok && data.session_id) {
      localStorage.setItem("jobtory_livecoding_session_id", data.session_id);
      router.replace({ name: "coding-session", query: { session_id: data.session_id } });
    } else { window.alert("시작 실패: " + (data.detail || "알 수 없는 오류")); }
  } catch (err) { console.error(err); window.alert("오류 발생"); }
  finally { isStarting.value = false; }
};

const runInitialSetup = async () => {
  const token = ensureLoggedIn();
  if (!token) return false;
  try {
    const resp = await fetch(`${BACKEND_BASE}/api/livecoding/preload/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ language: DEFAULT_LANGUAGE }),
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      window.alert("?ˆë¹„?¤ì§€ ??íŒ¨: " + (data.detail || "?????†ëŠ” ?¤ë¥˜"));
      return false;
    }
    problemData.value = data;
    return true;
  } catch (err) {
    console.error(err);
    window.alert("?¤ë¥˜ ë°œìƒ");
    return false;
  }
};

onBeforeUnmount(() => { stopCamera(); stopMic(); });
onMounted(() => { if(ensureLoggedIn()) runInitialSetup(); });
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap");
@import url("https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500&display=swap");

/* [핵심] 화면 고정 설정 */
.setting-root {
  height: 100vh; /* 화면 높이 100% 고정 */
  width: 100vw;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0B1120; /* Dark Navy Background */
  color: #f8fafc;
  font-family: "Inter", sans-serif;
  position: relative;
  overflow: hidden; /* 스크롤바 원천 차단 */
}

/* 배경 그리드 */
.bg-grid {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  background-image: 
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
  z-index: 0;
}

/* [핵심] 카드 크기 고정 및 비율 설정 */
.setting-card {
  display: grid;
  grid-template-columns: 240px 1fr;
  background: rgba(30, 41, 59, 0.6);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
  
  width: 90%;
  max-width: 1000px;
  height: 85vh; /* 화면 높이의 85%만 차지하여 내부 스크롤 방지 */
  min-height: 500px;
  position: relative;
  z-index: 1;
}

/* 사이드바 */
.step-sidebar {
  background: rgba(15, 23, 42, 0.6);
  border-right: 1px solid rgba(255, 255, 255, 0.05);
  padding: 32px 24px;
  display: flex;
  flex-direction: column;
}

.sidebar-header { margin-bottom: 30px; }
.brand-logo {
  font-family: "JetBrains Mono", monospace;
  font-size: 13px; color: #818cf8; letter-spacing: 0.1em; display: block; margin-bottom: 6px;
}
.sidebar-title { font-size: 20px; font-weight: 800; color: #fff; margin: 0; }

.step-list {
  list-style: none; padding: 0; margin: 0; flex: 1;
  display: flex; flex-direction: column; gap: 12px;
}

.step-item {
  display: flex; align-items: center; gap: 12px; padding: 10px;
  border-radius: 10px; transition: all 0.3s ease; color: #64748b;
}

.step-indicator {
  width: 24px; height: 24px; border-radius: 50%;
  border: 2px solid #334155; display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; background: #0f172a; transition: all 0.3s ease;
}

.step-label { font-size: 14px; font-weight: 600; }

.step-item.is-active { background: rgba(129, 140, 248, 0.1); color: #fff; }
.step-item.is-active .step-indicator { border-color: #818cf8; color: #818cf8; }
.step-item.is-done { color: #94a3b8; }
.step-item.is-done .step-indicator { background: #10b981; border-color: #10b981; color: #fff; }
.step-status { font-size: 10px; color: #10b981; margin-left: auto; font-weight: 600; }

.sidebar-footer { margin-top: auto; font-size: 12px; color: #475569; line-height: 1.5; }

/* 오른쪽 컨텐츠 영역 */
.step-content {
  padding: 40px;
  background: transparent;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* [핵심] 내부 패널 Flex Layout: 헤더 - 본문(가변) - 푸터 */
.step-panel {
  display: flex;
  flex-direction: column;
  height: 100%; /* 부모 높이 꽉 채움 */
  animation: fadeIn 0.4s ease-out;
}

.panel-header { margin-bottom: 24px; flex-shrink: 0; }
.panel-header.center { text-align: center; margin-bottom: 40px; }

.step-tag {
  font-size: 12px; color: #818cf8; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.05em; display: block; margin-bottom: 6px;
}
.step-title { font-size: 24px; font-weight: 800; color: #fff; margin: 0 0 8px; }
.step-subtitle { font-size: 16px; color: #94a3b8; margin: 0; }

/* [핵심] 본문 영역 (남은 공간 차지, 필요시만 스크롤) */
.panel-body {
  flex: 1; /* 남은 높이 모두 차지 */
  overflow-y: auto; /* 내용 넘치면 여기만 스크롤 */
  display: flex;
  flex-direction: column;
  justify-content: center; /* 내용이 적을 땐 중앙 정렬 */
  padding-right: 8px; /* 스크롤바 공간 */
}
.panel-body.centered { align-items: center; }

/* Info Box */
.info-box {
  background: rgba(15, 23, 42, 0.4); border-radius: 16px; padding: 24px;
  border: 1px solid rgba(255, 255, 255, 0.05); display: flex; flex-direction: column; gap: 14px;
}
.info-item { display: flex; gap: 12px; align-items: center; font-size: 15px; color: #cbd5e1; }
.info-item.warning { color: #fbbf24; font-weight: 600; }

/* Camera UI */
.camera-frame {
  width: 100%; max-width: 500px; aspect-ratio: 16/9; /* 비율 유지 */
  background: #000; border-radius: 16px; position: relative; overflow: hidden;
  border: 2px solid #334155; display: flex; align-items: center; justify-content: center;
}
.camera-frame.is-active { border-color: #818cf8; }
.camera-frame.is-success { border-color: #10b981; }
.camera-frame.is-fail { border-color: #ef4444; }

.video-preview { width: 100%; height: 100%; object-fit: cover; transform: scaleX(-1); }
.guide-overlay { position: absolute; inset: 0; pointer-events: none; }
.face-guide {
  position: absolute; top: 15%; left: 25%; width: 50%; height: 70%;
  border: 2px dashed rgba(255, 255, 255, 0.3); border-radius: 50%;
}
.scan-line {
  position: absolute; top: 0; left: 0; width: 100%; height: 2px;
  background: #818cf8; animation: scan 2s infinite linear;
  box-shadow: 0 0 10px #818cf8;
}
.camera-placeholder { text-align: center; color: #475569; }
.placeholder-icon { font-size: 40px; margin-bottom: 10px; opacity: 0.5; }
.status-badge {
  position: absolute; top: 12px; right: 12px; padding: 4px 10px; border-radius: 99px;
  font-size: 11px; font-weight: 700; background: rgba(0, 0, 0, 0.6); backdrop-filter: blur(4px);
}
.status-badge.success { color: #10b981; border: 1px solid #10b981; }
.status-badge.fail { color: #ef4444; border: 1px solid #ef4444; }
.status-badge.idle { color: #94a3b8; border: 1px solid #94a3b8; }

/* Audio Grid */
.audio-check-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 20px;
}
.check-card {
  background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 16px; padding: 20px; display: flex; flex-direction: column; gap: 16px;
  transition: all 0.3s;
}
.check-card.passed { background: rgba(16, 185, 129, 0.05); border-color: rgba(16, 185, 129, 0.2); }
.card-head { display: flex; align-items: center; gap: 8px; }
.card-head h4 { margin: 0; font-size: 15px; font-weight: 700; color: #fff; }
.card-desc { font-size: 13px; color: #94a3b8; margin: 0; }

.meter-container { display: flex; flex-direction: column; gap: 8px; margin-bottom: auto; }
.meter-bar { height: 6px; background: #334155; border-radius: 99px; position: relative; overflow: hidden; }
.meter-fill { height: 100%; background: linear-gradient(to right, #818cf8, #10b981); width: 0%; transition: width 0.1s; }
.threshold-line { position: absolute; top: 0; bottom: 0; width: 2px; background: #ef4444; opacity: 0.7; }
.meter-labels { display: flex; justify-content: space-between; font-size: 11px; color: #64748b; }

.test-btn {
  padding: 10px; border-radius: 8px; border: none; background: #334155; color: #fff;
  font-weight: 600; font-size: 13px; cursor: pointer; transition: 0.2s; width: 100%;
}
.test-btn.outline { background: transparent; border: 1px solid #334155; margin-bottom: 8px; }
.test-btn:hover:not(:disabled) { background: #475569; }
.test-btn:disabled { opacity: 0.6; cursor: not-allowed; }

/* Final Check */
.success-icon { font-size: 60px; margin-bottom: 20px; }
.final-checklist {
  margin: 0 auto; display: flex; flex-direction: column; gap: 12px;
  background: rgba(255, 255, 255, 0.03); padding: 24px; border-radius: 12px; width: 100%; max-width: 320px;
}
.check-item { display: flex; gap: 10px; align-items: center; color: #cbd5e1; font-weight: 500; font-size: 15px; }
.check { color: #10b981; font-weight: 800; }

/* Footer Buttons */
.panel-footer {
  margin-top: 24px; padding-top: 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  display: flex; justify-content: flex-end; gap: 10px; flex-shrink: 0;
}
.panel-footer.center { justify-content: center; }

.primary-btn {
  background: #818cf8; color: #fff; padding: 10px 24px; border-radius: 8px; border: none;
  font-weight: 700; font-size: 14px; cursor: pointer; transition: all 0.2s;
  display: flex; align-items: center; gap: 8px;
}
.primary-btn:hover:not(:disabled) { background: #6366f1; transform: translateY(-2px); }
.primary-btn:disabled { background: #475569; cursor: not-allowed; color: #94a3b8; }
.primary-btn.large { padding: 14px 40px; font-size: 16px; }
.primary-btn.full-width { width: 100%; justify-content: center; }

.secondary-btn {
  background: transparent; color: #94a3b8; padding: 10px 20px; border: 1px solid #334155; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 14px;
}
.secondary-btn:hover { color: #fff; border-color: #64748b; }
.action-btn {
  background: #334155; color: #fff; padding: 10px 20px; border-radius: 8px; border: none; font-weight: 600; cursor: pointer; font-size: 14px;
}

.arrow-icon { width: 18px; height: 18px; }
.hidden-canvas { display: none; }

@keyframes scan { 0% { top: 0; } 100% { top: 100%; } }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

/* Mobile */
@media (max-width: 900px) {
  .setting-card { grid-template-columns: 1fr; height: auto; max-height: none; min-height: auto; }
  .step-sidebar { flex-direction: row; align-items: center; justify-content: space-between; padding: 16px; }
  .step-list { display: none; }
  .step-content { padding: 24px; }
  .audio-check-grid { grid-template-columns: 1fr; }
  .camera-frame { min-height: 240px; }
}
</style>
