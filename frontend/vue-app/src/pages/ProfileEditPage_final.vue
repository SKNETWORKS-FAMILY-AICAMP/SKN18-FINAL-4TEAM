<template>
  <div class="profile-edit-page">
    <header class="profile-header">
      <RouterLink to="/" class="brand">
        <span class="brand-mark">JOBTORY</span>
      </RouterLink>
      <p class="page-label">회원정보 수정</p>
    </header>

    <main class="profile-main">
      <section class="card">
        <h1 class="title">프로필 수정</h1>

        <div v-if="loading" class="loading-message">
          회원정보를 불러오는 중...
        </div>

        <div v-else-if="loadError" class="error-message">
          {{ loadError }}
        </div>

        <div v-else class="form-grid">
          <!-- 아이디 (읽기 전용) -->
          <div class="field-block">
            <label class="field-label">아이디</label>
            <div class="field-line readonly">
              <input 
                v-model="username" 
                class="field-input" 
                type="text" 
                readonly 
                disabled
              />
            </div>
            <p class="hint-text">아이디는 변경할 수 없습니다.</p>
          </div>

          <!-- 이름 -->
          <div class="field-block">
            <label class="field-label">이름</label>
            <div class="field-line">
              <input v-model="name" class="field-input" type="text" placeholder="홍길동" />
            </div>
          </div>

          <!-- 이메일 (읽기 전용) -->
          <div class="field-block">
            <label class="field-label">이메일</label>
            <div class="field-line readonly">
              <input 
                v-model="email" 
                class="field-input" 
                type="email" 
                readonly 
                disabled
              />
            </div>
            <p class="hint-text">이메일은 변경할 수 없습니다.</p>
          </div>

          <!-- 전화번호 -->
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

          <!-- 생년월일 -->
          <div class="field-block full-width">
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

          <!-- 비밀번호 변경 섹션 -->
          <div class="field-block full-width password-section">
            <div class="section-header">
              <label class="field-label">비밀번호 변경</label>
              <button 
                type="button" 
                class="toggle-button" 
                @click="showPasswordChange = !showPasswordChange"
              >
                {{ showPasswordChange ? '숨기기' : '변경하기' }}
              </button>
            </div>
            <p class="hint-text">비밀번호를 변경하지 않으려면 이 섹션을 비워두세요.</p>
          </div>

          <template v-if="showPasswordChange">
            <!-- 현재 비밀번호 -->
            <div class="field-block">
              <label class="field-label">현재 비밀번호</label>
              <div class="field-line">
                <input 
                  v-model="currentPassword" 
                  class="field-input" 
                  type="password" 
                  placeholder="현재 비밀번호 입력"
                />
              </div>
            </div>

            <!-- 새 비밀번호 -->
            <div class="field-block">
              <label class="field-label">새 비밀번호</label>
              <div class="field-line">
                <input 
                  v-model="newPassword" 
                  class="field-input" 
                  type="password" 
                  placeholder="새 비밀번호 입력"
                />
              </div>
            </div>

            <!-- 새 비밀번호 확인 -->
            <div class="field-block full-width">
              <label class="field-label">새 비밀번호 확인</label>
              <div class="field-line" :class="{ 'error-line': showPasswordError, 'success-line': showPasswordMatch }">
                <input 
                  v-model="newPasswordConfirm" 
                  class="field-input" 
                  type="password" 
                  placeholder="새 비밀번호 재입력"
                />
              </div>
              <p v-if="showPasswordMatch" class="password-hint success">비밀번호가 일치합니다.</p>
              <p v-else-if="showPasswordError" class="password-hint error">비밀번호가 일치하지 않습니다.</p>
            </div>
          </template>
        </div>

        <div class="button-group" v-if="!loading && !loadError">
          <button 
            type="button" 
            class="cancel-button" 
            @click="handleCancel"
          >
            취소
          </button>
          <button 
            type="button" 
            class="submit-button" 
            :disabled="pending" 
            @click="handleSubmit"
          >
            {{ pending ? "저장 중..." : "저장하기" }}
          </button>
        </div>

        <p v-if="message" :class="['message', messageType]">
          {{ message }}
        </p>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter, RouterLink } from "vue-router";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const router = useRouter();

// 날짜 옵션
const currentYear = new Date().getFullYear();
const years = Array.from({ length: 70 }, (_, i) => currentYear - i);
const months = Array.from({ length: 12 }, (_, i) => i + 1);
const days = Array.from({ length: 31 }, (_, i) => i + 1);

// 상태 관리
const loading = ref(true);
const loadError = ref("");
const pending = ref(false);
const message = ref("");
const messageType = ref("info");
const showPasswordChange = ref(false);

// 폼 데이터
const username = ref("");
const name = ref("");
const email = ref("");
const phone1 = ref("");
const phone2 = ref("");
const phone3 = ref("");
const birthYear = ref("");
const birthMonth = ref("");
const birthDay = ref("");
const currentPassword = ref("");
const newPassword = ref("");
const newPasswordConfirm = ref("");

