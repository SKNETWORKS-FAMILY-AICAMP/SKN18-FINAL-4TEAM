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
          <span class="chevron">&#9662;</span>
        </button>
        <div class="dropdown-menu" v-show="isMenuOpen">
          <RouterLink to="/aboutus" class="dropdown-link dropdown-link--menu" @click="isMenuOpen = false">
            ABOUT US
          </RouterLink>
          <RouterLink to="/coding-test" class="dropdown-link dropdown-link--menu" @click="isMenuOpen = false">
            LIVE CODING
          </RouterLink>
        </div>
      </div>
      <h1 class="nav-logo">JOBTORY</h1>
      <div class="nav-dropdown">
        <button
          class="nav-pill"
          @click="isDropdownOpen = !isDropdownOpen"
          aria-haspopup="true"
          :aria-expanded="isDropdownOpen"
        >
          <span>{{ isAuthenticated ? userName : "LOGIN" }}</span>
          <span class="chevron">&#9662;</span>
        </button>
        <div class="dropdown-menu" v-show="isDropdownOpen">
          <template v-if="isAuthenticated">
            <RouterLink :to="{ name: 'mypage' }" class="dropdown-link" @click="closeDropdown">
              마이페이지
            </RouterLink>
            <button
              type="button"
              class="dropdown-link dropdown-button"
              :class="{ 'dropdown-button--loading': isLoggingOut }"
              :disabled="isLoggingOut"
              @click="handleLogout"
            >
              <span v-if="isLoggingOut" class="spinner" aria-hidden="true"></span>
              <span>{{ isLoggingOut ? "로그아웃 중..." : "로그아웃" }}</span>
            </button>
          </template>
          <template v-else>
            <RouterLink :to="{ name: 'login' }" class="dropdown-link" @click="closeDropdown">
              로그인
            </RouterLink>
            <RouterLink :to="{ name: 'signup-choice' }" class="dropdown-link" @click="closeDropdown">
              회원가입
            </RouterLink>
          </template>
        </div>
      </div>
    </header>

    <section class="hero">
      <div class="hero-inner">
        <div class="hero-text scroll-reveal">
          <h2 class="hero-title">
            Build confidence through
            <br />
            every live challenge.
          </h2>
          <p class="hero-description">실시간 라이브 코딩과 행동 기반 인터뷰로 개발자의 문제 해결력과 커뮤니케이션을 있는 그대로 평가하세요.</p>
          <div class="hero-actions">
            <RouterLink to="/coding-test" class="secondary">라이브 코딩 테스트 보기</RouterLink>
          </div>
        </div>

        <div class="hero-image-wrap scroll-reveal">
          <img :src="heroImage" alt="Live coding interface" class="hero-image" />
        </div>
      </div>
    </section>

    <section class="insights">
      <div class="insights-header scroll-reveal">
        <h3 class="insights-title">
          Real-time coding.
          <br />
          Real insights.
        </h3>
        <p class="insights-description">정답을 맞히는 테스트를 넘어, 당신이라는 인재를 깊이 있게 이해하는 시간.
        <br />
        당신의 잠재력을 가장 입체적으로 보여주는 라이브 인터뷰 플랫폼입니다.</p>
      </div>

      <div class="insights-cards">
        <div class="insight-card card-one scroll-reveal">
          <h4 class="card-heading">라이브 코드 실행</h4>
          <p class="card-copy">작성된 코드는 실시간으로 실행되어 살아있는 결과물이 됩니다. 
          <br />
          논리 구조부터 최적화까지, 당신이 코딩에 담은 디테일한 고민들이 면접관에게 그대로 전달됩니다.</p>
          <div class="hero-image-wrap">
            <img :src="heroImage2" alt="Live coding interface" class="hero-image" />
          </div>
        </div>
        <div class="insight-card card-two scroll-reveal">
          <h4 class="card-heading">협업형 인터뷰</h4>
          <p class="card-copy">실시간 인터랙션을 통해 함께 일하고 싶은 동료로서의 매력을 발산합니다. 
          <br />
          대화를 통해 정답을 찾아가는 과정 자체가 당신의 훌륭한 커뮤니케이션 포트폴리오가 됩니다.</p>
          <div class="hero-image-wrap">
            <img :src="heroImage3" alt="Live coding interface" class="hero-image" />
          </div>
        </div>
        <div class="insight-card card-three scroll-reveal">
          <h4 class="card-heading">정량 + 정성 리포트</h4>
          <p class="card-copy">당신의 모든 인터뷰 여정은 데이터로 기록됩니다. 
          <br />
          코드 효율성 지표와 행동 분석이 결합된 상세 리포트는 당신의 실력을 가장 설득력 있게 대변해 줍니다.</p>
          <div class="hero-image-wrap">
            <img :src="heroImage4" alt="Live coding interface" class="hero-image" />
          </div>
        </div>
      </div>
    </section>

    <section class="email-banner scroll-reveal">
      <div class="email-inner">
        <p class="email-label">Company Email</p>
        <a href="mailto:jobtory@gmail.com" class="email-link">jobtory@gmail.com</a>
        <div class="email-logo">JOBTORY</div>
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

