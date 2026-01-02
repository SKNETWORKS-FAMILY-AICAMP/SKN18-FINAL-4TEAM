<template>
  <div class="signup-page">
    <header class="signup-header">
      <p class="page-label">개인용 회원가입</p>
    </header>

    <main class="signup-main">
      <section class="card">
        <h1 class="title">Sign in</h1>

        <form class="form-grid" @submit.prevent="handleSubmit" @keydown.enter.prevent="handleEnter">
          <div class="field-block">
            <label class="field-label">아이디</label>
            <div class="field-line">
              <input
                ref="usernameInput"
                v-model="username"
                class="field-input"
                type="text"
                placeholder="아이디"
              />
              <button type="button" class="pill-button" @click="handleCheckUsername">중복확인</button>
            </div>
            <p v-if="usernameStatus === 'ok'" class="hint-text success">사용 가능한 아이디입니다.</p>
            <p v-else-if="usernameStatus === 'taken'" class="hint-text error">이미 사용 중인 아이디입니다.</p>
            <p v-else-if="usernameStatus === 'empty'" class="hint-text error">아이디를 입력해 주세요.</p>
          </div>

          <div class="field-block">
            <label class="field-label">이름</label>
            <div class="field-line">
              <input v-model="name" class="field-input" type="text" placeholder="홍길동" />
            </div>
          </div>

          <div class="field-block">
            <label class="field-label">비밀번호</label>
            <div class="field-line">
              <input v-model="password" class="field-input" type="password" />
            </div>
          </div>

          <div class="field-block">
            <label class="field-label">전화번호</label>
            <div class="field-line phone-line">
              <input v-model="phone1" class="field-input phone-input" type="tel" maxlength="3" />
              <span class="hyphen">-</span>
              <input v-model="phone2" class="field-input phone-input" type="tel" maxlength="4" />
              <span class="hyphen">-</span>
              <input v-model="phone3" class="field-input phone-input" type="tel" maxlength="4" />
            </div>
          </div>

          <div class="field-block">
            <label class="field-label">비밀번호 확인</label>
            <div class="field-line" :class="{ 'error-line': showPasswordError, 'success-line': showPasswordMatch }">
              <input v-model="passwordConfirm" class="field-input" type="password" />
            </div>
            <p v-if="showPasswordMatch" class="password-hint success">비밀번호가 일치합니다.</p>
            <p v-else-if="showPasswordError" class="password-hint error">비밀번호가 일치하지 않습니다.</p>
          </div>

          <div class="field-block">
            <label class="field-label">이메일</label>
            <div class="field-line email-line">
              <input
                ref="emailLocalInput"
                v-model="emailLocal"
                class="field-input email-local"
                type="text"
                placeholder="username"
              />
              <span class="at">@</span>
              <input
                ref="emailDomainInputRef"
                v-model="emailDomainInput"
                class="field-input email-domain-input"
                type="text"
                placeholder="example.com"
              />
              <select v-model="emailDomainSelect" class="email-domain">
                <option value="">직접 입력</option>
                <option value="gmail.com">gmail.com</option>
                <option value="naver.com">naver.com</option>
                <option value="daum.net">daum.net</option>
                <option value="kakao.com">kakao.com</option>
              </select>
              <button
                type="button"
                class="pill-button email-send-button"
                :disabled="emailSending"
                @click="handleSendEmailCode"
              >
                {{ emailSending ? "발송 중..." : "인증번호 발송" }}
              </button>
            </div>
            <p v-if="emailInlineMessage" :class="['email-inline-msg', emailInlineType]">
              {{ emailInlineMessage }}
            </p>
          </div>

          <div class="field-block">
            <label class="field-label">생년월일</label>
            <div class="birth-row">
              <select v-model="birthYear" class="birth-select">
                <option value="">년</option>
                <option v-for="year in years" :key="year" :value="year">
                  {{ year }}
                </option>
              </select>
              <select v-model="birthMonth" class="birth-select">
                <option value="">월</option>
                <option v-for="month in months" :key="month" :value="month">
                  {{ month }}
                </option>
              </select>
              <select v-model="birthDay" class="birth-select">
                <option value="">일</option>
                <option v-for="day in days" :key="day" :value="day">
                  {{ day }}
                </option>
              </select>
            </div>
          </div>

          <div class="field-block">
            <label class="field-label">인증번호</label>
            <div class="field-line">
              <input
                ref="emailCodeInput"
                v-model="emailCode"
                class="field-input"
                type="text"
                placeholder="인증번호 입력"
              />
              <button
                type="button"
                class="pill-button"
                :disabled="emailVerifying"
                @click="handleVerifyEmailCode"
              >
                {{ emailVerifying ? "확인 중..." : "인증" }}
              </button>
            </div>
          </div>

          <!-- 약관 동의 -->
          <div class="field-block terms-block">
            <div class="terms-header">
              <label class="field-label">약관 동의</label>

              <label class="terms-all">
                <input type="checkbox" v-model="allChecked" />
                전체동의
              </label>
            </div>

            <div class="terms-list">
              <div v-for="term in terms" :key="term.id" class="terms-item">
                <label class="term-check">
                  <input type="checkbox" v-model="term.checked" />
                  <button type="button" class="term-link" @click="openTerm(term)">
                    {{ term.title }}
                  </button>
                  <span v-if="term.required" class="term-required">*</span>
                </label>
                <span v-if="term.subtext" class="term-subtext">{{ term.subtext }}</span>
              </div>
            </div>
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

          <div class="form-actions">
            <button type="submit" class="submit-button" :disabled="pending" formnovalidate>
              {{ pending ? "가입 중..." : "회원가입" }}
            </button>
          </div>
        </form>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { useRouter } from "vue-router";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const router = useRouter();
