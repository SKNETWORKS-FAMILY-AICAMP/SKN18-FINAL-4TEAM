<template>
  <div class="chat-page">
    <header class="chat-header">
      <div>
        <p class="eyebrow">JobTory Chatbot</p>
        <h1>AI 챗봇과 대화해 보세요</h1>
        <p class="subtitle">연습 질문, 코드 힌트, 면접 답변을 빠르게 물어볼 수 있어요.</p>
      </div>
      <button type="button" class="new-chat-button" @click="startNewChat">
        + 새 채팅
      </button>
    </header>

    <div class="chat-layout">
      <!-- Sidebar -->
      <aside class="chat-sidebar">
        <div class="sidebar-header">
          <h3>대화 목록</h3>
          <span class="badge">{{ conversations.length }}</span>
        </div>

        <div class="chat-list" v-if="conversations.length">
          <button
            v-for="conv in conversations"
            :key="conv.id"
            type="button"
            class="chat-list-item"
            :class="{ active: conv.id === selectedConversationId }"
            @click="selectConversation(conv.id)"
          >
            <div class="chat-list-row">
              <div class="chat-list-title">{{ conv.title }}</div>
              <button
                type="button"
                class="chat-delete-button"
                @click.stop="removeConversation(conv.id)"
              >
                삭제
              </button>
            </div>
            <div class="chat-list-meta">
              <span class="chat-list-updated">{{ formatRelativeTime(conv.updatedAt) }}</span>
              <span class="chat-list-last">{{ conv.lastMessage }}</span>
            </div>
          </button>
        </div>

        <div class="empty-state" v-else>
          <p>아직 대화가 없습니다.</p>
          <p class="hint">새 채팅을 시작해 보세요.</p>
        </div>
      </aside>

      <!-- Chat -->
      <section class="chat-main">
        <div class="message-area" ref="messageAreaRef">
          <div v-if="!currentMessages.length" class="empty-chat">
            <p>메시지가 없습니다.</p>
            <p class="hint">아래 입력창에서 첫 메시지를 보내보세요.</p>
          </div>

          <div
            v-for="(msg, idx) in currentMessages"
            :key="idx"
            class="message-row"
            :class="msg.from === 'user' ? 'from-user' : 'from-bot'"
          >
            <div class="avatar" :aria-label="msg.from === 'user' ? '나' : '봇'">
              {{ msg.from === "user" ? "나" : "봇" }}
            </div>
            <div class="bubble" :class="{ 'plan-bubble': !!msg.plan }">
              <template v-if="msg.plan && (msg.plan.items?.length || 0) > 0">
                <div class="plan-bubble-head">
                  <span class="plan-badge">DeepAgent</span>
                  <div class="plan-head-text">
                    <div class="plan-title">{{ msg.plan.plan_title || "추천 로드맵" }}</div>
                    <div v-if="msg.plan.plan_subtitle" class="plan-subtitle">
                      {{ msg.plan.plan_subtitle }}
                    </div>
                  </div>
                </div>

                <div class="plan-card-stack">
                  <div
                    v-for="(it, idx) in msg.plan.items"
                    :key="it.id || idx"
                    class="roadmap-card compact"
                  >
                    <div class="card-top">
                      <div class="card-index">{{ idx + 1 }}</div>
                      <div class="card-main">
                        <div class="card-title-row">
                          <h4 class="card-title">{{ it.title }}</h4>
                          <span class="card-minutes">⏱ {{ it.minutes }}분</span>
                        </div>
                        <p class="card-why">{{ it.why }}</p>
                      </div>
                    </div>

                    <div class="card-section" v-if="(it.success_criteria?.length || 0) > 0">
                      <div class="section-label">완료 기준</div>
                      <ul class="criteria-list">
                        <li v-for="(c, i) in it.success_criteria" :key="i">
                          {{ c }}
                        </li>
                      </ul>
                    </div>

                    <div class="card-actions">
                      <button type="button" class="chip" @click="markPlan(msg.plan, it.id, 'done')">
                        완료
                      </button>
                      <button type="button" class="chip" @click="markPlan(msg.plan, it.id, 'blocked')">
                        막힘
                      </button>
                      <button
                        type="button"
                        class="chip"
                        @click="markPlan(msg.plan, it.id, 'alternative')"
                      >
                        대체
                      </button>
                      <button
                        type="button"
                        class="chip"
                        @click="markPlan(msg.plan, it.id, 'reduce_time')"
                      >
                        시간 줄이기
                      </button>
                    </div>

                    <div v-if="it.status && it.status !== 'todo'" class="card-status">
                      <span class="status-pill">상태: {{ it.status }}</span>
                      <span v-if="it.last_action" class="status-pill subtle">
                        최근: {{ it.last_action }}
                      </span>
                    </div>

                    <div v-if="it.status === 'blocked'" class="card-hint">
                      <div class="section-label">힌트</div>
                      <p class="hint-text">{{ it.actions?.blocked?.hint || "힌트가 없습니다." }}</p>
                    </div>

                    <div
                      v-if="it.status === 'blocked' && (it.actions?.blocked?.alternatives?.length || 0) > 0"
                      class="card-alt"
                    >
                      <div class="section-label">대체 루트</div>
                      <ul class="criteria-list">
                        <li v-for="(a, i) in it.actions.blocked.alternatives" :key="i">
                          {{ a.title }} ({{ a.minutes }}분)
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>
              </template>

              <template v-else>
                <div class="bubble-text">{{ msg.text }}</div>
              </template>

              <div class="bubble-meta">{{ msg.timestamp }}</div>
            </div>
          </div>
        </div>

        <form class="composer" @submit.prevent="handleSend">
          <textarea
            v-model="inputText"
            placeholder="메시지를 입력하세요 (Shift+Enter 줄바꿈)"
            rows="2"
            @keydown.enter.exact.prevent="handleSend"
          ></textarea>
          <div class="composer-actions">
            <button
              type="button"
              class="ghost-button"
              :disabled="roadmapLoading || !currentConversation"
              @click="loadTodayRoadmap"
              title="오늘 로드맵 불러오기"
            >
              {{ roadmapLoading ? "로드맵 불러오는 중..." : "로드맵 불러오기" }}
            </button>
            <button
              type="submit"
              class="send-button"
              :disabled="!inputText.trim() || isSending"
            >
              {{ isSending ? "전송 중..." : "보내기" }}
            </button>
          </div>
        </form>
      </section>

      <!-- Roadmap Panel -->
      <aside class="roadmap-panel">
        <div class="roadmap-head">
          <div class="roadmap-title-wrap">
            <p class="roadmap-eyebrow">Roadmap</p>
            <h3 class="roadmap-title">오늘의 성장 로드맵</h3>
            <p class="roadmap-subtitle">
              {{ roadmapPlan?.plan_title || "오늘 로드맵을 불러오거나 생성해 보세요." }}
            </p>
          </div>

          <div class="roadmap-head-actions">
            <button
              type="button"
              class="roadmap-btn"
              :disabled="roadmapLoading || !currentConversation"
              @click="loadTodayRoadmap"
            >
              {{ roadmapLoading ? "불러오는 중..." : "불러오기" }}
            </button>
            <button
              type="button"
              class="roadmap-btn primary"
              :disabled="roadmapLoading || !currentConversation"
              @click="generateRoadmap"
            >
              새로 만들기
            </button>
          </div>
        </div>

        <div class="roadmap-body">
          <div v-if="roadmapError" class="roadmap-error">
            {{ roadmapError }}
          </div>

          <div v-if="!roadmapPlan && !roadmapLoading" class="roadmap-empty">
            <p>오른쪽 패널은 “진짜 기능”처럼 보이게 로드맵을 카드로 보여줍니다.</p>
            <p class="hint">먼저 “불러오기” 또는 “새로 만들기”를 눌러보세요.</p>
          </div>

          <div v-if="roadmapPlan" class="roadmap-content">
            <div class="roadmap-meta">
              <span class="pill">목표 <b>{{ roadmapPlan.profile?.goal || "-" }}</b></span>
              <span class="pill">언어 <b>{{ roadmapPlan.profile?.main_lang || "-" }}</b></span>
              <span class="pill">시간 <b>{{ roadmapPlan.profile?.daily_minutes ?? "-" }}분</b></span>
            </div>

            <div class="roadmap-cards">
              <div
                v-for="(it, idx) in roadmapPlan.items || []"
                :key="it.id"
                class="roadmap-card"
              >
                <div class="card-top">
                  <div class="card-index">{{ idx + 1 }}</div>
                  <div class="card-main">
                    <div class="card-title-row">
                      <h4 class="card-title">{{ it.title }}</h4>
                      <span class="card-minutes">⏱ {{ it.minutes }}분</span>
                    </div>
                    <p class="card-why">{{ it.why }}</p>
                  </div>
                </div>

                <div class="card-section">
                  <div class="section-label">완료 기준</div>
                  <ul class="criteria-list">
                    <li v-for="(c, i) in it.success_criteria || []" :key="i">
                      {{ c }}
                    </li>
                  </ul>
                </div>

                <div class="card-actions">
                  <button type="button" class="chip" @click="markLocal(it.id, 'done')">완료</button>
                  <button type="button" class="chip" @click="markLocal(it.id, 'blocked')">막힘</button>
                  <button type="button" class="chip" @click="markLocal(it.id, 'alternative')">대체</button>
                  <button type="button" class="chip" @click="markLocal(it.id, 'reduce_time')">시간 줄이기</button>
                </div>

                <div v-if="it.status && it.status !== 'todo'" class="card-status">
                  <span class="status-pill">상태: {{ it.status }}</span>
                  <span v-if="it.last_action" class="status-pill subtle">최근: {{ it.last_action }}</span>
                </div>

                <div v-if="it.status === 'blocked'" class="card-hint">
                  <div class="section-label">힌트</div>
                  <p class="hint-text">{{ it.actions?.blocked?.hint || "힌트가 없습니다." }}</p>
                </div>

                <div
                  v-if="it.status === 'blocked' && (it.actions?.blocked?.alternatives?.length || 0) > 0"
                  class="card-alt"
                >
                  <div class="section-label">대체 루트</div>
                  <ul class="criteria-list">
                    <li v-for="(a, i) in it.actions.blocked.alternatives" :key="i">
                      {{ a.title }} ({{ a.minutes }}분)
                    </li>
                  </ul>
                </div>
              </div>
            </div>

            <div class="roadmap-footnote">
              <p class="hint">
                ※ 지금 버튼은 “로컬 UI 반영”만 합니다. 다음 단계로 /api/plan/action 붙이면 Redis에도 상태 저장됩니다.
              </p>
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { useAuth } from "../hooks/useAuth";

