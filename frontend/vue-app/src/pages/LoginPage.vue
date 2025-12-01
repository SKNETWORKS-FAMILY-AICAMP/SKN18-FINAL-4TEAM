<template>
  <div class="page">
    <header class="top-bar">
      <div class="top-bar-inner">
        <div class="window-controls">
          <span class="wc-dot wc-red"></span>
          <span class="wc-dot wc-amber"></span>
          <span class="wc-dot wc-green"></span>
        </div>
        <div class="address-pill">
          <span class="domain-text">jobtory.com</span>
        </div>
        <button class="top-right-icon" aria-label="Share window">
          <span class="top-right-icon-arrow"></span>
        </button>
      </div>
    </header>

    <div class="inner-panel">
      <div class="watermark">JobTory</div>

      <div class="content">
        <section class="login-card">
          <h1>Login</h1>
          <form class="form">
            <label class="label label-email">
              <span>Email</span>
              <input class="email-input" type="email" placeholder="username@gmail.com" />
            </label>
            <label class="label label-password">
              <span>Password</span>
              <div class="password-field">
                <input class="password-input" type="password" placeholder="Password" />
                <button type="button" class="ghost-button" aria-label="Show password">
                  <svg viewBox="0 0 24 24" class="icon">
                    <path
                      fill="currentColor"
                      d="M12 5c-4.5 0-8.3 2.7-10 7 1.7 4.3 5.5 7 10 7s8.3-2.7 10-7c-1.7-4.3-5.5-7-10-7Zm0 12a5 5 0 1 1 0-10 5 5 0 0 1 0 10Zm0-2a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"
                    />
                  </svg>
                </button>
              </div>
            </label>
            <div class="row">
              <a class="link" href="#">Forgot Password?</a>
            </div>
            <button type="submit" class="primary">Sign in</button>
            <div class="divider">
              <span></span>
              <p>Or Continue With</p>
              <span></span>
            </div>
            <button type="button" class="google">
              <svg viewBox="0 0 533.5 544.3" class="google-icon">
                <path
                  fill="#4285f4"
                  d="M533.5 278.4c0-17.4-1.6-34.1-4.6-50.3H272v95.2h146.9c-6.4 34.7-25.8 64-55 83.6v68.9h88.8c51.9-47.8 80.8-118.2 80.8-197.4Z"
                />
                <path
                  fill="#34a853"
                  d="M272 544.3c74 0 136-24.4 181.3-66.5l-88.8-68.9c-24.7 16.6-56.4 26.3-92.5 26.3-71 0-131.2-47.9-152.8-112.2H26v70.7C71.2 477.7 165.6 544.3 272 544.3Z"
                />
                <path
                  fill="#fbbc04"
                  d="M119.2 322.9c-5.6-16.6-8.8-34.4-8.8-52.9s3.2-36.3 8.8-52.9V146.4H26C9.4 179.6 0 219 0 270s9.4 90.4 26 123.6l93.2-70.7Z"
                />
                <path
                  fill="#ea4335"
                  d="M272 107.7c40.3 0 76.5 13.9 105 41.2l78.6-78.6C408 24.2 346 0 272 0 165.6 0 71.2 66.6 26 146.4l93.2 70.7C140.8 155.6 201 107.7 272 107.7Z"
                />
              </svg>
              Google
            </button>
            <p class="helper">
              Don't have an account yet?
              <a class="link" href="#">Register for free</a>
            </p>
          </form>
        </section>

        <section class="brand-card">
          <div class="brand-img-wrap">
            <img :src="logo" alt="JobTory logo" class="brand-img" />
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
const logo = new URL("../assets/JOBTORY_main.png", import.meta.url).href;
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap");

:root {
  --mint: #9ac8a6;
  --mint-dark: #84b091;
  --cream: #fff6e2;
  --ink: #234059;
  --salmon: #f4834d;
}

.page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: flex-start;
  padding: 0 0 40px;
  position: relative;
  background: #d9e9d0;
  color: var(--ink);
  font-family: "Nunito", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  overflow: hidden;
}

.page::before,
.page::after {
  content: "";
  position: absolute;
  width: 520px;
  height: 520px;
  border-radius: 50%;
  filter: blur(70px);
  opacity: 0.55;
  pointer-events: none;
}

.page::before {
  background: #fef3c7;
  top: -140px;
  left: -80px;
  animation: loginGlow1 8s ease-in-out infinite;
}

.page::after {
  background: #bae6fd;
  bottom: -160px;
  right: -120px;
  animation: loginGlow2 9s ease-in-out infinite;
}

.top-bar {
  width: 100%;
  display: flex;
  justify-content: center;
  margin-bottom: 12px;
}

