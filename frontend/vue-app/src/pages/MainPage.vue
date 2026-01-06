<template>
  <div class="landing">
    <header class="landing-header">
      <button
        ref="mobileHamburgerButton"
        type="button"
        class="mobile-hamburger mobile-only"
        aria-label="Open menu"
        :aria-expanded="isMobileMenuOpen"
        aria-haspopup="true"
        @click.stop="toggleMobileMenu"
      >
        <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" focusable="false">
          <path
            fill="currentColor"
            d="M4 6.5h16a1 1 0 0 0 0-2H4a1 1 0 0 0 0 2Zm16 4.5H4a1 1 0 0 0 0 2h16a1 1 0 0 0 0-2Zm0 6.5H4a1 1 0 0 0 0 2h16a1 1 0 0 0 0-2Z"
          />
        </svg>
      </button>

      <div class="nav-dropdown desktop-only" ref="dropdownContainer">
        <button
          class="nav-pill"
          @click="toggleMenu"
          aria-haspopup="true"
          :aria-expanded="isMenuOpen"
        >
          <span>MENU</span>
          <span class="chevron" :class="{ rotate: isMenuOpen }">&#9662;</span>
        </button>
        
        <Transition name="dropdown">
          <div class="dropdown-menu" v-show="isMenuOpen">
            <RouterLink to="/aboutus" class="dropdown-link dropdown-link--menu" @click="closeMenu">
              ABOUT US
            </RouterLink>
            <RouterLink to="/coding-test" class="dropdown-link dropdown-link--menu" @click="closeMenu">
              LIVE CODING
            </RouterLink>
            <RouterLink to="/studyplan" class="dropdown-link dropdown-link--menu" @click="closeMenu">
              PLANNER
            </RouterLink>
          </div>
        </Transition>
      </div>

      <h1 class="nav-logo desktop-only">JOBTORY</h1>
      <h1 class="nav-logo nav-logo--mobile mobile-only">JOBTORY</h1>

      <div class="nav-dropdown desktop-only" ref="userDropdownContainer">
        <button
          class="nav-pill"
          @click="toggleUserMenu"
          aria-haspopup="true"
          :aria-expanded="isDropdownOpen"
        >
          <span>{{ isAuthenticated ? userName : "Dropdown" }}</span>
          <span class="chevron" :class="{ rotate: isDropdownOpen }">&#9662;</span>
        </button>
        
        <Transition name="dropdown">
          <div class="dropdown-menu right-align" v-show="isDropdownOpen">
            <template v-if="isAuthenticated">
              <RouterLink :to="{ name: 'mypage' }" class="dropdown-link" @click="closeUserMenu">
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
              <RouterLink :to="{ name: 'login' }" class="dropdown-link" @click="closeUserMenu">
                LOGIN
              </RouterLink>
              <RouterLink :to="{ name: 'signup-choice' }" class="dropdown-link" @click="closeUserMenu">
                SIGNUP
              </RouterLink>
            </template>
          </div>
        </Transition>
      </div>

      <Transition name="mobile-drawer">
        <div
          v-show="isMobileMenuOpen"
          class="mobile-drawer-overlay"
          role="presentation"
          @click="closeMobileMenu"
        >
          <aside
            ref="mobileMenuContainer"
            class="mobile-drawer"
            role="dialog"
            aria-modal="true"
            aria-label="Mobile navigation menu"
            @click.stop
          >
            <div class="mobile-drawer-header">
              <div class="mobile-drawer-title">MENU</div>
              <button type="button" class="mobile-drawer-close" aria-label="Close menu" @click="closeMobileMenu">
                ✕
              </button>
            </div>

            <nav class="mobile-drawer-nav">
              <RouterLink to="/aboutus" class="mobile-drawer-link" @click="closeMobileMenu">ABOUT US</RouterLink>
              <RouterLink to="/coding-test" class="mobile-drawer-link" @click="closeMobileMenu">LIVE CODING</RouterLink>
              <RouterLink to="/studyplan" class="mobile-drawer-link" @click="closeMobileMenu">PLANNER</RouterLink>

              <div class="mobile-drawer-divider"></div>

              <template v-if="isAuthenticated">
                <div class="mobile-drawer-user">{{ userName }}</div>
                <RouterLink :to="{ name: 'mypage' }" class="mobile-drawer-link" @click="closeMobileMenu">MYPAGE</RouterLink>
                <button
                  type="button"
                  class="mobile-drawer-link mobile-drawer-button"
                  :class="{ 'mobile-drawer-button--loading': isLoggingOut }"
                  :disabled="isLoggingOut"
                  @click="handleLogout"
                >
                  <span v-if="isLoggingOut" class="spinner" aria-hidden="true"></span>
                  <span>{{ isLoggingOut ? "LOGOUT" : "LOGOUT" }}</span>
                </button>
              </template>
              <template v-else>
                <RouterLink :to="{ name: 'login' }" class="mobile-drawer-link" @click="closeMobileMenu">LOGIN</RouterLink>
                <RouterLink
                  :to="{ name: 'signup-choice' }"
                  class="mobile-drawer-link"
                  @click="closeMobileMenu"
                >
                  SIGNUP
                </RouterLink>
              </template>
            </nav>
          </aside>
        </div>
      </Transition>
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

    <div v-if="showProfileModal" class="modal-overlay">
      <div class="modal-card profile-card">
        <div class="modal-header">
          <div class="header-content">
            <h3>프로필 설정</h3>
            <p class="step-desc">
              {{ currentProfileStep === 1 ? '기본적인 학력 정보를 입력해주세요.' : '상세 직무 정보를 설정해주세요.' }}
            </p>
          </div>
          <button type="button" class="modal-close" @click="closeProfileModal">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        
        <div class="modal-body profile-body">
          <template v-if="currentProfileStep === 1">
            <div class="modal-field">
              <label>최종 학력 <span class="required">*</span></label>
              <select v-model="profileForm.graduated_school">
                <option value="">선택하세요</option>
                <option v-for="opt in graduatedOptions" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </div>
            
            <div class="modal-field">
              <label>학교명</label>
              <input v-model="profileForm.university" type="text" placeholder="예: 한국대학교" />
            </div>
            
            <div class="modal-field">
              <label>전공 여부</label>
              <select v-model="profileForm.major">
                <option value="">선택하세요</option>
                <option v-for="opt in majorOptions" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </div>
            
            <div class="modal-field">
              <label>재학 상태</label>
              <select v-model="profileForm.academic_status">
                <option value="">선택하세요</option>
                <option v-for="opt in academicOptions" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </div>
            
            <div class="modal-field full-width">
              <label>졸업(예정) 연도</label>
              <input v-model="profileForm.graduation_year" type="number" min="1900" max="2100" placeholder="YYYY" />
            </div>
          </template>

          <template v-else>
            <div class="modal-field">
              <label>경력 레벨 <span class="required">*</span></label>
              <select v-model="profileForm.career_level">
                <option value="">선택하세요</option>
                <option v-for="opt in careerOptions" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </div>
            
            <div class="modal-field">
              <label>현재 상태</label>
              <select v-model="profileForm.current_status">
                <option value="">선택하세요</option>
                <option v-for="opt in statusOptions" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </div>
            
            <div class="modal-field full-width">
              <label>기술 스택</label>
              <div class="checkbox-group">
                <label v-for="opt in techStackOptions" :key="opt" class="checkbox-item">
                  <input type="checkbox" :value="opt" v-model="profileForm.tech_stack" />
                  <span>{{ opt }}</span>
                </label>
              </div>
            </div>

            <div class="modal-field full-width">
              <label>희망 직무</label>
              <div class="checkbox-group">
                <label v-for="opt in desiredRoleOptions" :key="opt" class="checkbox-item">
                  <input type="checkbox" :value="opt" v-model="profileForm.desired_role" />
                  <span>{{ opt }}</span>
                </label>
              </div>
            </div>

            <div class="modal-field full-width">
              <label>세부 희망 직무</label>
              <div class="checkbox-group">
                <label v-for="opt in detailedRoleOptions" :key="opt" class="checkbox-item">
                  <input type="checkbox" :value="opt" v-model="profileForm.detailed_role" />
                  <span>{{ opt }}</span>
                </label>
              </div>
            </div>

            <div class="modal-field full-width">
              <label>희망 근무지</label>
              <select v-model="profileForm.region">
                <option value="">선택하세요</option>
                <option v-for="opt in regionOptions" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </div>
          </template>
        </div>
        
        <div class="modal-footer">
          <div class="step-indicator">
            <div class="step-dot" :class="{ active: currentProfileStep >= 1 }"></div>
            <div class="step-line"></div>
            <div class="step-dot" :class="{ active: currentProfileStep >= 2 }"></div>
          </div>
          
          <div class="modal-actions">
            <button 
              v-if="currentProfileStep === 2" 
              type="button" 
              class="btn-secondary" 
              @click="currentProfileStep = 1"
            >
              이전
            </button>
            <button 
              v-if="currentProfileStep === 1" 
              type="button" 
              class="btn-primary" 
              @click="currentProfileStep = 2"
            >
              다음 단계
            </button>
            <button 
              v-else 
              class="btn-primary" 
              :disabled="savingProfile" 
              @click="saveProfile"
            >
              {{ savingProfile ? "저장 중..." : "설정 완료" }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import { useAuth } from "../hooks/useAuth";
import ForcedExitAlert from "../components/ForcedExitAlert.vue";
import { useProfileOptions } from "../hooks/useProfileOptions";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

const route = useRoute();
const router = useRouter();
const { isAuthenticated, user, fetchProfile, logout, token } = useAuth();
const { options: optionData, loading: optionsLoading, error: optionsError, fetchProfileOptions } = useProfileOptions();
const isMenuOpen = ref(false);
const isDropdownOpen = ref(false); 
const isMobileMenuOpen = ref(false);
const dropdownContainer = ref(null); 
const userDropdownContainer = ref(null); 
const mobileMenuContainer = ref(null);
const mobileHamburgerButton = ref(null);
const toggleMenu = () => { isMenuOpen.value = !isMenuOpen.value; };
const closeMenu = () => { isMenuOpen.value = false; };
const toggleUserMenu = () => { isDropdownOpen.value = !isDropdownOpen.value; };
const closeUserMenu = () => { isDropdownOpen.value = false; };
const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value;
  closeMenu();
  closeUserMenu();
};
const closeMobileMenu = () => {
  isMobileMenuOpen.value = false;
};
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