const closeDropdown = () => {
  isDropdownOpen.value = false;
};

const handleLogout = async () => {
  if (isLoggingOut.value) return;
  isLoggingOut.value = true;
  setTimeout(async () => {
    await logout(); // 실제 세션 종료는 약간 뒤에 수행해 전환을 부드럽게
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

let revealObserver;

const setupScrollReveal = () => {
  const targets = Array.from(document.querySelectorAll(".scroll-reveal"));
  if (!targets.length) return;
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    targets.forEach((el) => el.classList.add("is-visible"));
    return;
  }
  if (!("IntersectionObserver" in window)) {
    targets.forEach((el) => el.classList.add("is-visible"));
    return;
  }
  revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          revealObserver.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15, rootMargin: "0px 0px -10% 0px" }
  );
  targets.forEach((el) => revealObserver.observe(el));
};


onMounted(() => {
  window.addEventListener("storage", syncProfile);
  syncProfile();
  checkForcedAlert();
  setupScrollReveal();
});

onUnmounted(() => {
  window.removeEventListener("storage", syncProfile);
  if (revealObserver) {
    revealObserver.disconnect();
  }
});

const heroImage = new URL("../assets/mainpage_image1.png", import.meta.url).href;
const heroImage2 = new URL("../assets/mainpage_image2.png", import.meta.url).href;
const heroImage3 = new URL("../assets/mainpage_image3.png", import.meta.url).href;
const heroImage4 = new URL("../assets/mainpage_image4.png", import.meta.url).href;
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap");
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@900&display=swap");

:global(html),
:global(body) {
  scroll-snap-type: y proximity;
  scroll-padding-top: 8px;
}



.landing {
  min-height: 100vh;
  background: #f8f4eb;
  font-family: "Nunito", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #111827;
}

.landing-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 70px 220px;
  border-bottom: 1px solid #e5e7eb;
  position: relative;
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

.nav-pill .chevron {
  font-size: 12px;
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
  background: #0b0b0e;
  border: none;
  border-radius: 12px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.3);
}

.dropdown-link {
  padding: 10px 14px;
  color: #f9fafb;
  font-size: 16px;
  font-weight: 800;
  text-decoration: none;
  border-radius: 8px;
}

.dropdown-link--menu {
  font-family: "SF Pro", sans-serif;
}

