export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function getToken() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("tradepilot_token");
}

export function setSession(token: string, user: unknown) {
  window.localStorage.setItem("tradepilot_token", token);
  window.localStorage.setItem("tradepilot_user", JSON.stringify(user));
}

export function clearSession() {
  window.localStorage.removeItem("tradepilot_token");
  window.localStorage.removeItem("tradepilot_user");
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers
    },
    cache: "no-store"
  });
  const payload = await response.json().catch(() => ({ message: "Invalid server response" }));
  if (!response.ok) throw new Error(payload.message || "Request failed");
  return payload as T;
}
