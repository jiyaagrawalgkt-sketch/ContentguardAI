"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { ShieldCheck, ArrowRight, Sparkles, AlertCircle, Loader2, ShieldAlert } from "lucide-react";

export default function LoginPage() {
  const { login, demoLogin, isLoading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loadingRole, setLoadingRole] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await login(email, password);
    } catch (err: any) {
      if (!err.response || err.code === "ERR_NETWORK" || err.message?.includes("Network Error")) {
        setError("Cannot connect to backend server. Please verify the backend window is running on http://127.0.0.1:8000.");
      } else {
        setError(err.response?.data?.detail || "Invalid email or password. Please try again.");
      }
    }
  };

  const handleDemoLogin = async (role: "creator" | "reviewer" | "admin") => {
    setError(null);
    setLoadingRole(role);
    try {
      await demoLogin(role);
    } catch (err: any) {
      if (!err.response || err.code === "ERR_NETWORK" || err.message?.includes("Network Error")) {
        setError("Cannot connect to backend server. Please verify the backend window is running on http://127.0.0.1:8000.");
      } else {
        setError(err.response?.data?.detail || "Failed to initialize session. Please try again.");
      }
    } finally {
      setLoadingRole(null);
    }
  };

  return (
    <div className="min-h-screen bg-lavender-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <Link href="/" className="flex items-center justify-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-midnight-900 flex items-center justify-center shadow-md shadow-midnight-900/10">
            <ShieldCheck className="w-6 h-6 text-brand-400" />
          </div>
          <span className="font-extrabold text-2xl tracking-tight text-midnight-950">
            ContentGuard<span className="text-brand-500">.ai</span>
          </span>
        </Link>
        <h2 className="mt-4 text-center text-xl font-bold tracking-tight text-midnight-900">
          Sign in to your account
        </h2>
        <p className="mt-1 text-center text-xs text-midnight-600">
          Tagline: <strong className="text-midnight-800">Review it before it ships.</strong>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow-card sm:rounded-3xl sm:px-10 border border-midnight-100">
          {/* Quick Demo Personas Box */}
          <div className="mb-6 p-4 rounded-2xl bg-brand-50/60 border border-brand-200">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-4 h-4 text-brand-600" />
              <p className="text-xs font-bold text-brand-900 uppercase tracking-wide">
                Role Personas (Instant Access)
              </p>
            </div>
            <p className="text-[11px] text-midnight-600 mb-3">
              Explore ContentGuard with verified pre-configured roles:
            </p>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleDemoLogin("creator")}
                disabled={isLoading}
                className="flex flex-col items-center justify-center gap-1.5 p-2 rounded-xl bg-white border border-brand-300 hover:border-brand-500 text-midnight-900 font-semibold text-[11px] shadow-sm hover:shadow transition-all disabled:opacity-50"
              >
                {loadingRole === "creator" ? (
                  <Loader2 className="w-4 h-4 animate-spin text-brand-600" />
                ) : (
                  <div className="w-6 h-6 rounded-md bg-blue-100 text-blue-700 flex items-center justify-center text-[10px] font-bold">
                    C
                  </div>
                )}
                <span>Creator</span>
              </button>

              <button
                type="button"
                onClick={() => handleDemoLogin("reviewer")}
                disabled={isLoading}
                className="flex flex-col items-center justify-center gap-1.5 p-2 rounded-xl bg-white border border-brand-300 hover:border-brand-500 text-midnight-900 font-semibold text-[11px] shadow-sm hover:shadow transition-all disabled:opacity-50"
              >
                {loadingRole === "reviewer" ? (
                  <Loader2 className="w-4 h-4 animate-spin text-purple-600" />
                ) : (
                  <div className="w-6 h-6 rounded-md bg-purple-100 text-purple-700 flex items-center justify-center text-[10px] font-bold">
                    R
                  </div>
                )}
                <span>Reviewer</span>
              </button>

              <button
                type="button"
                onClick={() => handleDemoLogin("admin")}
                disabled={isLoading}
                className="flex flex-col items-center justify-center gap-1.5 p-2 rounded-xl bg-white border border-brand-300 hover:border-brand-500 text-midnight-900 font-semibold text-[11px] shadow-sm hover:shadow transition-all disabled:opacity-50"
              >
                {loadingRole === "admin" ? (
                  <Loader2 className="w-4 h-4 animate-spin text-emerald-600" />
                ) : (
                  <div className="w-6 h-6 rounded-md bg-emerald-100 text-emerald-700 flex items-center justify-center text-[10px] font-bold">
                    A
                  </div>
                )}
                <span>Admin</span>
              </button>
            </div>
          </div>

          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-midnight-100" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="bg-white px-2 text-midnight-400">Or sign in with email</span>
            </div>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 flex items-center gap-2 text-xs text-rose-700">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs font-semibold text-midnight-700">
                Email address
              </label>
              <div className="mt-1">
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your-name@company.com"
                  className="block w-full rounded-xl border border-midnight-200 px-3.5 py-2.5 text-sm text-midnight-900 placeholder:text-midnight-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-midnight-700">
                Password
              </label>
              <div className="mt-1">
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="block w-full rounded-xl border border-midnight-200 px-3.5 py-2.5 text-sm text-midnight-900 placeholder:text-midnight-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-sm font-semibold text-white bg-midnight-900 hover:bg-midnight-800 shadow-md hover:shadow-lg transition-all disabled:opacity-50"
            >
              {isLoading && !loadingRole ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="w-4 h-4 text-brand-400" />
                </>
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-xs text-midnight-500">
            Need an account?{" "}
            <Link href="/register" className="font-semibold text-brand-600 hover:underline">
              Create account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
