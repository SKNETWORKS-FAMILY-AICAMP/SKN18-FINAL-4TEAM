<template>
  <div class="page">
    <main class="panel">
      <section class="header">
        <p class="eyebrow">Behavioral Interview</p>
        <h1>실전 면접 세션</h1>
        <p class="subtitle">
          STT, 시선 추적, 표정 분석을 활용해 지원자의 커뮤니케이션과 태도를
          정량적으로 평가하는 공간입니다.
        </p>
      </section>

      <section class="grid">
        <div class="card">
          <h2>질문 흐름</h2>
          <ul class="list">
            <li>Ice-breaking · 자기소개</li>
            <li>경험 기반 행동 질문 4~5개</li>
            <li>후속 질문 및 꼬리 질문</li>
          </ul>
        </div>
        <div class="card">
          <h2>분석 요소</h2>
          <ul class="list">
            <li>음성 톤 · 속도 · 일관성</li>
            <li>시선 및 표정 안정성</li>
            <li>콘텐츠 구조화 및 명확성</li>
          </ul>
        </div>
        <div class="card full">
          <h2>결과 리포트</h2>
          <p class="body">
            답변 전사, 요약, 핵심 키워드와 함께 행동 역량(커뮤니케이션, 협업,
            문제 해결 등)에 대한 점수와 코멘트를 제공합니다.
          </p>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap");

.page {
  min-height: 100vh;
  margin: 0;
  padding: 56px 24px;
  display: flex;
  justify-content: center;
  align-items: center;
  background: radial-gradient(circle at 0% 100%, #fee2e2 0, #fef3c7 25%, #d9e9d0 55%, #b9d6b1 100%);
  background-size: 180% 180%;
  animation: interviewWave 9s ease-in-out infinite alternate;
  font-family: "Nunito", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #111827;
}

@keyframes interviewWave {
  0% {
    background-position: 0% 100%;
  }
  50% {
    background-position: 40% 60%;
  }
  100% {
    background-position: 80% 20%;
  }
}

.panel {
  width: min(1040px, 100%);
  background: rgba(255, 255, 255, 0.96);
  border-radius: 24px;
  padding: 32px 32px 26px;
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.25);
}

.header {
  margin-bottom: 24px;
}

.eyebrow {
  margin: 0 0 4px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #e15959;
}

h1 {
  margin: 0 0 10px;
  font-size: 28px;
  color: #1f2937;
}

.subtitle {
  margin: 0;
  color: #4b5563;
  line-height: 1.5;
}

.grid {
  margin-top: 20px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.card {
  background: #f9fafb;
  border-radius: 18px;
  padding: 16px 18px 18px;
  border: 1px solid #e5e7eb;
}

.card.full {
  grid-column: 1 / -1;
}

h2 {
  margin: 0 0 10px;
  font-size: 17px;
}

.list {
  margin: 0;
  padding-left: 18px;
  color: #4b5563;
  font-size: 14px;
  line-height: 1.6;
}

.body {
  margin: 0;
  color: #4b5563;
  font-size: 14px;
  line-height: 1.6;
}

@media (max-width: 800px) {
  .panel {
    padding: 24px 20px 22px;
  }

  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