.dropdown-button {
  width: 100%;
  text-align: left;
  background: transparent;
  border: none;
  cursor: pointer;
  font: inherit;
  font-size: 16px;
  font-weight: 800;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.dropdown-link:hover {
  background: rgba(255, 255, 255, 0.08);
}

.dropdown-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.dropdown-button--loading .spinner {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid #111827;
  border-top-color: transparent;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.hero {
  position: relative;
  padding: 100px 56px 150px;
}

.hero-inner {
  max-width: 1120px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  align-items: center;
  gap: 48px;
}

.hero-text {
  text-align: left;
  position: relative;
  z-index: 1;
}

.hero-title {
  max-width: 640px;
  font-family: "SF Pro", sans-serif;
  font-style: normal;
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
}

.secondary {
  border: 1px solid #d1d5db;
  background: #f9fafb;
  color: #111827;
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
  border: none;
  background: transparent;
  object-fit: cover;
}

.email-banner {
  box-sizing: border-box;
  background: #caa3b1;
  padding: 80px 50px;
  display: flex;
  justify-content: center;
}

.email-inner {
  max-width: 980px;
  width: 100%;
  margin: 0 auto;
  color: #0b1120;
  text-align: center;
  display: grid;
  flex-direction: column;
  align-items: center;
  gap: 25px;
}

.email-label {
  margin: 0;
  font-family: "Inter";
  font-style: normal;
  font-weight: 200; /* ExtraLight */
  font-size: 24px;
  line-height: 1.4;
  color: #000000;
}

.email-link {
  font-family: "Inter";
  font-style: normal;
  font-weight: 900;
  font-size: 32px;
  line-height: 1.3;
  text-decoration-line: underline;
  color: #000000;
}

.email-logo {
  font-family: "Inter";
  font-style: normal;
  font-weight: 900;
  font-size: 100px;
  line-height: 1;
  color: #000000;
}

.insights {
  scroll-snap-align: start;
  background: #1f252d;
  color: #f9fafb;
  min-height: 100vh;
  min-height: 100svh;
  height: 100svh;
  box-sizing: border-box;
  padding: clamp(100px, 3vh, 48px) clamp(16px, 3vw, 32px);
  display: grid;
  grid-template-rows: auto 0fr;
  gap: clamp(10px, 2vh, 20px);
}

.insights-header {
  max-width: 1280px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: clamp(12px, 2.5vw, 24px);
  align-items: center;
  text-align: left;
}

.insights-title {
  margin: 0;
  font-family: "SF Pro", sans-serif;
  font-style: normal;
  font-weight: 800;
  font-size: clamp(34px, 4.6vw, 52px);
  line-height: 1.2;
  color: #f9fafb;
}

.insights-description {
  margin: clamp(8px, 1.5vh, 16px) 0 0;
  max-width: 800px;
  font-family: 'SF Pro', sans-serif;
  font-weight: 400;
  font-size: clamp(14px, 1.6vw, 18px);
  line-height: 1.6;
  color: #cbd5e1;
}

.insights-cards {
  max-width: 1280px;
  margin: 0 auto;
  display: grid;
  width: 100%;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  align-items: stretch;
  gap: clamp(20px, 3vw, 32px);
  justify-items: center;
}



.insight-card {
  border-radius: 18px;
  padding: clamp(28px, 4vh, 48px) clamp(20px, 0.6vw, 32px);
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: center;
  text-align: center;
  min-height: clamp(240px, 32vh, 380px);
  color: #111827;
  width: min(94%, 420px);
  max-width: none;
  box-shadow: 0 20px 48px rgba(0, 0, 0, 0.24);
  border: 1px solid rgba(255, 255, 255, 0.06);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.insight-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 28px 60px rgba(0, 0, 0, 0.3);
}

.insight-card h4 {
  margin-bottom: clamp(12px, 2vh, 20px);
  font-size: clamp(26px, 3vw, 36px);
  line-height: 1.15;
}

.insight-card p {
  margin: 0;
  max-width: 90%;
  font-size: clamp(13px, 1.6vw, 17px);
  line-height: 1.65;
}

.card-heading {
  font-size: clamp(26px, 3vw, 36px);
  font-weight: 800;
  letter-spacing: 0.01em;
  color: #0f172a;
}

.card-copy {
  margin: 0px;
  font-size: clamp(13px, 1.6vw, 17px);
  line-height: 1.65;
  color: #1f2937;
}

.insight-card .hero-image-wrap {
  margin-top: clamp(18px, 3vh, 36px);
  display: flex;
  justify-content: center;
  align-items: flex-start;
  width: 100%;
  min-height: clamp(120px, 14vh, 180px);
}

.insight-card .hero-image {
  max-width: clamp(180px, 14vw, 220px);
  box-shadow: none;
  border: none;
  border-radius: 12px;
  object-fit: contain;
}

.card-one {
  background: #f9c5d5;
}

.card-two {
  background: #f7d56f;
}

.card-three {
  background: #bfacf9;
}


.scroll-reveal {
  opacity: 0;
  transform: translateY(18px);
  transition: opacity 0.6s ease, transform 0.6s ease;
  will-change: opacity, transform;
}

.scroll-reveal.is-visible {
  opacity: 1;
  transform: translateY(0);
}

.insights-cards .insight-card.scroll-reveal {
  transition-delay: 0ms;
}

.insights-cards .insight-card.scroll-reveal:nth-child(2) {
  transition-delay: 120ms;
}

.insights-cards .insight-card.scroll-reveal:nth-child(3) {
  transition-delay: 240ms;
}

@media (prefers-reduced-motion: reduce) {
  .scroll-reveal {
    opacity: 1;
    transform: none;
    transition: none;
  }
}

@media (max-width: 768px) {
  .landing-header {
    padding: 16px 20px;
  }

  .nav-logo {
    font-size: 24px;
  }

  .hero {
    padding: 56px 20px 100px;
  }

  .hero-title {
    font-size: 32px;
    line-height: 1.2;
    margin-bottom: 16px;
  }

  .insights-header {
    gap: 16px;
    grid-template-columns: 1fr;
    text-align: center;
  }

  .insights-cards {
    grid-template-columns: 1fr;
  }


  .insights {
    height: auto;
    min-height: 100svh;
    padding: 40px 20px 64px;
  }

}

</style>
