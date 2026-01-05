<template>
  <div class="aboutus">
    <nav class="nav-header">
      <RouterLink to="/" class="brand">JOBTORY</RouterLink>
    </nav>

    <div class="scroll-container">
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
            <h1 class="hero-title">About us</h1>
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
                
                <div class="qr-section">
                  <div class="qr-divider"></div>
                  <div class="qr-wrapper">
                    <img 
                      :src="`https://api.qrserver.com/v1/create-qr-code/?size=150x150&color=111827&data=${member.github}`" 
                      alt="GitHub QR" 
                      class="qr-code"
                    />
                    <span class="qr-label">GITHUB SCAN</span>
                  </div>
                </div>
                
              </div>
            </article>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { useRouter, RouterLink } from "vue-router";

const router = useRouter();

const members = [
  { name: "김규리", role: "Project Manager", img: new URL("../assets/김규리.png", import.meta.url).href, github: "https://github.com/GyuriKimm" },
  { name: "김준규", role: "Assoc. PM", img: new URL("../assets/김준규.png", import.meta.url).href, github: "https://github.com/JungyuOO" },
  { name: "김민주", role: "Crew", img: new URL("../assets/김민주.png", import.meta.url).href, github: "https://github.com/kmjj0801" },
  { name: "손주영", role: "Crew", img: new URL("../assets/손주영.png", import.meta.url).href, github: "https://github.com/sonjuyeong00" },
  { name: "정동석", role: "Crew", img: new URL("../assets/정동석.jpg", import.meta.url).href, github: "https://github.com/dsj-1004" },
  { name: "채린", role: "Crew", img: new URL("../assets/채린.png", import.meta.url).href, github: "https://github.com/cofls99" },
];
</script>

<style scoped>
@import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css");
@import url("https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&display=swap");
@import url("https://fonts.googleapis.com/css2?family=Anton&display=swap");
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;900&display=swap");

:root {
  --bg-color: #f3f4f6;
  --text-primary: #111827;
  --accent-color: #caa3b1;
}

/* 1. 전체 레이아웃 (화면 고정) */
.aboutus {
  position: relative;
  width: 100vw;
  height: 100vh;
  background-color: var(--bg-color);
  font-family: "Inter", sans-serif;
  color: var(--text-primary);
  overflow: hidden; /* 바깥쪽 스크롤 차단 */
}

/* 2. 네비게이션 (고정) */
.nav-header {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  padding: 32px 40px;
  z-index: 100;
  display: flex;
  align-items: center;
}

.brand {
  font-family: "Inter", sans-serif;
  font-size: 24px;
  font-weight: 900;
  color: #111827;
  text-decoration: none;
  letter-spacing: -0.02em;
  cursor: pointer;
}

/* 3. 내부 스크롤 컨테이너 (스크롤바 숨김) */
.scroll-container {
  width: 100%;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  
  /* Firefox */
  scrollbar-width: none;
  /* IE, Edge */
  -ms-overflow-style: none;
}

/* Chrome, Safari */
.scroll-container::-webkit-scrollbar {
  display: none;
}

/* Hero Section */
.hero {
  position: relative;
  height: 100vh; /* 화면 꽉 채우기 */
  min-height: 550px;
  background: #f8f4eb;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

/* Marquee */
.marquee-container {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(-5deg);
  width: 120vw;
  display: flex;
  flex-direction: column;
  gap: 20px;
  opacity: 0.08;
  pointer-events: none;
  z-index: 0;
}

.marquee-track {
  display: flex;
  white-space: nowrap;
  animation: marquee 40s linear infinite;
  font-family: "Anton", sans-serif;
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

/* Glass Panel */
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
  font-family: "SF Pro", sans-serif, Inter;
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

/* Scroll Arrow */
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
  font-family: "Inter", sans-serif;
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

/* Team Section */
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
  font-family: "Inter", sans-serif;
  font-size: 48px; color: #111827; margin: 0;
}

.team-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 40px;
}

/* ID Card Style */
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
}

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
  font-family: "Inter", sans-serif;
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

/* QR Code Styles */
.qr-section {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.qr-divider {
  width: 100%;
  height: 1px;
  background: #e5e7eb;
  margin-bottom: 16px;
  border-bottom: 1px dashed #d1d5db; 
}

.qr-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.qr-code {
  width: 70px;
  height: 70px;
  mix-blend-mode: multiply; 
  opacity: 0.9;
  transition: transform 0.3s;
}

.id-card:hover .qr-code {
  transform: scale(1.1);
}

.qr-label {
  font-size: 10px;
  font-weight: 800;
  color: #9ca3af;
  letter-spacing: 0.15em;
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
@media (max-width: 768px) {
  .nav-header { padding: 20px; justify-content: center; }
}
@media (max-width: 600px) {
  .team-grid { grid-template-columns: 1fr; }
  .hero { height: 100vh; }
}
</style>