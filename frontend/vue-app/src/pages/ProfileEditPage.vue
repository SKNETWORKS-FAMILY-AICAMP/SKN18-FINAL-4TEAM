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
        <h1 class="title">프로필 및 계정 수정</h1>
        <p class="subtitle">필수 항목을 채우고 저장하면 마이페이지에 바로 반영됩니다.</p>

        <div v-if="loading" class="loading-message">회원정보를 불러오는 중...</div>
        <div v-else-if="loadError" class="error-message">{{ loadError }}</div>

        <div v-else class="form-grid">
          <div class="field-block">
            <label class="field-label">아이디</label>
            <div class="field-line readonly">
              <input v-model="username" class="field-input" type="text" readonly disabled />
            </div>
            <p class="hint-text">아이디는 변경할 수 없습니다.</p>
          </div>

          <div class="field-block">
            <label class="field-label">이름</label>
            <div class="field-line">
              <input v-model="name" class="field-input" type="text" placeholder="이름을 입력하세요" />
            </div>
          </div>

          <div class="field-block">
            <label class="field-label">이메일</label>
            <div class="field-line readonly">
              <input v-model="email" class="field-input" type="email" readonly disabled />
            </div>
            <p class="hint-text">이메일은 변경할 수 없습니다.</p>
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

          <div class="field-block full-width">
            <label class="field-label">생년월일</label>
            <div class="birth-row">
              <select v-model="birthYear" class="birth-select">
                <option value="">년</option>
                <option v-for="year in years" :key="year" :value="year">{{ year }}</option>
              </select>
              <select v-model="birthMonth" class="birth-select">
                <option value="">월</option>
                <option v-for="month in months" :key="month" :value="month">{{ month }}</option>
              </select>
              <select v-model="birthDay" class="birth-select">
                <option value="">일</option>
                <option v-for="day in days" :key="day" :value="day">{{ day }}</option>
              </select>
            </div>
          </div>

          <div class="subsection full-width">
            <h2 class="section-title">프로필</h2>
            <p class="section-desc">메인페이지 모달에서 입력한 user_profile 정보를 여기서도 수정할 수 있습니다.</p>
          </div>

          <div class="field-block">
            <label class="field-label">최종 학력 *</label>
            <div class="field-line">
              <select v-model="profileForm.graduated_school" class="field-input">
                <option value="">선택</option>
                <option v-for="opt in graduatedOptions" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </div>
          </div>

          <div class="field-block">
            <label class="field-label">학교명</label>
            <div class="field-line">
              <input v-model="profileForm.university" class="field-input" type="text" placeholder="학교명을 입력하세요" />
            </div>
          </div>

          <div class="field-block">
            <label class="field-label">전공</label>
            <div class="field-line">
              <select v-model="profileForm.major" class="field-input">
                <option value="">선택</option>
                <option value="전공">전공</option>
                <option value="비전공">비전공</option>
              </select>
            </div>
          </div>

          <div class="field-block">
            <label class="field-label">학적 상태</label>
            <div class="field-line">
              <select v-model="profileForm.academic_status" class="field-input">
                <option value="">선택</option>
                <option v-for="opt in academicOptions" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </div>
          </div>

          <div class="field-block">
            <label class="field-label">졸업(예정) 연도</label>
            <div class="field-line">
              <input v-model="profileForm.graduation_year" class="field-input" type="number" min="1900" max="2100" />
            </div>
          </div>

          <div class="field-block">
            <label class="field-label">경력 레벨 *</label>
            <div class="field-line">
              <select v-model="profileForm.career_level" class="field-input">
                <option value="">선택</option>
                <option v-for="opt in careerOptions" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </div>
          </div>

          <div class="field-block">
            <label class="field-label">현재 상태</label>
            <div class="field-line">
              <select v-model="profileForm.current_status" class="field-input">
                <option value="">선택</option>
                <option v-for="opt in statusOptions" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </div>
          </div>

          <div class="field-block full-width">
            <label class="field-label">기술 스택</label>
            <div class="chip-list">
              <label v-for="opt in techStackOptions" :key="opt" class="chip">
                <input type="checkbox" :value="opt" v-model="profileForm.tech_stack" />
                <span>{{ opt }}</span>
              </label>
            </div>
          </div>

          <div class="field-block full-width">
            <label class="field-label">희망 직무</label>
            <div class="chip-list">
              <label v-for="opt in desiredRoleOptions" :key="opt" class="chip">
                <input type="checkbox" :value="opt" v-model="profileForm.desired_role" />
                <span>{{ opt }}</span>
              </label>
            </div>
          </div>

          <div class="field-block full-width">
            <label class="field-label">세부 희망 직무</label>
            <div class="chip-list">
              <label v-for="opt in detailedRoleOptions" :key="opt" class="chip">
                <input type="checkbox" :value="opt" v-model="profileForm.detailed_role" />
                <span>{{ opt }}</span>
              </label>
            </div>
          </div>

          <div class="field-block">
            <label class="field-label">희망 근무지</label>
            <div class="field-line">
              <select v-model="profileForm.region_single" class="field-input">
                <option value="">선택</option>
                <option v-for="opt in regionOptions" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </div>
          </div>

          <div class="field-block full-width password-section">
            <div class="section-header">
              <label class="field-label">비밀번호 변경</label>
              <button type="button" class="toggle-button" @click="showPasswordChange = !showPasswordChange">
                {{ showPasswordChange ? "접기" : "변경하기" }}
              </button>
            </div>
            <p class="hint-text">비밀번호를 변경하지 않으려면 펼치지 않아도 됩니다.</p>
          </div>

          <template v-if="showPasswordChange">
            <div class="field-block">
              <label class="field-label">현재 비밀번호</label>
              <div class="field-line">
                <input v-model="currentPassword" class="field-input" type="password" placeholder="현재 비밀번호 입력" />
              </div>
            </div>

            <div class="field-block">
              <label class="field-label">새 비밀번호</label>
              <div class="field-line">
                <input v-model="newPassword" class="field-input" type="password" placeholder="새 비밀번호 입력" />
              </div>
            </div>

            <div class="field-block full-width">
              <label class="field-label">새 비밀번호 확인</label>
              <div class="field-line" :class="{ 'error-line': showPasswordError, 'success-line': showPasswordMatch }">
                <input
                  v-model="newPasswordConfirm"
                  class="field-input"
                  type="password"
                  placeholder="새 비밀번호 확인"
                />
              </div>
              <p v-if="showPasswordMatch" class="password-hint success">비밀번호가 일치합니다.</p>
              <p v-else-if="showPasswordError" class="password-hint error">비밀번호가 일치하지 않습니다.</p>
            </div>
          </template>
        </div>

        <div class="button-group" v-if="!loading && !loadError">
          <button type="button" class="cancel-button" @click="handleCancel">취소</button>
          <button type="button" class="submit-button" :disabled="pending" @click="handleSubmit">
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
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter, RouterLink } from "vue-router";
import { useAuth } from "../hooks/useAuth";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const router = useRouter();
const auth = useAuth();

