<template>
  <div class="signup-page">
    <div class="bg-grid"></div>

    <nav class="nav-header">
      <RouterLink to="/" class="brand">JOBTORY</RouterLink>
    </nav>

    <div class="signup-scroll-container">
      <div class="signup-wrapper">
        <header class="page-header">
          <p class="eyebrow">MEMBERSHIP</p>
          <h1 class="page-title">Sign Up for Business</h1>
          <p class="page-desc">기업 회원을 위한 가입 페이지입니다.</p>
        </header>

        <section class="signup-card">
          <form class="signup-form" @submit.prevent="handleSubmit" @keydown.enter.prevent="handleEnter">
            
            <div class="form-section">
              <h3 class="section-title">계정 정보</h3>
              
              <div class="form-group">
                <label class="form-label">아이디</label>
                <div class="input-with-btn">
                  <input ref="usernameInput" v-model="username" class="form-input" type="text" placeholder="아이디 입력" />
                  <button type="button" class="btn-outline" @click="handleCheckUsername">중복확인</button>
                </div>
                <p v-if="usernameStatus === 'ok'" class="msg-text success">사용 가능한 아이디입니다.</p>
                <p v-else-if="usernameStatus === 'taken'" class="msg-text error">이미 사용 중인 아이디입니다.</p>
              </div>

              <div class="form-group">
                <label class="form-label">비밀번호</label>
                <input v-model="password" class="form-input" type="password" placeholder="비밀번호 입력" />
              </div>

              <div class="form-group">
                <label class="form-label">비밀번호 확인</label>
                <input 
                  v-model="passwordConfirm" 
                  class="form-input" 
                  :class="{ 'error-border': showPasswordError, 'success-border': showPasswordMatch }"
                  type="password" 
                  placeholder="비밀번호 재입력" 
                />
                <p v-if="showPasswordMatch" class="msg-text success">비밀번호가 일치합니다.</p>
                <p v-else-if="showPasswordError" class="msg-text error">비밀번호가 일치하지 않습니다.</p>
              </div>
            </div>

            <div class="form-section">
              <h3 class="section-title">담당자 및 기업 정보</h3>

              <div class="form-group">
                <label class="form-label">기업명</label>
                <input v-model="companyName" class="form-input" type="text" placeholder="기업명 입력" />
              </div>

              <div class="form-group">
                <label class="form-label">담당자 이름</label>
                <input v-model="managerName" class="form-input" type="text" placeholder="담당자 성함" />
              </div>

              <div class="form-group">
                <label class="form-label">담당자 전화번호</label>
                <div class="phone-group">
                  <input v-model="phone1" class="form-input center-text" type="tel" maxlength="3" placeholder="010" />
                  <span class="dash">-</span>
                  <input v-model="phone2" class="form-input center-text" type="tel" maxlength="4" />
                  <span class="dash">-</span>
                  <input v-model="phone3" class="form-input center-text" type="tel" maxlength="4" />
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">회사 이메일</label>
                <div class="email-group">
                  <input ref="emailLocalInput" v-model="emailLocal" class="form-input" type="text" placeholder="이메일" />
                  <span class="at">@</span>
                  <input
                    ref="emailDomainInputRef"
                    v-model="emailDomainInput"
                    class="form-input"
                    type="text"
                    placeholder="직접입력"
                  />
                </div>
                <div class="email-actions">
                  <select v-model="emailDomainSelect" class="form-select">
                    <option value="">직접 입력</option>
                    <option value="gmail.com">gmail.com</option>
                    <option value="naver.com">naver.com</option>
                    <option value="daum.net">daum.net</option>
                    <option value="jobtory.com">jobtory.com</option>
                  </select>
                  <button 
                    type="button" 
                    class="btn-black"
                    :disabled="emailSending"
                    @click="handleSendEmailCode"
                  >
                    {{ emailSending ? "발송 중.." : "인증번호 발송" }}
                  </button>
                </div>
                <p v-if="emailInlineMessage" :class="['msg-text', emailInlineType === 'error' ? 'error' : 'success']">
                  {{ emailInlineMessage }}
                </p>
              </div>

              <div class="form-group">
                <label class="form-label">인증번호 확인</label>
                <div class="input-with-btn">
                  <input ref="emailCodeInput" v-model="emailCode" class="form-input" type="text" placeholder="인증번호 6자리" />
                  <button 
                    type="button" 
                    class="btn-outline"
                    :disabled="emailVerifying"
                    @click="handleVerifyEmailCode"
                  >
                    {{ emailVerifying ? "확인 중.." : "확인" }}
                  </button>
                </div>
              </div>
            </div>

            <div class="form-footer">
              <div class="terms-container">
                <div class="terms-header-row">
                  <h4 class="terms-title">약관 동의</h4>
                  <label class="terms-all-check">
                    <input type="checkbox" v-model="allChecked" />
                    <span>전체 동의하기</span>
                  </label>
                </div>
                
                <div class="terms-list">
                  <div v-for="term in terms" :key="term.id" class="term-item">
                    <label class="term-label">
                      <input type="checkbox" v-model="term.checked" />
                      <span class="check-text">
                        {{ term.title }} <span v-if="term.required" class="required">*</span>
                      </span>
                    </label>
                    <button type="button" class="term-view-btn" @click="openTerm(term)">보기</button>
                  </div>
                </div>
              </div>

              <button type="submit" class="btn-submit" :disabled="pending">
                {{ pending ? "가입 처리 중..." : "회원가입 완료" }}
              </button>
            </div>

          </form>
        </section>
      </div>

      <div v-if="activeTerm" class="modal-overlay" @click.self="closeModal">
        <div class="modal-card">
          <div class="modal-header">
            <h3>{{ activeTerm.title }}</h3>
            <button type="button" class="modal-close" @click="closeModal">✕</button>
          </div>
          <div class="modal-body" v-html="activeTerm.content"></div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { useRouter, RouterLink } from "vue-router";

