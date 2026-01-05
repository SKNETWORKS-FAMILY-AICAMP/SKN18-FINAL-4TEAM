<template>
  <div class="profile-edit-page">
    <div class="bg-grid"></div>

    <header class="page-header">
      <div class="nav-left">
        <RouterLink to="/mypage" class="nav-back-btn">
          &larr; MYPAGE
        </RouterLink>
      </div>

      <RouterLink to="/" class="nav-logo">JOBTORY</RouterLink>

      <div class="nav-right">
        </div>
    </header>

    <main class="edit-content">
      <div class="stylized-card form-card">
        <div class="card-header">
          <h1 class="title">EDIT PROFILE</h1>
          <p class="subtitle">계정 정보와 프로필 상세 내용을 수정합니다.</p>
        </div>

        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>회원정보를 불러오는 중...</p>
        </div>
        
        <div v-else-if="loadError" class="error-state">
          {{ loadError }}
        </div>

        <div v-else class="form-body">
          <section class="form-section">
            <h3 class="section-label">ACCOUNT INFO</h3>
            <div class="form-grid">
              <div class="field-group">
                <label>아이디</label>
                <input v-model="username" type="text" class="input-field readonly" readonly disabled />
                <span class="field-hint">아이디는 변경 불가</span>
              </div>

              <div class="field-group">
                <label>이메일</label>
                <input v-model="email" type="email" class="input-field readonly" readonly disabled />
                <span class="field-hint">이메일은 변경 불가</span>
              </div>

              <div class="field-group">
                <label>이름</label>
                <input v-model="name" type="text" class="input-field" placeholder="이름 입력" />
              </div>

              <div class="field-group">
                <label>전화번호</label>
                <div class="multi-input-row">
                  <input v-model="phone1" type="tel" maxlength="3" class="input-field center-text" />
                  <span class="separator">-</span>
                  <input v-model="phone2" type="tel" maxlength="4" class="input-field center-text" />
                  <span class="separator">-</span>
                  <input v-model="phone3" type="tel" maxlength="4" class="input-field center-text" />
                </div>
              </div>

              <div class="field-group full-width">
                <label>생년월일</label>
                <div class="multi-input-row">
                  <select v-model="birthYear" class="input-field">
                    <option value="">년도</option>
                    <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
                  </select>
                  <select v-model="birthMonth" class="input-field">
                    <option value="">월</option>
                    <option v-for="m in months" :key="m" :value="m">{{ m }}</option>
                  </select>
                  <select v-model="birthDay" class="input-field">
                    <option value="">일</option>
                    <option v-for="d in days" :key="d" :value="d">{{ d }}</option>
                  </select>
                </div>
              </div>
            </div>
          </section>

          <div class="divider"></div>

          <section class="form-section">
            <h3 class="section-label">CAREER PROFILE</h3>
            <div class="form-grid">
              <div class="field-group">
                <label>최종 학력 *</label>
                <div class="select-wrapper">
                  <select v-model="profileForm.graduated_school" class="input-field">
                    <option value="">선택해주세요</option>
                    <option v-for="opt in graduatedOptions" :key="opt" :value="opt">{{ opt }}</option>
                  </select>
                </div>
              </div>

              <div class="field-group">
                <label>학교명</label>
                <input v-model="profileForm.university" type="text" class="input-field" placeholder="학교명 입력" />
              </div>

              <div class="field-group">
                <label>전공</label>
                <div class="select-wrapper">
                  <select v-model="profileForm.major" class="input-field">
                    <option value="">선택해주세요</option>
                    <option v-for="opt in majorOptions" :key="opt" :value="opt">{{ opt }}</option>
                  </select>
                </div>
              </div>

              <div class="field-group">
                <label>학적 상태</label>
                <div class="select-wrapper">
                  <select v-model="profileForm.academic_status" class="input-field">
                    <option value="">선택해주세요</option>
                    <option v-for="opt in academicOptions" :key="opt" :value="opt">{{ opt }}</option>
                  </select>
                </div>
              </div>

              <div class="field-group">
                <label>졸업(예정) 연도</label>
                <input v-model="profileForm.graduation_year" type="number" class="input-field" placeholder="YYYY" />
              </div>

              <div class="field-group">
                <label>경력 레벨 *</label>
                <div class="select-wrapper">
                  <select v-model="profileForm.career_level" class="input-field">
                    <option value="">선택해주세요</option>
                    <option v-for="opt in careerOptions" :key="opt" :value="opt">{{ opt }}</option>
                  </select>
                </div>
              </div>

              <div class="field-group">
                <label>현재 구직 상태</label>
                <div class="select-wrapper">
                  <select v-model="profileForm.current_status" class="input-field">
                    <option value="">선택해주세요</option>
                    <option v-for="opt in statusOptions" :key="opt" :value="opt">{{ opt }}</option>
                  </select>
                </div>
              </div>
              
              <div class="field-group">
                <label>희망 근무지</label>
                <div class="select-wrapper">
                  <select v-model="profileForm.region_single" class="input-field">
                    <option value="">선택해주세요</option>
                    <option v-for="opt in regionOptions" :key="opt" :value="opt">{{ opt }}</option>
                  </select>
                </div>
              </div>

              <div class="field-group full-width">
                <label>기술 스택</label>
                <div class="chips-container">
                  <label v-for="opt in techStackOptions" :key="opt" class="chip-item">
                    <input type="checkbox" :value="opt" v-model="profileForm.tech_stack" />
                    <span class="chip-label">{{ opt }}</span>
                  </label>
                </div>
              </div>

              <div class="field-group full-width">
                <label>희망 직무</label>
                <div class="chips-container">
                  <label v-for="opt in desiredRoleOptions" :key="opt" class="chip-item">
                    <input type="checkbox" :value="opt" v-model="profileForm.desired_role" />
                    <span class="chip-label">{{ opt }}</span>
                  </label>
                </div>
              </div>
              
               <div class="field-group full-width">
                <label>세부 희망 직무</label>
                <div class="chips-container">
                  <label v-for="opt in detailedRoleOptions" :key="opt" class="chip-item">
                    <input type="checkbox" :value="opt" v-model="profileForm.detailed_role" />
                    <span class="chip-label">{{ opt }}</span>
                  </label>
                </div>
              </div>
            </div>
          </section>

          <div class="divider"></div>

          <section class="form-section">
            <div class="toggle-header" @click="showPasswordChange = !showPasswordChange">
              <h3 class="section-label">PASSWORD CHANGE</h3>
              <span class="toggle-icon">{{ showPasswordChange ? '−' : '+' }}</span>
            </div>
            
            <div v-if="showPasswordChange" class="password-form form-grid">
               <div class="field-group full-width">
                <label>현재 비밀번호</label>
                <input v-model="currentPassword" type="password" class="input-field" placeholder="현재 사용 중인 비밀번호" />
              </div>
              <div class="field-group">
                <label>새 비밀번호</label>
                <input v-model="newPassword" type="password" class="input-field" placeholder="변경할 비밀번호" />
              </div>
              <div class="field-group">
                <label>새 비밀번호 확인</label>
                <input 
                  v-model="newPasswordConfirm" 
                  type="password" 
                  class="input-field" 
                  placeholder="비밀번호 재입력" 
                  :class="{ 'error': showPasswordError, 'success': showPasswordMatch }"
                />
                <p v-if="showPasswordMatch" class="msg success">일치합니다</p>
                <p v-if="showPasswordError" class="msg error">일치하지 않습니다</p>
              </div>
            </div>
          </section>

          <div class="action-bar sticky-bottom">
            <p v-if="message" :class="['status-msg', messageType]">{{ message }}</p>
            <div class="btn-group">
              <button type="button" class="btn ghost" @click="handleCancel">취소</button>
              <button type="button" class="btn primary" :disabled="pending" @click="handleSubmit">
                {{ pending ? "저장 중..." : "변경사항 저장" }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter, RouterLink } from "vue-router";
