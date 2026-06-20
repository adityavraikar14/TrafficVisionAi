import { createContext, useContext, useState, type ReactNode } from "react";
import { getStoredSession, login as apiLogin, logout as apiLogout } from "../api/auth";

interface AuthState {
  officerName: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [officerName, setOfficerName] = useState<string | null>(
    () => getStoredSession()?.officer_name ?? null
  );

  const login = async (username: string, password: string) => {
    const session = await apiLogin(username, password);
    setOfficerName(session.officer_name);
  };

  const logout = () => {
    apiLogout();
    setOfficerName(null);
  };

  return (
    <AuthContext.Provider
      value={{ officerName, isAuthenticated: !!officerName, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
