// Kleiner API-Client fürs Dashboard. Token liegt im localStorage.
const API = import.meta.env.PUBLIC_API_URL || "http://localhost:8787";
const TOKEN_KEY = "consentflow_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(t) {
  localStorage.setItem(TOKEN_KEY, t);
}
export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}
export function isLoggedIn() {
  return Boolean(getToken());
}

async function request(method, path, body) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers.Authorization = "Bearer " + token;
  const res = await fetch(API + path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 401) {
    clearToken();
    throw new ApiError("Sitzung abgelaufen. Bitte erneut anmelden.", 401);
  }
  const isJson = (res.headers.get("Content-Type") || "").includes("json");
  const data = isJson ? await res.json() : await res.text();
  if (!res.ok) throw new ApiError((data && data.error) || "Fehler", res.status, data);
  return data;
}

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

export const api = {
  apiBase: API,
  register: (email, password) => request("POST", "/v1/auth/register", { email, password }),
  login: (email, password) => request("POST", "/v1/auth/login", { email, password }),
  me: () => request("GET", "/v1/me"),
  listSites: () => request("GET", "/v1/sites"),
  createSite: (data) => request("POST", "/v1/sites", data),
  getSite: (id) => request("GET", "/v1/sites/" + id),
  updateSite: (id, data) => request("PUT", "/v1/sites/" + id, data),
  deleteSite: (id) => request("DELETE", "/v1/sites/" + id),
  stats: (id) => request("GET", "/v1/sites/" + id + "/stats"),
  csvUrl: (id) => API + "/v1/sites/" + id + "/export.csv",
  checkout: (plan) => request("POST", "/v1/billing/checkout", { plan }),
  portal: () => request("POST", "/v1/billing/portal"),
};
