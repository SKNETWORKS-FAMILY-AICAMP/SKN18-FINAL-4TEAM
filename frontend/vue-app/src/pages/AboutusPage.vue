<template>
  <div class="aboutus">
    <section class="hero">
      <div class="hero-grid">
        <div class="hero-panel">
          <img :src="heroLeft" alt="Live interview" />
        </div>
        <div class="hero-panel">
          <img :src="heroCenter" alt="Team collaboration" />
        </div>
        <div class="hero-panel">
          <img :src="heroRight" alt="Feedback review" />
        </div>
      </div>
      <div class="hero-overlay">
        <p>Build Well.</p>
        <p>Effortless.</p>
        <p>Conscious. Clear.</p>
      </div>
    </section>

    <section class="manifesto">
      <div class="manifesto-inner">
        <h1>Our JOBTORY Philosophy</h1>
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
          JOBTORY는 누구나 설득 가능한 채용 근거를 만들 수 있어야 한다고 믿습니다.
          <br />
          실시간 라이브 코딩과 협업형 인터뷰 환경을 통해 문제 해결 흐름과 커뮤니케이션을 명확히 기록하고, 
          <br />
          신뢰할 수 있는 리포트를 제공합니다.
        </p>
      </div> 
    </section>
  </div>
</template>

<script setup>
const heroLeft = new URL("../assets/aboutus1.png", import.meta.url).href;
const heroCenter = new URL("../assets/aboutus2.png", import.meta.url).href;
const heroRight = new URL("../assets/aboutus3.png", import.meta.url).href;
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap");
@import url("https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&display=swap");

.aboutus {
  min-height: 100vh;
  background: #f6efe8;
  font-family: "SF Pro", sans-serif;
  color: #111827;
}

.hero {
  position: relative;
  background: #bfbfbf;
  overflow: hidden;
}

.hero-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  min-height: 380px;
}

.hero-panel {
  position: relative;
  overflow: hidden;
}

.hero-panel img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.hero-overlay {
  position: absolute;
  inset: 0;
  display: grid;
  place-content: center;
  text-align: center;
  gap: 12px;
  font-family: "Playfair Display", "Times New Roman", serif;
  font-size: clamp(26px, 3.4vw, 44px);
  color: #ffffff;
  text-shadow: 0 12px 30px rgba(0, 0, 0, 0.35);
  background: rgba(0, 0, 0, 0.18);
}

.hero-overlay p {
  margin: 0;
}

.manifesto {
  background: #f6ded2;
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

@media (max-width: 900px) {
  .hero-grid {
    grid-template-columns: 1fr;
  }

  .hero-panel {
    min-height: 220px;
  }
}
</style>
