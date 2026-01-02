<template>
  <div class="signup-page">
    <div class="bg-grid"></div>

    <div class="signup-scroll-container">
      <div class="signup-wrapper">
        <header class="page-header">
          <p class="eyebrow">MEMBERSHIP</p>
          <h1 class="page-title">Sign Up for Personal</h1>
          <p class="page-desc">개인 회원을 위한 가입 페이지입니다.</p>
        </header>

        <section class="signup-card">
          <form class="signup-form" @submit.prevent="handleSubmit" @keydown.enter.prevent="handleEnter">
            
            <div class="form-section">
              <h3 class="section-title">기본 정보</h3>
              
              <div class="form-group">
                <label class="form-label">아이디</label>
                <div class="input-with-btn">
                  <input 
                    ref="usernameInput" 
                    v-model="username" 
                    class="form-input" 
                    type="text" 
                    placeholder="아이디 입력" 
                  />
                  <button type="button" class="btn-outline" @click="handleCheckUsername">중복확인</button>
                </div>
                <p v-if="usernameStatus === 'ok'" class="msg-text success">사용 가능한 아이디입니다.</p>
                <p v-else-if="usernameStatus === 'taken'" class="msg-text error">이미 사용 중인 아이디입니다.</p>
                <p v-else-if="usernameStatus === 'empty'" class="msg-text error">아이디를 입력해 주세요.</p>
              </div>

              <div class="form-group">
                <label class="form-label">이름</label>
                <input v-model="name" class="form-input" type="text" placeholder="성함 입력" />
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
              <h3 class="section-title">상세 정보</h3>

              <div class="form-group">
                <label class="form-label">전화번호</label>
                <div class="phone-group">
                  <input v-model="phone1" class="form-input center-text" type="tel" maxlength="3" placeholder="010" />
                  <span class="dash">-</span>
                  <input v-model="phone2" class="form-input center-text" type="tel" maxlength="4" />
                  <span class="dash">-</span>
                  <input v-model="phone3" class="form-input center-text" type="tel" maxlength="4" />
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">이메일</label>
                <div class="email-group">
                  <input 
                    ref="emailLocalInput" 
                    v-model="emailLocal" 
                    class="form-input" 
                    type="text" 
                    placeholder="username" 
                  />
                  <span class="at">@</span>
                  <input
                    ref="emailDomainInputRef"
                    v-model="emailDomainInput"
                    class="form-input"
                    type="text"
                    placeholder="example.com"
                  />
                </div>
                <div class="email-actions">
                  <select v-model="emailDomainSelect" class="form-select">
                    <option value="">직접 입력</option>
                    <option value="gmail.com">gmail.com</option>
                    <option value="naver.com">naver.com</option>
                    <option value="kakao.com">kakao.com</option>
                    <option value="daum.net">daum.net</option>
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
                  <input 
                    ref="emailCodeInput" 
                    v-model="emailCode" 
                    class="form-input" 
                    type="text" 
                    placeholder="인증번호 6자리" 
                  />
                  <button 
                    type="button" 
                    class="btn-outline" 
                    :disabled="emailVerifying"
                    @click="handleVerifyEmailCode"
                  >
                    {{ emailVerifying ? "확인 중.." : "인증" }}
                  </button>
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">생년월일</label>
                <div class="birth-group">
                  <select v-model="birthYear" class="form-select">
                    <option value="">년도</option>
                    <option v-for="year in years" :key="year" :value="year">{{ year }}</option>
                  </select>
                  <select v-model="birthMonth" class="form-select">
                    <option value="">월</option>
                    <option v-for="month in months" :key="month" :value="month">{{ month }}</option>
                  </select>
                  <select v-model="birthDay" class="form-select">
                    <option value="">일</option>
                    <option v-for="day in days" :key="day" :value="day">{{ day }}</option>
                  </select>
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
import { useRouter } from "vue-router";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const router = useRouter();

// Refs
const usernameInput = ref(null);
const emailLocalInput = ref(null);
const emailDomainInputRef = ref(null);
const emailCodeInput = ref(null);

// Date Data
const currentYear = new Date().getFullYear();
const years = Array.from({ length: 70 }, (_, i) => currentYear - i);
const months = Array.from({ length: 12 }, (_, i) => i + 1);
const days = Array.from({ length: 31 }, (_, i) => i + 1);

// Form Data
const birthYear = ref("");
const birthMonth = ref("");
const birthDay = ref("");
const name = ref("");
const username = ref("");
const phone1 = ref("");
const phone2 = ref("");
const phone3 = ref("");
const password = ref("");
const passwordConfirm = ref("");

