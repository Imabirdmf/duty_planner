import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
console.log(import.meta.env.VITE_API_URL)

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return null;
}

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: { "Content-Type": "application/json" },
  timeout: 5000,
  withCredentials: true
});

const SAFE_METHODS = ["get", "head", "options"];
 
api.interceptors.request.use((config) => {
  if (!SAFE_METHODS.includes(config.method?.toLowerCase())) {
    const csrfToken = getCookie("csrftoken");
    if (csrfToken) {
      config.headers["X-CSRFToken"] = csrfToken;
    }
  }
  return config;
});

export default api;
