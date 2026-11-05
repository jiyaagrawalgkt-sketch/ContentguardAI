"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { User, UserRole } from "@/types";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<User>;
  demoLogin: (role: "creator" | "reviewer" | "admin") => Promise<User>;
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
    // Restore session from localStorage
    const savedToken = localStorage.getItem("contentguard_token");
    const savedUser = localStorage.getItem("contentguard_user");

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
            // Expired or invalid
            localStorage.removeItem("contentguard_token");
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

  const handleAuthSuccess = (accessToken: string, userData: User) => {
    setToken(accessToken);
    setUser(userData);
    localStorage.setItem("contentguard_token", accessToken);
    localStorage.setItem("contentguard_user", JSON.stringify(userData));

    // Redirect strictly based on assigned role
    if (userData.role === "admin") {
      router.push("/admin");
    } else if (userData.role === "reviewer") {
      router.push("/reviewer");
    } else {
      router.push("/creator");
    }
  };

  const login = async (email: string, password: string): Promise<User> => {
    setIsLoading(true);
    // Purge previous state before authenticating new user
    localStorage.removeItem("contentguard_token");
    localStorage.removeItem("contentguard_user");
    delete api.defaults.headers.common["Authorization"];

    try {
      const res = await api.post("/auth/login", { email, password });
      handleAuthSuccess(res.data.access_token, res.data.user);
      return res.data.user;
    } finally {
      setIsLoading(false);
    }
  };

  const demoLogin = async (role: "creator" | "reviewer" | "admin"): Promise<User> => {
    setIsLoading(true);
    localStorage.removeItem("contentguard_token");
    localStorage.removeItem("contentguard_user");
    delete api.defaults.headers.common["Authorization"];

    try {
      const res = await api.post("/auth/demo-login", { role });
      handleAuthSuccess(res.data.access_token, res.data.user);
      return res.data.user;
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
    localStorage.removeItem("contentguard_user");
    delete api.defaults.headers.common["Authorization"];

    try {
      const res = await api.post("/auth/register", data);
      handleAuthSuccess(res.data.access_token, res.data.user);
      return res.data.user;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("contentguard_token");
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
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