import { useAuth } from "../hooks/useAuth";
import { useProfileOptions } from "../hooks/useProfileOptions";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const router = useRouter();
const auth = useAuth();
const { options: optionData, fetchProfileOptions } = useProfileOptions();

// Date Utils
const currentYear = new Date().getFullYear();
const years = Array.from({ length: 70 }, (_, i) => currentYear - i);
const months = Array.from({ length: 12 }, (_, i) => i + 1);
const days = Array.from({ length: 31 }, (_, i) => i + 1);

// State
const loading = ref(true);
const loadError = ref("");
const pending = ref(false);
const message = ref("");
const messageType = ref("info");
const showPasswordChange = ref(false);

// Form Data
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

const profileForm = reactive({
  graduated_school: "",
  university: "",
  major: "",
  academic_status: "",
  graduation_year: "",
  career_level: "",
  current_status: "",
  tech_stack: [],
  desired_role: [],
  detailed_role: [],
  region_single: "",
});

// Options
const graduatedOptions = computed(() => optionData.value?.graduated_school || []);
const majorOptions = computed(() => optionData.value?.major || []);
const academicOptions = computed(() => optionData.value?.academic_status || []);
const careerOptions = computed(() => optionData.value?.career_level || []);
const statusOptions = computed(() => optionData.value?.current_status || []);
const techStackOptions = computed(() => optionData.value?.tech_stack || []);
const desiredRoleOptions = computed(() => optionData.value?.desired_role || []);
const detailedRoleOptions = computed(() => optionData.value?.detailed_role || []);
const regionOptions = computed(() => optionData.value?.region || []);