const currentYear = new Date().getFullYear();
const years = Array.from({ length: 70 }, (_, i) => currentYear - i);
const months = Array.from({ length: 12 }, (_, i) => i + 1);
const days = Array.from({ length: 31 }, (_, i) => i + 1);

const loading = ref(true);
const loadError = ref("");
const pending = ref(false);
const message = ref("");
const messageType = ref("info");
const showPasswordChange = ref(false);

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

const graduatedOptions = ["고졸", "전문대졸(2,3년제)", "대졸(4년제 이상)", "석사 이상", "박사 이상"];
const academicOptions = ["재학", "휴학", "졸업", "중퇴"];
const careerOptions = ["junior (0~3년차)", "mid (4~7년차)", "senior (8~10년차)", "lead (10년차~)"];
const statusOptions = ["재직중", "이직", "구직중", "프리랜서", "기타"];
const techStackOptions = [
  "Python",
  "NumPy",
  "Pandas",
  "SciPy",
  "Scikit-learn",
  "XGBoost",
  "LightGBM",
  "CatBoost",
  "TensorFlow",
  "Keras",
  "PyTorch",
  "Transformers",
  "LangChain",
  "LangGraph",
  "OpenAI API",
  "HuggingFace Hub",
  "SentenceTransformers",
  "spaCy",
  "NLTK",
  "MLflow",
  "Airflow",
  "DVC",
  "Optuna",
  "Jupyter Notebook",
  "JupyterLab",
];
const desiredRoleOptions = [
  "AI/ML 엔지니어",
  "데이터사이언티스트",
  "LLM 엔지니어",
  "컴퓨터비전엔지니어",
  "연구원/리서처",
  "음성인식 엔지니어",
  "MLOps 엔지니어",
  "데이터엔지니어",
  "AI 서비스/제품기획",
];
const detailedRoleOptions = [
  "제너럴리스트",
  "지능비서개발",
  "강화학습",
  "추천 시스템",
  "설계/최적화",
  "연구/실험관리",
  "테크스카우팅/분석",
  "테크스펙/품질/계약",
  "트레이닝 엔지니어링",
  "LLM 파인튜닝/서빙",
  "컴퓨터비전",
  "지리정보 분석/지도화",
  "OCR/문서 인식",
  "음성 인식/TTS",
  "MLOps/데이터인프라",
  "모델 서빙/배포",
  "데이터 엔지니어링",
  "AI 보안/안전",
];
const regionOptions = [
  "서울",
  "인천",
  "부산",
  "대구",
  "대전",
  "광주",
  "울산",
  "세종"
];

