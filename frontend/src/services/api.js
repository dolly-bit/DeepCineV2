import axios from "axios";

console.log(
  "API BASE URL:",
  import.meta.env.VITE_API_BASE_URL
);

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: false,
  timeout: 60000,
});

// Automatically attach JWT token (after login)
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// If the backend ever rejects our token as invalid/expired (401), clear
// the stale auth state instead of leaving the UI in a broken "looks
// logged in but nothing actually works" limbo. This is also what
// prevents an old token from a wiped/reset database (e.g. re-seeding a
// local dev DB) from silently sticking around forever - localStorage
// tokens never expire client-side on their own.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("token");
      localStorage.removeItem("user_id");
      localStorage.removeItem("username");

      // Only force a redirect if we're not already on an auth page -
      // avoids a redirect loop while the user is actively logging in.
      const authPages = ["/login", "/signup", "/"];
      if (
        typeof window !== "undefined" &&
        !authPages.includes(window.location.pathname)
      ) {
        window.location.href = "/login";
      }
    }

    return Promise.reject(error);
  }
);

export default api;