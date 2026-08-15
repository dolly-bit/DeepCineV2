import api from "./api";

const AUTH_KEYS = {
  accessToken: "access_token",
  token: "token",
  userId: "user_id",
  username: "username",
};

export function getAuthState() {
  if (typeof window === "undefined") {
    return {
      accessToken: "",
      token: "",
      userId: "",
      username: "",
    };
  }

  return {
    accessToken: localStorage.getItem(AUTH_KEYS.accessToken) || "",
    token: localStorage.getItem(AUTH_KEYS.token) || "",
    userId: localStorage.getItem(AUTH_KEYS.userId) || "",
    username: localStorage.getItem(AUTH_KEYS.username) || "",
  };
}

export function isAuthenticated() {
  const { accessToken, userId } = getAuthState();
  return Boolean(accessToken && userId);
}

export function setAuthState({ accessToken, userId, username }) {
  if (typeof window === "undefined") {
    return;
  }

  const safeAccessToken = accessToken || "";
  const safeUserId = userId ? String(userId) : "";
  const safeUsername = username || "";

  localStorage.setItem(AUTH_KEYS.accessToken, safeAccessToken);
  localStorage.setItem(AUTH_KEYS.token, safeAccessToken);
  localStorage.setItem(AUTH_KEYS.userId, safeUserId);
  localStorage.setItem(AUTH_KEYS.username, safeUsername);
}

export function clearAuthState() {
  if (typeof window === "undefined") {
    return;
  }

  localStorage.removeItem(AUTH_KEYS.accessToken);
  localStorage.removeItem(AUTH_KEYS.token);
  localStorage.removeItem(AUTH_KEYS.userId);
  localStorage.removeItem(AUTH_KEYS.username);
}

// Fetches the real profile for whoever the stored token belongs to.
// Doubles as a validity check: if the token is stale/expired or points
// at a user that no longer exists, the backend 401s and api.js's
// response interceptor clears the dead session automatically.
export async function getCurrentUser() {
  const res = await api.get("/auth/me");
  return res.data;
}
