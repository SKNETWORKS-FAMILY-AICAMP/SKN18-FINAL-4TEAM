<template>
  <div class="aboutus">
    <nav class="nav-header">
      <button type="button" class="back-button" @click="goBack" aria-label="뒤로 가기">
        <svg class="back-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="19" y1="12" x2="5" y2="12"></line>
          <polyline points="12 19 5 12 12 5"></polyline>
        </svg>
      </button>
    </nav>

    <header class="hero">
      <div class="marquee-container">
        <div class="marquee-track">
          <span>PROCESS & LOGIC • COMMUNICATION • GROWTH • JOBTORY • </span>
          <span>PROCESS & LOGIC • COMMUNICATION • GROWTH • JOBTORY • </span>
        </div>
        <div class="marquee-track reverse">
          <span>TEAMWORK • VALUE • INSIGHT • DEVELOPER • STORY • </span>
          <span>TEAMWORK • VALUE • INSIGHT • DEVELOPER • STORY • </span>
        </div>
      </div>

      <div class="hero-content fade-in-up">
        <div class="glass-panel">
          <h1 class="hero-title">About Us</h1>
          <div class="hero-line"></div>
          <p class="hero-desc">The story of how we build together.</p>
        </div>
      </div>
      
      <div class="scroll-indicator fade-in-up delay-2">
        <div class="arrow-down"></div>
      </div>
    </header>

    <section class="manifesto fade-in-up delay-1">
      <div class="manifesto-inner">
        <h2 class="manifesto-title">
          우리는 당신의 '결과'보다<br />
          <span class="highlight">'과정'에 담긴 가치</span>를 믿습니다.
        </h2>
        <div class="manifesto-text">
          <p>
            단순히 정답을 맞히는 코딩 테스트는 <br class="mobile-break"/>
            한 사람의 진면목을 보여주기에 부족합니다.
          </p>
          <p>
            JOBTORY는 코드가 작성되는 찰나의 고민, <br />
            문제를 해결해 나가는 <strong>논리적인 흐름</strong>, <br />
            그리고 동료와 나누는 <strong>유연한 소통</strong>에 집중합니다.
          </p>
          <p>
            누구나 설득 가능한 채용 근거를 만들 수 있어야 합니다.<br />
            실시간 라이브 코딩과 협업형 인터뷰 환경을 통해 <br />
            당신의 진짜 실력을 증명하세요.
          </p>
        </div>
      </div>
    </section>

    <section class="team fade-in-up delay-2">
      <div class="team-inner">
        <div class="section-header">
          <span class="sub-label">THE CREW</span>
          <h2>Meet the Builders</h2>
        </div>
        
        <div class="team-grid">
          <article v-for="(member, index) in members" :key="index" class="id-card">
            <div class="card-hole"></div>
            
            <div class="image-area">
              <img :src="member.img" :alt="member.name" loading="lazy" />
              <div class="id-badge">JOBTORY</div>
            </div>
            
            <div class="info-area">
              <h3>{{ member.name }}</h3>
              <p class="role">{{ member.role }}</p>
              <div class="barcode"></div> </div>
          </article>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { useRouter } from "vue-router";

const router = useRouter();
const goBack = () => {
  router.back();
};

const members = [
  { name: "김규리", role: "Project Manager", img: new URL("../assets/김규리.png", import.meta.url).href },
  { name: "김준규", role: "Assoc. PM", img: new URL("../assets/김준규.png", import.meta.url).href },
  { name: "김민주", role: "Crew", img: new URL("../assets/김민주.png", import.meta.url).href },
  { name: "손주영", role: "Crew", img: new URL("../assets/손주영.png", import.meta.url).href },
  { name: "정동석", role: "Crew", img: new URL("../assets/정동석.jpg", import.meta.url).href },
  { name: "채린", role: "Crew", img: new URL("../assets/채린.png", import.meta.url).href },
];
</script>

<style scoped>
@import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css");
@import url("https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&display=swap");
@import url("https://fonts.googleapis.com/css2?family=Anton&display=swap"); /* 임팩트 있는 폰트 추가 */

:root {
  --bg-color: #f3f4f6;
  --text-primary: #111827;
  --accent-color: #caa3b1;
}

.aboutus {
  min-height: 100vh;
  background-color: var(--bg-color);
  font-family: "Inter", sans-serif;
  color: var(--text-primary);
  overflow-x: hidden;
}

