<template>
  <div class="landing">
    <header class="landing-header">
      <button class="nav-pill">
        <span>MENU</span>
        <span class="chevron">▾</span>
      </button>
      <h1 class="nav-logo">JOBTORY</h1>
      <button class="nav-pill">
        <span>Dropdown</span>
        <span class="chevron">▾</span>
      </button>
    </header>

    <section class="hero">
      <div class="hero-inner">
        <div class="hero-text">
          <h2 class="hero-title">
            Build confidence through
            <br />
            every live challenge.
          </h2>
          <p class="hero-description">
            실시간 라이브 코딩과 행동 기반 인터뷰로 개발자의 문제 해결력과 커뮤니케이션을
            있는 그대로 평가하세요.
          </p>
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
        <p class="insights-description">
          실시간 코딩 인터뷰를 통해 문제 해결 과정과 커뮤니케이션을 함께 평가하고,
          지원자의 잠재력을 깊이 있게 이해할 수 있습니다.
        </p>
      </div>

      <div class="insights-cards">
        <div class="insight-card card-one">
          <h4>라이브 코드 실행</h4>
          <p>코드를 작성하고 바로 실행하면서 사고 과정을 확인합니다.</p>
          <div class="hero-image-wrap">
          <img :src="heroImage2" alt="Live coding interface" class="hero-image" />
        </div>
        </div>
        <div class="insight-card card-two">
          <h4>대화형 인터뷰</h4>
          <p>화상 인터뷰와 채팅을 통해 협업 능력을 평가합니다.</p>
          <div class="hero-image-wrap">
          <img :src="heroImage3" alt="Live coding interface" class="hero-image" />
        </div>
        </div>
        <div class="insight-card card-three">
          <h4>정량 + 정성 피드백</h4>
          <p>코딩 결과와 행동 기록을 함께 저장해 채용 의사결정을 돕습니다.</p>
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
import { RouterLink } from "vue-router";

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

.hero {
  position: relative;
  padding: 80px 56px 120px;
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
  margin: 0 0 24px;
  max-width: 640px;
  font-family: "SF Pro", sans-serif;
  font-style: normal;
  font-weight: 700;
  font-size: 64px;
  line-height: 1.05;
  color: #000000;
}

.hero-description {
  max-width: 540px;
  margin: 0 0 32px;
  font-size: 16px;
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
  padding: 60px 24px;
  display: flex;
  justify-content: center;
}

.email-inner {
  max-width: 980px;
  width: 100%;
  margin: 0 auto;
  color: #0b1120;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.email-label {
  margin: 0;
  font-family: "Inter";
  font-style: normal;
  font-weight: 200;
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
  font-size: 96px;
  line-height: 1;
  color: #000000;
}

.insights {
  background: #111827;
  color: #f9fafb;
  padding: 72px 24px 96px;
}

.insights-header {
  max-width: 980px;
  margin: 0 auto 40px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  text-align: center;
  align-items: center;
}

.insights-title {
  margin: 0;
  font-family: "SF Pro", sans-serif;
  font-style: normal;
  font-weight: 700;
  font-size: 36px;
  line-height: 1.1;
  color: #ffffff;
}

.insights-description {
  margin: 0;
  max-width: 640px;
  font-family: 'SF Pro', sans-serif;
  font-weight: 400;
  font-size: 16px;
  line-height: 1.5;
  color: #e5e7eb;
}

.insights-cards {
  max-width: 1080px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 20px;
  justify-items: center;
}



.insight-card {
  border-radius: 18px;
  padding: 20px 18px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  min-height: 260px;
  color: #111827;
  width: 100%;
  max-width: 320px;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: #f9fafb;
}

.insight-card h4 {
  margin-bottom: 8px;
  font-size: 16px;
}

.insight-card p {
  margin: 0;
  font-size: 14px;
}

.insight-card .hero-image-wrap {
  margin-top: 16px;
}

.insight-card .hero-image {
  max-width: 100%;
  box-shadow: none;
  border: none;
  border-radius: 12px;
}

.card-one {
  background: #f2c3d3;
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
    font-size: 48px;
  }

  .insights-header {
    gap: 12px;
  }

  .insights-cards {
    grid-template-columns: 1fr;
  }
}
</style>