const showPasswordMatch = computed(
  () => !!newPassword.value && !!newPasswordConfirm.value && newPassword.value === newPasswordConfirm.value
);

const showPasswordError = computed(
  () => !!newPassword.value && !!newPasswordConfirm.value && newPassword.value !== newPasswordConfirm.value
);

const buildPhone = () => {
  if (!phone1.value || !phone2.value || !phone3.value) return "";
  return `${phone1.value}-${phone2.value}-${phone3.value}`;
};

const parsePhone = (phoneStr) => {
  if (!phoneStr) return;
  const parts = phoneStr.split("-");
  if (parts.length === 3) {
    phone1.value = parts[0];
    phone2.value = parts[1];
    phone3.value = parts[2];
  }
};

const buildBirthdate = () => {
  if (!birthYear.value || !birthMonth.value || !birthDay.value) return null;
  const month = String(birthMonth.value).padStart(2, "0");
  const day = String(birthDay.value).padStart(2, "0");
  return `${birthYear.value}-${month}-${day}`;
};

const parseBirthdate = (dateStr) => {
  if (!dateStr) return;
  const parts = dateStr.split("-");
  if (parts.length === 3) {
    birthYear.value = parts[0];
    birthMonth.value = parseInt(parts[1], 10);
    birthDay.value = parseInt(parts[2], 10);
  }
};

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
    if (!valid) {
      loadError.value = "로그인 세션이 만료되었습니다. 다시 로그인해주세요.";
      setTimeout(() => {
        router.push({ name: "login", query: { redirect: "/profile/edit" } });
      }, 1500);
      return;
    }

    const token = auth.token?.value;
    if (!token) {
      loadError.value = "로그인 정보가 없습니다. 다시 로그인해주세요.";
      setTimeout(() => {
        router.push({ name: "login", query: { redirect: "/profile/edit" } });
      }, 1500);
      return;
    }

    const res = await fetch(`${API_BASE}/api/user/profile/`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (!res.ok) {
      if (res.status === 401) {
        loadError.value = "로그인 세션이 만료되었습니다. 다시 로그인해주세요.";
        setTimeout(() => {
          router.push({ name: "login", query: { redirect: "/profile/edit" } });
        }, 1500);
        return;
      }
      throw new Error("회원정보를 불러오지 못했습니다.");
    }

    const data = await res.json();
    username.value = data.user_id || "";
    name.value = data.name || "";
    email.value = data.email || "";
    if (data.phone_number) parsePhone(data.phone_number);
    if (data.birthdate) parseBirthdate(data.birthdate);

    const detailRes = await fetch(`${API_BASE}/api/user/profile/detail/`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });
    if (detailRes.ok) {
      const detail = await detailRes.json();
      mapProfileDetail(detail);
    }
  } catch (err) {
    loadError.value = err?.message || "회원정보를 불러오는 중 오류가 발생했습니다.";
  } finally {
    loading.value = false;
  }
};

