<template>
  <div class="landing">
    <header class="landing-header">
      <div class="nav-dropdown">
        <button
          class="nav-pill"
          @click="isMenuOpen = !isMenuOpen"
          aria-haspopup="true"
          :aria-expanded="isMenuOpen"
        >
          <span>MENU</span>
          <span class="chevron" :class="{ rotate: isMenuOpen }">&#9662;</span>
        </button>
        
        <Transition name="dropdown">
          <div class="dropdown-menu" v-show="isMenuOpen">
            <RouterLink to="/aboutus" class="dropdown-link dropdown-link--menu" @click="isMenuOpen = false">
              ABOUT US
            </RouterLink>
            <RouterLink to="/coding-test" class="dropdown-link dropdown-link--menu" @click="isMenuOpen = false">
              LIVE CODING
            </RouterLink>
          </div>
        </Transition>
      </div>

      <h1 class="nav-logo">JOBTORY</h1>

      <div class="nav-dropdown">
        <button
          class="nav-pill"
          @click="isDropdownOpen = !isDropdownOpen"
          aria-haspopup="true"
          :aria-expanded="isDropdownOpen"
        >
          <span>{{ isAuthenticated ? userName : "Dropdown" }}</span>
          <span class="chevron" :class="{ rotate: isDropdownOpen }">&#9662;</span>
        </button>
        
        <Transition name="dropdown">
          <div class="dropdown-menu right-align" v-show="isDropdownOpen">
            <template v-if="isAuthenticated">
              <RouterLink :to="{ name: 'mypage' }" class="dropdown-link" @click="closeDropdown">
                MYPAGE
              </RouterLink>
              <button
                type="button"
                class="dropdown-link dropdown-button"
                :class="{ 'dropdown-button--loading': isLoggingOut }"
                :disabled="isLoggingOut"
                @click="handleLogout"
              >
                <span v-if="isLoggingOut" class="spinner" aria-hidden="true"></span>
                <span>{{ isLoggingOut ? "LOGOUT" : "LOGOUT" }}</span>
              </button>
            </template>
            <template v-else>
              <RouterLink :to="{ name: 'login' }" class="dropdown-link" @click="closeDropdown">
                LOGIN
              </RouterLink>
              <RouterLink :to="{ name: 'signup-choice' }" class="dropdown-link" @click="closeDropdown">
                SIGN-IN
              </RouterLink>
            </template>
          </div>
        </Transition>
      </div>
    </header>

    <section class="hero">
      <div class="hero-bg-grid"></div>

      <div class="hero-inner">
        <div class="hero-text">
          <h2 class="hero-title">
            Build confidence through
            <br />
            every live challenge.
          </h2>
          <p class="hero-description">
            실시간 라이브 코딩과 행동 기반 인터뷰로
            <br />
            개발자의 문제 해결력과 커뮤니케이션을 있는 그대로 평가하세요.
          </p>
          <div class="hero-actions">
            <RouterLink to="/coding-test" class="secondary hover-scale">라이브 코딩 테스트 보기</RouterLink>
            <button
              v-if="isAuthenticated"
              type="button"
              class="primary hover-scale"
              @click="openProfileModal"
            >
              프로필 입력/수정
            </button>
          </div>
        </div>

        <div class="hero-image-wrap">
          <img :src="heroImage" alt="Live coding interface" class="hero-image floating-anim" />
        </div>
      </div>
    </section>

    <section class="insights">
      <div class="insights-header">
        <h3 class="insights-title">
          Real-time coding.
          <br />
          Real insights.
        </h3>
        <p class="insights-description">
          실시간 코딩 인터뷰를 통해 문제 해결 과정과 커뮤니케이션을
          <br />
          함께 평가하고, 지원자의 잠재력을 깊이 있게 이해할 수 있습니다.
        </p>
      </div>

      <div class="insights-cards">
        <div 
          class="insight-card card-one spotlight-card"
          @mousemove="handleMouseMove"
        >
          <div class="spotlight-overlay"></div>
          <div class="card-content">
            <div class="card-text-group">
              <h4 class="card-heading">라이브 코드 실행</h4>
              <p class="card-copy">
                코드를 작성하고 바로 실행하며<br />
                사고 과정을 투명하게 보여줍니다.
              </p>
            </div>
            <div class="card-image-wrap">
              <img :src="heroImage2" alt="Live coding interface" class="card-image-content" />
            </div>
          </div>
        </div>

        <div 
          class="insight-card card-two spotlight-card"
          @mousemove="handleMouseMove"
        >
          <div class="spotlight-overlay"></div>
          <div class="card-content">
            <div class="card-text-group">
              <h4 class="card-heading">협업형 인터뷰</h4>
              <p class="card-copy">
                실시간 채팅으로 문제 해결 과정과<br />
                커뮤니케이션을 함께 확인합니다.
              </p>
            </div>
            <div class="card-image-wrap">
              <img :src="heroImage3" alt="Live coding interface" class="card-image-content" />
            </div>
          </div>
        </div>

        <div 
          class="insight-card card-three spotlight-card"
          @mousemove="handleMouseMove"
        >
          <div class="spotlight-overlay"></div>
          <div class="card-content">
            <div class="card-text-group">
              <h4 class="card-heading">정량 + 정성 리포트</h4>
              <p class="card-copy">
                결과와 행동 기록을 모두 남겨<br />
                채용 의사결정을 뒷받침합니다.
              </p>
            </div>
            <div class="card-image-wrap">
              <img :src="heroImage4" alt="Live coding interface" class="card-image-content" />
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="footer-marquee">
      <div class="marquee-track">
        <div class="marquee-content">
          <span>CONTACT US • JOBTORY@GMAIL.COM • JOBTORY • RECRUITMENT • INTERVIEW • </span>
          <span>CONTACT US • JOBTORY@GMAIL.COM • JOBTORY • RECRUITMENT • INTERVIEW • </span>
        </div>
        <div class="marquee-content">
          <span>CONTACT US • JOBTORY@GMAIL.COM • JOBTORY • RECRUITMENT • INTERVIEW • </span>
          <span>CONTACT US • JOBTORY@GMAIL.COM • JOBTORY • RECRUITMENT • INTERVIEW • </span>
        </div>
      </div>
      
      <div class="footer-center">
        <a href="mailto:jobtory@gmail.com" class="footer-logo-link">JOBTORY</a>
      </div>
    </section>

    <ForcedExitAlert
      :visible="showForcedExit"
      @close="showForcedExit = false"
    />

    <!-- 프로필 입력 모달 -->
    <div v-if="showProfileModal" class="modal-overlay" @click.self="closeProfileModal">
      <div class="modal-card profile-card">
        <div class="modal-header">
          <h3>프로필 입력</h3>
          <button type="button" class="modal-close" @click="closeProfileModal">✕</button>
        </div>
        <div class="modal-body profile-body">
          <template v-if="currentProfileStep === 1">
            <label class="modal-field">
              <span>최종 학력 *</span>
              <select v-model="profileForm.graduated_school">
                <option value="">선택</option>
                <option v-for="opt in graduatedOptions" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </label>
            <label class="modal-field">
              <span>학교명</span>
              <input v-model="profileForm.university" type="text" placeholder="학교명" />
            </label>
            <label class="modal-field">
              <span>전공 여부</span>
              <select v-model="profileForm.major">
                <option value="">선택</option>
                <option value="전공">전공</option>
                <option value="비전공">비전공</option>
              </select>
            </label>
            <label class="modal-field">
              <span>재학 상태</span>
              <select v-model="profileForm.academic_status">
                <option value="">선택</option>
                <option v-for="opt in academicOptions" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </label>
            <label class="modal-field">
              <span>졸업(예정) 연도</span>
              <input v-model="profileForm.graduation_year" type="number" min="1900" max="2100" />
            </label>
          </template>

          <template v-else>
            <label class="modal-field">
              <span>경력 레벨 *</span>
              <select v-model="profileForm.career_level">
                <option value="">선택</option>
                <option v-for="opt in careerOptions" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </label>
            <label class="modal-field">
              <span>현재 상태</span>
              <select v-model="profileForm.current_status">
                <option value="">선택</option>
                <option v-for="opt in statusOptions" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </label>
            <label class="modal-field">
              <span>기술 스택</span>
              <div class="checkbox-group">
                <label
                  v-for="opt in techStackOptions"
                  :key="opt"
                  class="checkbox-item"
                >
                <input
                  type="checkbox"
                  :value="opt"
                  v-model="profileForm.tech_stack"
                />
                <span>{{ opt }}</span>
              </label>
            </div>
          </label>

            <label class="modal-field">
              <span>희망 직무</span>
              <div class="checkbox-group">
                <label
                  v-for="opt in desiredRoleOptions"
                  :key="opt"
                  class="checkbox-item"
                >
                  <input
                    type="checkbox"
                    :value="opt"
                    v-model="profileForm.desired_role"
                  />
                  <span>{{ opt }}</span>
                </label>
              </div>
            </label>

            <label class="modal-field">
              <span>세부 희망 직무</span>
              <div class="checkbox-group">
                <label
                  v-for="opt in detailedRoleOptions"
                  :key="opt"
                  class="checkbox-item"
                >
                  <input
                    type="checkbox"
                    :value="opt"
                    v-model="profileForm.detailed_role"
                  />
                  <span>{{ opt }}</span>
                </label>
              </div>
            </label>

            <label class="modal-field">
              <span>희망 근무지</span>
              <select v-model="profileForm.region">
                <option value="">선택</option>
                <option v-for="opt in regionOptions" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </label>
          </template>
        </div>
        <div class="modal-footer">
          <div class="modal-steps">
            <span :class="{ active: currentProfileStep === 1 }">1</span>
            <span :class="{ active: currentProfileStep === 2 }">2</span>
          </div>
          <div class="modal-actions">
            <button v-if="currentProfileStep === 2" type="button" class="pill-button ghost" @click="currentProfileStep = 1">
              이전
            </button>
            <button
              v-if="currentProfileStep === 1"
              type="button"
              class="pill-button"
              @click="currentProfileStep = 2"
            >
              다음
            </button>
            <button
              v-else
              class="pill-button"
              :disabled="savingProfile"
              @click="saveProfile"
            >
              {{ savingProfile ? "저장 중..." : "저장" }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import { useAuth } from "../hooks/useAuth";
import ForcedExitAlert from "../components/ForcedExitAlert.vue";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

const route = useRoute();
const router = useRouter();
const { isAuthenticated, user, fetchProfile, logout, token } = useAuth();
const isMenuOpen = ref(false);
const isDropdownOpen = ref(false);
const isLoggingOut = ref(false);
const showForcedExit = ref(false);
const showProfileModal = ref(false);
const currentProfileStep = ref(1);
const savingProfile = ref(false);
const profileForm = reactive({
  graduated_school: "",
  university: "",
  major: "",
  academic_status: "",
  graduation_year: "",
  career_level: "",
  current_status: "",
  tech_stack: [],
  desired_role: [],
  detailed_role: [],
  region: [],
  region_single: ""
});

const graduatedOptions = ["고졸", "전문대졸(2,3년제)", "대졸(4년제 이상)", "석사 이상", "박사 이상"];
const academicOptions = ["재학", "휴학", "졸업", "중퇴"];
const careerOptions = ["junior (0~3년차)", "mid (4~7년차)", "senior (8~10년차)", "lead (10년차~)"];
const statusOptions = ["재직중", "퇴사", "구직중", "프리랜서", "기타"];
const techStackOptions = [
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
  "JupyterLab"
];
const desiredRoleOptions = [
  "AI/ML 엔지니어",
  "데이터 사이언티스트",
  "LLM 엔지니어",
  "컴퓨터비전 엔지니어",
  "자연어처리 엔지니어",
  "음성인식 엔지니어",
  "MLOps 엔지니어",
  "데이터 엔지니어",
  "AI 서비스 개발자"
];
const detailedRoleOptions = [
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
  "AI 보안/안전"
];
const regionOptions = ["서울", "인천", "부산", "대구", "대전", "세종", "울산", "광주"];

const toggleMultiSelect = (field, value) => {
  const current = Array.isArray(profileForm[field]) ? profileForm[field] : [];
  profileForm[field] = current.includes(value)
    ? current.filter((item) => item !== value)
    : [...current, value];
};

const userName = computed(() => user.value?.name || "회원");

const handleMouseMove = (e) => {
  const card = e.currentTarget;
  const rect = card.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;
  
  card.style.setProperty("--mouse-x", `${x}px`);
  card.style.setProperty("--mouse-y", `${y}px`);
};

const closeDropdown = () => {
  isDropdownOpen.value = false;
};

const handleLogout = async () => {
  if (isLoggingOut.value) return;
  isLoggingOut.value = true;
  setTimeout(async () => {
    await logout();
    isLoggingOut.value = false;
    closeDropdown();
    void router.push({ name: "home" });
  }, 360);
};

const syncProfile = () => {
  if (isAuthenticated.value && !user.value) {
    void fetchProfile();
  }
};

const needProfileModal = (profile) => {
  // 간단한 기준: 학력/경력 레벨이 비어 있으면 추가 입력 안내
  return !profile?.graduated_school || !profile?.career_level;
};

const loadProfile = async () => {
  if (!isAuthenticated.value) return;
  try {
    const res = await fetch(`${API_BASE}/api/user/profile/detail/`, {
      headers: token.value ? { Authorization: `Bearer ${token.value}` } : {},
    });
    if (!res.ok) throw new Error("프로필 조회 실패");
    const data = await res.json();
    Object.assign(profileForm, {
      graduated_school: data.graduated_school || "",
      university: data.university || "",
      major: data.major || "",
      academic_status: data.academic_status || "",
      graduation_year: data.graduation_year || "",
      career_level: data.career_level || "",
      current_status: data.current_status || "",
      tech_stack: data.tech_stack || [],
      desired_role: data.desired_role || [],
      detailed_role: data.detailed_role || [],
      region: data.region || [],
      region_single: (data.region && data.region[0]) || ""
    });
    if (needProfileModal(data)) {
      showProfileModal.value = true;
    }
  } catch (err) {
    // 조회 실패 시 새 입력을 안내
    showProfileModal.value = true;
  }
};

const saveProfile = async () => {
  savingProfile.value = true;
  try {
    const res = await fetch(`${API_BASE}/api/user/profile/detail/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token.value ? { Authorization: `Bearer ${token.value}` } : {}),
      },
      body: JSON.stringify({
        ...profileForm,
        region: profileForm.region_single ? [profileForm.region_single] : []
      }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      const detail = data?.detail || "프로필 저장에 실패했습니다.";
      throw new Error(detail);
    }
    showProfileModal.value = false;
  } catch (err) {
    window.alert(err.message || "프로필 저장 중 오류가 발생했습니다.");
  } finally {
    savingProfile.value = false;
  }
};

const openProfileModal = () => {
  showProfileModal.value = true;
  currentProfileStep.value = 1;
};

const closeProfileModal = () => {
  showProfileModal.value = false;
  currentProfileStep.value = 1;
};

const checkForcedAlert = () => {
  if (route.query.alert === "anti-cheat") {
    showForcedExit.value = true;
    const cleanedQuery = { ...route.query };
    delete cleanedQuery.alert;
    router.replace({ name: "home", query: cleanedQuery });
  }
};

onMounted(() => {
  window.addEventListener("storage", syncProfile);
  syncProfile();
  void loadProfile();
  checkForcedAlert();
});

onUnmounted(() => {
  window.removeEventListener("storage", syncProfile);
});

const heroImage = new URL("../assets/mainpage_image1.png", import.meta.url).href;
const heroImage2 = new URL("../assets/mainpage_image2.png", import.meta.url).href;
const heroImage3 = new URL("../assets/mainpage_image3.png", import.meta.url).href;
const heroImage4 = new URL("../assets/mainpage_image4.png", import.meta.url).href;
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap");
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap");
@import url("https://fonts.googleapis.com/css2?family=SF+Pro&display=swap");

.landing {
  min-height: 100vh;
  background: #f8f4eb;
  font-family: "Inter", sans-serif;
  color: #111827;
  overflow-x: hidden;
}

/* Header Styles */
.landing-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 70px 220px;
  border-bottom: 1px solid #e5e7eb;
  position: relative;
  z-index: 100;
}
.nav-logo {
  position: absolute;
  width: 471px;
  height: 245px;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  font-family: "Inter", sans-serif;
  font-style: normal;
  font-weight: 900;
  font-size: 96px;
  line-height: 116px;
  color: #000000;
}
.nav-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 20px 22px;
  border-radius: 999px;
  background: #020617;
  color: #f9fafb;
  border: none;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
}
.nav-pill .chevron { font-size: 12px; }
.chevron.rotate { transform: rotate(180deg); }
.nav-dropdown { position: relative; }

/* ▼▼▼ [변경된 드롭다운 스타일: 검정 배경 + 흰색 텍스트] ▼▼▼ */
.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  min-width: 160px;
  padding: 8px 0;
  
  /* 검정 배경 및 테두리 수정 */
  background: #111827; 
  border: 1px solid #374151;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
  z-index: 100;
}

.dropdown-menu.right-align {
  left: auto; 
  right: 0;
}

.dropdown-link {
  padding: 10px 14px;
  color: #f9fafb; /* 흰색 텍스트 */
  font-size: 16px;
  font-weight: 700; /* 좀 더 굵게 */
  text-decoration: none;
  border-radius: 8px;
  transition: background 0.2s;
}

.dropdown-link:hover {
  background: #374151; /* 호버 시 진한 회색 */
}

.dropdown-button {
  width: 100%;
  text-align: left;
  background: transparent;
  border: none;
  cursor: pointer;
  font: inherit;
  font-size: 16px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #f9fafb; /* 버튼 텍스트도 흰색 */
}

/* 스피너 색상도 흰색으로 변경 */
.dropdown-button--loading .spinner {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid #ffffff; /* 흰색 테두리 */
  border-top-color: transparent;
  animation: spin 0.8s linear infinite;
}
/* ▲▲▲ [변경 완료] ▲▲▲ */

.dropdown-button:disabled { opacity: 0.7; cursor: not-allowed; }

/* Dropdown Animation */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  transform-origin: top center;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-10px) scaleY(0.95);
}
.dropdown-enter-to,
.dropdown-leave-from {
  opacity: 1;
  transform: translateY(0) scaleY(1);
}

/* Hero Section */
.hero {
  position: relative;
  padding: 100px 56px 150px;
  overflow: hidden;
}

/* Grid Background */
.hero-bg-grid {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  z-index: 0;
  background-size: 40px 40px;
  background-image:
    linear-gradient(to right, rgba(0, 0, 0, 0.05) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(0, 0, 0, 0.05) 1px, transparent 1px);
  mask-image: linear-gradient(to bottom, black 60%, transparent 100%);
  pointer-events: none;
}

.hero-inner {
  max-width: 1120px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  align-items: center;
  gap: 48px;
  position: relative;
  z-index: 1;
}
.hero-text {
  text-align: left;
  position: relative;
  z-index: 1;
}
.hero-title {
  max-width: 640px;
  font-family: "Inter", sans-serif;
  font-weight: 700;
  font-size: 64px;
  line-height: 1.30;
  color: #000000;
}
.hero-description {
  max-width: 540px;
  margin: 0 0 32px;
  font-size: 17px;
  color: #4b5563;
}
.hero-actions {
  display: inline-flex;
  justify-content: flex-start;
  gap: 12px;
  flex-wrap: wrap;
}
.secondary {
  border-radius: 999px;
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  text-decoration: none;
  border: 1px solid #d1d5db;
  background: #f9fafb;
  color: #111827;
  transition: all 0.3s ease;
}
.primary {
  border-radius: 999px;
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 700;
  border: none;
  background: #111827;
  color: #f9fafb;
  cursor: pointer;
  transition: all 0.3s ease;
}
.primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 18px rgba(0, 0, 0, 0.22);
}
.hover-scale:hover {
  transform: scale(1.05);
  background: #111827;
  color: #ffffff;
  border-color: #111827;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.hero-image-wrap {
  width: 100%;
  display: flex;
  justify-content: center;
}
.hero-image {
  width: 100%;
  max-width: 620px;
  border-radius: 18px;
  box-shadow: 0 22px 40px rgba(15, 23, 42, 0.4);
  object-fit: cover;
}
.floating-anim {
  animation: float 6s ease-in-out infinite;
}
@keyframes float {
  0% { transform: translateY(0px); }
  50% { transform: translateY(-15px); }
  100% { transform: translateY(0px); }
}

/* Insights Section */
.insights {
  background: #1f252d;
  color: #f9fafb;
  padding: 120px 40px;
}

.insights-header {
  max-width: 900px;
  margin: 0 auto 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 24px;
}

.insights-title {
  margin: 0;
  font-family: "SF Pro", sans-serif;
  font-weight: 900;
  font-size: 72px;
  line-height: 1.1;
  color: #f9fafb;
}

.insights-description {
  margin: 0;
  max-width: 600px;
  font-family: 'SF Pro', sans-serif;
  font-weight: 400;
  font-size: 20px;
  line-height: 1.6;
  color: #cbd5e1;
}

.insights-cards {
  max-width: 1280px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 32px;
  justify-items: center;
}

.insight-card {
  padding: 48px 36px;
  min-height: auto;
  border-radius: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  color: #111827;
  width: 100%;
  max-width: 420px;
  box-shadow: 0 20px 48px rgba(0, 0, 0, 0.24);
  border: 1px solid rgba(255, 255, 255, 0.06);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.card-content {
  position: relative;
  z-index: 2;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 40px;
}

.card-text-group {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card-heading {
  margin: 0;
  font-size: 32px;
  font-weight: 800;
  color: #0f172a;
  line-height: 1.3;
}

.card-copy {
  margin: 0;
  font-size: 18px;
  line-height: 1.6;
  color: #374151;
}

.card-image-wrap {
  margin-top: auto;
  display: flex;
  justify-content: center;
  align-items: flex-end;
  width: 100%;
}

.card-image-content {
  max-width: 100%;
  max-height: 220px;
  object-fit: contain;
  border-radius: 12px;
  transition: transform 0.3s ease;
}

/* Spotlight Effect */
.spotlight-card {
  position: relative;
  overflow: hidden;
  --mouse-x: -500px;
  --mouse-y: -500px;
}
.spotlight-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 30px 60px rgba(0, 0, 0, 0.3);
}
.spotlight-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  pointer-events: none;
  z-index: 1;
  background: radial-gradient(
    600px circle at var(--mouse-x) var(--mouse-y),
    rgba(255, 255, 255, 0.4),
    transparent 40%
  );
  opacity: 0;
  transition: opacity 0.3s;
}
.spotlight-card:hover .spotlight-overlay { opacity: 1; }
.spotlight-card:hover .card-image-content { transform: scale(1.05); }

/* Card Colors */
.card-one { background: #f9c5d5; }
.card-two { background: #f7d56f; }
.card-three { background: #bfacf9; }


/* Footer Marquee Section */
.footer-marquee {
  background: #caa3b1;
  padding: 80px 0;
  overflow: hidden;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.marquee-track {
  display: flex;
  white-space: nowrap;
  position: absolute;
  animation: marquee 30s linear infinite;
}

.marquee-content span {
  font-family: "Inter", sans-serif;
  font-weight: 900;
  font-size: 80px;
  color: rgba(0, 0, 0, 0.1);
  margin-right: 40px;
}

@keyframes marquee {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}

.footer-center {
  position: relative;
  z-index: 10;
  text-align: center;
}

.footer-logo-link {
  font-family: "Inter", sans-serif;
  font-weight: 900;
  font-size: 60px;
  color: #111827;
  text-decoration: none;
  border-bottom: 4px solid #111827;
  transition: all 0.3s;
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(4px);
  padding: 0 20px;
  border-radius: 12px;
}

.footer-logo-link:hover {
  color: #ffffff;
  border-color: #ffffff;
  background: #111827;
}

/* Profile modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-card.profile-card {
  width: min(900px, 92vw);
  max-height: 85vh;
  background: #ffffff;
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.25);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  font-weight: 800;
  font-size: 18px;
}

.modal-close {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
}

.modal-body.profile-body {
  padding: 20px;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 14px 16px;
}

.modal-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 14px;
}

.modal-field input,
.modal-field select {
  border: 1px solid #d1d5db;
  border-radius: 10px;
  padding: 8px 10px;
  font-size: 13px;
}

.modal-field select[multiple] {
  min-height: 120px;
}
.modal-field select[multiple] {
  width: 100%;
}

.modal-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 20px 16px;
  border-top: 1px solid #e5e7eb;
}
.modal-actions {
  display: flex;
  gap: 8px;
}
.modal-steps {
  display: inline-flex;
  gap: 6px;
  align-items: center;
}
.modal-steps span {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 1px solid #d1d5db;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #6b7280;
}
.modal-steps span.active {
  background: #111827;
  color: #f9fafb;
  border-color: #111827;
}
.pill-button.ghost {
  border: 1px solid #d1d5db;
  background: #fff;
  color: #111827;
}
.tag-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 8px;
}
.tag-option {
  border: 1px solid #d1d5db;
  background: #fff;
  padding: 6px 10px;
  border-radius: 12px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
}
.tag-option.active {
  background: #111827;
  color: #f9fafb;
  border-color: #111827;
}
.tag-option:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 14px rgba(0, 0, 0, 0.12);
}

/* Mobile Styles */
@media (max-width: 768px) {
  .landing-header { padding: 16px 20px; }
  .nav-logo { font-size: 24px; position: static; transform: none; width: auto; height: auto; }
  .hero { padding: 56px 20px 100px; }
  .hero-title { font-size: 32px; margin-bottom: 16px; }
  
  .insights-header { 
    gap: 16px; 
    margin-bottom: 40px;
  }
  .insights-title {
    font-size: 48px;
  }
  .insights-cards { grid-template-columns: 1fr; }
  .insight-card {
    max-width: 100%;
    padding: 40px 24px;
  }
  .marquee-content span { font-size: 48px; }
}

/* ===== Profile Modal polish ===== */
.modal-card.profile-card {
  border: 1px solid rgba(0,0,0,0.08);
}

.modal-header {
  background: rgba(248, 244, 235, 0.75);
  backdrop-filter: blur(8px);
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 900;
  letter-spacing: -0.02em;
}

.modal-close {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s ease;
}
.modal-close:hover {
  background: rgba(17, 24, 39, 0.08);
}

/* form grid inside modal */
.modal-body.profile-body {
  background: #ffffff;
}

/* field label */
.modal-field > span {
  font-weight: 800;
  color: #111827;
}

/* inputs */
.modal-field input,
.modal-field select {
  background: #ffffff;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.modal-field input:focus,
.modal-field select:focus {
  outline: none;
  border-color: #111827;
  box-shadow: 0 0 0 4px rgba(17, 24, 39, 0.12);
}

/* checkbox group -> chip style */
.checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 10px;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  background: #f9fafb;
}

.checkbox-item {
  position: relative;
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  user-select: none;
}

/* hide native checkbox */
.checkbox-item input[type="checkbox"] {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

/* chip */
.checkbox-item span {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid #d1d5db;
  background: #ffffff;
  font-size: 13px;
  font-weight: 700;
  color: #111827;
  transition: transform 0.12s ease, background 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.checkbox-item:hover span {
  transform: translateY(-1px);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.10);
}

/* checked style */
.checkbox-item input[type="checkbox"]:checked + span {
  background: #111827;
  color: #f9fafb;
  border-color: #111827;
  box-shadow: 0 12px 26px rgba(15, 23, 42, 0.18);
}

/* footer polish */
.modal-footer {
  background: rgba(248, 244, 235, 0.65);
  backdrop-filter: blur(8px);
}

.pill-button {
  padding: 10px 16px;
  border-radius: 999px;
  border: none;
  background: #111827;
  color: #f9fafb;
  font-weight: 800;
  cursor: pointer;
}
.pill-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.pill-button.ghost {
  background: #ffffff;
  border: 1px solid #d1d5db;
  color: #111827;
}
.pill-button.ghost:hover {
  box-shadow: 0 10px 22px rgba(15, 23, 42, 0.10);
}

</style>
