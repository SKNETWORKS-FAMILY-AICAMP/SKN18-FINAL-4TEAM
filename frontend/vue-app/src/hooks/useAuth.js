import { computed, ref } from "vue";

const tokenKey = "jobtory_access_token";
const BACKEND_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

const token = ref(localStorage.getItem(tokenKey) || "");
const user = ref(null);

const isAuthenticated = computed(() => !!token.value);

const setToken = (nextToken) => {
  token.value = nextToken || "";
  if (token.value) {
    localStorage.setItem(tokenKey, token.value);
  } else {
    localStorage.removeItem(tokenKey);
  }
};

const setUser = (profile) => {
  user.value = profile || null;
};

const isTokenExpired = (rawToken) => {
  if (!rawToken) return true;
  try {
    const payload = JSON.parse(atob(rawToken.split(".")[1]));
    const expMs = payload.exp * 1000;
    return Date.now() >= expMs;
  } catch (err) {
    console.error("Failed to decode token", err);
    return true;
  }
};

const fetchProfile = async () => {
  if (!token.value) {
    setUser(null);
    return null;
  }

  if (isTokenExpired(token.value)) {
    clearSession();
    return null;
  }

  try {
    const resp = await fetch(`${BACKEND_BASE}/api/auth/me/`, {
      headers: {
        Authorization: `Bearer ${token.value}`
      }
    });

    if (!resp.ok) {
      setToken("");
      setUser(null);
      return null;
    }

    const data = await resp.json();
    setUser(data);
    return data;
  } catch (err) {
    console.error("Failed to fetch profile", err);
    return null;
  }
};

const setSession = async (nextToken, profile) => {
  setToken(nextToken);
  if (profile) {
    setUser(profile);
    return profile;
  }
  return fetchProfile();
};

const clearSession = () => {
  setToken("");
  setUser(null);
};

const ensureValidSession = async () => {
  if (!token.value) return false;
  if (isTokenExpired(token.value)) {
    clearSession();
    return false;
  }
  if (!user.value) {
    await fetchProfile();
  }
  return true;
};

const logout = async () => {
  const currentToken = token.value;
  clearSession(); // 즉시 UI 반영
  try {
    if (currentToken) {
      await fetch(`${BACKEND_BASE}/api/auth/logout/`, {
        method: "POST",
        headers: { Authorization: `Bearer ${currentToken}` }
      });
    }
  } catch (err) {
    console.error("Logout request failed", err);
  }
};

export function useAuth() {
  return {
    token,
    user,
    isAuthenticated,
    setSession,
    fetchProfile,
    clearSession,
    ensureValidSession,
    logout,
    BACKEND_BASE
  };
}
