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
            <span v-if="item.id === 3 && micPassed" class="pass-badge">통과</span>
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
            아래 영역에 본인 얼굴이 잘 보이는지 확인해 주세요. 일정 밝기 이상이 감지되면 자동으로 통과 처리됩니다.
          </p>

          <div class="preview-box">
            <video
              ref="videoRef"
              autoplay
              playsinline
              class="video-preview"
              v-show="cameraActive"
            ></video>
            <div v-show="!cameraActive" class="preview-placeholder">
              <span class="placeholder-icon">📷</span>
              <span class="placeholder-text">웹캠이 아직 활성화되지 않았습니다.</span>
            </div>
          </div>

          <p class="help-text">
            상태:
            <strong>
              {{ cameraPassed ? "웹캠 통과 ✅" : (cameraChecking ? "밝기 측정 중..." : "테스트 필요 ❗") }}
            </strong>
          </p>

          <canvas ref="canvasRef" class="hidden-canvas"></canvas>

          <div class="panel-footer">
            <button class="secondary-btn" @click="goPrev">이전</button>
            <button class="secondary-btn" @click="stopCamera" v-if="cameraActive">
              웹캠 종료
            </button>
            <button class="primary-btn" @click="startCameraTest">
              {{ cameraActive ? "다시 테스트" : "웹캠 테스트 시작" }}
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

        <!-- 3. 마이크 연결 -->
        <div v-else-if="currentStep === 3" class="step-panel">
          <h3 class="step-title">마이크 연결</h3>
          <p class="step-desc">
            아래 버튼을 눌러 마이크/스피커 테스트를 진행해 주세요. 몇 초 동안 말하면 자동으로 통과 여부를 판단합니다.
          </p>

          <div class="audio-test-box">
            <label class="audio-label">마이크 입력 레벨</label>
            <div class="audio-bar-wrapper">
              <div class="audio-bar-bg">
                <div
                  class="audio-bar-fill"
                  :style="{ width: micLevel + '%' }"
                ></div>
              </div>
              <span class="audio-level-text">{{ micLevel }}%</span>
            </div>
          </div>

          <p class="help-text">
            상태:
            <strong>
              {{
                micPassed
                  ? "마이크 통과 ✅"
                  : micChecking
                  ? "음성 분석 중... 말을 해보세요 🎤"
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
              :disabled="!micPassed"
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
              :disabled="!cameraPassed || !micPassed"
              @click="startTest"
            >
              시작
            </button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onBeforeUnmount } from "vue";
import { useRouter } from "vue-router";
import { nextTick } from "vue";

const router = useRouter();

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
  if (currentStep.value < 4) currentStep.value += 1;
};

const goPrev = () => {
  if (currentStep.value > 1) currentStep.value -= 1;
};

/* ----- 웹캠 체크 ----- */
const videoRef = ref(null);
const canvasRef = ref(null);
const cameraActive = ref(false);
const cameraPassed = ref(false);
const cameraChecking = ref(false);
let cameraStream = null;

const startCameraTest = async () => {
  cameraPassed.value = false;
  cameraChecking.value = true;

  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: true });

    // video DOM 표시하도록 상태 변경
    cameraActive.value = true;

    // DOM이 실제로 만들어질 때까지 기다림
    await nextTick();

    // 이제 videoRef가 null이 아님
    if (videoRef.value) {
      videoRef.value.srcObject = cameraStream;
    }

    // 밝기 체크 시작
    setTimeout(() => {
      checkCameraBrightness();
    }, 1000);
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
      // 간단한 밝기 값 (gray = (r+g+b)/3)
      total += (data[i] + data[i + 1] + data[i + 2]) / 3;
    }
    const avgBrightness = total / (width * height);

    // 임계값 약 30 이상이면 "어두운 화면이 아니다"라고 보고 통과
    cameraPassed.value = avgBrightness > 30;
  } catch (e) {
    cameraPassed.value = false;
  } finally {
    cameraChecking.value = false;
  }
};

const stopCamera = () => {
  if (cameraStream) {
    cameraStream.getTracks().forEach((t) => t.stop());
    cameraStream = null;
  }
  cameraActive.value = false;
};

/* ----- 마이크 체크 ----- */
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

  // 이전 것들 정리
  stopMic();

  try {
    micStream = await navigator.mediaDevices.getUserMedia({ audio: true });

    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioCtx.createMediaStreamSource(micStream);
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 2048;

    source.connect(analyser);

    const dataArray = new Uint8Array(analyser.fftSize);

    let sumRms = 0;      // 모든 프레임의 rms 합
    let frameCount = 0;  // 측정한 프레임 수
    let maxVolume = 0;   // (옵션) 최고 볼륨 – 참고용

    const AVG_RMS_THRESHOLD = 20; // ✅ 5초 평균 rms 기준 (말하기 톤 정도)

    const updateLevel = () => {
      if (!analyser) return;
      analyser.getByteTimeDomainData(dataArray);

      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) {
        const v = dataArray[i] - 128;
        sum += v * v;
      }
      const rms = Math.sqrt(sum / dataArray.length); // 0~약 90

      // 평균 계산용 누적
      sumRms += rms;
      frameCount += 1;
      maxVolume = Math.max(maxVolume, rms);

      // UI용 레벨 (0~100)
      micLevel.value = Math.min(100, Math.round((rms / 60) * 100));

      micAnimationId = requestAnimationFrame(updateLevel);
    };

    updateLevel();

    // 🔴 5초 동안 측정 후 평균값으로 통과 여부 결정
    micCheckTimeout = setTimeout(() => {
      micChecking.value = false;

      const avgRms = frameCount > 0 ? sumRms / frameCount : 0;
      console.log("avgRms:", avgRms, "maxVolume:", maxVolume);

      // ✅ 5초 동안의 평균 말하기 크기가 기준 이상일 때 통과
      micPassed.value = avgRms > AVG_RMS_THRESHOLD;

      stopMic(false); // 스트림은 끊되 마지막 레벨은 그대로 남김
    }, 5000); // 5000ms = 5초
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

/* ----- 마지막: 테스트 시작 ----- */
const startTest = () => {
  router.push("/coding-test/session");
};

/* ----- 컴포넌트 언마운트 시 정리 ----- */
onBeforeUnmount(() => {
  stopCamera();
  stopMic();
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
  flex: 1;
  border-radius: 10px;
  border: 1px dashed #9ca3af;
  background: #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
}

.video-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 9px;
}

.preview-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #6b7280;
}

.placeholder-icon {
  font-size: 32px;
}

.placeholder-text {
  font-size: 13px;
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
}

.audio-bar-fill {
  height: 100%;
  border-radius: 999px;
  background: #10b981;
  transition: width 0.12s ease-out;
}

.audio-level-text {
  font-size: 12px;
  color: #4b5563;
}

/* 공통 */
.help-text {
  margin-top: 10px;
  font-size: 13px;
  color: #4b5563;
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