const showPasswordMatch = computed(() => !!newPassword.value && newPassword.value === newPasswordConfirm.value);
const showPasswordError = computed(() => !!newPasswordConfirm.value && newPassword.value !== newPasswordConfirm.value);

// Helpers
const buildPhone = () => (!phone1.value || !phone2.value || !phone3.value) ? "" : `${phone1.value}-${phone2.value}-${phone3.value}`;
const parsePhone = (str) => { if(!str) return; const p = str.split("-"); if(p.length===3) { phone1.value=p[0]; phone2.value=p[1]; phone3.value=p[2]; }};
const buildBirthdate = () => (!birthYear.value || !birthMonth.value || !birthDay.value) ? null : `${birthYear.value}-${String(birthMonth.value).padStart(2,"0")}-${String(birthDay.value).padStart(2,"0")}`;
const parseBirthdate = (str) => { if(!str) return; const p = str.split("-"); if(p.length===3) { birthYear.value=p[0]; birthMonth.value=parseInt(p[1],10); birthDay.value=parseInt(p[2],10); }};

const mapProfileDetail = (data) => {
  profileForm.graduated_school = data.graduated_school || "";
  profileForm.university = data.university || "";
  profileForm.major = data.major || "";
  profileForm.academic_status = data.academic_status || "";
  profileForm.graduation_year = data.graduation_year || "";
  profileForm.career_level = data.career_level || "";
  profileForm.current_status = data.current_status || "";
  profileForm.tech_stack = data.tech_stack || [];
  profileForm.desired_role = data.desired_role || [];
  profileForm.detailed_role = data.detailed_role || [];
  profileForm.region_single = (data.region && data.region[0]) || "";
};