// Email
const emailLocal = ref("");
const emailDomainInput = ref("");
const emailDomainSelect = ref("");
const emailCode = ref("");

// State
const pending = ref(false);
const emailSending = ref(false);
const emailVerifying = ref(false);
const emailVerified = ref(false);
const emailInlineMessage = ref("");
const emailInlineType = ref("info");
const usernameStatus = ref(""); // '', 'ok', 'taken', 'empty'

// Terms
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
        <p>본 약관은 잡토리(이하 "회사")가 제공하는 개인용 코딩 역량 평가 및 채용 연계 서비스(이하 "서비스")의 이용과 관련하여 회사와 개인 회원(이하 "회원") 간의 권리, 의무 및 책임사항을 규정함을 목적으로 합니다.</p>

        <h4 style="margin: 16px 0 8px; font-size: 15px; color: #111827;">제2조 (용어의 정의)</h4>
        <ol style="padding-left: 20px; margin: 0;">
          <li>"개인 회원"이라 함은 서비스를 이용하기 위해 약관에 동의하고 가입한 자를 말합니다.</li>
          <li>"서비스"라 함은 회사가 제공하는 라이브 코딩 테스트, 모의 면접, 역량 리포트 발급 등을 말합니다.</li>
          <li>"콘텐츠"라 함은 서비스 내에서 제공되는 문제, 해설, 영상 등을 의미합니다.</li>
        </ol>

        <h4 style="margin: 16px 0 8px; font-size: 15px; color: #111827;">제3조 (회원의 의무)</h4>
        <ul style="padding-left: 20px; margin: 0;">
          <li>회원은 가입 신청 시 사실에 입각하여 본인의 정보를 등록해야 합니다. 허위 정보를 등록한 경우 서비스 이용 및 채용 지원에 불이익이 있을 수 있습니다.</li>
          <li>회원은 코딩 테스트 및 면접 진행 시 부정행위(대리 응시, 답안 유출 등)를 해서는 안 됩니다. 부정행위 적발 시 계정 차단 및 합격 취소 등의 조치가 취해질 수 있습니다.</li>
          <li>회원은 타인의 계정 정보를 도용하거나 서비스를 통해 얻은 정보를 상업적으로 이용해서는 안 됩니다.</li>
        </ul>

        <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 24px 0;" />

        <h3 style="margin-bottom: 12px; font-size: 18px; color: #111827;">제2장 서비스 이용</h3>

        <h4 style="margin: 16px 0 8px; font-size: 15px; color: #111827;">제4조 (서비스 제공 및 변경)</h4>
        <p>회사는 회원에게 코딩 테스트 연습, 실전 모의고사, 역량 분석 리포트 등의 서비스를 제공하며, 운영상 필요에 따라 서비스 내용을 변경하거나 종료할 수 있습니다.</p>

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
        <p>잡토리(이하 "회사")는 회원가입, 원활한 서비스 제공, 채용 매칭 등을 위해 아래와 같이 개인정보를 수집·이용합니다.</p>

        <h4 style="margin: 20px 0 12px; font-size: 15px; color: #111827;">1. 수집하는 개인정보 항목</h4>
        <table style="width: 100%; border-collapse: collapse; border: 1px solid #e5e7eb; font-size: 14px;">
          <thead style="background: #f9fafb;">
            <tr>
              <th style="padding: 10px; border: 1px solid #e5e7eb; text-align: left;">구분</th>
              <th style="padding: 10px; border: 1px solid #e5e7eb; text-align: left;">수집 항목</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style="padding: 10px; border: 1px solid #e5e7eb; font-weight: 600;">필수 항목</td>
              <td style="padding: 10px; border: 1px solid #e5e7eb;">아이디, 비밀번호, 이름, 휴대전화번호, 이메일, 생년월일</td>
            </tr>
            <tr>
              <td style="padding: 10px; border: 1px solid #e5e7eb; font-weight: 600;">선택 항목</td>
              <td style="padding: 10px; border: 1px solid #e5e7eb;">최종 학력, 경력 사항, 보유 기술 스택, 희망 직무, 희망 연봉, 포트폴리오</td>
            </tr>
            <tr>
              <td style="padding: 10px; border: 1px solid #e5e7eb; font-weight: 600;">자동 수집</td>
              <td style="padding: 10px; border: 1px solid #e5e7eb;">IP 주소, 쿠키, 서비스 이용 기록, 기기 정보</td>
            </tr>
          </tbody>
        </table>

        <h4 style="margin: 20px 0 12px; font-size: 15px; color: #111827;">2. 수집 및 이용 목적</h4>
        <ul style="padding-left: 20px; margin: 0;">
          <li>본인 확인 및 회원 식별</li>
          <li>코딩 테스트 응시 자격 확인 및 결과 리포트 생성</li>
          <li>채용 공고 매칭 및 입사 지원 서비스 제공</li>
          <li>부정 이용 방지 및 고객 상담 처리</li>
        </ul>

        <h4 style="margin: 20px 0 12px; font-size: 15px; color: #111827;">3. 보유 및 이용 기간</h4>
        <p><strong>회원 탈퇴 시까지</strong> (단, 관계 법령에 따라 보존할 필요가 있는 경우 해당 기간 동안 보관)</p>
        <ul style="padding-left: 20px; margin-top: 8px; font-size: 13px; color: #6b7280;">
          <li>접속에 관한 기록: 3개월 (통신비밀보호법)</li>
          <li>소비자의 불만 또는 분쟁처리에 관한 기록: 3년 (전자상거래법)</li>
        </ul>

        <p style="margin-top: 20px; font-weight: 600;">귀하는 개인정보 수집 및 이용에 동의를 거부할 권리가 있으나, 필수 항목 미동의 시 회원가입이 불가능합니다.</p>
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
        <p>잡토리에서 제공하는 맞춤형 채용 정보, 이벤트 혜택 등 광고성 정보를 수신하는 것에 동의합니다.</p>

        <h4 style="margin: 20px 0 12px; font-size: 15px; color: #111827;">1. 수집 목적 및 항목</h4>
        <table style="width: 100%; border-collapse: collapse; border: 1px solid #e5e7eb; font-size: 14px;">
          <thead style="background: #f9fafb;">
            <tr>
              <th style="padding: 10px; border: 1px solid #e5e7eb; text-align: left;">목적</th>
              <th style="padding: 10px; border: 1px solid #e5e7eb; text-align: left;">항목</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style="padding: 10px; border: 1px solid #e5e7eb;">맞춤형 채용 공고 추천,<br>이벤트 및 프로모션 안내</td>
              <td style="padding: 10px; border: 1px solid #e5e7eb;">이메일, 휴대전화번호, 희망 직무, 기술 스택</td>
            </tr>
          </tbody>
        </table>

        <h4 style="margin: 20px 0 12px; font-size: 15px; color: #111827;">2. 보유 및 이용 기간</h4>
        <p><strong>회원 탈퇴 시 또는 동의 철회 시까지</strong></p>

        <p style="margin-top: 20px; font-size: 13px; color: #6b7280;">
          ※ 본 동의를 거부하시더라도 기본 서비스(코딩 테스트 등) 이용에는 제한이 없습니다.<br>
          ※ 수신 동의 이후에도 마이페이지 설정 또는 고객센터를 통해 언제든지 철회할 수 있습니다.
        </p>
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
  if (val) emailDomainInput.value = val;
});
watch(username, () => {
  usernameStatus.value = "";
});

