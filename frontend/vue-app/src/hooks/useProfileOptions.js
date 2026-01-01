import { ref } from "vue";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

// 서버가 준비되지 않았을 때도 화면이 비어 보이지 않도록 기본값 제공
const defaultOptions = {
  graduated_school: ["고졸", "전문대졸(2,3년제)", "대졸(4년제 이상)", "석사 이상", "박사 이상"],
  major: ["전공", "비전공"],
  academic_status: ["재학", "휴학", "졸업", "중퇴"],
  career_level: ["junior (0~3년차)", "mid (4~7년차)", "senior (8~10년차)", "lead (10년차~)"],
  current_status: ["재직중", "퇴사", "구직중", "프리랜서", "기타"],
  tech_stack: [
    "Python",
    "NumPy",
    "Pandas",
    "SciPy",
    "Scikit-learn",
    "XGBoost",
    "LightGBM",
    "CatBoost",
    "TensorFlow",
    "Keras",
    "PyTorch",
    "Transformers",
    "LangChain",
    "LangGraph",
    "OpenAI API",
    "HuggingFace Hub",
    "SentenceTransformers",
    "spaCy",
    "NLTK",
    "MLflow",
    "Airflow",
    "DVC",
    "Optuna",
    "Jupyter Notebook",
    "JupyterLab",
  ],
  desired_role: [
    "AI/ML 엔지니어",
    "데이터 사이언티스트",
    "LLM 엔지니어",
    "컴퓨터비전 엔지니어",
    "자연어처리 엔지니어",
    "음성인식 엔지니어",
    "MLOps 엔지니어",
    "데이터 엔지니어",
    "AI 서비스 개발자",
  ],
  detailed_role: [
    "딥러닝 모델링",
    "지도/비지도 학습",
    "강화학습",
    "추천 시스템",
    "시계열 예측",
    "자연어 처리",
    "텍스트 분류/분석",
    "텍스트 생성/요약",
    "프롬프트 엔지니어링",
    "LLM 파인튜닝/서빙",
    "컴퓨터 비전",
    "이미지 분류/탐지",
    "OCR/문서 인식",
    "음성 인식/TTS",
    "MLOps/파이프라인",
    "모델 서빙/배포",
    "데이터 파이프라인",
    "AI 보안/안전",
  ],
  region: ["서울", "인천", "부산", "대구", "대전", "세종", "울산", "광주"],
};

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