const loadProfile = async () => {
  loading.value = true;
  loadError.value = "";
  try {
    const valid = await auth.ensureValidSession();
    if (!valid) throw new Error("로그인이 필요합니다.");
    const token = auth.token?.value;
    
    // 1. User Info
    const res = await fetch(`${API_BASE}/api/user/profile/`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if(!res.ok) throw new Error("회원정보 로드 실패");
    const data = await res.json();
    username.value = data.user_id || "";
    name.value = data.name || "";
    email.value = data.email || "";
    parsePhone(data.phone_number);
    parseBirthdate(data.birthdate);

    // 2. Profile Detail
    const detailRes = await fetch(`${API_BASE}/api/user/profile/detail/`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if(detailRes.ok) mapProfileDetail(await detailRes.json());
    
  } catch (err) {
    loadError.value = err.message;
  } finally {
    loading.value = false;
  }
};

const handleCancel = () => {
  if (confirm("수정을 취소하시겠습니까?")) router.push("/mypage");
};

const handleSubmit = async () => {
  message.value = "";
  if (!name.value) return alert("이름을 입력해주세요.");
  
  if (showPasswordChange.value) {
    if (!currentPassword.value || !newPassword.value) return alert("비밀번호 항목을 입력해주세요.");
    if (newPassword.value !== newPasswordConfirm.value) return alert("새 비밀번호가 일치하지 않습니다.");
  }

  const updateData = {
    name: name.value,
    phone_number: buildPhone() || null,
    birthdate: buildBirthdate() || null,
  };
  
  if (showPasswordChange.value) {
    updateData.current_password = currentPassword.value;
    updateData.new_password = newPassword.value;
  }

  pending.value = true;
  try {
    const token = auth.token?.value;
    // 1. Update User
    const res = await fetch(`${API_BASE}/api/user/profile/`, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify(updateData),
    });
    if (!res.ok) {
       const d = await res.json();
       throw new Error(d.detail || "회원정보 수정 실패");
    }

    // 2. Update Profile Detail
    const detailPayload = {
      ...profileForm,
      region: profileForm.region_single ? [profileForm.region_single] : []
    };
    const detailRes = await fetch(`${API_BASE}/api/user/profile/detail/`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify(detailPayload),
    });
    if (!detailRes.ok) throw new Error("프로필 상세 저장 실패");

    message.value = "저장되었습니다.";
    messageType.value = "success";
    showPasswordChange.value = false;
    currentPassword.value = ""; newPassword.value = ""; newPasswordConfirm.value = "";
    
    setTimeout(() => router.push("/mypage"), 1000);
  } catch (err) {
    message.value = err.message;
    messageType.value = "error";
  } finally {
    pending.value = false;
  }
};

onMounted(() => {
  fetchProfileOptions();
  loadProfile();
});
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap");