const STORAGE_KEY = "jobtory-chatbot-conversations";
const auth = useAuth();

const nowTick = ref(Date.now());
let relativeTimer = null;

const conversations = ref(loadConversations());
const selectedConversationId = ref(conversations.value[0]?.id || null);

const inputText = ref("");
const isSending = ref(false);
const messageAreaRef = ref(null);

// ✅ Roadmap state
const roadmapPlan = ref(null);
const roadmapLoading = ref(false);
const roadmapError = ref("");

function newCommunicationId() {
  return `coach-${crypto.randomUUID?.() || `${Date.now()}-${Math.random()}`}`;
}

function reviveConversation(conv) {
  const updatedAt = conv.updatedAt ? new Date(conv.updatedAt) : new Date();
  return {
    ...conv,
    updatedAt,
    communicationId: conv.communicationId || newCommunicationId(),
  };
}

function getDefaultConversations() {
  const now = new Date();
  return [
    {
      id: "welcome",
      communicationId: newCommunicationId(),
      title: "온보딩 가이드",
      lastMessage: "무엇을 도와드릴까요?",
      updatedAt: now,
      messages: [
        {
          from: "bot",
          text: "안녕하세요! JobTory 챗봇입니다. 무엇을 도와드릴까요?",
          timestamp: formatTime(now),
        },
      ],
    },
  ];
}