.top-bar-inner {
  width: 100%;
  max-width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  border-radius: 0;
  background: linear-gradient(180deg, #343d38, #252c28);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.6);
  gap: 16px;
  transition: background 160ms ease-out, box-shadow 160ms ease-out;
}

.window-controls {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 2px 0 4px;
}

.wc-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  box-shadow: 0 0 0 1px rgba(15, 23, 42, 0.12);
}

.wc-red {
  background: #ff5f57;
}

.wc-amber {
  background: #febc2e;
}

.wc-green {
  background: #27c840;
}

.address-pill {
  flex: 1;
  display: flex;
  justify-content: center;
}

.domain-text {
  min-width: 180px;
  max-width: 260px;
  text-align: center;
  padding: 4px 32px;
  border-radius: 999px;
  background: rgba(248, 250, 252, 0.12);
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.45);
  color: #e5e7eb;
  font-size: 11px;
  letter-spacing: 0.04em;
  transition: background 160ms ease-out, box-shadow 160ms ease-out, transform 160ms ease-out;
}

.domain-text:hover {
  background: rgba(248, 250, 252, 0.22);
  box-shadow: 0 0 0 1px rgba(248, 250, 252, 0.4);
  transform: translateY(-1px) scale(1.02);
}

.top-right-icon {
  border: none;
  background: transparent;
  padding: 4px 6px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
   transition: background 160ms ease-out, transform 160ms ease-out;
}

.top-right-icon:hover {
  background: rgba(15, 23, 42, 0.3);
  transform: translateY(-0.5px);
}

.top-right-icon-arrow {
  width: 13px;
  height: 13px;
  border-radius: 999px;
  border: 1px solid #e5e7eb;
  position: relative;
}

.top-right-icon-arrow::after {
  content: "";
  position: absolute;
  top: 55%;
  left: 50%;
  transform: translate(-50%, -60%) rotate(0deg);
  border-style: solid;
  border-width: 4px 0 0 4px;
  border-color: #e5e7eb transparent transparent #e5e7eb;
}

.inner-panel {
  position: relative;
  width: calc(100% - 80px);
  max-width: 1200px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  padding: 40px 72px 40px 250px;
  min-height: 640px;
  margin: 28px auto 0;
}

.content {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(360px, 460px) minmax(420px, 520px);
  column-gap: 64px;
  align-items: center;
}

.watermark {
  position: absolute;
  left: 56px;
  bottom: 42px;
  font-size: 120px;
  font-weight: 800;
  color: rgba(35, 64, 89, 0.12);
  z-index: 0;
  user-select: none;
  pointer-events: none;
}

.login-card,
.brand-card {
  border-radius: 20px;
}

.login-card {
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(255, 255, 255, 0.95);
  padding: 40px 40px 34px;
  box-shadow: 0 30px 70px rgba(15, 23, 42, 0.32);
  backdrop-filter: blur(22px);
  -webkit-backdrop-filter: blur(22px);
  position: relative;
  overflow: hidden;
  transform-origin: center;
  animation: loginCardEnter 650ms cubic-bezier(0.22, 0.61, 0.36, 1) 80ms both;
  transition: box-shadow 180ms ease-out, transform 180ms ease-out;
}

.login-card::before {
  content: "";
  position: absolute;
  width: 420px;
  height: 420px;
  background: radial-gradient(circle at 20% 0%, rgba(250, 204, 21, 0.35), transparent 58%),
    radial-gradient(circle at 80% 120%, rgba(56, 189, 248, 0.3), transparent 55%);
  top: -160px;
  left: -120px;
  opacity: 0.7;
  mix-blend-mode: soft-light;
  transform-origin: 50% 50%;
  animation: loginRingOrbit 18s linear infinite;
  pointer-events: none;
}

.login-card:has(input:focus, textarea:focus) {
  box-shadow: 0 36px 80px rgba(15, 23, 42, 0.4);
  transform: translateY(-2px);
}

.brand-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 18px;
  padding: 16px 0 12px;
}

h1 {
  margin: 6px 0 24px;
  font-size: 34px;
  color: #304c64;
}

.form {
  display: grid;
  gap: 14px;
  justify-items: start;
  max-width: 420px;
}

.label {
  display: grid;
  gap: 6px;
  font-size: 14px;
  color: #546a7b;
}

.label-email {
  width: 100%;
}

.label-password {
  width: 100%;
}

.email-input {
  width: 100%;
  padding: 14px 16px;
  box-sizing: border-box;
  border-radius: 8px;
  border: 1px solid #d7e1d8;
  background: #fff;
  color: #304c64;
  font-size: 14px;
  outline: none;
  transition: border 0.2s ease, box-shadow 0.2s ease;
}

.email-input:focus {
  border-color: var(--mint-dark);
  box-shadow: 0 0 0 3px rgba(132, 176, 145, 0.45);
}

