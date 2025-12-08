import { createRouter, createWebHistory } from "vue-router";
import { useAuth } from "../hooks/useAuth";
import MainPage from "../pages/MainPage.vue";
import LoginPage from "../pages/LoginPage.vue";
import LiveCodingPage from "../pages/LiveCodingPage.vue";
import InterviewPage from "../pages/InterviewPage.vue";
import LiveCodingSessionPage from "../pages/LiveCodingSessionPage.vue";
import SignUpChoicePage from "../pages/SignUpChoicePage.vue";
import SignUpTermsPage from "../pages/SignUpTermsPage.vue";
import SignUpPersonalPage from "../pages/SignUpPersonalPage.vue";
import SignUpCompanyPage from "../pages/SignUpCompanyPage.vue";
import MyPage from "../pages/MyPage.vue";
import LiveCodingSettingPage from "../pages/LiveCodingSettingPage.vue";
import ProfileEditPage from "../pages/ProfileEditPage.vue";

const routes = [
  { path: "/", name: "home", component: MainPage },
  { path: "/login", name: "login", component: LoginPage },
  { path: "/signup", name: "signup-choice", component: SignUpChoicePage },
  { path: "/signup/terms", name: "signup-terms", component: SignUpTermsPage },
  { path: "/signup/personal", name: "signup-personal", component: SignUpPersonalPage },
  { path: "/signup/company", name: "signup-company", component: SignUpCompanyPage },
  { path: "/coding-test", name: "coding-test", component: LiveCodingPage },
  { path: "/coding-test/settings", name: "coding-settings", component: LiveCodingSettingPage },
  { path: "/coding-test/session", name: "coding-session", component: LiveCodingSessionPage },
  { path: "/interview", name: "interview", component: InterviewPage },
  { path: "/mypage", name: "mypage", component: MyPage, meta: { requiresAuth: true } },
  { path: "/profile/edit", name: "profile-edit", component: ProfileEditPage, meta: { requiresAuth: true } },
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach(async (to, from, next) => {
  const auth = useAuth();

  if (to.meta.requiresAuth) {
    const valid = await auth.ensureValidSession();
    if (!valid) {
      next({ name: "login", query: { redirect: to.fullPath } });
      return;
    }
  } else if (auth.isAuthenticated.value && !auth.user.value) {
    await auth.fetchProfile();
  }

  next();
});

export default router;