// Handlers
const openTerm = (term) => { activeTerm.value = term; };
const closeModal = () => { activeTerm.value = null; };

const buildEmail = () => {
  const domain = emailDomainSelect.value || emailDomainInput.value;
  if (!emailLocal.value || !domain) return "";
  return `${emailLocal.value}@${domain}`;
};

const handleCheckUsername = async () => {
  const value = username.value.trim();
  if (!value) {
    usernameStatus.value = "empty";
    return;
  }
  try {
    const res = await fetch(`${API_BASE}/api/auth/user-id/check/?user_id=${encodeURIComponent(value)}`);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data?.detail || "실패");
    usernameStatus.value = data.available ? "ok" : "taken";
  } catch (err) {
    usernameStatus.value = "";
    window.alert("중복 확인 중 오류가 발생했습니다.");
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
  try {
    // API 호출 시뮬레이션
    await new Promise(r => setTimeout(r, 800));
    // 실제: await fetch(...)
    emailInlineMessage.value = "인증번호가 발송되었습니다.";
    emailInlineType.value = "success";
  } catch(e) {
    emailInlineMessage.value = "발송 실패";
    emailInlineType.value = "error";
  } finally {
    emailSending.value = false;
  }
};

const handleVerifyEmailCode = async () => {
  if(!emailCode.value) return;
  emailVerifying.value = true;
  try {
    // API 호출 시뮬레이션
    await new Promise(r => setTimeout(r, 800));
    // 실제: await fetch(...)
    emailVerified.value = true;
    emailInlineMessage.value = "이메일 인증 완료!";
    emailInlineType.value = "success";
  } catch(e) {
    emailInlineMessage.value = "인증 실패";
    emailInlineType.value = "error";
  } finally {
    emailVerifying.value = false;
  }
};

