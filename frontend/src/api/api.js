import axios from "axios";

// All API calls use relative path so they go through the Vite dev proxy
// (Vite forwards /api/* → http://localhost:8000/api/*)
// This avoids CORS issues in development.
const API_BASE_URL = import.meta.env.VITE_API_URL || "/api/v1";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/*
 * Attach the access token to every API request.
 */
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    } else {
      delete config.headers.Authorization;
    }

    return config;
  },
  (error) => Promise.reject(error),
);

/*
 * Handle API responses.
 *
 * IMPORTANT:
 * We only clear credentials when an authentication request (like /users/me)
 * returns 401 Unauthorized. React Router guard components handle smooth
 * in-app redirects without requiring destructive window.location.href reloads.
 */
api.interceptors.response.use(
  (response) => response,

  (error) => {
    const status = error.response?.status;
    const requestUrl = error.config?.url || "";

    if (status === 401) {
      const isAuthenticationRequest =
        requestUrl.includes("/users/me") ||
        requestUrl.includes("/auth/login");

      if (isAuthenticationRequest) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("current_user");
      }
    }

    return Promise.reject(error);
  },
);

export default api;