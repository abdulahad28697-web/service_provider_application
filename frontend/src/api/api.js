import axios from "axios";

const api = axios.create({
  baseURL:
    import.meta.env.VITE_API_URL ||
    "/api/v1",

  headers: {
    "Content-Type": "application/json",
  },
});

/*
 * Human-readable fallbacks for responses that carry no message.
 */
const DEFAULT_MESSAGES = {
  400: "The request was invalid. Please review the form and try again.",
  401: "Your session has expired. Please sign in again.",
  403: "You do not have permission to perform this action.",
  404: "The requested record could not be found.",
  409: "This action conflicts with the current data.",
  422: "Some fields are invalid. Please review the form.",
  429: "Too many requests. Please wait a moment and try again.",
  500: "Something went wrong on the server. Please try again.",
  502: "The server is unreachable. Please try again shortly.",
  503: "The server is unreachable. Please try again shortly.",
};

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
 * We do NOT automatically log the user out for every 401 response.
 *
 * A 401 from something like /bookings can mean that the
 * particular endpoint does not allow the current role.
 * It should not destroy the user's login session.
 *
 * We only clear authentication when an authentication-related
 * request proves that the token/session is actually invalid.
 */
api.interceptors.response.use(
  (response) => response,

  (error) => {
    const status = error.response?.status;
    const requestUrl = error.config?.url || "";
    const payload = error.response?.data;

    if (error.response && payload && !payload.message) {
      payload.message = payload.detail || DEFAULT_MESSAGES[status];
    }

    if (!error.response) {
      error.response = {
        data: {
          message:
            "Network error. Check your connection and try again.",
        },
      };
    }

    if (status === 401) {
      const isAuthenticationRequest =
        requestUrl.includes("/users/me") ||
        requestUrl.includes("/auth/");

      if (isAuthenticationRequest) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("current_user");

        const currentPath = window.location.pathname;

        if (
          currentPath !== "/login" &&
          currentPath !== "/register"
        ) {
          window.location.href = "/login";
        }
      }
    }

    return Promise.reject(error);
  },
);

export default api;