const handleEnter = () => {
  const active = document.activeElement;
  if(active === usernameInput.value) return handleCheckUsername();
  if(active === emailCodeInput.value) return handleVerifyEmailCode();
  handleSubmit();
};

const handleSubmit = async () => {
  // 간단 유효성 검사
  if (!username.value || usernameStatus.value !== 'ok') return alert("아이디 중복확인이 필요합니다.");
  if (!password.value || !showPasswordMatch.value) return alert("비밀번호를 확인해주세요.");
  if (!emailVerified.value) return alert("이메일 인증이 필요합니다.");
  const notAgreed = terms.value.filter(t => t.required && !t.checked);
  if (notAgreed.length) return alert("필수 약관에 동의해주세요.");

  pending.value = true;
  try {
    // 실제 회원가입 API 호출
    const birth = `${birthYear.value}-${String(birthMonth.value).padStart(2,'0')}-${String(birthDay.value).padStart(2,'0')}`;
    const phone = `${phone1.value}-${phone2.value}-${phone3.value}`;
    
    const res = await fetch(`${API_BASE}/api/auth/signup/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: username.value,
        password: password.value,
        name: name.value,
        email: buildEmail(),
        phone_number: phone,
        birthdate: birth
      })
    });
    
    if(!res.ok) throw new Error("가입 실패");
    
    alert("가입이 완료되었습니다!");
    router.push("/login");
  } catch (e) {
    alert("가입 중 오류가 발생했습니다.");
  } finally {
    pending.value = false;
  }
};
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap");

/* 1. 전체 페이지 설정 (고정) */
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

/* 배경 그리드 */
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
  
  /* Firefox: 스크롤바 숨김 */
  scrollbar-width: none; 
  /* IE, Edge: 스크롤바 숨김 */
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
.page-header { text-align: center; }
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

/* 카드 스타일 */
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

/* 폼 요소 공통 */
.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.form-input, .form-select {
  width: 100%;
  height: 46px;
  padding: 0 14px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  font-size: 14px;
  color: #111827;
  outline: none;
  transition: all 0.2s;
}

.form-input:focus, .form-select:focus {
  background: #fff;
  border-color: #111827;
  box-shadow: 0 0 0 1px #111827;
}

.input-with-btn { display: flex; gap: 8px; }

/* 버튼 */
.btn-outline {
  height: 46px;
  padding: 0 16px;
  border-radius: 8px;
  border: 1px solid #d1d5db;
  background: #fff;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  cursor: pointer;
  white-space: nowrap;
}
.btn-outline:hover { background: #f3f4f6; border-color: #9ca3af; }

.btn-black {
  height: 46px;
  padding: 0 16px;
  border-radius: 8px;
  background: #111827;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  white-space: nowrap;
}
.btn-black:hover { background: #000; }
.btn-black:disabled { background: #9ca3af; cursor: not-allowed; }

/* 그룹 필드 */
.phone-group, .birth-group, .email-group, .email-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
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
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.terms-title { margin: 0; font-size: 16px; font-weight: 700; }
.terms-all-check { display: flex; align-items: center; gap: 8px; font-weight: 700; cursor: pointer; }

.terms-list { display: flex; flex-direction: column; gap: 12px; }
.term-item { display: flex; justify-content: space-between; align-items: center; font-size: 14px; }
.term-label { display: flex; align-items: center; gap: 8px; cursor: pointer; }
.required { color: #dc2626; font-size: 12px; }
.term-view-btn { background: none; border: none; text-decoration: underline; color: #6b7280; cursor: pointer; font-size: 12px; }

.btn-submit {
  min-width: 280px;
  height: 56px;
  border-radius: 999px;
  background: #111827;
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
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
}

.modal-body::-webkit-scrollbar {
  width: 6px; 
}

.modal-body::-webkit-scrollbar-track {
  background: transparent;
  margin: 4px 0; 
}

.modal-body::-webkit-scrollbar-thumb {
  background-color: #374151;
  border-radius: 10px; 
  border: 2px solid transparent; 
  background-clip: content-box;
}

.modal-body::-webkit-scrollbar-thumb:hover {
  background-color: #94a3b8; 
}

.modal-close { background: none; border: none; font-size: 20px; cursor: pointer; }

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .signup-card { padding: 32px 24px; }
  .signup-form { grid-template-columns: 1fr; gap: 40px; }
  .email-group { flex-wrap: wrap; }
  .page-title { font-size: 32px; }
}
</style>