const graduatedOptions = computed(() => optionData.value?.graduated_school || []);
const majorOptions = computed(() => optionData.value?.major || []);
const academicOptions = computed(() => optionData.value?.academic_status || []);
const careerOptions = computed(() => optionData.value?.career_level || []);
const statusOptions = computed(() => optionData.value?.current_status || []);
const techStackOptions = computed(() => optionData.value?.tech_stack || []);
const desiredRoleOptions = computed(() => optionData.value?.desired_role || []);
const detailedRoleOptions = computed(() => optionData.value?.detailed_role || []);
const regionOptions = computed(() => optionData.value?.region || []);

const toggleMultiSelect = (field, value) => {
  const current = Array.isArray(profileForm[field]) ? profileForm[field] : [];
  profileForm[field] = current.includes(value)
    ? current.filter((item) => item !== value)
    : [...current, value];
};

const userName = computed(() => user.value?.name || "회원");

const handleClickOutside = (event) => {
  if (dropdownContainer.value && !dropdownContainer.value.contains(event.target)) {
    closeMenu();
  }
  if (userDropdownContainer.value && !userDropdownContainer.value.contains(event.target)) {
    closeUserMenu();
  }
  if (
    isMobileMenuOpen.value &&
    mobileMenuContainer.value &&
    !mobileMenuContainer.value.contains(event.target) &&
    !(mobileHamburgerButton.value && mobileHamburgerButton.value.contains(event.target))
  ) {
    closeMobileMenu();
  }
};

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
  try {
    await logout();
    closeDropdown();
    isMenuOpen.value = false;
    closeMobileMenu();
    await router.push({ name: "login" });
  } catch (err) {
    console.error("[logout] failed", err);
  } finally {
    isLoggingOut.value = false;
  }
};

