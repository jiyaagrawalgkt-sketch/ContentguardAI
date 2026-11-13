"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { getApiBaseUrl } from "@/lib/api";
import {
  ShieldCheck,
  ArrowRight,
  AlertCircle,
  Loader2,
  Sparkles,
  Copy,
  Check,
  Lock,
  Mail,
} from "lucide-react";

export default function LoginPage() {
  const { login, demoLogin, isLoading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<string | null>(null);
  const [isDemoSigningIn, setIsDemoSigningIn] = useState<boolean>(false);
  const apiBase = getApiBaseUrl();

  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopied(label);
    setTimeout(() => setCopied(null), 2000);
  };

  const fillDemoCredentials = () => {
    setEmail("demo@contentguard.ai");
    setPassword("Demo@12345");
    setError(null);
  };

  const handleDirectDemoLogin = async () => {
    setError(null);
    setIsDemoSigningIn(true);
    try {
      await demoLogin("demo");
    } catch (err: any) {
      if (!err.response || err.code === "ERR_NETWORK" || err.message?.includes("Network Error")) {
        setError(
          `Cannot reach API backend at ${apiBase}. If using a free-tier hosting instance, it may take 30-45s to wake up.`
        );
      } else {
        setError(err.response?.data?.detail || "Demo login failed. Please verify credentials.");
      }
    } finally {
      setIsDemoSigningIn(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email.trim() || !password) {
      setError("Please enter both email address and password.");
      return;
    }

    try {
      await login(email, password);
    } catch (err: any) {
      if (!err.response || err.code === "ERR_NETWORK" || err.message?.includes("Network Error")) {
        setError(
          `Cannot connect to backend server at ${apiBase}. Please verify the backend is running.`
        );
      } else if (err.response?.status === 401) {
        setError("Incorrect email address or password. Please check your credentials and try again.");
      } else if (err.response?.status === 403) {
        setError(err.response?.data?.detail || "This account has been deactivated. Contact your administrator.");
      } else {
        setError(err.response?.data?.detail || "An unexpected authentication error occurred. Please try again.");
      }
    }
  };

  return (
    <div className="min-h-screen bg-lavender-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <Link href="/" className="flex items-center justify-center gap-2.5">
          <div className="w-10 h-10 rounded-xl bg-midnight-900 flex items-center justify-center shadow-md shadow-midnight-900/10">
            <ShieldCheck className="w-6 h-6 text-brand-400" />
          </div>
          <span className="font-extrabold text-2xl tracking-tight text-midnight-950">
            ContentGuard<span className="text-brand-500">.ai</span>
          </span>
        </Link>
        <h1 className="mt-4 text-center text-xl font-bold tracking-tight text-midnight-900">
          Sign in to your account
        </h1>
        <p className="mt-1 text-center text-xs text-midnight-500">
          Review it before it ships.
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow-card sm:rounded-3xl sm:px-10 border border-midnight-100 space-y-6">

          {/* ======================================================== */}
          {/* SEEDED CREATOR DEMO ACCOUNT CALLOUT BANNER               */}
          {/* ======================================================== */}
          <div className="p-4 rounded-2xl bg-gradient-to-br from-brand-50/70 via-white to-purple-50/60 border border-brand-200">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-midnight-900 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-brand-600" />
                Demo Account (Creator)
              </span>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-brand-100 text-brand-800">
                Creator Role
              </span>
            </div>

            <p className="text-[11px] text-midnight-600 mb-3 leading-relaxed">
              Sign in with this pre-configured Creator account to explore content drafting, automated AI compliance analysis, the Knowledge Hub, and the Evidence Graph.
            </p>

            <div className="bg-white/90 rounded-xl border border-midnight-100 p-2.5 space-y-1.5 text-xs font-mono">
              <div className="flex items-center justify-between">
                <span className="text-midnight-500 text-[11px]">Email:</span>
                <div className="flex items-center gap-1.5">
                  <span className="font-semibold text-midnight-900">demo@contentguard.ai</span>
                  <button
                    type="button"
                    onClick={() => handleCopy("demo@contentguard.ai", "email")}
                    className="p-1 text-midnight-400 hover:text-midnight-900 rounded"
                    title="Copy email"
                  >
                    {copied === "email" ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between border-t border-midnight-100/60 pt-1.5">
                <span className="text-midnight-500 text-[11px]">Password:</span>
                <div className="flex items-center gap-1.5">
                  <span className="font-semibold text-midnight-900">Demo@12345</span>
                  <button
                    type="button"
                    onClick={() => handleCopy("Demo@12345", "password")}
                    className="p-1 text-midnight-400 hover:text-midnight-900 rounded"
                    title="Copy password"
                  >
                    {copied === "password" ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                  </button>
                </div>
              </div>
            </div>

            <div className="mt-3 flex items-center gap-2">
              <button
                type="button"
                onClick={fillDemoCredentials}
                className="flex-1 py-1.5 px-3 rounded-xl border border-midnight-200 hover:bg-white text-[11px] font-semibold text-midnight-700 transition-colors"
              >
                Auto-Fill Creator Demo
              </button>
              <button
                type="button"
                onClick={handleDirectDemoLogin}
                disabled={isDemoSigningIn || isLoading}
                className="flex-1 py-1.5 px-3 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-[11px] font-semibold shadow-sm transition-colors flex items-center justify-center gap-1.5 disabled:opacity-50"
              >
                {isDemoSigningIn ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <ArrowRight className="w-3 h-3" />
                )}
                <span>Enter Creator Workspace</span>
              </button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600 mt-0.5" />
              <div className="flex-1 font-medium leading-relaxed">{error}</div>
            </div>
          )}

          {/* Standard Email / Password Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-midnight-800 mb-1">
                Email address
              </label>
              <div className="relative">
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-midnight-200 text-xs text-midnight-900 placeholder:text-midnight-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
                <Mail className="w-4 h-4 text-midnight-400 absolute left-3 top-3" />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-semibold text-midnight-800">
                  Password
                </label>
              </div>
              <div className="relative">
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-midnight-200 text-xs text-midnight-900 placeholder:text-midnight-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
                <Lock className="w-4 h-4 text-midnight-400 absolute left-3 top-3" />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading || isDemoSigningIn}
              className="w-full py-2.5 rounded-xl bg-midnight-900 hover:bg-midnight-800 text-white font-semibold text-xs shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50 mt-2"
            >
              {isLoading && !isDemoSigningIn ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Verifying credentials...</span>
                </>
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </form>

          {/* Registration link */}
          <div className="text-center pt-2 border-t border-midnight-100">
            <p className="text-xs text-midnight-600">
              Need a new organization workspace?{" "}
              <Link href="/register" className="font-semibold text-brand-600 hover:text-brand-700">
                Register account
              </Link>
            </p>
          </div>

        </div>
      </div>
    </div>
  );
}