const router = useRouter();
import API_BASE from "../config/apiBase";

// Refs & Form Data
const usernameInput = ref(null);
const username = ref("");
const password = ref("");
const passwordConfirm = ref("");

const companyName = ref("");
const managerName = ref("");
const phone1 = ref("");
const phone2 = ref("");
const phone3 = ref("");

const emailLocalInput = ref(null);
const emailDomainInputRef = ref(null);
const emailCodeInput = ref(null);

const emailLocal = ref("");
const emailDomainInput = ref("");
const emailDomainSelect = ref("");
const emailCode = ref("");

// State
const pending = ref(false);
const usernameStatus = ref(""); // '', 'ok', 'taken'
const emailSending = ref(false);
const emailVerifying = ref(false);
const emailVerified = ref(false);
const emailInlineMessage = ref("");
const emailInlineType = ref("info");

// Terms Data
const activeTerm = ref(null);
const terms = ref([
  {
    id: "tos",
    title: "서비스 이용약관 동의",
    required: true,
    checked: false,
    content: `
      <div style="line-height: 1.6; color: #374151;">
        <h3 style="margin-bottom: 12px; font-size: 18px; color: #111827;">제1장 총칙</h3>
        <h4 style="margin: 16px 0 8px; font-size: 15px; color: #111827;">제1조 (목적)</h4>
        <p>본 약관은 잡토리(이하 "회사")가 제공하는 기업용 채용 관리 및 코딩 테스트 서비스(이하 "서비스")의 이용과 관련하여 회사와 기업 회원(이하 "회원") 간의 권리, 의무 및 책임사항을 규정함을 목적으로 합니다.</p>
        <h4 style="margin: 16px 0 8px; font-size: 15px; color: #111827;">제2조 (용어의 정의)</h4>
        <ol style="padding-left: 20px; margin: 0;">
          <li>"기업 회원"이라 함은 사업자등록증을 소지하고 서비스를 이용하기 위해 약관에 동의하고 가입한 법인 또는 개인사업자를 말합니다.</li>
          <li>"서비스"라 함은 회사가 제공하는 온라인 코딩 테스트, 리포트 열람, 지원자 관리 시스템 등을 말합니다.</li>
        </ol>
        <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 24px 0;" />
        <h3 style="margin-bottom: 12px; font-size: 18px; color: #111827;">제2장 계약 당사자의 의무</h3>
        <h4 style="margin: 16px 0 8px; font-size: 15px; color: #111827;">제4조 (회사의 의무)</h4>
        <p>회사는 지속적이고 안정적인 서비스 제공을 위해 노력하며, 서비스 장애 발생 시 이를 신속하게 복구할 의무가 있습니다.</p>
        <p style="margin-top: 24px; font-size: 13px; color: #6b7280;">부칙: 본 약관은 2026년 1월 1일부터 시행됩니다.</p>
      </div>
    `
  },
  {
    id: "privacy",
    title: "개인정보 수집 및 이용 동의",
    required: true,
    checked: false,
    content: `
      <div style="line-height: 1.6; color: #374151;">
        <p>잡토리(이하 "회사")는 기업 회원 가입 및 서비스 제공을 위해 아래와 같이 개인정보를 수집·이용합니다.</p>
        <h4 style="margin: 20px 0 12px; font-size: 15px; color: #111827;">1. 수집하는 개인정보 항목</h4>
        <table style="width: 100%; border-collapse: collapse; border: 1px solid #e5e7eb; font-size: 14px;">
          <thead style="background: #f9fafb;">
            <tr><th style="padding: 10px; border: 1px solid #e5e7eb; text-align: left;">구분</th><th style="padding: 10px; border: 1px solid #e5e7eb; text-align: left;">수집 항목</th></tr>
          </thead>
          <tbody>
            <tr><td style="padding: 10px; border: 1px solid #e5e7eb; font-weight: 600;">필수 항목</td><td style="padding: 10px; border: 1px solid #e5e7eb;">아이디, 비밀번호, 기업명, 담당자 이름, 연락처, 이메일</td></tr>
          </tbody>
        </table>
        <h4 style="margin: 20px 0 12px; font-size: 15px; color: #111827;">2. 보유 및 이용 기간</h4>
        <p><strong>회원 탈퇴 시까지</strong></p>
      </div>
    `
  },
  {
    id: "marketing",
    title: "마케팅 활용 동의",
    required: false,
    checked: false,
    content: `
      <div style="line-height: 1.6; color: #374151;">
        <p>잡토리에서 제공하는 이벤트, 신규 서비스 안내 등 광고성 정보를 수신하는 것에 동의합니다.</p>
        <h4 style="margin: 20px 0 12px; font-size: 15px; color: #111827;">1. 수집 목적 및 항목</h4>
        <p>신규 서비스(기능) 안내, 이벤트 및 프로모션 정보 제공 (담당자 이메일, 연락처)</p>
        <h4 style="margin: 20px 0 12px; font-size: 15px; color: #111827;">2. 보유 및 이용 기간</h4>
        <p><strong>회원 탈퇴 시 또는 동의 철회 시까지</strong></p>
      </div>
    `
  }
]);

