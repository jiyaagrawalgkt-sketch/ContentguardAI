import axios from "axios";

/**
 * Normalizes the API Base URL to ensure it always ends with `/api/v1`
 * regardless of whether the user set:
 * - https://contentguard-backend.onrender.com
 * - https://contentguard-backend.onrender.com/
 * - https://contentguard-backend.onrender.com/api/v1
 * - or left it empty (defaults to http://127.0.0.1:8000/api/v1)
 */
export function getApiBaseUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!envUrl || envUrl.trim() === "") {
    return "http://127.0.0.1:8000/api/v1";
  }
  let clean = envUrl.trim().replace(/\/+$/, "");
  if (!clean.endsWith("/api/v1")) {
    if (clean.endsWith("/api")) {
      clean = `${clean}/v1`;
    } else {
      clean = `${clean}/api/v1`;
    }
  }
  return clean;
}

export const API_BASE_URL = getApiBaseUrl();

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 45000, // 45 seconds to accommodate free-tier cold starts on Render
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to attach JWT token or clean authorization
api.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("contentguard_token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      } else {
        delete config.headers.Authorization;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle unauthenticated 401s and token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (typeof window !== "undefined" && error.response?.status === 401) {
      const refreshToken = localStorage.getItem("contentguard_refresh_token");
      if (refreshToken && !error.config._retry) {
        error.config._retry = true;
        try {
          const res = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          const newAccess = res.data.access_token;
          const newRefresh = res.data.refresh_token;
          localStorage.setItem("contentguard_token", newAccess);
          if (newRefresh) {
            localStorage.setItem("contentguard_refresh_token", newRefresh);
          }
          error.config.headers.Authorization = `Bearer ${newAccess}`;
          return api(error.config);
        } catch {
          localStorage.removeItem("contentguard_token");
          localStorage.removeItem("contentguard_refresh_token");
          localStorage.removeItem("contentguard_user");
          delete api.defaults.headers.common["Authorization"];
        }
      } else {
        localStorage.removeItem("contentguard_token");
        localStorage.removeItem("contentguard_refresh_token");
        localStorage.removeItem("contentguard_user");
        delete api.defaults.headers.common["Authorization"];
      }
    }
    return Promise.reject(error);
  }
);