.password-field {
  position: relative;
  width: 100%;
  border-radius: 8px;
  border: 1px solid #d7e1d8;
  background: #fff;
  overflow: hidden;
  box-sizing: border-box;
}

.password-input {
  width: 100%;
  padding: 14px 44px 14px 16px;
  border: none;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  font-size: 14px;
  color: #304c64;
}

.password-input:focus {
  border: none;
  box-shadow: none;
}

.password-field:focus-within {
  border-color: var(--mint-dark);
  box-shadow: 0 0 0 3px rgba(132, 176, 145, 0.45);
}

.ghost-button {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  cursor: pointer;
  color: #7a8f89;
}

@keyframes loginGlow1 {
  0% {
    transform: scale(0.9);
    opacity: 0.3;
  }
  50% {
    transform: scale(1.12);
    opacity: 0.7;
  }
  100% {
    transform: scale(0.9);
    opacity: 0.3;
  }
}

@keyframes loginGlow2 {
  0% {
    transform: scale(0.88);
    opacity: 0.25;
  }
  50% {
    transform: scale(1.13);
    opacity: 0.65;
  }
  100% {
    transform: scale(0.88);
    opacity: 0.25;
  }
}

@keyframes loginCardEnter {
  0% {
    opacity: 0;
    transform: translateY(24px) scale(0.97);
  }
  60% {
    opacity: 1;
    transform: translateY(-4px) scale(1.01);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes loginRingOrbit {
  0% {
    transform: rotate(0deg) translate3d(0, 0, 0);
  }
  50% {
    transform: rotate(12deg) translate3d(10px, 6px, 0);
  }
  100% {
    transform: rotate(24deg) translate3d(0, 0, 0);
  }
}

.icon {
  width: 18px;
  height: 18px;
}

.row {
  display: flex;
  justify-content: flex-end;
}

.link {
  color: #d98a28;
  text-decoration: none;
  font-weight: 700;
  font-size: 13px;
}

.primary {
  width: 100%;
  padding: 12px 14px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(180deg, #f48f54 0%, #e67235 100%);
  color: #fff;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 10px 20px rgba(228, 114, 53, 0.35);
  position: relative;
  overflow: hidden;
  transform-origin: center;
  transition: transform 140ms ease-out, box-shadow 140ms ease-out, filter 140ms ease-out;
}

.primary:hover {
  filter: brightness(0.97);
}

.primary::after {
  content: "";
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at center, rgba(255, 255, 255, 0.5) 0, transparent 55%);
  opacity: 0;
  transform: scale(0);
  transition: opacity 350ms ease-out, transform 350ms ease-out;
  pointer-events: none;
}

.primary:active {
  transform: translateY(1px) scale(0.98);
  box-shadow: 0 6px 14px rgba(180, 83, 31, 0.4);
  filter: brightness(0.96);
}

.primary:active::after {
  opacity: 1;
  transform: scale(2.4);
}

.divider {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #7a8f89;
  font-size: 12px;
}

.divider span {
  flex: 1;
  height: 1px;
  background: #d7e1d8;
}

.google {
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 30px;
  border: 1px solid #d7e1d8;
  background: #fff;
  color: #304c64;
  font-weight: 700;
  cursor: pointer;
}

.google-icon {
  width: 20px;
  height: 20px;
}

.helper {
  margin: 2px 0 0;
  color: #7a8f89;
  font-size: 13px;
  text-align: center;
}

.brand-img-wrap {
  padding: 10px 24px 0;
}

.brand-img {
  display: block;
  width: min(440px, 100%);
  height: auto;
  border-radius: 24px;
  animation: logoFloat 8s ease-in-out infinite;
}

.brand-text {
  margin-top: 24px;
  font-size: 42px;
  font-weight: 800;
  letter-spacing: 1px;
  color: #2f5574;
  text-align: center;
}

@media (max-width: 980px) {
  .content {
    grid-template-columns: 1fr;
  }

  .brand-card {
    order: -1;
  }

  .watermark {
    display: none;
  }
}

@media (max-width: 540px) {
  .page {
    padding: 24px 12px;
  }

  .login-card {
    padding: 24px 22px;
  }
}

@keyframes logoFloat {
  0% {
    transform: translate3d(0, 0, 0) scale(1) rotate(0deg);
    filter: brightness(1);
  }
  25% {
    transform: translate3d(-4px, -8px, 0) scale(1.02) rotate(-3deg);
  }
  50% {
    transform: translate3d(3px, 6px, 0) scale(1.03) rotate(3.2deg);
    filter: brightness(1.06);
  }
  75% {
    transform: translate3d(-3px, -6px, 0) scale(1.01) rotate(-2.2deg);
  }
  100% {
    transform: translate3d(0, 0, 0) scale(1) rotate(0deg);
    filter: brightness(1);
  }
}
</style>
