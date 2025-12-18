<template>
  <transition name="slide-down">
    <div
      v-if="visible"
      class="anti-cheat-alert"
      :class="[`level-${level}`, state !== 'idle' ? 'is-active' : '']"
    >
      <div class="alert-left">
        <span class="pulse" :class="`tone-${level}`"></span>
        <div class="text-block">
          <p class="alert-label">{{ resolvedTitle }}</p>
          <p class="alert-message">{{ description }}</p>
        </div>
      </div>
      <div class="alert-right">
        <span v-if="formattedTime" class="alert-time">{{ formattedTime }}</span>
        <button v-if="closable" type="button" class="alert-close" @click="$emit('dismiss')">
          확인
        </button>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  visible: { type: Boolean, default: false },
  state: { type: String, default: "idle" },
  title: { type: String, default: "모니터링 알림" },
  description: { type: String, default: "" },
  level: { type: String, default: "info" },
  timestamp: { type: [Number, Date, String], default: null },
  closable: { type: Boolean, default: true }
});

defineEmits(["dismiss"]);

const resolvedTitle = computed(() => props.title || props.state || "모니터링 알림");

const formattedTime = computed(() => {
  if (!props.timestamp) return "";
  const date = props.timestamp instanceof Date ? props.timestamp : new Date(props.timestamp);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleTimeString("ko-KR", { hour12: false });
});
</script>

<style scoped>
.anti-cheat-alert {
  position: sticky;
  top: 0;
  z-index: 30;
  padding: 12px 16px;
  border-radius: 12px;
  border: 1px solid #1f2937;
  background: linear-gradient(90deg, #0f172a 0%, #0b1222 100%);
  color: #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.4);
}

.is-active {
  box-shadow: 0 12px 32px rgba(59, 130, 246, 0.15);
}

.level-warning {
  border-color: #f59e0b;
  box-shadow: 0 12px 32px rgba(245, 158, 11, 0.15);
}

.level-critical {
  border-color: #f87171;
  box-shadow: 0 12px 32px rgba(248, 113, 113, 0.18);
  background: linear-gradient(90deg, #0f172a 0%, #1c0f0f 100%);
}

.alert-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.pulse {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #38bdf8;
  box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.3);
  animation: pulse 1.6s infinite;
  flex-shrink: 0;
}

.tone-warning {
  background: #fbbf24;
  box-shadow: 0 0 0 0 rgba(251, 191, 36, 0.3);
}

.tone-critical {
  background: #f43f5e;
  box-shadow: 0 0 0 0 rgba(244, 63, 94, 0.25);
}

.text-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.alert-label {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: #f8fafc;
  letter-spacing: 0.2px;
}

.alert-message {
  margin: 0;
  font-size: 12px;
  color: #cbd5e1;
  line-height: 1.5;
  word-break: keep-all;
}

.alert-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.alert-time {
  font-size: 11px;
  color: #94a3b8;
}

.alert-close {
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(56, 189, 248, 0.14);
  color: #e0f2fe;
  border: 1px solid rgba(56, 189, 248, 0.4);
  cursor: pointer;
  font-size: 12px;
  font-weight: 700;
}

.alert-close:hover {
  background: rgba(56, 189, 248, 0.2);
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.2s ease;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 currentColor;
  }
  70% {
    box-shadow: 0 0 0 10px transparent;
  }
  100% {
    box-shadow: 0 0 0 0 transparent;
  }
}

@media (max-width: 720px) {
  .anti-cheat-alert {
    align-items: flex-start;
    flex-direction: column;
    gap: 8px;
  }

  .alert-right {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