// Computed
const allChecked = computed({
  get() {
    return terms.value.length > 0 && terms.value.every((t) => t.checked);
  },
  set(val) {
    terms.value.forEach((t) => { t.checked = val; });
  }
});

const showPasswordMatch = computed(
  () => !!password.value && !!passwordConfirm.value && password.value === passwordConfirm.value
);

const showPasswordError = computed(
  () => !!password.value && !!passwordConfirm.value && password.value !== passwordConfirm.value
);

// Watchers
watch(emailDomainSelect, (val) => {
  if (val) {
    emailDomainInput.value = val;
  }
});
watch(username, () => {
  usernameStatus.value = "";
});

// Logic
const openTerm = (term) => { activeTerm.value = term; };
const closeModal = () => { activeTerm.value = null; };

const buildEmail = () => {
  const domain = emailDomainSelect.value || emailDomainInput.value;
  if (!emailLocal.value || !domain) return "";
  return `${emailLocal.value}@${domain}`;
};

const handleCheckUsername = async () => {
  if (!username.value) return;
  // API Mock Logic
  if (username.value === "admin") {
    usernameStatus.value = "taken";
  } else {
    usernameStatus.value = "ok";
  }
};

const handleSendEmailCode = async () => {
  const email = buildEmail();
  if (!email) {
    emailInlineMessage.value = "이메일을 입력해주세요.";
    emailInlineType.value = "error";
    return;
  }
  emailSending.value = true;
  emailVerified.value = false;
  try {
    const resp = await fetch(`${API_BASE}/api/auth/email/send/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email })
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      throw new Error(data?.detail || "발송 실패");
    }
    emailInlineMessage.value = "인증번호가 발송되었습니다.";
    emailInlineType.value = "success";
  } catch (err) {
    emailInlineMessage.value = err?.message || "발송 실패";
    emailInlineType.value = "error";
  } finally {
    emailSending.value = false;
  }
};

const handleVerifyEmailCode = async () => {
  const email = buildEmail();
  if (!email || !emailCode.value) return;
  emailVerifying.value = true;
  try {
    const resp = await fetch(`${API_BASE}/api/auth/email/verify/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, code: emailCode.value })
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      throw new Error(data?.detail || "인증 실패");
    }
    emailVerified.value = true;
    emailInlineMessage.value = data?.message || "인증되었습니다.";
    emailInlineType.value = "success";
  } catch (err) {
    emailVerified.value = false;
    emailInlineMessage.value = err?.message || "인증 실패";
    emailInlineType.value = "error";
  } finally {
    emailVerifying.value = false;
  }
};

