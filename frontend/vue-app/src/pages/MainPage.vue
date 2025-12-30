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
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import { useAuth } from "../hooks/useAuth";
import ForcedExitAlert from "../components/ForcedExitAlert.vue";

const route = useRoute();
const router = useRouter();
const { isAuthenticated, user, fetchProfile, logout } = useAuth();
const isMenuOpen = ref(false);
const isDropdownOpen = ref(false);
const isLoggingOut = ref(false);
const showForcedExit = ref(false);

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
</style>