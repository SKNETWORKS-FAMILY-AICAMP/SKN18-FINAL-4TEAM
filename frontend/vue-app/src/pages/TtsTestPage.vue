<template>
  <div class="page-root">
    <header class="page-header">
      <h1>TTS Test Page</h1>
      <p>백엔드 /api/interview/ask/ 엔드포인트 테스트용 임시 페이지입니다.</p>
      <RouterLink class="back-link" to="/coding-test">
        ← 라이브 코딩 설정 페이지로 돌아가기
      </RouterLink>
    </header>

    <section class="tester-card">
      <h2 class="card-title">🎤 인터뷰 TTS 테스트</h2>

      <label class="field-label">질문</label>
      <textarea
        v-model="question"
        class="question-input"
        rows="4"
        placeholder="질문을 입력한 뒤 [질문 보내기]를 눌러보세요."
      />

      <button
        class="send-button"
        :disabled="loading || !question.trim()"
        @click="sendQuestion"
      >
        {{ loading ? "생성 중..." : "질문 보내기" }}
      </button>

      <p v-if="error" class="error-text">{{ error }}</p>

      <div v-if="answer" class="answer-box">
        <h3>LLM 답변 전체</h3>
        <p>{{ answer }}</p>
      </div>

      <div v-if="sentences.length" class="audio-list">
        <h3>문장별 오디오</h3>
        <div
          v-for="(s, idx) in sentences"
          :key="idx"
          class="audio-item"
        >
          <p class="sentence-text">
            {{ idx + 1 }}. {{ s.text }}
          </p>
          <audio
            controls
            :src="`data:audio/mp3;base64,${s.audio}`"
          />
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { RouterLink } from "vue-router";

const question = ref("DFS와 BFS의 차이를 설명해주세요.");
const loading = ref(false);
const error = ref("");
const answer = ref("");
const sentences = ref([]);

// 백엔드 주소 (같은 도메인에서 프록시 쓰면 '/api/interview/ask/' 만 써도 됨)
const API_URL = "http://localhost:8000/api/interview/ask/";

const sendQuestion = async () => {
  error.value = "";
  answer.value = "";
  sentences.value = [];
  loading.value = true;

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: question.value })
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.error || `HTTP ${res.status}`);
    }

    const data = await res.json();

    answer.value = data.answer || "";
    sentences.value = data.sentences || [];
  } catch (e) {
    console.error(e);
    error.value = e.message || "요청 중 오류가 발생했습니다.";
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.page-root {
  max-width: 900px;
  margin: 0 auto;
  padding: 32px 16px 64px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 4px;
}

.page-header p {
  font-size: 14px;
  color: #555;
  margin-bottom: 8px;
}

.back-link {
  font-size: 13px;
  color: #007bff;
  text-decoration: none;
}

.back-link:hover {
  text-decoration: underline;
}

.tester-card {
  border-radius: 16px;
  border: 1px solid #e2e2e2;
  padding: 20px 18px;
  background: #fafafa;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
}

.field-label {
  font-size: 13px;
  font-weight: 500;
}

.question-input {
  width: 100%;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid #ccc;
  resize: vertical;
  font-size: 14px;
}

.send-button {
  align-self: flex-start;
  margin-top: 4px;
  padding: 6px 14px;
  border-radius: 999px;
  border: none;
  background: #222;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
}

.send-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-text {
  color: #d00;
  font-size: 13px;
}

.answer-box {
  margin-top: 8px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid #eee;
  font-size: 14px;
}

.audio-list {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.audio-item {
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid #eee;
  background: #fff;
}

.sentence-text {
  font-size: 13px;
  margin-bottom: 4px;
}
</style>
