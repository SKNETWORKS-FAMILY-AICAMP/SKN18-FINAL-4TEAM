<template>
  <div v-if="visible" class="forced-alert">
    <div
      class="forced-card"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="forced-exit-title"
      aria-describedby="forced-exit-message"
    >
      <div id="forced-exit-title" class="forced-title">{{ title }}</div>
      <p id="forced-exit-message" class="forced-message">{{ message }}</p>
      <button
        ref="closeButton"
        type="button"
        class="forced-close"
        aria-label="알림 닫기"
        @click="emitClose"
      >
        ✕
      </button>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from "vue";

const emit = defineEmits(["close"]);

defineProps({
  visible: { type: Boolean, default: false },
  title: {
    type: String,
    default: "부정행위 의심 행동으로 세션이 종료되었습니다."
  },
  message: {
    type: String,
    default:
      "시험 화면 이탈이 5회 누적되어 라이브 코딩 세션이 종료되었습니다. 다시 시작하려면 라이브 코딩 페이지로 이동해 주세요."
  }
});

const closeButton = ref(null);

const emitClose = () => emit("close");

const handleKeydown = (event) => {
  if (event.key === "Escape") {
    emitClose();
  }
};

onMounted(() => {
  document.addEventListener("keydown", handleKeydown);
  nextTick(() => {
    if (closeButton.value) {
      closeButton.value.focus();
    }
  });
});

onBeforeUnmount(() => {
  document.removeEventListener("keydown", handleKeydown);
});
</script>

<style scoped>
.forced-alert {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.35);
  z-index: 1200;
  padding: 24px;
}

.forced-card {
  position: relative;
  max-width: 520px;
  width: 100%;
  background: #0f172a;
  color: #f8fafc;
  border: 1px solid #334155;
  border-radius: 16px;
  padding: 24px 20px 20px;
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.4);
}

.forced-title {
  font-size: 18px;
  font-weight: 800;
  margin: 0 0 8px;
}

.forced-message {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: #cbd5e1;
}

.forced-close {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid #475569;
  background: #0b1220;
  color: #e2e8f0;
  cursor: pointer;
  font-size: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.forced-close:hover {
  background: #111827;
}
</style>
