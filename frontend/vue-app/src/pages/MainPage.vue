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
          <RouterLink to="/interview" class="dropdown-link" @click="isMenuOpen = false">
            인터뷰
          </RouterLink>
          <RouterLink to="/coding-test" class="dropdown-link" @click="isMenuOpen = false">
            라이브코딩
          </RouterLink>
        </div>
      </div>
      <h1 class="nav-logo">JOBTORY</h1>
      <div class="nav-dropdown">
        <button class="nav-pill" @click="isDropdownOpen = !isDropdownOpen" aria-haspopup="true" :aria-expanded="isDropdownOpen">
          <span>Dropdown</span>
          <span class="chevron">&#9662;</span>
        </button>
        <div class="dropdown-menu" v-show="isDropdownOpen">
          <RouterLink to="/login" class="dropdown-link" @click="isDropdownOpen = false">로그인</RouterLink>
          <RouterLink to="/signup" class="dropdown-link" @click="isDropdownOpen = false">회원가입</RouterLink>
        </div>
      </div>
    </header>

    <section class="hero">
      <div class="hero-inner">
        <div class="hero-text">
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

        <div class="hero-image-wrap">
          <img :src="heroImage" alt="Live coding interface" class="hero-image" />
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
        <p class="insights-description">실시간 코딩 인터뷰를 통해 문제 해결 과정과 커뮤니케이션을 함께 평가하고, 지원자의 잠재력을 깊이 있게 이해할 수 있습니다.</p>
      </div>

      <div class="insights-cards">
        <div class="insight-card card-one">
          <h4 class="card-heading">라이브 코드 실행</h4>
          <p class="card-copy">코드를 작성하고 바로 실행하며 사고 과정을 투명하게 보여줍니다.</p>
          <div class="hero-image-wrap">
            <img :src="heroImage2" alt="Live coding interface" class="hero-image" />
          </div>
        </div>
        <div class="insight-card card-two">
          <h4 class="card-heading">협업형 인터뷰</h4>
          <p class="card-copy">실시간 채팅으로 문제 해결 과정과 커뮤니케이션을 함께 확인합니다.</p>
          <div class="hero-image-wrap">
            <img :src="heroImage3" alt="Live coding interface" class="hero-image" />
          </div>
        </div>
        <div class="insight-card card-three">
          <h4 class="card-heading">정량 + 정성 리포트</h4>
          <p class="card-copy">결과와 행동 기록을 모두 남겨 채용 의사결정을 뒷받침합니다.</p>
          <div class="hero-image-wrap">
            <img :src="heroImage4" alt="Live coding interface" class="hero-image" />
          </div>
        </div>
      </div>
    </section>

    <section class="email-banner">
      <div class="email-inner">
        <p class="email-label">Company Email</p>
        <a href="mailto:jobtory@gmail.com" class="email-link">jobtory@gmail.com</a>
        <div class="email-logo">JOBTORY</div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { RouterLink } from "vue-router";

const isMenuOpen = ref(false);
const isDropdownOpen = ref(false);

const heroImage = new URL("../assets/mainpage_image1.png", import.meta.url).href;
const heroImage2 = new URL("../assets/mainpage_image2.png", import.meta.url).href;
const heroImage3 = new URL("../assets/mainpage_image3.png", import.meta.url).href;
const heroImage4 = new URL("../assets/mainpage_image4.png", import.meta.url).href;
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap");
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@900&display=swap");

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
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.12);
}

.dropdown-link {
  padding: 10px 14px;
  color: #111827;
  font-size: 14px;
  font-weight: 700;
  text-decoration: none;
  border-radius: 8px;
}

.dropdown-link:hover {
  background: #f3f4f6;
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
  background: #1f252d;
  color: #f9fafb;
  padding: 100px 40px 170px;
}

.insights-header {
  max-width: 1280px;
  margin: 0 auto 50px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
  gap: 36px;
  align-items: start;
  text-align: left;
}

.insights-title {
  margin: 50;
  font-family: "SF Pro", sans-serif;
  font-style: normal;
  font-weight: 800;
  font-size: 56px;
  line-height: 1.54;
  color: #f9fafb;
}

.insights-description {
  margin: 125px 0 0;
  max-width: 800px;
  font-family: 'SF Pro', sans-serif;
  font-weight: 400;
  font-size: 20px;
  line-height: 1.7;
  color: #cbd5e1;
}

.insights-cards {
  max-width: 1280px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: 32px;
  justify-items: center;
}



.insight-card {
  border-radius: 18px;
  padding: 100px 10px 20px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: center;
  text-align: center;
  min-height: 650px;
  color: #111827;
  width: 100%;
  max-width: 420px;
  box-shadow: 0 20px 48px rgba(0, 0, 0, 0.24);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.insight-card h4 {
  margin-bottom: 30px;
  font-size: 40px;
}

.insight-card p {
  margin: 30px;
  font-size: 20px;
}

.card-heading {
  margin: 0 0 18px;
  font-size: 32px;
  font-weight: 800;
  letter-spacing: 0.01em;
  color: #0f172a;
}

.card-copy {
  margin: 0px;
  font-size: 20px;
  line-height: 1.7;
  color: #1f2937;
}

.insight-card .hero-image-wrap {
  margin-top: 32px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  width: 100%;
  min-height: 320px;
}

.insight-card .hero-image {
  max-width: 320px;
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

  .email-logo {
    font-size: 40px;
  }

  .insights-header {
    gap: 16px;
    grid-template-columns: 1fr;
    text-align: center;
  }

  .insights-cards {
    grid-template-columns: 1fr;
  }
}
</style>
