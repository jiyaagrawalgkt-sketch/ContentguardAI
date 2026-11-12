"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api, getApiBaseUrl } from "@/lib/api";
import { User } from "@/types";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<User>;
  demoLogin: (role?: "demo" | "judge" | "creator" | "reviewer" | "admin" | "compliance_officer") => Promise<User>;
  register: (data: {
    email: string;
    password: string;
    full_name: string;
    role?: string;
    organization_name?: string;
  }) => Promise<User>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const router = useRouter();

  useEffect(() => {
    // Clean any legacy fake demo tokens
    if (typeof window !== "undefined") {
      localStorage.removeItem("contentguard_is_demo");
      const savedToken = localStorage.getItem("contentguard_token");
      if (savedToken && savedToken.startsWith("demo_jwt_token_")) {
        localStorage.removeItem("contentguard_token");
        localStorage.removeItem("contentguard_refresh_token");
        localStorage.removeItem("contentguard_user");
      }
    }

    const savedToken = localStorage.getItem("contentguard_token");
    const savedUser = localStorage.getItem("contentguard_user");

    if (savedToken && savedUser) {
      try {
        const parsedUser = JSON.parse(savedUser);
        setToken(savedToken);
        setUser(parsedUser);

        // Verify token with backend /auth/me
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
    localStorage.setItem("contentguard_token", accessToken);
    if (refreshToken) {
      localStorage.setItem("contentguard_refresh_token", refreshToken);
    }
    localStorage.setItem("contentguard_user", JSON.stringify(userData));

    // Role-based route redirection
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

  const login = async (email: string, password: string): Promise<User> => {
    setIsLoading(true);
    localStorage.removeItem("contentguard_token");
    localStorage.removeItem("contentguard_refresh_token");
    localStorage.removeItem("contentguard_user");
    delete api.defaults.headers.common["Authorization"];

    try {
      const res = await api.post("/auth/login", {
        email: email.trim().toLowerCase(),
        password: password,
      });
      handleAuthSuccess(res.data.access_token, res.data.user, res.data.refresh_token);
      return res.data.user;
    } finally {
      setIsLoading(false);
    }
  };

  const demoLogin = async (
    role: "demo" | "judge" | "creator" | "reviewer" | "admin" | "compliance_officer" = "demo"
  ): Promise<User> => {
    const roleEmailMap: Record<string, string> = {
      demo: "demo@contentguard.ai",
      judge: "demo@contentguard.ai",
      creator: "creator@contentguard.demo",
      reviewer: "reviewer@contentguard.demo",
      admin: "admin@contentguard.demo",
      compliance_officer: "compliance@contentguard.demo",
    };

    const targetEmail = roleEmailMap[role] || "demo@contentguard.ai";
    return await login(targetEmail, "Demo@12345");
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
      const res = await api.post("/auth/register", {
        ...data,
        email: data.email.trim().toLowerCase(),
      });
      handleAuthSuccess(res.data.access_token, res.data.user, res.data.refresh_token);
      return res.data.user;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    // Notify backend if refresh token exists
    const refreshToken = localStorage.getItem("contentguard_refresh_token");
    if (refreshToken) {
      api.post("/auth/logout", { refresh_token: refreshToken }).catch(() => {});
    }

    setToken(null);
    setUser(null);
    localStorage.removeItem("contentguard_token");
    localStorage.removeItem("contentguard_refresh_token");
    localStorage.removeItem("contentguard_user");
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
        login,
        demoLogin,
        register,
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