const syncProfile = () => {
  if (isAuthenticated.value && !user.value) {
    void fetchProfile();
  }
};

const needProfileModal = (profile) => {
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

const handleKeydown = (event) => {
  if (event.key === "Escape") {
    closeMobileMenu();
    closeMenu();
    closeUserMenu();
  }
};

onMounted(() => {
  document.addEventListener("click", handleClickOutside);
  window.addEventListener("keydown", handleKeydown);
  window.addEventListener("storage", syncProfile);
  syncProfile();
  void fetchProfileOptions().catch(() => {});
  void loadProfile();
  checkForcedAlert();
  window.addEventListener("storage", syncProfile);
  syncProfile();
  void fetchProfileOptions().catch(() => {});
  void loadProfile();
  checkForcedAlert();
});

onUnmounted(() => {
  document.removeEventListener("click", handleClickOutside);
  window.removeEventListener("keydown", handleKeydown);
  window.removeEventListener("storage", syncProfile);
  window.removeEventListener("storage", syncProfile);
});

watch(isMobileMenuOpen, (open) => {
  try {
    document.body.style.overflow = open ? "hidden" : "";
  } catch {
    // ignore
  }
});

const heroImage = new URL("../assets/mainpage_image1.png", import.meta.url).href;
const heroImage2 = new URL("../assets/mainpage_image2.png", import.meta.url).href;
const heroImage3 = new URL("../assets/mainpage_image3.png", import.meta.url).href;
const heroImage4 = new URL("../assets/mainpage_image4.png", import.meta.url).href;
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap");
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;900&display=swap");
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

.desktop-only {
  display: block;
}

.mobile-only {
  display: none !important;
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

.nav-logo--mobile {
  position: static;
  width: auto;
  height: auto;
  transform: none;
  font-weight: 900;
  font-size: 28px;
  line-height: 1;
}

.mobile-hamburger {
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border-radius: 999px;
  background: #020617;
  color: #f9fafb;
  border: none;
  cursor: pointer;
}

.mobile-drawer-overlay {
  position: fixed;
  inset: 0;
  background: rgba(2, 6, 23, 0.45);
  backdrop-filter: blur(6px);
  z-index: 200;
}

.mobile-drawer {
  position: absolute;
  top: 0;
  right: 0;
  height: 100%;
  width: min(360px, 92vw);
  background: #0b1220;
  border-left: 1px solid rgba(255, 255, 255, 0.08);
  padding: 18px 16px;
  box-shadow: -20px 0 60px rgba(0, 0, 0, 0.35);
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.mobile-drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 2px 2px;
}

.mobile-drawer-title {
  color: #f9fafb;
  font-weight: 800;
  letter-spacing: 0.04em;
}

.mobile-drawer-close {
  width: 40px;
  height: 40px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.06);
  color: #f9fafb;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.mobile-drawer-nav {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-top: 6px;
}

.mobile-drawer-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 12px;
  border-radius: 12px;
  color: #f9fafb;
  text-decoration: none;
  font-weight: 800;
  letter-spacing: 0.02em;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.mobile-drawer-link:hover {
  background: rgba(255, 255, 255, 0.10);
}

.mobile-drawer-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.10);
  margin: 8px 0;
}