function loadConversations() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved);
      if (Array.isArray(parsed) && parsed.length) {
        return parsed.map(reviveConversation);
      }
      return getDefaultConversations();
    }
  } catch (err) {
    console.warn("대화 내역을 불러올 수 없습니다.", err);
  }
  return getDefaultConversations();
}

function persistConversations() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations.value));
  } catch (err) {
    console.warn("대화 내역을 저장하지 못했습니다.", err);
  }
}

function deriveTitle(text) {
  const trimmed = text.trim();
  if (!trimmed) return "새 채팅";
  return trimmed.length > 24 ? `${trimmed.slice(0, 24)}...` : trimmed;
}

function formatTime(date) {
  const h = String(date.getHours()).padStart(2, "0");
  const m = String(date.getMinutes()).padStart(2, "0");
  return `${h}:${m}`;
}

function formatRelativeTime(dateLike) {
  const d = dateLike instanceof Date ? dateLike : new Date(dateLike);
  if (Number.isNaN(d.getTime())) return "-";
  const diff = nowTick.value - d.getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "방금 전";
  if (minutes < 60) return `${minutes}분 전`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}시간 전`;
  const days = Math.floor(hours / 24);
  return `${days}일 전`;
}

function stripJsonFence(text = "") {
  let trimmed = text.trim();
  if (trimmed.startsWith("```")) {
    trimmed = trimmed.replace(/^```json/i, "").replace(/^```/, "").replace(/```$/, "").trim();
  }
  return trimmed;
}

function isRoadmapLike(obj) {
  return obj && typeof obj === "object" && Array.isArray(obj.items) && obj.items.length > 0;
}

function normalizePlanForUi(plan) {
  if (!isRoadmapLike(plan)) return null;

  const normalized = {
    ...plan,
    plan_title: plan.plan_title || plan.title || "추천 로드맵",
    plan_subtitle: plan.plan_subtitle || plan.subtitle || "",
  };

  const items = Array.isArray(plan.items) ? plan.items : [];
  normalized.items = items.slice(0, 3).map((it, idx) => ({
    id: it.id || `item-${idx + 1}`,
    title: it.title || `할 일 ${idx + 1}`,
    minutes: typeof it.minutes === "number" ? it.minutes : Number(it.minutes) || 0,
    why: it.why || it.reason || "",
    success_criteria: Array.isArray(it.success_criteria) ? it.success_criteria : [],
    actions: it.actions || {},
    status: it.status || "todo",
    last_action: "last_action" in it ? it.last_action : null,
  }));

  return normalized;
}

function tryParsePlanFromText(text) {
  const cleaned = stripJsonFence(text);
  if (!cleaned) return null;

  try {
    const parsed = JSON.parse(cleaned);
    const candidate = isRoadmapLike(parsed) ? parsed : parsed?.plan;
    return normalizePlanForUi(candidate);
  } catch (err) {
    return null;
  }
}

const currentConversation = computed(() =>
  conversations.value.find((c) => c.id === selectedConversationId.value)
);

const currentMessages = computed(() => currentConversation.value?.messages || []);

function selectConversation(id) {
  selectedConversationId.value = id;
  scrollToBottom();
  loadTodayRoadmap();
}

function removeConversation(id) {
  const idx = conversations.value.findIndex((c) => c.id === id);
  if (idx === -1) return;
  const ok = window.confirm("이 채팅을 삭제할까요?");
  if (!ok) return;
  conversations.value.splice(idx, 1);
  if (selectedConversationId.value === id) {
    selectedConversationId.value = conversations.value[0]?.id || null;
  }
  persistConversations();
  loadTodayRoadmap();
}

function startNewChat() {
  const id = `chat-${Date.now()}`;
  const now = new Date();
  const welcome = {
    from: "bot",
    text: "새 채팅을 시작했습니다. 무엇을 도와드릴까요?",
    timestamp: formatTime(now),
  };

  conversations.value.unshift({
    id,
    communicationId: newCommunicationId(),
    title: "새 채팅",
    lastMessage: welcome.text,
    updatedAt: now,
    messages: [welcome],
  });

  selectedConversationId.value = id;
  inputText.value = "";
  scrollToBottom();
  persistConversations();
  loadTodayRoadmap();
}

async function handleSend() {
  const text = inputText.value.trim();
  if (!text || isSending.value) return;

  if (!currentConversation.value) {
    startNewChat();
  }

  if (!auth.isAuthenticated.value) {
    window.alert("로그인이 필요한 서비스입니다. 로그인 후 이용해 주세요.");
    return;
  }

  const valid = await auth.ensureValidSession?.();
  if (!valid) {
    window.alert("로그인 세션이 만료되었습니다. 다시 로그인해 주세요.");
    return;
  }

  isSending.value = true;

  const now = new Date();
  const userMessage = { from: "user", text, timestamp: formatTime(now) };
  const target = currentConversation.value;

  if (!target) {
    isSending.value = false;
    return;
  }

  if (!target.communicationId) {
    target.communicationId = newCommunicationId();
  }

  target.messages.push(userMessage);
  target.lastMessage = text;
  target.updatedAt = now;
  if (!target.title || target.title === "새 채팅") {
    target.title = deriveTitle(text);
  }

  inputText.value = "";
  scrollToBottom();
  persistConversations();

  await nextTick();

  try {
    const resp = await sendToCoach({
      communicationId: target.communicationId,
      message: text,
      mode: "chat",
    });

    const replyText =
      resp?.type === "chat" ? resp.reply : "응답을 받았지만 메시지를 해석하지 못했습니다.";
    const planFromReply =
      (resp?.type === "roadmap" && resp.plan && normalizePlanForUi(resp.plan)) ||
      tryParsePlanFromText(replyText);

    if (planFromReply) {
      const botMessage = {
        from: "bot",
        text: planFromReply.plan_title || "추천 로드맵 제안",
        plan: planFromReply,
        timestamp: formatTime(new Date()),
      };

      roadmapPlan.value = planFromReply;
      target.messages.push(botMessage);
      target.lastMessage = botMessage.text;
      target.updatedAt = new Date();
    } else {
      const botMessage = {
        from: "bot",
        text: replyText,
        timestamp: formatTime(new Date()),
      };

      target.messages.push(botMessage);
      target.lastMessage = replyText;
      target.updatedAt = new Date();

      // 사용자가 로드맵을 요청했을 수도 있으니 갱신
      await loadTodayRoadmap();
    }
  } catch (err) {
    console.error("CoachChat 호출 실패", err);
    const fallback = "답변을 가져오지 못했습니다. 잠시 후 다시 시도해 주세요.";
    const botMessage = {
      from: "bot",
      text: fallback,
      timestamp: formatTime(new Date()),
    };
    target.messages.push(botMessage);
    target.lastMessage = fallback;
    target.updatedAt = new Date();
  } finally {
    isSending.value = false;
    scrollToBottom();
    persistConversations();
  }
}

async function sendToCoach({ communicationId, message, mode }) {
  const resp = await fetch(`${auth.BACKEND_BASE}/api/chatbot/coach/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${auth.token.value}`,
      "X-Communication-Id": communicationId,
    },
    body: JSON.stringify({
      communication_id: communicationId,
      message,
      mode, // ✅ 추가
    }),
  });

  if (!resp.ok) {
    let detail = "";
    try {
      const err = await resp.json();
      detail = err?.detail || err?.error || JSON.stringify(err);
    } catch (e) {}
    throw new Error(`CoachChat API 오류: ${resp.status} ${detail}`);
  }

  const data = await resp.json();

  if (data?.type === "roadmap" && data?.plan) {
    return { type: "roadmap", plan: data.plan, raw: data };
  }

  const reply =
    data?.reply ||
    data?.output ||
    data?.message ||
    (typeof data === "string" ? data : "") ||
    "";

  return { type: "chat", reply, raw: data };
}

async function loadTodayRoadmap() {
  roadmapError.value = "";
  roadmapLoading.value = true;

  try {
    const target = currentConversation.value;
    if (!target) {
      roadmapPlan.value = null;
      return;
    }
    if (!target.communicationId) target.communicationId = newCommunicationId();

    const resp = await sendToCoach({
      communicationId: target.communicationId,
      message: "오늘 로드맵 불러오기",
      mode: "roadmap_today",
    });

    if (resp?.type === "roadmap") roadmapPlan.value = resp.plan;
    else roadmapPlan.value = null;
  } catch (e) {
    roadmapPlan.value = null;
    roadmapError.value = "로드맵을 불러오지 못했습니다.";
    console.error(e);
  } finally {
    roadmapLoading.value = false;
  }
}

async function generateRoadmap() {
  roadmapError.value = "";
  roadmapLoading.value = true;

  try {
    const target = currentConversation.value;
    if (!target) return;
    if (!target.communicationId) target.communicationId = newCommunicationId();

    const resp = await sendToCoach({
      communicationId: target.communicationId,
      message: "오늘 학습 로드맵을 만들어줘. 최대 3개로.",
      mode: "roadmap",
    });

    if (resp?.type === "roadmap") roadmapPlan.value = resp.plan;
    else roadmapPlan.value = null;
  } catch (e) {
    roadmapPlan.value = null;
    roadmapError.value = "로드맵 생성에 실패했습니다.";
    console.error(e);
  } finally {
    roadmapLoading.value = false;
  }
}

/**
 * ✅ 지금은 로컬 표시만 변경 (다음: /api/plan/action 붙이면 Redis에도 반영)
 */
function markPlan(plan, itemId, status) {
  if (!plan?.items) return;
  const it = plan.items.find((x) => x.id === itemId);
  if (!it) return;

  if (status === "done") {
    it.status = "done";
    it.last_action = "complete";
    return;
  }
  if (status === "blocked") {
    it.status = "blocked";
    it.last_action = "blocked";
    return;
  }
  if (status === "alternative") {
    it.last_action = "alternative";
    // status는 유지(또는 todo)
    return;
  }
  if (status === "reduce_time") {
    it.last_action = "reduce_time";
    const reduced = it.actions?.reduce_time?.minutes;
    if (typeof reduced === "number") it.minutes = reduced;
  }
}

function markLocal(itemId, status) {
  markPlan(roadmapPlan.value, itemId, status);
}

function scrollToBottom() {
  nextTick(() => {
    const el = messageAreaRef.value;
    if (el) el.scrollTop = el.scrollHeight;
  });
}

onMounted(async () => {
  scrollToBottom();
  relativeTimer = window.setInterval(() => {
    nowTick.value = Date.now();
  }, 60000);

  await loadTodayRoadmap();
});

onUnmounted(() => {
  if (relativeTimer) {
    clearInterval(relativeTimer);
    relativeTimer = null;
  }
});

watch(
  conversations,
  () => {
    persistConversations();
  },
  { deep: true }
);
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap");

/* ===== 기존 스타일(네가 준 스타일) 그대로 ===== */
.chat-page {
  font-family: "Inter", "Noto Sans KR", system-ui, -apple-system, sans-serif;
  background: #0b1224;
  min-height: 100vh;
  padding: 32px 28px;
  color: #e5ecff;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  gap: 16px;
}

.eyebrow {
  font-size: 13px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #8da2ff;
  margin: 0 0 6px;
  font-weight: 700;
}

.chat-header h1 {
  margin: 0;
  font-size: 28px;
  color: #f7f9ff;
  font-weight: 800;
}

.subtitle {
  margin: 4px 0 0;
  color: #a9b7d9;
  font-size: 14px;
}

.new-chat-button {
  border: none;
  background: linear-gradient(135deg, #4f8bff, #7f7bff);
  color: #fff;
  font-weight: 700;
  padding: 12px 16px;
  border-radius: 12px;
  cursor: pointer;
  box-shadow: 0 12px 30px rgba(79, 139, 255, 0.25);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.new-chat-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 32px rgba(79, 139, 255, 0.35);
}

.chat-layout {
  display: grid;
  grid-template-columns: 280px 1fr 360px; /* ✅ 로드맵 패널 컬럼 추가 */
  gap: 20px;
}

.chat-sidebar {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 16px;
  padding: 16px;
  backdrop-filter: blur(4px);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.35);
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  color: #dce5ff;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
}

.badge {
  background: rgba(127, 123, 255, 0.15);
  color: #cdd6ff;
  border: 1px solid rgba(127, 123, 255, 0.35);
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.chat-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chat-list-item {
  width: 100%;
  text-align: left;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.02);
  color: #dbe6ff;
  padding: 12px;
  border-radius: 12px;
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.chat-list-item.active {
  border-color: rgba(127, 123, 255, 0.6);
  background: rgba(127, 123, 255, 0.1);
}

.chat-list-title {
  font-weight: 700;
  font-size: 14px;
  margin-bottom: 6px;
  color: #f7f9ff;
}

.chat-list-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #a7b6d9;
}

.chat-list-last {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  text-align: right;
}

.chat-list-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.chat-delete-button {
  border: none;
  background: transparent;
  color: #9bb0de;
  font-size: 12px;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 8px;
  transition: background 0.15s ease, color 0.15s ease;
}

.chat-delete-button:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #f5f7ff;
}

.empty-state {
  text-align: center;
  color: #9cb0d9;
  border: 1px dashed rgba(255, 255, 255, 0.2);
  padding: 20px 12px;
  border-radius: 12px;
  margin-top: 10px;
}

.empty-state .hint {
  margin-top: 6px;
  font-size: 13px;
  color: #7f91c2;
}

.chat-main {
  background: #0f182e;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 18px;
  min-height: 70vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.4);
}

.message-area {
  flex: 1;
  padding: 18px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.empty-chat {
  text-align: center;
  color: #96a5c7;
}

.empty-chat .hint {
  margin-top: 4px;
  color: #7f91c2;
}

.message-row {
  display: grid;
  grid-template-columns: 44px 1fr;
  gap: 12px;
  align-items: flex-start;
}

.message-row.from-user .avatar {
  background: #4f8bff;
}

.message-row.from-bot .avatar {
  background: #7f7bff;
}

.avatar {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  color: #fff;
  font-weight: 800;
}

.bubble {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 12px 14px;
  color: #e9f1ff;
}

.from-user .bubble {
  background: rgba(79, 139, 255, 0.15);
  border-color: rgba(79, 139, 255, 0.35);
}

.plan-bubble {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(127, 123, 255, 0.45);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.35);
}

.plan-bubble-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.plan-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 10px;
  background: rgba(127, 123, 255, 0.18);
  border: 1px solid rgba(127, 123, 255, 0.45);
  color: #dfe5ff;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.03em;
}

.plan-head-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.plan-title {
  font-size: 15px;
  font-weight: 800;
  color: #f7f9ff;
}

.plan-subtitle {
  font-size: 12px;
  color: #a9b7d9;
}

.plan-card-stack {
  display: grid;
  gap: 10px;
  margin-top: 6px;
}

.bubble-text {
  white-space: pre-wrap;
  line-height: 1.5;
}

.bubble-meta {
  margin-top: 6px;
  font-size: 12px;
  color: #9eb0d8;
}

.roadmap-card.compact {
  padding: 10px;
  background: rgba(15, 24, 46, 0.8);
  border-color: rgba(127, 123, 255, 0.3);
}

.roadmap-card.compact .card-title {
  font-size: 13px;
}

.roadmap-card.compact .card-why {
  font-size: 12px;
}

.roadmap-card.compact .criteria-list {
  font-size: 12px;
}

.roadmap-card.compact .chip {
  padding: 6px 8px;
  font-size: 11px;
}

.composer {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: rgba(10, 14, 26, 0.9);
  border-radius: 0 0 18px 18px;
}

.composer textarea {
  width: 100%;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  color: #e9f1ff;
  padding: 12px;
  resize: vertical;
  min-height: 80px;
  font-family: inherit;
}

.composer textarea:focus {
  outline: 2px solid rgba(79, 139, 255, 0.5);
}

.composer-actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
}

.ghost-button {
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: transparent;
  color: #dbe6ff;
  border-radius: 10px;
  padding: 10px 12px;
  cursor: pointer;
}

.send-button {
  border: none;
  background: linear-gradient(135deg, #4f8bff, #7f7bff);
  color: #fff;
  font-weight: 700;
  padding: 12px 18px;
  border-radius: 12px;
  cursor: pointer;
  min-width: 110px;
  box-shadow: 0 12px 28px rgba(79, 139, 255, 0.32);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.send-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}

.send-button:not(:disabled):hover {
  transform: translateY(-1px);
  box-shadow: 0 16px 34px rgba(79, 139, 255, 0.4);
}

/* ===== 로드맵 패널 스타일(네 톤에 맞춘 추가) ===== */
.roadmap-panel {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 16px;
  backdrop-filter: blur(4px);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.35);
  display: flex;
  flex-direction: column;
  min-height: 70vh;
  overflow: hidden;
}

.roadmap-head {
  padding: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
  display: grid;
  gap: 12px;
}

.roadmap-eyebrow {
  margin: 0;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #8da2ff;
  font-weight: 800;
}

.roadmap-title {
  margin: 6px 0 0;
  font-size: 18px;
  color: #f7f9ff;
  font-weight: 800;
}

.roadmap-subtitle {
  margin: 6px 0 0;
  font-size: 13px;
  color: #a9b7d9;
}

.roadmap-head-actions {
  display: flex;
  gap: 10px;
}

.roadmap-btn {
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.03);
  color: #dbe6ff;
  border-radius: 12px;
  padding: 10px 12px;
  cursor: pointer;
  font-weight: 700;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.roadmap-btn.primary {
  border: none;
  background: linear-gradient(135deg, #4f8bff, #7f7bff);
  color: #fff;
  box-shadow: 0 12px 28px rgba(79, 139, 255, 0.24);
}

.roadmap-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}

.roadmap-body {
  padding: 16px;
  overflow-y: auto;
  flex: 1;
}

.roadmap-error {
  border: 1px solid rgba(255, 106, 106, 0.35);
  background: rgba(255, 106, 106, 0.08);
  color: #ffd6d6;
  padding: 10px 12px;
  border-radius: 12px;
  margin-bottom: 12px;
  font-size: 13px;
}

.roadmap-empty {
  color: #9cb0d9;
  border: 1px dashed rgba(255, 255, 255, 0.2);
  padding: 18px 12px;
  border-radius: 12px;
}

.roadmap-empty .hint {
  margin-top: 6px;
  font-size: 13px;
  color: #7f91c2;
}

.roadmap-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.pill {
  background: rgba(127, 123, 255, 0.15);
  color: #cdd6ff;
  border: 1px solid rgba(127, 123, 255, 0.35);
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.roadmap-cards {
  display: grid;
  gap: 10px;
}

.roadmap-card {
  border: 1px solid rgba(255, 255, 255, 0.07);
  background: rgba(15, 24, 46, 0.65);
  border-radius: 14px;
  padding: 12px;
}

.card-top {
  display: grid;
  grid-template-columns: 30px 1fr;
  gap: 10px;
  align-items: start;
}

.card-index {
  width: 30px;
  height: 30px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  background: rgba(127, 123, 255, 0.15);
  border: 1px solid rgba(127, 123, 255, 0.35);
  font-weight: 800;
  color: #e5ecff;
}

.card-title-row {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: baseline;
}

.card-title {
  margin: 0;
  font-size: 14px;
  font-weight: 800;
  color: #f7f9ff;
}

.card-minutes {
  font-size: 12px;
  color: #a9b7d9;
  white-space: nowrap;
}

.card-why {
  margin: 6px 0 0;
  color: #a9b7d9;
  font-size: 12px;
  line-height: 1.45;
}

.card-section {
  margin-top: 10px;
}

.section-label {
  font-size: 12px;
  color: #8da2ff;
  font-weight: 800;
  margin-bottom: 6px;
}

.criteria-list {
  margin: 0;
  padding-left: 18px;
  color: #dbe6ff;
  font-size: 12px;
  line-height: 1.5;
}

.card-actions {
  margin-top: 10px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.chip {
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.03);
  color: #dbe6ff;
  border-radius: 999px;
  padding: 8px 10px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 800;
}

.card-status {
  margin-top: 10px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.status-pill {
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.04);
  font-size: 12px;
  font-weight: 800;
  color: #dbe6ff;
}

.status-pill.subtle {
  opacity: 0.75;
}

.card-hint,
.card-alt {
  margin-top: 10px;
  border: 1px solid rgba(255, 255, 255, 0.07);
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  padding: 10px 12px;
}

.hint-text {
  margin: 0;
  font-size: 12px;
  color: #dbe6ff;
  line-height: 1.5;
}

.roadmap-footnote {
  margin-top: 12px;
  color: #7f91c2;
}

/* 반응형 */
@media (max-width: 1200px) {
  .chat-layout {
    grid-template-columns: 280px 1fr; /* ✅ 좁아지면 패널 숨김 */
  }
  .roadmap-panel {
    display: none;
  }
}

@media (max-width: 1024px) {
  .chat-layout {
    grid-template-columns: 1fr;
  }
  .chat-sidebar {
    order: 2;
  }
  .roadmap-panel {
    display: none;
  }
}

@media (max-width: 640px) {
  .chat-page {
    padding: 20px 16px;
  }

  .chat-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .chat-layout {
    gap: 12px;
  }

  .message-row {
    grid-template-columns: 36px 1fr;
  }

  .avatar {
    width: 36px;
    height: 36px;
    font-size: 12px;
  }
}
</style>
