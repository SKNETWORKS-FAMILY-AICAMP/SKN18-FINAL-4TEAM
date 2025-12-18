<template>
  <div class="aboutus">
    <button type="button" class="back-button" @click="goBack" aria-label="Back">
      <svg class="back-icon" viewBox="0 0 28 24" aria-hidden="true">
        <path d="M14.5 5.5L8 12l6.5 6.5" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="3" />
        <path d="M9 12h15" fill="none" stroke="currentColor" stroke-linecap="round" stroke-width="3" />
      </svg>
    </button>
    <section class="hero">
      <div class="hero-overlay">
        <p>About Us</p>
      </div>
    </section>

    <section class="manifesto">
      <div class="manifesto-inner">
        <p class="manifesto-subtitle">우리는 당신의 '결과'보다 '과정'에 담긴 가치를 믿습니다.</p>
        <p>
          단순히 정답을 맞히는 코딩 테스트는 한 사람의 진면목을 보여주기에 부족합니다. 
          <br />
          JOBTORY는 코드가 작성되는 찰나의 고민, 
          문제를 해결해 나가는 논리적인 흐름, 
          <br />
          그리고 동료와 나누는 유연한 소통에 집중합니다.
        </p>
        <p>
          JOBTORY는 누구나 설득 가능한 채용 근거를 만들 수 있어야 한다고 생각합니다.
          <br />
          실시간 라이브 코딩과 협업형 인터뷰 환경을 통해 문제 해결 흐름과 커뮤니케이션을 명확히 기록하고, 
          <br />
          신뢰할 수 있는 리포트를 제공합니다.
        </p>
      </div> 
  

    <section class="team">
      <div class="team-inner">
        <h2>JOBTORY</h2>
        <p class="team-subtitle">우리팀 소개</p>
        <div class="team-grid">
          <article class="team-card">
            <img :src="memberImages[0]" alt="Team member 1" />
            <h3>김규리</h3>
            <p>PM</p>
          </article>
          <article class="team-card">
            <img :src="memberImages[1]" alt="Team member 2" />
            <h3>김준규</h3>
            <p>APM</p>
          </article>
          <article class="team-card">
            <img :src="memberImages[2]" alt="Team member 3" />
            <h3>김민주</h3>
            <p>팀원</p>
          </article>
          <article class="team-card">
            <img :src="memberImages[3]" alt="Team member 4" />
            <h3>손주영</h3>
            <p>팀원</p>
          </article>
          <article class="team-card">
            <img :src="memberImages[4]" alt="Team member 5" />
            <h3>정동석</h3>
            <p>팀원</p>
          </article>
          <article class="team-card">
            <img :src="memberImages[5]" alt="Team member 6" />
            <h3>채린</h3>
            <p>팀원</p>
          </article>
        </div>
      </div>
    </section>

  </section>
  </div>
</template>

<script setup>
import { useRouter } from "vue-router";

const router = useRouter();
const goBack = () => {
  router.back();
};

const memberImages = [
  new URL("../assets/김규리.png", import.meta.url).href,
  new URL("../assets/김준규.png", import.meta.url).href,
  new URL("../assets/김민주.png", import.meta.url).href,
  new URL("../assets/손주영.png", import.meta.url).href,
  new URL("../assets/정동석.jpg", import.meta.url).href,
  new URL("../assets/채린.png", import.meta.url).href,
];
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap");
@import url("https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&display=swap");

.aboutus {
  min-height: 100vh;
  background: #f6f4ef;
  font-family: "SF Pro", sans-serif;
  color: #111827;
  position: relative;
}

.back-button {
  position: absolute;
  top: 24px;
  left: 24px;
  z-index: 10;
  width: 42px;
  height: 42px;
  padding: 0;
  border-radius: 12px;
  border: none;
  background: transparent;
  color: #ffffff;
  cursor: pointer;
  box-shadow: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.back-button:hover {
  background: rgba(17, 24, 39, 0.08);
}

.back-icon {
  width: 24px;
  height: 20px;
  display: block;
}

.hero {
  position: relative;
  background: #caa3b1;
  min-height: 530px;
  display: grid;
  place-content: center;
}

.hero-overlay {
  text-align: center;
  gap: 0;
  font-family: "Inter", sans-serif;
  font-style: normal;
  font-weight: 900;
  font-size: 90px;
  color: #111827;
}

.hero-overlay p {
  margin: 0;
}

.manifesto {
  background: #f6f4ef;
  padding: 56px 24px 64px;
}

.manifesto-inner {
  max-width: 840px;
  margin: 0 auto;
  text-align: center;
}

.manifesto-inner h1 {
  margin: 0 0 12px;
  font-family: "Playfair Display", "Times New Roman", serif;
  font-size: clamp(28px, 3vw, 40px);
  color: #1f2937;
}

.manifesto-subtitle {
  margin: 0 0 20px;
  font-size: 16px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #6b7280;
}

.manifesto-inner p {
  margin: 0 0 18px;
  color: #374151;
  line-height: 1.7;
  font-size: 16px;
}



.team {
  background: #f6f4ef;
  padding: 56px 24px 72px;
}

.team-inner {
  max-width: 980px;
  margin: 0 auto;
  text-align: center;
}

.team-inner h2 {
  margin: 0 0 12px;
  font-size: clamp(28px, 2.6vw, 40px);
  color: #1f2937;
}

.team-subtitle {
  margin: 0 0 28px;
  color: #6b7280;
  font-size: 15px;
}

.team-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(220px, 1fr));
  gap: 20px;
}

.team-card {
  background: #ffffff;
  border-radius: 18px;
  padding: 18px;
  display: grid;
  gap: 12px;
  text-align: left;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

.team-card img {
  width: 100%;
  height: 180px;
  object-fit: cover;
  border-radius: 14px;
  display: block;
}

.team-card h3 {
  margin: 0;
  font-size: 18px;
  color: #111827;
}

.team-card p {
  margin: 0;
  color: #4b5563;
  font-size: 14px;
}

@media (max-width: 900px) {
  .hero {
    min-height: 180px;
  }
}
</style>