const usernameInput = ref(null);
const emailLocalInput = ref(null);
const emailDomainInputRef = ref(null);
const emailCodeInput = ref(null);

const currentYear = new Date().getFullYear();
const years = Array.from({ length: 70 }, (_, i) => currentYear - i);
const months = Array.from({ length: 12 }, (_, i) => i + 1);
const days = Array.from({ length: 31 }, (_, i) => i + 1);

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

const emailLocal = ref("");
const emailDomainInput = ref("");
const emailDomainSelect = ref("");
const pending = ref(false);
const message = ref("");
const messageType = ref("info");
const emailVerified = ref(false);
const emailCode = ref("");
const emailSending = ref(false);
const emailVerifying = ref(false);
const emailInlineMessage = ref("");
const emailInlineType = ref("info");
const usernameStatus = ref(""); // '', 'ok', 'taken', 'empty'
const activeTerm = ref(null);
const terms = ref([
  /* =========================
   * 1. 이용약관 동의 (필수)
   * ========================= */
  {
    id: "tos",
    title: "[필수] 이용약관 동의",
    required: true,
    checked: false,
    content: `
      <h3>잡토리 서비스 이용약관</h3>
      <p>본 약관은 잡토리(이하 “회사”)가 제공하는 서비스 이용과 관련하여 회사와 이용자 간의 권리·의무 및 책임사항을 규정합니다.</p>

      <h4>제1조 (목적)</h4>
      <p>본 약관은 회사가 제공하는 코딩 학습, 라이브 코딩 테스트, 면접 대비 서비스의 이용 조건 및 절차를 규정함을 목적으로 합니다.</p>

      <h4>제2조 (용어 정의)</h4>
      <table style="border-collapse:collapse; width:100%; border:1px solid #d1d5db;">
        <thead style="background:#f3f4f6;">
          <tr>
            <th style="padding:10px; border:1px solid #d1d5db; width:25%;">용어</th>
            <th style="padding:10px; border:1px solid #d1d5db;">정의</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style="padding:10px; border:1px solid #d1d5db;"><b>이용자</b></td>
            <td style="padding:10px; border:1px solid #d1d5db;">본 약관에 동의하고 서비스를 이용하는 자</td>
          </tr>
          <tr>
            <td style="padding:10px; border:1px solid #d1d5db;"><b>회원</b></td>
            <td style="padding:10px; border:1px solid #d1d5db;">회원가입을 완료하고 서비스를 이용하는 자</td>
          </tr>
          <tr>
            <td style="padding:10px; border:1px solid #d1d5db;"><b>계정</b></td>
            <td style="padding:10px; border:1px solid #d1d5db;">회원 식별을 위해 설정한 아이디(ID)와 비밀번호</td>
          </tr>
        </tbody>
      </table>

      <h4>제3조 (서비스 제공)</h4>
      <ul>
        <li>회사는 코딩 문제 풀이, 라이브 코딩 테스트, 면접 대비 콘텐츠 등을 제공합니다.</li>
        <li>서비스 내용은 개선을 위해 변경될 수 있습니다.</li>
      </ul>

      <h4>제4조 (금지행위)</h4>
      <table style="border-collapse:collapse; width:100%; border:1px solid #d1d5db;">
        <thead style="background:#f3f4f6;">
          <tr>
            <th style="padding:10px; border:1px solid #d1d5db; width:22%;">구분</th>
            <th style="padding:10px; border:1px solid #d1d5db;">행위 예시</th>
            <th style="padding:10px; border:1px solid #d1d5db; width:22%;">조치</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style="padding:10px; border:1px solid #d1d5db;"><b>계정 도용</b></td>
            <td style="padding:10px; border:1px solid #d1d5db;">타인 명의 가입, 계정 공유</td>
            <td style="padding:10px; border:1px solid #d1d5db;">경고, 이용 제한</td>
          </tr>
          <tr>
            <td style="padding:10px; border:1px solid #d1d5db;"><b>운영 방해</b></td>
            <td style="padding:10px; border:1px solid #d1d5db;">비정상 트래픽, 자동화 도구 사용</td>
            <td style="padding:10px; border:1px solid #d1d5db;">즉시 차단</td>
          </tr>
          <tr>
            <td style="padding:10px; border:1px solid #d1d5db;"><b>권리 침해</b></td>
            <td style="padding:10px; border:1px solid #d1d5db;">저작권 침해 콘텐츠 업로드</td>
            <td style="padding:10px; border:1px solid #d1d5db;">삭제, 이용 제한</td>
          </tr>
        </tbody>
      </table>

      <h4>제5조 (면책)</h4>
      <p>회사는 천재지변, 이용자 귀책 사유로 인한 서비스 장애에 대해 책임을 지지 않습니다.</p>

      <hr/>
      <p style="font-size:12px; color:#6b7280;">시행일: 2026-01-01</p>
    `
  },

  /* =========================
   * 2. 개인정보 수집·이용 동의 (필수)
   * ========================= */
  {
    id: "privacy",
    title: "[필수] 개인정보 수집 및 이용 동의",
    required: true,
    checked: false,
    content: `
      <h3>잡토리 개인정보 수집·이용 동의</h3>
      <p>회사는 개인정보 보호법에 따라 아래와 같이 개인정보를 수집·이용합니다.</p>

      <h4>1. 수집 항목 및 이용 목적</h4>
      <table style="border-collapse:collapse; width:100%; border:1px solid #d1d5db;">
        <thead style="background:#f3f4f6;">
          <tr>
            <th style="padding:10px; border:1px solid #d1d5db; width:18%;">구분</th>
            <th style="padding:10px; border:1px solid #d1d5db; width:42%;">수집 항목</th>
            <th style="padding:10px; border:1px solid #d1d5db;">이용 목적</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style="padding:10px; border:1px solid #d1d5db;"><b>필수</b></td>
            <td style="padding:10px; border:1px solid #d1d5db;">아이디, 비밀번호, 이름, 이메일</td>
            <td style="padding:10px; border:1px solid #d1d5db;">회원 식별, 서비스 제공</td>
          </tr>
          <tr>
            <td style="padding:10px; border:1px solid #d1d5db;"><b>선택</b></td>
            <td style="padding:10px; border:1px solid #d1d5db;">전화번호, 생년월일</td>
            <td style="padding:10px; border:1px solid #d1d5db;">고객 문의 대응, 통계 분석</td>
          </tr>
        </tbody>
      </table>

      <h4>2. 보유 및 이용기간</h4>
      <table style="border-collapse:collapse; width:100%; border:1px solid #d1d5db;">
        <tr>
          <th style="padding:10px; border:1px solid #d1d5db; width:40%;">항목</th>
          <th style="padding:10px; border:1px solid #d1d5db;">보유 기간</th>
        </tr>
        <tr>
          <td style="padding:10px; border:1px solid #d1d5db;">회원 정보</td>
          <td style="padding:10px; border:1px solid #d1d5db;">회원 탈퇴 시까지</td>
        </tr>
      </table>

      <p>필수 항목 동의 거부 시 서비스 이용이 제한될 수 있습니다.</p>

      <hr/>
      <p style="font-size:12px; color:#6b7280;">시행일: 2026-01-01</p>
    `
  },

  /* =========================
   * 3. 마케팅 활용 동의 (선택)
   * ========================= */
  {
    id: "marketing",
    title: "[선택] 마케팅 활용 동의",
    required: false,
    checked: false,
    content: `
      <h3>마케팅 정보 수신 동의</h3>

      <table style="border-collapse:collapse; width:100%; border:1px solid #d1d5db;">
        <thead style="background:#f3f4f6;">
          <tr>
            <th style="padding:10px; border:1px solid #d1d5db; width:25%;">항목</th>
            <th style="padding:10px; border:1px solid #d1d5db;">내용</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style="padding:10px; border:1px solid #d1d5db;"><b>수신 채널</b></td>
            <td style="padding:10px; border:1px solid #d1d5db;">이메일, 문자(SMS)</td>
          </tr>
          <tr>
            <td style="padding:10px; border:1px solid #d1d5db;"><b>안내 내용</b></td>
            <td style="padding:10px; border:1px solid #d1d5db;">이벤트, 프로모션, 신규 기능 안내</td>
          </tr>
          <tr>
            <td style="padding:10px; border:1px solid #d1d5db;"><b>보유 기간</b></td>
            <td style="padding:10px; border:1px solid #d1d5db;">동의 철회 시까지</td>
          </tr>
        </tbody>
      </table>

      <p>동의하지 않아도 서비스 이용에는 제한이 없습니다.</p>

      <hr/>
      <p style="font-size:12px; color:#6b7280;">시행일: 2026-01-01</p>
    `
  }
]);