const handleEnter = () => {
  const active = document.activeElement;
  if (active === usernameInput.value) return handleCheckUsername();
  if (active === emailCodeInput.value) return handleVerifyEmailCode();
  handleSubmit();
};

const handleSubmit = async () => {
  if (!username.value) return alert("아이디를 입력해주세요.");
  if (!password.value || !showPasswordMatch.value) return alert("비밀번호를 확인해주세요.");
  if (!companyName.value) return alert("기업명을 입력해주세요.");
  if (!managerName.value) return alert("담당자 이름을 입력해주세요.");
  if (!emailVerified.value) return alert("이메일 인증이 필요합니다.");
  
  const notAgreed = terms.value.filter(t => t.required && !t.checked);
  if (notAgreed.length) return alert("필수 약관에 동의해주세요.");

  pending.value = true;
  try {
    await new Promise(r => setTimeout(r, 1000));
    alert("기업 회원가입이 완료되었습니다.");
    router.push("/login");
  } catch (e) {
    alert("가입 중 오류가 발생했습니다.");
  } finally {
    pending.value = false;
  }
};
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap");

/* [추가된 스타일] 상단 네비게이션 (로고) */
.nav-header {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  padding: 24px 40px;
  z-index: 50; /* 배경보다 위에 */
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

/* 1. 전체 페이지 설정 */
.signup-page {
  position: relative;
  width: 100vw;
  height: 100vh;
  background: #f8f4eb;
  font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #111827;
  display: flex;
  justify-content: center;
  overflow: hidden;
}

.bg-grid {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  z-index: 0;
  background-size: 40px 40px;
  background-image:
    linear-gradient(to right, rgba(0, 0, 0, 0.05) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(0, 0, 0, 0.05) 1px, transparent 1px);
  mask-image: linear-gradient(to bottom, black 40%, transparent 100%);
  pointer-events: none;
}

/* 2. 메인 스크롤 컨테이너 (스크롤바 숨김 처리) */
.signup-scroll-container {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  overflow-y: auto;
  padding: 40px 20px;
  
  /* Firefox */
  scrollbar-width: none;
  /* IE, Edge */
  -ms-overflow-style: none;
}

/* Chrome, Safari, Opera: 스크롤바 숨김 */
.signup-scroll-container::-webkit-scrollbar {
  display: none;
}

/* 3. 컨텐츠 래퍼 */
.signup-wrapper {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 40px;
  padding-bottom: 60px;
  animation: fadeUp 0.6s ease-out;
}

/* 헤더 */
.page-header {
  text-align: center;
  margin-top: 60px; /* 로고 영역 확보 */
}
.eyebrow {
  font-size: 13px;
  font-weight: 700;
  color: #9ca3af;
  letter-spacing: 0.05em;
  margin-bottom: 8px;
}
.page-title {
  font-size: 42px;
  font-weight: 800;
  margin: 0 0 12px;
}
.page-desc {
  font-size: 16px;
  color: #4b5563;
  margin: 0;
}

/* 카드 */
.signup-card {
  background: #ffffff;
  border-radius: 24px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.05);
  padding: 48px;
  border: 1px solid rgba(0,0,0,0.05);
}