const handleCancel = () => {
  if (confirm("수정을 취소하시겠습니까? 변경사항이 저장되지 않습니다.")) {
    router.push("/mypage");
  }
};

const handleSubmit = async () => {
  message.value = "";
  messageType.value = "info";

  if (!name.value) {
    window.alert("이름을 입력해주세요.");
    return;
  }

  if (showPasswordChange.value) {
    if (!currentPassword.value) {
      window.alert("현재 비밀번호를 입력해주세요.");
      return;
    }
    if (!newPassword.value) {
      window.alert("새 비밀번호를 입력해주세요.");
      return;
    }
    if (!newPasswordConfirm.value) {
      window.alert("새 비밀번호 확인을 입력해주세요.");
      return;
    }
    if (newPassword.value !== newPasswordConfirm.value) {
      window.alert("새 비밀번호와 확인 비밀번호가 다릅니다.");
      return;
    }
  }

  if (!profileForm.graduated_school || !profileForm.career_level) {
    window.alert("최종 학력과 경력 레벨을 선택해주세요.");
    return;
  }

  const phone_number = buildPhone();
  const birthdate = buildBirthdate();

  const updateData = {
    name: name.value,
    phone_number: phone_number || null,
    birthdate: birthdate || null,
  };

  if (showPasswordChange.value && currentPassword.value && newPassword.value) {
    updateData.current_password = currentPassword.value;
    updateData.new_password = newPassword.value;
  }

  const valid = await auth.ensureValidSession();
  if (!valid) {
    window.alert("로그인 세션이 만료되었습니다. 다시 로그인해 주세요.");
    router.push({ name: "login", query: { redirect: "/profile/edit" } });
    return;
  }

  const token = auth.token?.value;
  if (!token) {
    window.alert("로그인 정보가 없습니다. 다시 로그인해 주세요.");
    router.push({ name: "login", query: { redirect: "/profile/edit" } });
    return;
  }

  pending.value = true;
  try {
    const res = await fetch(`${API_BASE}/api/user/profile/`, {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(updateData),
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      if (res.status === 401) {
        window.alert("로그인 세션이 만료되었습니다. 다시 로그인해 주세요.");
        router.push({ name: "login", query: { redirect: "/profile/edit" } });
        return;
      }
      const detail = data.detail || "회원정보 수정에 실패했습니다.";
      throw new Error(detail);
    }

    const profilePayload = {
      ...profileForm,
      region: profileForm.region_single ? [profileForm.region_single] : [],
    };
    const detailRes = await fetch(`${API_BASE}/api/user/profile/detail/`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(profilePayload),
    });
    if (!detailRes.ok) {
      const d = await detailRes.json().catch(() => ({}));
      throw new Error(d?.detail || "프로필 저장에 실패했습니다.");
    }

    message.value = "회원정보가 성공적으로 수정되었습니다.";
    messageType.value = "success";

    currentPassword.value = "";
    newPassword.value = "";
    newPasswordConfirm.value = "";
    showPasswordChange.value = false;

    setTimeout(() => {
      router.push("/mypage");
    }, 1000);
  } catch (err) {
    message.value = err?.message || "회원정보 저장 중 오류가 발생했습니다.";
    messageType.value = "error";
  } finally {
    pending.value = false;
  }
};

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

/* ===== Header (랜딩 톤) ===== */
.profile-header {
  position: sticky;
  top: 0;
  z-index: 10;

  display: flex;
  align-items: center;
  justify-content: space-between;

  padding: 18px 28px;
  border-bottom: 1px solid rgba(17, 24, 39, 0.08);
  background: rgba(246, 245, 239, 0.82);
  backdrop-filter: blur(10px);
}