const allChecked = computed({
  get() {
    return terms.value.length > 0 && terms.value.every((t) => t.checked);
  },
  set(val) {
    terms.value.forEach((t) => {
      t.checked = val;
    });
  }
});

const openTerm = (term) => {
  activeTerm.value = term;
};

const closeModal = () => {
  activeTerm.value = null;
};

watch(emailDomainSelect, (val) => {
  if (val) {
    emailDomainInput.value = val;
  }
});

// 아이디를 수정하면 중복검사 상태를 초기화
watch(username, () => {
  usernameStatus.value = "";
});

const handleCheckUsername = async () => {
  const value = username.value.trim();
  if (!value) {
    usernameStatus.value = "empty";
    return;
  }

  try {
    const res = await fetch(
      `${API_BASE}/api/auth/user-id/check/?user_id=${encodeURIComponent(value)}`,
      {
        method: "GET"
      }
    );
    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      const detail = data?.detail || "아이디 중복 확인에 실패했습니다.";
      throw new Error(detail);
    }

    usernameStatus.value = data.available ? "ok" : "taken";
  } catch (err) {
    usernameStatus.value = "";
    message.value = err.message || "아이디 중복 확인 중 오류가 발생했습니다.";
    messageType.value = "error";
  }
};

const showPasswordMatch = computed(
  () => !!password.value && !!passwordConfirm.value && password.value === passwordConfirm.value
);

