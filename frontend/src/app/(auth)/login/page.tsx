"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { getApiBaseUrl, api } from "@/lib/api";
import {
  ShieldCheck,
  ArrowRight,
  AlertCircle,
  Loader2,
  Sparkles,
  Lock,
  Mail,
  Eye,
  EyeOff,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  X,
  Server,
  UserCheck,
} from "lucide-react";

export default function LoginPage() {
  const { login, isLoading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [demoExpanded, setDemoExpanded] = useState(false);
  const [selectedDemoRole, setSelectedDemoRole] = useState<string | null>(null);

  // Forgot password modal state
  const [showForgotModal, setShowForgotModal] = useState(false);
  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotLoading, setForgotLoading] = useState(false);
  const [forgotSuccess, setForgotSuccess] = useState<string | null>(null);
  const [forgotError, setForgotError] = useState<string | null>(null);

  const apiBase = getApiBaseUrl();

  const demoAccounts = [
    {
      role: "Creator",
      badge: "Creator Role",
      email: "demo@contentguard.ai",
      password: "Demo@12345",
      desc: "Draft content, run automated compliance analysis, and review fixes.",
    },
    {
      role: "Reviewer",
      badge: "Reviewer Role",
      email: "reviewer@contentguard.demo",
      password: "Demo@12345",
      desc: "Inspect pending submissions, compare revisions, and approve copy.",
    },
    {
      role: "Administrator",
      badge: "Admin Role",
      email: "admin@contentguard.demo",
      password: "Demo@12345",
      desc: "Manage organization guidelines, approved facts, and audit logs.",
    },
  ];

  const handleSelectDemo = (acc: typeof demoAccounts[0]) => {
    setEmail(acc.email);
    setPassword(acc.password);
    setSelectedDemoRole(acc.role);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const cleanEmail = email.trim();
    if (!cleanEmail || !password) {
      setError("Please enter both email address and password.");
      return;
    }

    try {
      await login(cleanEmail, password);
    } catch (err: any) {
      if (!err.response || err.code === "ERR_NETWORK" || err.message?.includes("Network Error")) {
        setError(
          `Cannot connect to backend server at ${apiBase}. If using a free-tier hosting instance, it may take 30-45s to wake up.`
        );
      } else if (err.response?.status === 401) {
        setError("Invalid email address or password. Please verify your credentials.");
      } else if (err.response?.status === 403) {
        setError(err.response?.data?.detail || "This account is inactive or access has been restricted.");
      } else {
        setError(err.response?.data?.detail || "An unexpected error occurred during sign-in. Please try again.");
      }
    }
  };

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setForgotError(null);
    setForgotSuccess(null);

    if (!forgotEmail.trim()) {
      setForgotError("Please enter your email address.");
      return;
    }

    try {
      setForgotLoading(true);
      const res = await api.post("/auth/forgot-password", { email: forgotEmail.trim() });
      setForgotSuccess(res.data.message || "Password reset instructions dispatched.");
    } catch (err: any) {
      setForgotError(err.response?.data?.detail || "Failed to initiate password reset.");
    } finally {
      setForgotLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      {/* Brand Header */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <Link href="/" className="inline-flex items-center gap-2.5">
          <div className="w-10 h-10 rounded-xl bg-midnight-950 flex items-center justify-center shadow-md">
            <ShieldCheck className="w-6 h-6 text-brand-400" />
          </div>
          <span className="font-extrabold text-2xl tracking-tight text-midnight-950">
            ContentGuard<span className="text-brand-600">.ai</span>
          </span>
        </Link>
        <h1 className="mt-4 text-xl font-bold tracking-tight text-midnight-900">
          Sign in to your account
        </h1>
        <p className="mt-1 text-xs text-slate-500">
          Enterprise Brand Governance & Factual Intelligence
        </p>
      </div>

      {/* Login Card */}
      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-5 shadow-xl shadow-slate-200/50 sm:rounded-2xl sm:px-10 border border-slate-200">

          {/* Error Notice */}
          {error && (
            <div className="mb-5 p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600 mt-0.5" />
              <div className="flex-1 font-medium leading-relaxed">{error}</div>
            </div>
          )}

          {/* Normal Login Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Email address
              </label>
              <div className="relative">
                <input
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    setSelectedDemoRole(null);
                  }}
                  placeholder="name@company.com"
                  className="w-full pl-9 pr-3.5 py-2.5 rounded-xl border border-slate-300 text-xs text-slate-900 placeholder:text-slate-400 focus:border-brand-600 focus:outline-none focus:ring-1 focus:ring-brand-600 transition-colors"
                />
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-semibold text-slate-700">
                  Password
                </label>
                <button
                  type="button"
                  onClick={() => {
                    setForgotEmail(email);
                    setShowForgotModal(true);
                  }}
                  className="text-[11px] font-medium text-brand-600 hover:text-brand-700 hover:underline"
                >
                  Forgot password?
                </button>
              </div>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    setSelectedDemoRole(null);
                  }}
                  placeholder="••••••••"
                  className="w-full pl-9 pr-10 py-2.5 rounded-xl border border-slate-300 text-xs text-slate-900 placeholder:text-slate-400 focus:border-brand-600 focus:outline-none focus:ring-1 focus:ring-brand-600 transition-colors"
                />
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600 p-0.5 rounded"
                  title={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Remember Me */}
            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-3.5 h-3.5 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                />
                <span className="text-xs text-slate-600">Remember me</span>
              </label>

              {selectedDemoRole && (
                <span className="text-[11px] font-semibold text-brand-700 bg-brand-50 px-2 py-0.5 rounded-md border border-brand-200">
                  {selectedDemoRole} Demo Selected
                </span>
              )}
            </div>

            {/* Sign In Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 px-4 rounded-xl bg-midnight-950 hover:bg-midnight-900 text-white font-semibold text-xs shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50 mt-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-brand-400" />
                  <span>Signing in...</span>
                </>
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </form>

          {/* ======================================================== */}
          {/* 1.2 COLLAPSIBLE DEMO ACCOUNTS SECTION                    */}
          {/* ======================================================== */}
          <div className="pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setDemoExpanded(!demoExpanded)}
              className="w-full flex items-center justify-between py-1 px-1.5 text-xs font-semibold text-slate-700 hover:text-midnight-900 rounded-lg hover:bg-slate-50 transition-colors"
            >
              <span className="flex items-center gap-1.5 text-slate-700">
                <Sparkles className="w-3.5 h-3.5 text-brand-600" />
                Explore Demo Accounts (Auto-Fill)
              </span>
              {demoExpanded ? (
                <ChevronUp className="w-4 h-4 text-slate-400" />
              ) : (
                <ChevronDown className="w-4 h-4 text-slate-400" />
              )}
            </button>

            {demoExpanded && (
              <div className="mt-3 space-y-2">
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  Select a pre-seeded demonstration persona to test role-specific workflows:
                </p>
                <div className="grid grid-cols-3 gap-2">
                  {demoAccounts.map((acc) => {
                    const isSelected = selectedDemoRole === acc.role;
                    return (
                      <button
                        key={acc.role}
                        type="button"
                        onClick={() => handleSelectDemo(acc)}
                        className={`p-2.5 rounded-xl border text-left transition-all flex flex-col justify-between ${
                          isSelected
                            ? "bg-brand-50 border-brand-500 ring-1 ring-brand-500 shadow-sm"
                            : "bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50/70"
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[11px] font-bold text-slate-900">
                            {acc.role}
                          </span>
                          {isSelected && <UserCheck className="w-3 h-3 text-brand-600" />}
                        </div>
                        <span className="text-[10px] text-slate-500 line-clamp-1">
                          {acc.badge}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Registration link */}
          <div className="text-center pt-2 border-t border-slate-100">
            <p className="text-xs text-slate-600">
              Need a new workspace?{" "}
              <Link href="/register" className="font-semibold text-brand-600 hover:text-brand-700 hover:underline">
                Register account
              </Link>
            </p>
          </div>

          {/* Subtle diagnostic target indicator */}
          <div className="pt-2 flex items-center justify-between text-[10px] text-slate-400 font-mono">
            <span className="flex items-center gap-1">
              <Server className="w-3 h-3" /> API Gateway
            </span>
            <span className="truncate max-w-[200px]" title={apiBase}>
              {apiBase}
            </span>
          </div>

        </div>
      </div>

      {/* Forgot Password Modal */}
      {showForgotModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-midnight-950/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-sm font-bold text-midnight-950">Reset Password</h3>
              <button
                onClick={() => setShowForgotModal(false)}
                className="p-1 text-slate-400 hover:text-slate-600 rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Enter your verified email address to receive password reset instructions.
            </p>

            {forgotError && (
              <div className="p-2.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-[11px]">
                {forgotError}
              </div>
            )}

            {forgotSuccess && (
              <div className="p-2.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-[11px] flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>{forgotSuccess}</span>
              </div>
            )}

            <form onSubmit={handleForgotPassword} className="space-y-3">
              <input
                type="email"
                required
                value={forgotEmail}
                onChange={(e) => setForgotEmail(e.target.value)}
                placeholder="name@company.com"
                className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-600"
              />
              <button
                type="submit"
                disabled={forgotLoading}
                className="w-full py-2 rounded-xl bg-midnight-950 text-white font-semibold text-xs shadow-sm hover:bg-midnight-900 disabled:opacity-50"
              >
                {forgotLoading ? "Sending..." : "Send Reset Token"}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