/* Nav */
.nav-header {
  position: absolute;
  top: 0; left: 0; width: 100%;
  padding: 32px;
  z-index: 100;
}
.back-button {
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(0,0,0,0.1);
  width: 48px; height: 48px;
  border-radius: 50%;
  color: #111827;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.3s;
}
.back-button:hover { background: #111827; color: #fff; }
.back-icon { width: 24px; height: 24px; }

/* --- [NEW] Hero Section Style --- */
.hero {
  position: relative;
  height: 70vh;
  min-height: 550px;
  background: #eaddd5;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden; /* 텍스트 넘침 방지 */
}

/* 1. 흐르는 텍스트 배경 (Marquee) */
.marquee-container {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(-5deg); /* 살짝 기울여서 힙하게 */
  width: 120vw;
  display: flex;
  flex-direction: column;
  gap: 20px;
  opacity: 0.08; /* 은은하게 배경으로 */
  pointer-events: none;
  z-index: 0;
}

.marquee-track {
  display: flex;
  white-space: nowrap;
  animation: marquee 40s linear infinite;
  font-family: "Anton", sans-serif; /* 굵고 임팩트 있는 폰트 */
  font-size: 100px;
  color: #111827;
  line-height: 1;
}

.marquee-track.reverse {
  animation-direction: reverse;
}

@keyframes marquee {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}

/* 2. 글래스모피즘 패널 */
.hero-content {
  position: relative;
  z-index: 10;
}

.glass-panel {
  background: rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(12px);
  padding: 60px 80px;
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow: 0 20px 50px rgba(0,0,0,0.05);
  text-align: center;
}

.hero-title {
  font-family: "Playfair Display", serif;
  font-size: clamp(50px, 6vw, 90px);
  margin: 0;
  line-height: 1;
  color: #1f2937;
}

.hero-line {
  width: 40px;
  height: 4px;
  background: #1f2937;
  margin: 24px auto;
}

.hero-desc {
  font-size: 18px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  font-weight: 500;
  margin: 0;
  color: #4b5563;
}

/* 스크롤 화살표 */
.scroll-indicator {
  position: absolute;
  bottom: 40px;
  animation: bounce 2s infinite;
}
.arrow-down {
  width: 20px; height: 20px;
  border-bottom: 2px solid #1f2937;
  border-right: 2px solid #1f2937;
  transform: rotate(45deg);
}
@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {transform: translateY(0) rotate(45deg);}
  40% {transform: translateY(-10px) rotate(45deg);}
  60% {transform: translateY(-5px) rotate(45deg);}
}

/* Manifesto Section */
.manifesto {
  padding: 120px 24px;
  background: #ffffff;
  position: relative;
  z-index: 2;
}
.manifesto-inner {
  max-width: 760px;
  margin: 0 auto;
  text-align: center;
}
.manifesto-title {
  font-family: "Playfair Display", serif;
  font-size: 36px;
  line-height: 1.5;
  margin-bottom: 50px;
  color: #1f2937;
}
.highlight {
  background: linear-gradient(to top, rgba(202, 163, 177, 0.5) 40%, transparent 40%);
}
.manifesto-text p {
  font-size: 18px;
  line-height: 1.8;
  color: #4b5563;
  margin-bottom: 24px;
}
.manifesto-text strong { color: #111827; }

/* --- [NEW] Team Section (ID Card Style) --- */
.team {
  padding: 100px 24px 150px;
  background: #f3f4f6;
}
.team-inner { max-width: 1000px; margin: 0 auto; }

.section-header { text-align: center; margin-bottom: 70px; }
.sub-label {
  font-size: 12px; font-weight: 800; letter-spacing: 0.2em;
  color: #9ca3af; margin-bottom: 12px; display: block;
}
.section-header h2 {
  font-family: "Playfair Display", serif;
  font-size: 48px; color: #111827; margin: 0;
}

.team-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 40px;
}

/* 사원증 카드 스타일 */
.id-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 24px;
  text-align: center;
  box-shadow: 0 10px 30px rgba(0,0,0,0.05);
  position: relative;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  border: 1px solid #e5e7eb;
}

.id-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 20px 40px rgba(0,0,0,0.1);
  border-color: #caa3b1;
}

/* 상단 구멍 */
.card-hole {
  width: 60px; height: 6px;
  background: #e5e7eb;
  border-radius: 4px;
  margin: 0 auto 20px;
}

.image-area {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 20px;
  background: #f9fafb;
}

.image-area img {
  width: 100%; height: 100%; object-fit: cover;
  transition: transform 0.5s;
}
.id-card:hover img { transform: scale(1.05); }

.id-badge {
  position: absolute;
  bottom: 0; left: 0; width: 100%;
  background: rgba(17, 24, 39, 0.8);
  color: #fff;
  font-size: 10px; font-weight: 700;
  padding: 6px 0;
  letter-spacing: 0.1em;
}

.info-area h3 {
  font-family: "Playfair Display", serif;
  font-size: 20px;
  margin: 0 0 6px;
  color: #111827;
}

.info-area .role {
  font-size: 13px;
  color: #6b7280;
  font-weight: 600;
  text-transform: uppercase;
  margin-bottom: 16px;
  letter-spacing: 0.05em;
}

/* 장식용 바코드 */
.barcode {
  height: 24px;
  width: 80%;
  margin: 0 auto;
  background-image: linear-gradient(90deg, 
    #000 0%, #000 4%, transparent 4%, transparent 6%, 
    #000 6%, #000 12%, transparent 12%, transparent 14%,
    #000 14%, #000 20%, transparent 20%, transparent 24%,
    #000 24%, #000 30%, transparent 30%, transparent 32%,
    #000 32%, #000 60%, transparent 60%, transparent 64%,
    #000 64%, #000 68%, transparent 68%, transparent 72%,
    #000 72%, #000 80%, transparent 80%, transparent 84%,
    #000 84%, #000 100%
  );
  opacity: 0.2;
}

/* Animations */
.fade-in-up { opacity: 0; animation: fadeInUp 0.8s ease-out forwards; }
.delay-1 { animation-delay: 0.2s; }
.delay-2 { animation-delay: 0.4s; }
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 900px) {
  .team-grid { grid-template-columns: repeat(2, 1fr); }
  .marquee-track { font-size: 60px; }
  .glass-panel { padding: 40px 20px; width: 90%; }
}
@media (max-width: 600px) {
  .team-grid { grid-template-columns: 1fr; }
  .hero { height: 60vh; }
}
</style>