const showPasswordError = computed(
  () => !!password.value && !!passwordConfirm.value && password.value !== passwordConfirm.value
);

const buildEmail = () => {
  const domain = emailDomainSelect.value || emailDomainInput.value;
  if (!emailLocal.value || !domain) return "";
  return `${emailLocal.value}@${domain}`;
};

const buildPhone = () => {
  if (!phone1.value || !phone2.value || !phone3.value) return "";
  return `${phone1.value}-${phone2.value}-${phone3.value}`;
};

const buildBirthdate = () => {
  if (!birthYear.value || !birthMonth.value || !birthDay.value) return null;
  const month = String(birthMonth.value).padStart(2, "0");
  const day = String(birthDay.value).padStart(2, "0");
  return `${birthYear.value}-${month}-${day}`;
};

const handleEnter = () => {
  const active = document.activeElement;
  if (active === usernameInput.value) {
    handleCheckUsername();
    return;
  }
  if (active === emailLocalInput.value || active === emailDomainInputRef.value) {
    handleSendEmailCode();
    return;
  }
  if (active === emailCodeInput.value) {
    handleVerifyEmailCode();
    return;
  }
  handleSubmit();
};

const handleSubmit = async () => {
  message.value = "";

  // 필수 필드 하나씩 체크하면서 비어 있으면 개별 안내
  if (!username.value) {
    window.alert("아이디를 입력해 주세요.");
    return;
  }

  // 아이디 중복확인 선행
  if (usernameStatus.value !== "ok") {
    window.alert("아이디 중복확인을 먼저 해 주세요.");
    return;
  }

  if (!name.value) {
    window.alert("이름을 입력해 주세요.");
    return;
  }

  // 이메일 로컬파트를 안 적었으면 아이디를 대신 사용
  if (!emailLocal.value && username.value) {
    emailLocal.value = username.value;
  }

  if (!emailLocal.value) {
    window.alert("이메일 아이디(username)를 입력해 주세요.");
    return;
  }

  const hasEmailDomain = emailDomainSelect.value || emailDomainInput.value;
  if (!hasEmailDomain) {
    window.alert("이메일 도메인을 선택하거나 입력해 주세요.");
    return;
  }

  const email = buildEmail();
  if (!email) {
    window.alert("이메일을 올바르게 입력해 주세요.");
    return;
  }

  if (!emailVerified.value) {
    window.alert("이메일 인증을 완료해 주세요.");
    return;
  }

  if (!password.value) {
    window.alert("비밀번호를 입력해 주세요.");
    return;
  }

  if (!passwordConfirm.value) {
    window.alert("비밀번호 확인을 입력해 주세요.");
    return;
  }

  if (password.value !== passwordConfirm.value) {
    window.alert("비밀번호와 비밀번호 확인이 일치하지 않습니다.");
    return;
  }

  if (!birthYear.value || !birthMonth.value || !birthDay.value) {
    window.alert("생년월일을 모두 선택해 주세요.");
    return;
  }

  const notAgreed = terms.value.filter((t) => t.required && !t.checked);
  if (notAgreed.length) {
    window.alert("필수 약관에 동의해 주세요.");
    return;
  }

  const phone_number = buildPhone();
  const birthdate = buildBirthdate();

  pending.value = true;
  try {
    const res = await fetch(`${API_BASE}/api/auth/signup/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: username.value,
        email,
        name: name.value,
        password: password.value,
        phone_number: phone_number || null,
        birthdate
      })
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      // 필드별 에러 메시지(이메일/아이디/전화번호 중복 등)를 최대한 친절하게 추출
      let detail = data?.detail;
      if (!detail && data) {
        const messages = [];
        if (Array.isArray(data.email) && data.email.length) {
          messages.push(data.email[0]);
        }
        if (Array.isArray(data.user_id) && data.user_id.length) {
          messages.push(data.user_id[0]);
        }
        if (Array.isArray(data.phone_number) && data.phone_number.length) {
          messages.push(data.phone_number[0]);
        }

        if (!messages.length) {
          const firstKey = Object.keys(data)[0];
          const firstVal = data[firstKey];
          if (Array.isArray(firstVal) && firstVal.length) {
            detail = firstVal[0];
          } else if (typeof firstVal === "string") {
            detail = firstVal;
          }
        } else {
          detail = messages.join("\n");
        }
      }
      detail = detail || "가입에 실패했습니다.";
      window.alert(detail);
      throw new Error(detail);
    }
    message.value = "가입이 완료되었습니다. 로그인 페이지로 이동합니다.";
    messageType.value = "success";
    // 성공 안내 후 로그인 페이지로 이동
    window.alert("회원가입이 완료되었습니다. 로그인 페이지로 이동합니다.");
    password.value = "";
    passwordConfirm.value = "";
    router.push("/login");
  } catch (err) {
    message.value = err.message || "가입 중 오류가 발생했습니다.";
    messageType.value = "error";
  } finally {
    pending.value = false;
  }
};

const handleSendEmailCode = async () => {
  const email = buildEmail();
  if (!email) {
    message.value = "이메일을 올바르게 입력해 주세요.";
    messageType.value = "error";
    emailInlineMessage.value = message.value;
    emailInlineType.value = "error";
    return;
  }
  emailSending.value = true;
  message.value = "";
  try {
    const res = await fetch(`${API_BASE}/api/auth/email/send/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email })
    });
    let data = null;
    try {
      data = await res.json();
    } catch (e) {
      // non-JSON 응답일 경우 대비
    }
    if (!res.ok) {
      const detail = data?.detail || `인증번호 발송에 실패했습니다. (status ${res.status})`;
      throw new Error(detail);
    }
    message.value = "인증번호를 전송했습니다. 메일을 확인해 주세요.";
    messageType.value = "success";
    emailInlineMessage.value = message.value;
    emailInlineType.value = "success";
  } catch (err) {
    message.value = err.message || "인증번호 발송 중 오류가 발생했습니다.";
    messageType.value = "error";
    emailInlineMessage.value = message.value;
    emailInlineType.value = "error";
  } finally {
    emailSending.value = false;
  }
};