.mobile-drawer-user {
  color: rgba(255, 255, 255, 0.80);
  font-weight: 700;
  padding: 0 4px;
}

.mobile-drawer-button {
  width: 100%;
  text-align: left;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  cursor: pointer;
  font: inherit;
}

.mobile-drawer-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.mobile-drawer-button--loading .spinner {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid #ffffff;
  border-top-color: transparent;
  animation: spin 0.8s linear infinite;
}

.mobile-drawer-enter-active,
.mobile-drawer-leave-active {
  transition: opacity 0.2s ease;
}

.mobile-drawer-enter-from,
.mobile-drawer-leave-to {
  opacity: 0;
}

.mobile-drawer-enter-active .mobile-drawer,
.mobile-drawer-leave-active .mobile-drawer {
  transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.mobile-drawer-enter-from .mobile-drawer,
.mobile-drawer-leave-to .mobile-drawer {
  transform: translateX(18px);
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

.nav-pill .chevron {
  font-size: 12px;
}

.chevron.rotate {
  transform: rotate(180deg);
}

.nav-dropdown {
  position: relative;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  min-width: 160px;
  padding: 8px 0;
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
  color: #f9fafb;
  font-size: 16px;
  font-weight: 700;
  text-decoration: none;
  border-radius: 8px;
  transition: background 0.2s;
}

.dropdown-link:hover {
  background: #374151;
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
  color: #f9fafb;
}

.dropdown-button--loading .spinner {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid #ffffff;
  border-top-color: transparent;
  animation: spin 0.8s linear infinite;
}

.dropdown-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

@media (max-width: 1200px) {
  .landing-header {
    padding: 24px 18px;
    justify-content: center;
  }

  .desktop-only {
    display: none !important;
  }

  .mobile-only {
    display: block !important;
  }

  .mobile-hamburger {
    display: inline-flex !important;
    position: absolute;
    left: 18px;
  }
}

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
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
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
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
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
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
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

.spotlight-card:hover .spotlight-overlay {
  opacity: 1;
}

.spotlight-card:hover .card-image-content {
  transform: scale(1.05);
}

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

/* =========================================
   프로필 모달 디자인 (Clean & Standard Modern)
   ========================================= */

/* 모달 배경 (Backdrop) */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 16px;
}

/* 모달 카드 본체 */
.modal-card.profile-card {
  width: min(800px, 100%);
  max-height: 85vh;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 헤더 */
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 24px 32px 16px;
  background: #fff;
  border-bottom: 1px solid #f3f4f6;
}

.header-content h3 {
  margin: 0 0 4px;
  font-size: 20px;
  font-weight: 800;
  color: #111827;
}

.step-desc {
  margin: 0;
  font-size: 13px;
  color: #6b7280;
}

.modal-close {
  background: transparent;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
}

.modal-close:hover {
  background: #f3f4f6;
  color: #111827;
}

/* 바디 (Body) */
.modal-body.profile-body {
  padding: 32px;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  background: #fff;
}

/* 입력 필드 (Input Fields) */
.modal-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.modal-field.full-width {
  grid-column: 1 / -1;
}

.modal-field label {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}

.modal-field .required {
  color: #ef4444;
  margin-left: 2px;
}

/* Input & Select: Filled Style */
.modal-field input,
.modal-field select {
  width: 100%;
  height: 46px;
  padding: 0 16px;
  border-radius: 8px;
  border: 1px solid transparent;
  background: #f3f4f6;
  color: #111827;
  font-size: 14px;
  font-family: inherit;
  transition: all 0.2s ease;
  outline: none;
  box-sizing: border-box;
}

/* Focus State */
.modal-field input:focus,
.modal-field select:focus {
  background: #ffffff;
  border-color: #111827;
  box-shadow: 0 0 0 1px #111827;
}

/* Select 화살표 커스텀 */
.modal-field select {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%234b5563' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 14px center;
}

.modal-field input::placeholder {
  color: #9ca3af;
}

/* 체크박스 그룹 (Chips) */
.checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.checkbox-item {
  position: relative;
  cursor: pointer;
}

.checkbox-item input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

/* Chip Style */
.checkbox-item span {
  display: inline-flex;
  align-items: center;
  height: 34px;
  padding: 0 14px;
  border-radius: 6px;
  background: #ffffff;
  border: 1px solid #d1d5db;
  color: #4b5563;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.15s ease;
}

.checkbox-item:hover span {
  border-color: #9ca3af;
  color: #111827;
}

/* Chip Selected */
.checkbox-item input:checked + span {
  background: #111827;
  border-color: #111827;
  color: #ffffff;
  font-weight: 600;
}

/* 푸터 (Footer) */
.modal-footer {
  padding: 20px 32px;
  background: #ffffff;
  border-top: 1px solid #f3f4f6;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 단계 표시기 */
.step-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.step-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #e5e7eb;
  transition: all 0.3s;
}

.step-dot.active {
  background: #111827;
  transform: scale(1.2);
}

.step-line {
  width: 40px;
  height: 2px;
  background: #e5e7eb;
  border-radius: 99px;
}

/* 버튼 그룹 */
.modal-actions {
  display: flex;
  gap: 10px;
}

.btn-primary,
.btn-secondary {
  height: 44px;
  padding: 0 20px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #111827;
  color: #ffffff;
  border: 1px solid #111827;
}

.btn-primary:hover:not(:disabled) {
  background: #000000;
  transform: translateY(-1px);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #ffffff;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover {
  background: #f9fafb;
  border-color: #9ca3af;
  color: #111827;
}

/* Mobile Footer */
@media (max-width: 640px) {
  .modal-footer {
    flex-direction: column-reverse;
    gap: 16px;
  }

  .modal-actions {
    width: 100%;
    justify-content: stretch;
  }

  .btn-primary,
  .btn-secondary {
    flex: 1;
  }
}
</style>