// 비밀번호 검증
const showPasswordMatch = computed(
  () => !!newPassword.value && !!newPasswordConfirm.value && newPassword.value === newPasswordConfirm.value
);

const showPasswordError = computed(
  () => !!newPassword.value && !!newPasswordConfirm.value && newPassword.value !== newPasswordConfirm.value
);

// 전화번호 조합
const buildPhone = () => {
  if (!phone1.value || !phone2.value || !phone3.value) return "";
  return `${phone1.value}-${phone2.value}-${phone3.value}`;
};

// 생년월일 조합
const buildBirthdate = () => {
  if (!birthYear.value || !birthMonth.value || !birthDay.value) return null;
  const month = String(birthMonth.value).padStart(2, "0");
  const day = String(birthDay.value).padStart(2, "0");
  return `${birthYear.value}-${month}-${day}`;
};

// 전화번호 파싱
const parsePhone = (phoneStr) => {
  if (!phoneStr) return;
  const parts = phoneStr.split("-");
  if (parts.length === 3) {
    phone1.value = parts[0];
    phone2.value = parts[1];
    phone3.value = parts[2];
  }
};

// 생년월일 파싱
const parseBirthdate = (dateStr) => {
  if (!dateStr) return;
  const parts = dateStr.split("-");
  if (parts.length === 3) {
    birthYear.value = parts[0];
    birthMonth.value = parseInt(parts[1], 10);
    birthDay.value = parseInt(parts[2], 10);
  }
};