const handleVerifyEmailCode = async () => {
  const email = buildEmail();
  if (!email || !emailCode.value) {
    message.value = "이메일과 인증번호를 입력해 주세요.";
    messageType.value = "error";
    emailInlineMessage.value = message.value;
    emailInlineType.value = "error";
    return;
  }
  emailVerifying.value = true;
  message.value = "";
  try {
    const res = await fetch(`${API_BASE}/api/auth/email/verify/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, code: emailCode.value })
    });
    let data = null;
    try {
      data = await res.json();
    } catch (e) {
      // non-JSON 응답일 경우 대비
    }
    if (!res.ok) {
      const detail = data?.detail || `인증에 실패했습니다. (status ${res.status})`;
      throw new Error(detail);
    }
    emailVerified.value = true;
    message.value = "이메일 인증이 완료되었습니다.";
    messageType.value = "success";
    emailInlineMessage.value = message.value;
    emailInlineType.value = "success";
  } catch (err) {
    message.value = err.message || "인증 중 오류가 발생했습니다.";
    messageType.value = "error";
    emailInlineMessage.value = message.value;
    emailInlineType.value = "error";
  } finally {
    emailVerifying.value = false;
  }
};
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap");

.signup-page {
  min-height: 100vh;
  background: #f6f5ef;
  font-family: "Inter", sans-serif;
  color: #111827;
  display: flex;
  flex-direction: column;
}

.signup-header {
  padding: 12px 24px 0;
}

.page-label {
  margin: 0;
  font-size: 14px;
  color: #9ca3af;
}

.signup-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 16px 48px;
}

.card {
  width: 100%;
  max-width: 980px;
  background: #f8f6ee;
  border-radius: 8px;
  padding: 56px 52px 64px;
}

.title {
  margin: 0 0 40px;
  text-align: center;
  font-size: 52px;
  font-weight: 800;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: 72px;
  row-gap: 24px;
}

.form-actions {
  grid-column: 1 / -1;
  display: flex;
  justify-content: center;
  margin-top: 12px;
}

.field-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field-label {
  font-size: 16px;
  font-weight: 800;
}

.field-line {
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid #111827;
  padding-bottom: 4px;
}

.field-input {
  flex: 1;
  border: none;
  background: transparent;
  outline: none;
  font-size: 14px;
}

.phone-line {
  gap: 6px;
}

.phone-input {
  flex: 0 0 64px;
  text-align: center;
}

.hyphen {
  flex: 0 0 auto;
}

.hint-text {
  margin: 2px 0 0;
  font-size: 12px;
  color: #6b7280;
}

.hint-text.success {
  color: #16a34a;
}

.hint-text.error {
  color: #dc2626;
}

.password-hint {
  margin: 2px 0 0;
  font-size: 12px;
}

.password-hint.success {
  color: #16a34a;
}

.password-hint.error {
  color: #dc2626;
}

.error-line {
  border-bottom-color: #dc2626;
}

.success-line {
  border-bottom-color: #16a34a;
}

.pill-button {
  padding: 4px 12px;
  border-radius: 999px;
  border: none;
  background: #111827;
  color: #f9fafb;
  font-size: 12px;
  cursor: pointer;
}

.field-line.email-line {
  gap: 2px;
}

.email-local {
  flex: 0 0 70px;
  padding-bottom: 0;
}

.at {
  padding: 0 4px;
}

.email-domain {
  flex: 0 0 90px;
  border-radius: 999px;
  border: 1px solid #d1d5db;
  padding: 4px 10px;
  font-size: 12px;
}

.email-domain-input {
  flex: 1 1 auto;
  border: none;
  background: transparent;
  outline: none;
  font-size: 12px;
  padding-bottom: 0;
}

.email-send-button {
  flex: 0 0 auto;
  margin-left: auto;
  white-space: nowrap;
}

.chip {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 999px;
  background: #e5e7eb;
  font-size: 12px;
}

.birth-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.birth-select {
  flex: 1;
  min-width: 0;
  border-radius: 999px;
  border: 1px solid #d1d5db;
  padding: 6px 10px;
  font-size: 12px;
  background: #ffffff;
}

.submit-button {
  display: block;
  margin: 40px auto 0;
  padding: 11px 40px;
  border-radius: 999px;
  border: none;
  background: #111827;
  color: #f9fafb;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.3);
}

.submit-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}

.email-inline-msg {
  margin: 4px 0 0;
  font-size: 12px;
}

.email-inline-msg.success {
  color: #15803d;
}

.email-inline-msg.error {
  color: #b91c1c;
}

.terms-block {
  grid-column: 1 / -1;
  padding: 12px 0 4px;
}

.terms-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.terms-all {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
}

.terms-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.terms-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.term-check {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
}

.term-link {
  background: none;
  border: none;
  padding: 0;
  color: #111827;
  text-decoration: underline;
  cursor: pointer;
  font-weight: 700;
}

.term-required {
  color: #dc2626;
}

.term-subtext {
  font-size: 12px;
  color: #6b7280;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-card {
  width: min(800px, 90vw);
  max-height: 80vh;
  background: #ffffff;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.25);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  font-weight: 800;
  font-size: 18px;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  line-height: 1.6;
  font-size: 14px;
}

.modal-close {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
}

@media (max-width: 768px) {
  .card {
    padding: 40px 24px 48px;
  }

  .form-grid {
    grid-template-columns: 1fr;
    column-gap: 0;
  }
}
</style>