.profile-edit-page {
  min-height: 100vh;
  background: #f8f4eb;
  font-family: "Inter", sans-serif;
  color: #111827;
  position: relative;
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

/* 헤더 */
.page-header {
  position: relative;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 30px 40px;
}

.nav-logo {
  font-family: "Inter", sans-serif;
  font-weight: 900;
  font-size: 28px;
  color: #000;
  text-decoration: none;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.nav-back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 700;
  color: #4b5563;
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 8px;
  transition: all 0.2s;
}
.nav-back-btn:hover {
  background: rgba(0,0,0,0.05);
  color: #111827;
}

/* 메인 컨텐츠 */
.edit-content {
  position: relative;
  z-index: 1;
  max-width: 800px;
  margin: 0 auto;
  padding: 0 20px 80px;
}

/* 카드 스타일 */
.stylized-card {
  background: #ffffff;
  border-radius: 24px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 20px 48px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.card-header {
  padding: 40px 40px 24px;
  border-bottom: 1px solid #f3f4f6;
  text-align: center;
}

.title {
  margin: 0;
  font-size: 28px;
  font-weight: 900;
  letter-spacing: -0.02em;
}

.subtitle {
  margin: 8px 0 0;
  color: #6b7280;
  font-size: 15px;
}

.form-body {
  padding: 40px;
}

/* 폼 섹션 */
.form-section {
  margin-bottom: 32px;
}

.section-label {
  font-size: 12px;
  font-weight: 800;
  color: #9ca3af;
  letter-spacing: 0.05em;
  margin: 0 0 20px;
  text-transform: uppercase;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.field-group.full-width { grid-column: 1 / -1; }

.field-group label {
  font-size: 13px;
  font-weight: 700;
  color: #374151;
}

/* Input Styles */
.input-field {
  width: 100%;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  font-family: inherit;
  font-size: 14px;
  background: #ffffff;
  color: #111827;
  transition: all 0.2s;
  box-sizing: border-box;
}

.input-field:focus {
  outline: none;
  border-color: #111827;
  box-shadow: 0 0 0 3px rgba(17, 24, 39, 0.08);
}

.input-field.readonly {
  background: #f9fafb;
  color: #6b7280;
  border-color: #f3f4f6;
  cursor: not-allowed;
}

.field-hint {
  font-size: 12px;
  color: #9ca3af;
}

.select-wrapper {
  position: relative;
}

/* Multi Input Row (Phone, Birth) */
.multi-input-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.multi-input-row .input-field {
  flex: 1;
}
.center-text { text-align: center; }
.separator { font-weight: 700; color: #d1d5db; }

/* Chips / Checkboxes */
.chips-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip-item {
  position: relative;
  cursor: pointer;
}

.chip-item input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.chip-label {
  display: inline-block;
  padding: 8px 16px;
  border-radius: 8px;
  background: #ffffff;
  border: 1px solid #d1d5db;
  font-size: 13px;
  font-weight: 600;
  color: #4b5563;
  transition: all 0.2s;
}

.chip-item:hover .chip-label {
  border-color: #9ca3af;
  background: #f9fafb;
}

.chip-item input:checked + .chip-label {
  background: #111827;
  color: #ffffff;
  border-color: #111827;
  box-shadow: 0 4px 10px rgba(0,0,0,0.15);
}

/* Password Toggle */
.toggle-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  padding-bottom: 10px;
  border-bottom: 1px dashed #e5e7eb;
}
.toggle-header h3 { margin: 0; }
.toggle-icon { font-size: 24px; font-weight: 300; color: #9ca3af; }
.password-form { margin-top: 24px; padding: 20px; background: #f9fafb; border-radius: 12px; }

.msg { font-size: 12px; margin-top: 4px; font-weight: 600; }
.msg.success { color: #059669; }
.msg.error { color: #dc2626; }
.input-field.error { border-color: #dc2626; }
.input-field.success { border-color: #059669; }

/* Sticky Action Bar */
.action-bar {
  position: sticky;
  bottom: 0;
  background: #ffffff;
  padding: 20px 0 0;
  margin-top: 40px;
  border-top: 1px solid #f3f4f6;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.sticky-bottom { z-index: 5; }

.status-msg {
  font-size: 13px;
  font-weight: 600;
}
.status-msg.success { color: #059669; }
.status-msg.error { color: #dc2626; }

.btn-group {
  margin-left: auto;
  display: flex;
  gap: 12px;
}

.btn {
  padding: 12px 24px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn.ghost {
  background: transparent;
  color: #6b7280;
}
.btn.ghost:hover {
  background: #f3f4f6;
  color: #111827;
}

.btn.primary {
  background: #111827;
  color: #ffffff;
}
.btn.primary:hover {
  background: #000000;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.btn.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.divider { height: 1px; background: #f3f4f6; margin: 32px 0; }

/* Loading */
.loading-state { text-align: center; padding: 60px; color: #9ca3af; }
.spinner {
  width: 30px; height: 30px; border: 3px solid #e5e7eb; border-top-color: #111827;
  border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 16px;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Mobile */
@media (max-width: 640px) {
  .form-grid { grid-template-columns: 1fr; }
  .card-header, .form-body { padding: 24px; }
  .page-header { padding: 20px; }
  .action-bar { flex-direction: column; gap: 16px; align-items: stretch; }
  .btn-group { margin-left: 0; justify-content: stretch; }
  .btn { width: 100%; }
}
</style>