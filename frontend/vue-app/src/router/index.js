import { createRouter, createWebHistory } from "vue-router";
import MainPage from "../pages/MainPage.vue";
import LoginPage from "../pages/LoginPage.vue";
import LiveCodingPage from "../pages/LiveCodingPage.vue";
import InterviewPage from "../pages/InterviewPage.vue";
import LiveCodingSessionPage from "../pages/LiveCodingSessionPage.vue";
import SignUpChoicePage from "../pages/SignUpChoicePage.vue";
import SignUpTermsPage from "../pages/SignUpTermsPage.vue";
import SignUpPersonalPage from "../pages/SignUpPersonalPage.vue";
import SignUpCompanyPage from "../pages/SignUpCompanyPage.vue";
import LiveCodingSettingPage from "../pages/LiveCodingSettingPage.vue";

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
  { path: "/interview", name: "interview", component: InterviewPage }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