// 회원정보 불러오기
const loadProfile = async () => {
  loading.value = true;
  loadError.value = "";

  const token = localStorage.getItem("access_token");
  if (!token) {
    loadError.value = "로그인이 필요합니다.";
    loading.value = false;
    setTimeout(() => router.push("/login"), 2000);
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/user/profile/`, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      }
    });

    if (!res.ok) {
      if (res.status === 401) {
        throw new Error("로그인 세션이 만료되었습니다. 다시 로그인해주세요.");
      }
      throw new Error("회원정보를 불러오는데 실패했습니다.");
    }

    const data = await res.json();
    
    // 데이터 채우기
    username.value = data.user_id || "";
    name.value = data.name || "";
    email.value = data.email || "";
    
    if (data.phone_number) {
      parsePhone(data.phone_number);
    }
    
    if (data.birthdate) {
      parseBirthdate(data.birthdate);
    }

  } catch (err) {
    loadError.value = err.message || "회원정보를 불러오는 중 오류가 발생했습니다.";
    if (err.message.includes("로그인")) {
      setTimeout(() => router.push("/login"), 2000);
    }
  } finally {
    loading.value = false;
  }
};

// 취소 버튼
const handleCancel = () => {
  if (confirm("수정을 취소하시겠습니까? 변경사항이 저장되지 않습니다.")) {
    router.push("/");
  }
};

// 저장 버튼
const handleSubmit = async () => {
  message.value = "";
  messageType.value = "info";

  // 필수 필드 검증
  if (!name.value) {
    window.alert("이름을 입력해 주세요.");
    return;
  }

  // 비밀번호 변경 시 검증
  if (showPasswordChange.value) {
    if (!currentPassword.value) {
      window.alert("현재 비밀번호를 입력해 주세요.");
      return;
    }
    if (!newPassword.value) {
      window.alert("새 비밀번호를 입력해 주세요.");
      return;
    }
    if (!newPasswordConfirm.value) {
      window.alert("새 비밀번호 확인을 입력해 주세요.");
      return;
    }
    if (newPassword.value !== newPasswordConfirm.value) {
      window.alert("새 비밀번호와 비밀번호 확인이 일치하지 않습니다.");
      return;
    }
  }

  const phone_number = buildPhone();
  const birthdate = buildBirthdate();

  // 수정할 데이터 준비
  const updateData = {
    name: name.value,
    phone_number: phone_number || null,
    birthdate: birthdate || null
  };

  // 비밀번호 변경이 있으면 추가
  if (showPasswordChange.value && currentPassword.value && newPassword.value) {
    updateData.current_password = currentPassword.value;
    updateData.new_password = newPassword.value;
  }

  const token = localStorage.getItem("access_token");
  if (!token) {
    window.alert("로그인이 필요합니다.");
    router.push("/login");
    return;
  }

  pending.value = true;
  try {
    const res = await fetch(`${API_BASE}/api/user/profile/`, {
      method: "PATCH",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(updateData)
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      const detail = data.detail || "회원정보 수정에 실패했습니다.";
      throw new Error(detail);
    }

    message.value = "회원정보가 성공적으로 수정되었습니다.";
    messageType.value = "success";
    
    // 비밀번호 필드 초기화
    currentPassword.value = "";
    newPassword.value = "";
    newPasswordConfirm.value = "";
    showPasswordChange.value = false;

    // 2초 후 메인 페이지로 이동
    setTimeout(() => {
      router.push("/");
    }, 2000);

  } catch (err) {
    message.value = err.message || "회원정보 수정 중 오류가 발생했습니다.";
    messageType.value = "error";
  } finally {
    pending.value = false;
  }
};

// 컴포넌트 마운트 시 회원정보 로드
onMounted(() => {
  loadProfile();
});
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap");

.profile-edit-page {
  min-height: 100vh;
  background: #f6f5ef;
  font-family: "Nunito", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #111827;
  display: flex;
  flex-direction: column;
}

.profile-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 32px;
  border-bottom: 1px solid #e5e7eb;
}

.brand {
  text-decoration: none;
}

.brand-mark {
  display: inline-block;
  padding: 8px 18px;
  border-radius: 999px;
  background: linear-gradient(135deg, #111827, #1f2937);
  color: #f9fafb;
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 0.02em;
}

.page-label {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #6b7280;
}

.profile-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 16px 60px;
}

.card {
  width: 100%;
  max-width: 980px;
  background: #f8f6ee;
  border-radius: 16px;
  padding: 56px 52px 64px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
}

.title {
  margin: 0 0 40px;
  text-align: center;
  font-size: 48px;
  font-weight: 800;
  color: #111827;
}

.loading-message,
.error-message {
  text-align: center;
  padding: 40px 20px;
  font-size: 16px;
  color: #6b7280;
}

.error-message {
  color: #dc2626;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: 72px;
  row-gap: 24px;
}

.field-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-block.full-width {
  grid-column: 1 / -1;
}

.field-label {
  font-size: 16px;
  font-weight: 800;
  color: #111827;
}

.field-line {
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 2px solid #111827;
  padding-bottom: 6px;
  transition: border-color 0.2s ease;
}

.field-line.readonly {
  border-bottom-color: #d1d5db;
  background: #f3f4f6;
  padding: 8px 12px;
  border-radius: 8px;
}

.field-line:focus-within {
  border-bottom-color: #84b091;
}

.field-input {
  flex: 1;
  border: none;
  background: transparent;
  outline: none;
  font-size: 14px;
  font-family: inherit;
  color: #111827;
}

.field-input:disabled {
  color: #9ca3af;
  cursor: not-allowed;
}

.phone-line {
  gap: 8px;
}

.phone-input {
  flex: 0 0 70px;
  text-align: center;
}

.hyphen {
  flex: 0 0 auto;
  color: #6b7280;
}

.hint-text {
  margin: 4px 0 0;
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
  margin: 4px 0 0;
  font-size: 12px;
  font-weight: 600;
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

.birth-row {
  display: flex;
  gap: 12px;
  align-items: center;
}

.birth-select {
  flex: 1;
  min-width: 0;
  border-radius: 8px;
  border: 1px solid #d1d5db;
  padding: 8px 12px;
  font-size: 14px;
  background: #ffffff;
  font-family: inherit;
  cursor: pointer;
}

.password-section {
  margin-top: 16px;
  padding-top: 24px;
  border-top: 2px solid #e5e7eb;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.toggle-button {
  padding: 6px 16px;
  border-radius: 999px;
  border: 1px solid #d1d5db;
  background: #ffffff;
  color: #111827;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.toggle-button:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.button-group {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 40px;
}

.cancel-button,
.submit-button {
  padding: 12px 32px;
  border-radius: 999px;
  border: none;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cancel-button {
  background: #e5e7eb;
  color: #374151;
}

.cancel-button:hover {
  background: #d1d5db;
}

.submit-button {
  background: linear-gradient(135deg, #111827, #1f2937);
  color: #f9fafb;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.25);
}

.submit-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.35);
}

.submit-button:active {
  transform: translateY(0);
}

.submit-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.message {
  margin-top: 24px;
  padding: 12px 20px;
  border-radius: 8px;
  text-align: center;
  font-size: 14px;
  font-weight: 600;
}

.message.success {
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #10b981;
}

.message.error {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #dc2626;
}

.message.info {
  background: #dbeafe;
  color: #1e40af;
  border: 1px solid #3b82f6;
}

@media (max-width: 768px) {
  .card {
    padding: 40px 24px 48px;
  }

  .form-grid {
    grid-template-columns: 1fr;
    column-gap: 0;
  }

  .title {
    font-size: 36px;
  }

  .button-group {
    flex-direction: column;
  }

  .cancel-button,
  .submit-button {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .profile-header {
    padding: 16px 20px;
  }

  .brand-mark {
    font-size: 16px;
    padding: 6px 14px;
  }

  .card {
    padding: 32px 20px 40px;
    border-radius: 12px;
  }

  .title {
    font-size: 28px;
  }
}
</style>