.brand {
  text-decoration: none;
}

.brand-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;

  padding: 9px 16px;
  border-radius: 999px;

  background: #111827;
  color: #f9fafb;

  font-size: 16px;
  font-weight: 900;
  letter-spacing: 0.06em;

  box-shadow: 0 10px 24px rgba(17, 24, 39, 0.14);
}

.page-label {
  margin: 0;
  font-size: 13px;
  font-weight: 800;
  color: rgba(17, 24, 39, 0.55);
}

/* ===== Layout ===== */
.profile-main {
  flex: 1;
  padding: 34px 16px 60px;
  display: flex;
  justify-content: center;
}

.card {
  width: min(1100px, 100%);
  border-radius: 22px;
  border: 1px solid rgba(17, 24, 39, 0.08);
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(8px);

  padding: 26px 24px;
  box-shadow: 0 18px 50px rgba(17, 24, 39, 0.10);
}

.title {
  margin: 0;
  font-size: 26px;
  font-weight: 900;
  letter-spacing: -0.02em;
}

.subtitle {
  margin: 8px 0 0;
  font-size: 13px;
  color: rgba(17, 24, 39, 0.55);
  font-weight: 700;
}

/* ===== State ===== */
.loading-message,
.error-message {
  margin: 18px 0 0;
  padding: 14px 16px;
  border-radius: 14px;
  border: 1px solid rgba(17, 24, 39, 0.08);
  background: rgba(249, 250, 251, 0.9);
  color: rgba(17, 24, 39, 0.75);
  font-weight: 700;
}

.error-message {
  background: rgba(254, 242, 242, 0.9);
  border-color: rgba(185, 28, 28, 0.18);
  color: #b91c1c;
}

/* ===== Section blocks ===== */
.subsection {
  grid-column: 1 / -1;
  margin-top: 14px;
  padding: 16px 16px 12px;
  border-radius: 18px;
  border: 1px solid rgba(17, 24, 39, 0.08);
  background: rgba(246, 245, 239, 0.9);
}

.section-title {
  margin: 0;
  font-size: 16px;
  font-weight: 900;
  letter-spacing: -0.01em;
}

.section-desc {
  margin: 6px 0 0;
  font-size: 12px;
  color: rgba(17, 24, 39, 0.55);
  font-weight: 700;
}

/* ===== Form grid ===== */
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px 18px;
  margin-top: 16px;
}

@media (max-width: 860px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}

.field-block {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.field-block.full-width {
  grid-column: 1 / -1;
}

/* ===== Labels ===== */
.field-label {
  font-weight: 900;
  color: rgba(17, 24, 39, 0.78);
  font-size: 13px;
  letter-spacing: -0.01em;
}

/* ===== Inputs ===== */
.field-line {
  display: flex;
  align-items: center;

  border: 1px solid rgba(17, 24, 39, 0.10);
  border-radius: 14px;
  padding: 10px 12px;

  background: rgba(255, 255, 255, 0.85);
  transition: box-shadow 0.15s ease, border-color 0.15s ease, transform 0.15s ease;
}

.field-line:focus-within {
  border-color: rgba(17, 24, 39, 0.22);
  box-shadow: 0 10px 22px rgba(17, 24, 39, 0.10);
  transform: translateY(-1px);
}

.field-line.readonly {
  background: rgba(249, 250, 251, 0.9);
}

.field-input {
  width: 100%;
  border: none;
  outline: none;
  font-size: 14px;
  background: transparent;
  color: #111827;
}

.field-input::placeholder {
  color: rgba(17, 24, 39, 0.35);
  font-weight: 700;
}

.birth-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.birth-select {
  width: 100%;
  border: 1px solid rgba(17, 24, 39, 0.10);
  border-radius: 14px;
  padding: 10px 12px;
  font-size: 14px;
  background: rgba(255, 255, 255, 0.85);
  outline: none;
  transition: box-shadow 0.15s ease, border-color 0.15s ease, transform 0.15s ease;
}

.birth-select:focus {
  border-color: rgba(17, 24, 39, 0.22);
  box-shadow: 0 10px 22px rgba(17, 24, 39, 0.10);
  transform: translateY(-1px);
}

/* phone */
.phone-line {
  gap: 8px;
}

.phone-input {
  max-width: 92px;
  text-align: center;
  font-weight: 800;
}

.hyphen {
  color: rgba(17, 24, 39, 0.35);
  font-weight: 900;
}

/* hints */
.hint-text {
  margin: 0;
  font-size: 12px;
  color: rgba(17, 24, 39, 0.45);
  font-weight: 700;
}

/* ===== Chips ===== */
.chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;

  padding: 10px 12px;
  border-radius: 999px;

  border: 1px solid rgba(17, 24, 39, 0.10);
  background: rgba(255, 255, 255, 0.82);

  font-size: 13px;
  font-weight: 800;
  color: rgba(17, 24, 39, 0.80);

  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
}

.chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 20px rgba(17, 24, 39, 0.10);
  border-color: rgba(17, 24, 39, 0.18);
}

.chip input {
  width: 16px;
  height: 16px;
  accent-color: #111827;
}

/* ===== Password section ===== */
.password-section {
  margin-top: 8px;
  padding-top: 10px;
  border-top: 1px dashed rgba(17, 24, 39, 0.12);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.toggle-button {
  border: 1px solid rgba(17, 24, 39, 0.10);
  background: #111827;
  color: #f9fafb;
  padding: 10px 14px;
  border-radius: 14px;
  cursor: pointer;
  font-weight: 900;
  box-shadow: 0 12px 26px rgba(17, 24, 39, 0.14);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.toggle-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 16px 34px rgba(17, 24, 39, 0.16);
}

.password-hint {
  margin: 6px 0 0;
  font-size: 12px;
  font-weight: 800;
}

.password-hint.success {
  color: #16a34a;
}

.password-hint.error {
  color: #dc2626;
}

.error-line {
  border-color: rgba(220, 38, 38, 0.55) !important;
}

.success-line {
  border-color: rgba(22, 163, 74, 0.45) !important;
}

/* ===== Actions (sticky CTA) ===== */
.button-group {
  position: sticky;
  bottom: 14px;
  margin-top: 22px;

  display: flex;
  justify-content: flex-end;
  gap: 10px;

  padding: 14px;
  border-radius: 18px;
  border: 1px solid rgba(17, 24, 39, 0.08);
  background: rgba(246, 245, 239, 0.92);
  backdrop-filter: blur(10px);
}

.cancel-button,
.submit-button {
  padding: 12px 16px;
  border-radius: 14px;
  border: 1px solid rgba(17, 24, 39, 0.10);
  cursor: pointer;
  font-weight: 900;
  transition: transform 0.15s ease, box-shadow 0.15s ease, opacity 0.15s ease;
}

.cancel-button {
  background: rgba(255, 255, 255, 0.92);
  color: #111827;
}

.cancel-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 28px rgba(17, 24, 39, 0.12);
}

.submit-button {
  background: #111827;
  color: #f9fafb;
  box-shadow: 0 14px 28px rgba(17, 24, 39, 0.16);
}

.submit-button:hover {
  transform: translateY(-1px);
}

.submit-button:disabled {
  opacity: 0.65;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}

/* ===== Toast ===== */
.message {
  margin-top: 14px;
  padding: 12px 14px;
  border-radius: 14px;
  font-size: 13px;
  font-weight: 800;
  border: 1px solid rgba(17, 24, 39, 0.08);
}

.message.info {
  background: rgba(249, 250, 251, 0.92);
  color: rgba(17, 24, 39, 0.78);
}

.message.success {
  background: rgba(236, 253, 243, 0.92);
  color: #166534;
  border-color: rgba(22, 163, 74, 0.18);
}

.message.error {
  background: rgba(254, 242, 242, 0.92);
  color: #b91c1c;
  border-color: rgba(185, 28, 28, 0.18);
}
</style>
