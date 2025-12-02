import { computed, ref } from "vue";

export const ANTI_CHEAT_STATES = {
  idle: {
    title: "모니터링 중",
    message: "부정행위가 감지되면 알림이 표시됩니다.",
    level: "info"
  },
  tabSwitch: {
    title: "다른 화면 전환 감지",
    message: "시험 화면을 벗어났습니다. 지속될 경우 실격 처리될 수 있습니다.",
    level: "warning"
  },
  windowBlur: {
    title: "창 이탈 감지",
    message: "테스트 창이 백그라운드로 전환되었습니다.",
    level: "warning"
  },
  pasteDetected: {
    title: "외부 붙여넣기 감지",
    message: "코드 편집기에 외부 텍스트를 붙여넣는 행동이 감지되었습니다.",
    level: "warning"
  },
  cameraBlocked: {
    title: "카메라 비활성화",
    message: "웹캠 모니터링이 꺼졌거나 가려졌습니다.",
    level: "critical"
  },
  copyDetected: {
    title: "복사 동작 감지",
    message: "코드 편집기에서 복사 동작이 감지되었습니다.",
    level: "warning"
  },
  abnormalInput: {
    title: "비정상 입력 패턴 감지",
    message: "비정상적으로 빠른 입력 패턴이 감지되었습니다.",
    level: "warning"
  },
  networkDrop: {
    title: "네트워크 불안정",
    message: "모니터링 연결이 일시적으로 불안정합니다.",
    level: "info"
  },
  unknown: {
    title: "감지 알림",
    message: "확인되지 않은 행동이 감지되었습니다.",
    level: "warning"
  }
};

export function useAntiCheatStatus() {
  const state = ref("idle");
  const detail = ref("");
  const lastUpdated = ref(null);

  const alert = computed(() => {
    const fallback = ANTI_CHEAT_STATES.unknown;
    const cfg = ANTI_CHEAT_STATES[state.value] || fallback;

    return {
      ...cfg,
      state: state.value,
      description: detail.value || cfg.message,
      visible: state.value !== "idle",
      timestamp: lastUpdated.value
    };
  });

  const setState = (nextState, options = {}) => {
    state.value = ANTI_CHEAT_STATES[nextState] ? nextState : "unknown";
    detail.value = options.detail || "";
    lastUpdated.value = options.timestamp || Date.now();
  };

  const resetState = () => {
    state.value = "idle";
    detail.value = "";
    lastUpdated.value = null;
  };

  return {
    state,
    alert,
    setState,
    resetState
  };
}
