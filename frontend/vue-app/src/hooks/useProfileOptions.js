import { ref } from "vue";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

// 서버가 준비되지 않았을 때도 화면이 비어 보이지 않도록 기본값 제공

const options = ref(null);
const loading = ref(false);
const error = ref("");

let inflight = null;

const fetchProfileOptions = async () => {
  if (options.value) return options.value;
  if (inflight) return inflight;

  loading.value = true;
  error.value = "";

  inflight = fetch(`${API_BASE}/api/user/profile/options/`)
    .then(async (res) => {
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data?.detail || "프로필 선택지 불러오기에 실패했습니다.");
      }
      options.value = data;
      return data;
    })
    .catch((err) => {
      error.value = err?.message || "프로필 선택지 불러오기에 실패했습니다.";
      // 서버가 준비 안 됐을 때는 기본값으로라도 채워 UX 유지
      options.value = defaultOptions;
      return defaultOptions;
    })
    .finally(() => {
      loading.value = false;
      inflight = null;
    });

  return inflight;
};

export function useProfileOptions() {
  return {
    options,
    loading,
    error,
    fetchProfileOptions,
  };
}
