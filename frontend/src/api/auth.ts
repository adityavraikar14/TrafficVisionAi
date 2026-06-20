import { api, AUTH_STORAGE_KEY } from "./client";

export interface AuthSession {
  token: string;
  officer_name: string;
}

export const login = (username: string, password: string) =>
  api.post<AuthSession>("/api/auth/login", { username, password }).then((r) => {
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(r.data));
    return r.data;
  });

export const logout = () => {
  localStorage.removeItem(AUTH_STORAGE_KEY);
};

export const getStoredSession = (): AuthSession | null => {
  const raw = localStorage.getItem(AUTH_STORAGE_KEY);
  return raw ? JSON.parse(raw) : null;
};
