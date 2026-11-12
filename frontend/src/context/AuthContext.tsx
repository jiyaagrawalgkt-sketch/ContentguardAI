"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api, getApiBaseUrl } from "@/lib/api";
import { User, UserRole } from "@/types";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isDemoMode: boolean;
  login: (email: string, password: string) => Promise<User>;
  demoLogin: (role: "demo" | "judge" | "creator" | "reviewer" | "admin" | "compliance_officer") => Promise<User>;
  googleLogin: (credential: string) => Promise<User>;
  register: (data: {
    email: string;
    password: string;
    full_name: string;
    role?: string;
    organization_name?: string;
  }) => Promise<User>;
  enterJudgeSandbox: (role?: "demo" | "judge" | "creator" | "reviewer" | "admin" | "compliance_officer") => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const DEMO_PERSONAS: Record<string, User> = {
  demo: {
    id: "demo-judge-id",
    email: "demo@contentguard.ai",
    full_name: "Hackathon Judge (Demo Evaluator)",
    role: "creator",
    organization_id: "demo-org-acme",
    organization_name: "Acme Global Technologies (Judge Sandbox)",
    is_active: true,
    created_at: new Date().toISOString(),
  },
  judge: {
    id: "demo-judge-id",
    email: "demo@contentguard.ai",
    full_name: "Hackathon Judge (Demo Evaluator)",
    role: "creator",
    organization_id: "demo-org-acme",
    organization_name: "Acme Global Technologies (Judge Sandbox)",
    is_active: true,
    created_at: new Date().toISOString(),
  },
  creator: {
    id: "demo-creator-id",
    email: "creator@contentguard.demo",
    full_name: "Alex Rivera (Demo Creator)",
    role: "creator",
    organization_id: "demo-org-acme",
    organization_name: "Acme Global Technologies (Judge Sandbox)",
    is_active: true,
    created_at: new Date().toISOString(),
  },
  reviewer: {
    id: "demo-reviewer-id",
    email: "reviewer@contentguard.demo",
    full_name: "Samantha Chen (Demo Reviewer)",
    role: "reviewer",
    organization_id: "demo-org-acme",
    organization_name: "Acme Global Technologies (Judge Sandbox)",
    is_active: true,
    created_at: new Date().toISOString(),
  },
  admin: {
    id: "demo-admin-id",
    email: "admin@contentguard.demo",
    full_name: "Marcus Vance (Demo Admin)",
    role: "admin",
    organization_id: "demo-org-acme",
    organization_name: "Acme Global Technologies (Judge Sandbox)",
    is_active: true,
    created_at: new Date().toISOString(),
  },
  compliance_officer: {
    id: "demo-compliance-id",
    email: "compliance@contentguard.demo",
    full_name: "Elena Rostova (Compliance Officer)",
    role: "compliance_officer",
    organization_id: "demo-org-acme",
    organization_name: "Acme Global Technologies (Judge Sandbox)",
    is_active: true,
    created_at: new Date().toISOString(),
  },
};

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isDemoMode, setIsDemoMode] = useState<boolean>(false);
  const router = useRouter();

  useEffect(() => {
    // Restore session from localStorage
    const savedToken = localStorage.getItem("contentguard_token");
    const savedUser = localStorage.getItem("contentguard_user");
    const savedDemo = localStorage.getItem("contentguard_is_demo");

    if (savedDemo === "true" && savedUser) {
      try {
        setUser(JSON.parse(savedUser));
        setToken(savedToken || "demo-token");
        setIsDemoMode(true);
      } catch {
        // pass
      }
      setIsLoading(false);
      return;
    }

    if (savedToken && savedUser) {
      try {
        setToken(savedToken);
        setUser(JSON.parse(savedUser));
        // Verify token with backend
        api
          .get("/auth/me", {
            headers: { Authorization: `Bearer ${savedToken}` },
          })
          .then((res) => {
            setUser(res.data);
            localStorage.setItem("contentguard_user", JSON.stringify(res.data));
          })
          .catch(() => {
            // Token expired or invalid
            localStorage.removeItem("contentguard_token");
            localStorage.removeItem("contentguard_refresh_token");
            localStorage.removeItem("contentguard_user");
            delete api.defaults.headers.common["Authorization"];
            setToken(null);
            setUser(null);
          })
          .finally(() => setIsLoading(false));
      } catch (e) {
        setIsLoading(false);
      }
    } else {
      setIsLoading(false);
    }
  }, []);

  const handleAuthSuccess = (accessToken: string, userData: User, refreshToken?: string) => {
    setToken(accessToken);
    setUser(userData);
    setIsDemoMode(false);
    localStorage.removeItem("contentguard_is_demo");
    localStorage.setItem("contentguard_token", accessToken);
    if (refreshToken) {
      localStorage.setItem("contentguard_refresh_token", refreshToken);
    }
    localStorage.setItem("contentguard_user", JSON.stringify(userData));

    // Redirect strictly based on assigned role
    if (userData.role === "admin") {
      router.push("/admin");
    } else if (userData.role === "reviewer") {
      router.push("/reviewer");
    } else if (userData.role === "compliance_officer") {
      router.push("/compliance");
    } else {
      router.push("/creator");
    }
  };

  const enterJudgeSandbox = (role: "demo" | "judge" | "creator" | "reviewer" | "admin" | "compliance_officer" = "creator") => {
    const persona = DEMO_PERSONAS[role] || DEMO_PERSONAS.creator;
    const fakeToken = `demo_jwt_token_${role}_${Date.now()}`;
    setUser(persona);
    setToken(fakeToken);
    setIsDemoMode(true);
    localStorage.setItem("contentguard_is_demo", "true");
    localStorage.setItem("contentguard_token", fakeToken);
    localStorage.setItem("contentguard_user", JSON.stringify(persona));

    if (role === "admin") {
      router.push("/admin");
    } else if (role === "reviewer") {
      router.push("/reviewer");
    } else if (role === "compliance_officer") {
      router.push("/compliance");
    } else {
      router.push("/creator");
    }
  };

  const login = async (email: string, password: string): Promise<User> => {
    setIsLoading(true);
    localStorage.removeItem("contentguard_token");
    localStorage.removeItem("contentguard_refresh_token");
    localStorage.removeItem("contentguard_user");
    delete api.defaults.headers.common["Authorization"];

    try {
      const res = await api.post("/auth/login", { email, password });
      handleAuthSuccess(res.data.access_token, res.data.user, res.data.refresh_token);
      return res.data.user;
    } finally {
      setIsLoading(false);
    }
  };

  const demoLogin = async (role: "demo" | "judge" | "creator" | "reviewer" | "admin" | "compliance_officer"): Promise<User> => {
    setIsLoading(true);
    localStorage.removeItem("contentguard_token");
    localStorage.removeItem("contentguard_refresh_token");
    localStorage.removeItem("contentguard_user");
    delete api.defaults.headers.common["Authorization"];

    try {
      const res = await api.post("/auth/demo-login", { role });
      handleAuthSuccess(res.data.access_token, res.data.user, res.data.refresh_token);
      return res.data.user;
    } catch (err: any) {
      if (!err.response || err.code === "ERR_NETWORK" || err.message?.includes("Network Error")) {
        console.warn("Backend offline or waking up. Falling back to Public Demo Sandbox Mode.");
        enterJudgeSandbox(role);
        return DEMO_PERSONAS[role] || DEMO_PERSONAS.demo;
      }
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const googleLogin = async (credential: string): Promise<User> => {
    setIsLoading(true);
    localStorage.removeItem("contentguard_token");
    localStorage.removeItem("contentguard_refresh_token");
    localStorage.removeItem("contentguard_user");
    delete api.defaults.headers.common["Authorization"];

    try {
      const res = await api.post("/auth/google", { credential });
      handleAuthSuccess(res.data.access_token, res.data.user, res.data.refresh_token);
      return res.data.user;
    } catch (err: any) {
      if (!err.response || err.code === "ERR_NETWORK" || err.message?.includes("Network Error")) {
        console.warn("Backend offline during Google login. Falling back to Judge Sandbox Mode.");
        enterJudgeSandbox("creator");
        return DEMO_PERSONAS.demo;
      }
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: {
    email: string;
    password: string;
    full_name: string;
    role?: string;
    organization_name?: string;
  }): Promise<User> => {
    setIsLoading(true);
    localStorage.removeItem("contentguard_token");
    localStorage.removeItem("contentguard_refresh_token");
    localStorage.removeItem("contentguard_user");
    delete api.defaults.headers.common["Authorization"];

    try {
      const res = await api.post("/auth/register", data);
      handleAuthSuccess(res.data.access_token, res.data.user, res.data.refresh_token);
      return res.data.user;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    setIsDemoMode(false);
    localStorage.removeItem("contentguard_token");
    localStorage.removeItem("contentguard_refresh_token");
    localStorage.removeItem("contentguard_user");
    localStorage.removeItem("contentguard_is_demo");
    delete api.defaults.headers.common["Authorization"];
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    } else {
      router.push("/login");
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        isLoading,
        isDemoMode,
        login,
        demoLogin,
        googleLogin,
        register,
        enterJudgeSandbox,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