/* 폼 그리드 */
.signup-form {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 60px;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section-title {
  font-size: 18px;
  font-weight: 700;
  border-bottom: 2px solid #111827;
  padding-bottom: 12px;
  margin-bottom: 8px;
}

/* 폼 요소 */
.form-group { display: flex; flex-direction: column; gap: 8px; }
.form-label { font-size: 14px; font-weight: 600; color: #374151; }

.form-input, .form-select {
  width: 100%; height: 46px; padding: 0 14px;
  border-radius: 8px; border: 1px solid #e5e7eb;
  background: #f9fafb; font-size: 14px; color: #111827;
  outline: none; transition: all 0.2s;
}
.form-input:focus, .form-select:focus {
  background: #fff; border-color: #111827; box-shadow: 0 0 0 1px #111827;
}

/* 버튼 */
.btn-outline {
  height: 46px; padding: 0 16px; border-radius: 8px;
  border: 1px solid #d1d5db; background: #fff;
  font-size: 13px; font-weight: 600; color: #374151;
  cursor: pointer; white-space: nowrap;
}
.btn-outline:hover { background: #f3f4f6; border-color: #9ca3af; }

.btn-black {
  height: 46px; padding: 0 16px; border-radius: 8px;
  background: #111827; color: #fff;
  font-size: 13px; font-weight: 600; border: none;
  cursor: pointer; white-space: nowrap;
}
.btn-black:hover { background: #000; }
.btn-black:disabled { background: #9ca3af; cursor: not-allowed; }

/* 그룹 필드 */
.input-with-btn { display: flex; gap: 8px; }
.phone-group, .email-group, .email-actions { display: flex; gap: 8px; align-items: center; }
.center-text { text-align: center; }
.dash, .at { color: #9ca3af; font-weight: bold; }

/* 메시지 */
.msg-text { font-size: 12px; margin-top: 4px; }
.msg-text.success { color: #16a34a; }
.msg-text.error { color: #dc2626; }
.error-border { border-color: #dc2626; background: #fef2f2; }
.success-border { border-color: #16a34a; }

/* 약관 및 하단 버튼 */
.form-footer {
  grid-column: 1 / -1;
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 32px;
  align-items: center;
}

.terms-container {
  width: 100%;
  background: #f9fafb;
  padding: 24px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

.terms-header-row {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #e5e7eb;
}
.terms-title { margin: 0; font-size: 16px; font-weight: 700; }
.terms-all-check { display: flex; align-items: center; gap: 8px; font-weight: 700; cursor: pointer; }

.terms-list { display: flex; flex-direction: column; gap: 12px; }
.term-item { display: flex; justify-content: space-between; align-items: center; font-size: 14px; }
.term-label { display: flex; align-items: center; gap: 8px; cursor: pointer; }
.required { color: #dc2626; font-size: 12px; }
.term-view-btn { background: none; border: none; text-decoration: underline; color: #6b7280; cursor: pointer; font-size: 12px; }

.btn-submit {
  min-width: 280px; height: 56px; border-radius: 999px;
  background: #111827; color: #fff;
  font-size: 16px; font-weight: 700; border: none;
  cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  transition: transform 0.2s;
}
.btn-submit:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,0.2); }
.btn-submit:disabled { background: #9ca3af; cursor: not-allowed; }

/* 모달 */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.modal-card {
  width: min(600px, 90vw); max-height: 80vh; background: #fff;
  border-radius: 12px; display: flex; flex-direction: column;
}
.modal-header {
  padding: 16px 20px; border-bottom: 1px solid #eee;
  display: flex; justify-content: space-between; align-items: center; font-weight: bold;
}
.modal-body {
  padding: 20px;
  overflow-y: auto;
  line-height: 1.6;
  font-size: 14px;
  color: #374151;
  /* Firefox */
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 transparent;
}

/* Modal Custom Scrollbar (Webkit) */
.modal-body::-webkit-scrollbar { width: 6px; }
.modal-body::-webkit-scrollbar-track { background: transparent; margin: 4px 0; }
.modal-body::-webkit-scrollbar-thumb {
  background-color: #cbd5e1;
  border-radius: 10px;
  border: 2px solid transparent;
  background-clip: content-box;
}
.modal-body::-webkit-scrollbar-thumb:hover { background-color: #94a3b8; }

.modal-close { background: none; border: none; font-size: 20px; cursor: pointer; }

/* 애니메이션 */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .nav-header { padding: 20px; justify-content: center; }
  .signup-card { padding: 32px 24px; }
  .signup-form { grid-template-columns: 1fr; gap: 40px; }
  .email-group { flex-wrap: wrap; }
  .page-title { font-size: 32px; }
}
</style>
