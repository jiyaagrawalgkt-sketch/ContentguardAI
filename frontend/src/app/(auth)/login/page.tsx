"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { getApiBaseUrl, api } from "@/lib/api";
import {
  ShieldCheck,
  ArrowRight,
  Sparkles,
  AlertCircle,
  Loader2,
  Server,
  PlayCircle,
  KeyRound,
  Copy,
  Check,
  Info,
  X,
  ExternalLink,
} from "lucide-react";

export default function LoginPage() {
  const { login, demoLogin, googleLogin, enterJudgeSandbox, isLoading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loadingRole, setLoadingRole] = useState<string | null>(null);
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [showGoogleModal, setShowGoogleModal] = useState<boolean>(false);
  const [googleConfigured, setGoogleConfigured] = useState<boolean>(false);
  const [googleClientId, setGoogleClientId] = useState<string | null>(null);
  const [isGoogleLoading, setIsGoogleLoading] = useState<boolean>(false);
  const apiBase = getApiBaseUrl();

  useEffect(() => {
    // Check if Google OAuth is configured on backend
    api.get("/auth/google/config")
      .then((res) => {
        setGoogleConfigured(res.data.configured);
        setGoogleClientId(res.data.client_id);
      })
      .catch(() => {
        setGoogleConfigured(false);
      });
  }, []);

  const handleCopy = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await login(email, password);
    } catch (err: any) {
      if (!err.response || err.code === "ERR_NETWORK" || err.message?.includes("Network Error")) {
        setError(
          `Cannot reach API backend at ${apiBase}. If your backend is hosted on Render free-tier, it may take 30-45s to wake up, or verify your Vercel NEXT_PUBLIC_API_URL environment variable.`
        );
      } else {
        setError(err.response?.data?.detail || "Invalid email or password. Please try again.");
      }
    }
  };

  const handleDemoLogin = async (role: "demo" | "creator" | "reviewer" | "admin" | "compliance_officer") => {
    setError(null);
    setLoadingRole(role);
    try {
      await demoLogin(role);
    } catch (err: any) {
      if (!err.response || err.code === "ERR_NETWORK" || err.message?.includes("Network Error")) {
        setError(`Switched to Instant Judge Sandbox so you can explore immediately without waiting for backend wake up.`);
      } else {
        setError(err.response?.data?.detail || "Failed to initialize session. Please try again.");
      }
    } finally {
      setLoadingRole(null);
    }
  };

  const handleGoogleClick = () => {
    setError(null);
    if (!googleConfigured) {
      setShowGoogleModal(true);
      return;
    }

    // Google Identity Services flow when configured
    try {
      /* global google */
      if (typeof window !== "undefined" && (window as any).google?.accounts?.id) {
        (window as any).google.accounts.id.initialize({
          client_id: googleClientId,
          callback: async (response: any) => {
            if (response.credential) {
              setIsGoogleLoading(true);
              try {
                await googleLogin(response.credential);
              } catch (e: any) {
                setError(e.response?.data?.detail || "Google authentication failed.");
              } finally {
                setIsGoogleLoading(false);
              }
            }
          },
        });
        (window as any).google.accounts.id.prompt();
      } else {
        setShowGoogleModal(true);
      }
    } catch {
      setShowGoogleModal(true);
    }
  };

  const simulateGoogleLogin = async () => {
    setIsGoogleLoading(true);
    setShowGoogleModal(false);
    try {
      await googleLogin("test_google_token_judge.evaluator@contentguard.ai");
    } catch (err: any) {
      setError("Google simulation failed: " + (err.response?.data?.detail || err.message));
    } finally {
      setIsGoogleLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-lavender-50 flex flex-col justify-center py-10 sm:px-6 lg:px-8">
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

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow-card sm:rounded-3xl sm:px-10 border border-midnight-100 space-y-6">

          {/* ======================================================== */}
          {/* MANDATORY HACKATHON JUDGE DEMO CREDENTIALS SECTION       */}
          {/* ======================================================== */}
          <div className="p-4 rounded-2xl bg-gradient-to-br from-brand-50/80 via-white to-purple-50/70 border-2 border-brand-300 shadow-sm relative overflow-hidden">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-brand-600" />
                <span className="text-xs font-extrabold text-brand-950 uppercase tracking-wider">
                  Explore ContentGuard AI
                </span>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-brand-500 text-white">
                Hackathon Demo
              </span>
            </div>

            <p className="text-[11px] text-midnight-600 mb-3 leading-relaxed">
              Judges can use these pre-seeded demo credentials to test and explore the full brand governance workflow:
            </p>

            <div className="space-y-1.5 mb-3 bg-white/90 p-2.5 rounded-xl border border-brand-200/80 text-xs font-mono">
              <div className="flex items-center justify-between">
                <span className="text-midnight-500">Email:</span>
                <div className="flex items-center gap-1.5 font-bold text-midnight-900">
                  <span>demo@contentguard.ai</span>
                  <button
                    type="button"
                    onClick={() => handleCopy("demo@contentguard.ai", "email")}
                    className="p-1 text-midnight-400 hover:text-brand-600 rounded transition-colors"
                    title="Copy Email"
                  >
                    {copiedField === "email" ? (
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-midnight-500">Password:</span>
                <div className="flex items-center gap-1.5 font-bold text-midnight-900">
                  <span>Demo@12345</span>
                  <button
                    type="button"
                    onClick={() => handleCopy("Demo@12345", "password")}
                    className="p-1 text-midnight-400 hover:text-brand-600 rounded transition-colors"
                    title="Copy Password"
                  >
                    {copiedField === "password" ? (
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Prominent Login as Demo User Button */}
            <button
              type="button"
              onClick={() => handleDemoLogin("demo")}
              disabled={isLoading || loadingRole !== null}
              className="w-full py-2.5 px-4 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loadingRole === "demo" ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <KeyRound className="w-4 h-4 text-brand-200" />
                  <span>Login as Demo User</span>
                  <ArrowRight className="w-3.5 h-3.5 text-brand-200" />
                </>
              )}
            </button>

            {/* Role Persona Quick Switcher */}
            <div className="mt-3 pt-3 border-t border-brand-200/60">
              <span className="text-[10px] font-bold uppercase tracking-wider text-midnight-500 block mb-1.5">
                Switch Role Persona:
              </span>
              <div className="grid grid-cols-4 gap-1.5">
                {[
                  { id: "creator", label: "Creator", bg: "bg-blue-100 text-blue-700" },
                  { id: "reviewer", label: "Reviewer", bg: "bg-purple-100 text-purple-700" },
                  { id: "compliance_officer", label: "Officer", bg: "bg-amber-100 text-amber-700" },
                  { id: "admin", label: "Admin", bg: "bg-emerald-100 text-emerald-700" },
                ].map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => handleDemoLogin(p.id as any)}
                    disabled={isLoading}
                    className="py-1 px-1.5 rounded-lg bg-white border border-brand-200 hover:border-brand-400 text-midnight-800 text-[10px] font-semibold flex items-center justify-center gap-1 transition-all disabled:opacity-50"
                  >
                    <span className={`w-3.5 h-3.5 rounded text-[8px] flex items-center justify-center font-bold ${p.bg}`}>
                      {p.label.charAt(0)}
                    </span>
                    <span className="truncate">{p.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* ======================================================== */}
          {/* CONTINUE WITH GOOGLE                                      */}
          {/* ======================================================== */}
          <div>
            <button
              type="button"
              onClick={handleGoogleClick}
              disabled={isGoogleLoading || isLoading}
              className="w-full py-2.5 px-4 rounded-xl border border-midnight-200 bg-white hover:bg-midnight-50 text-midnight-800 font-semibold text-xs shadow-sm transition-all flex items-center justify-center gap-2.5 disabled:opacity-50"
            >
              {isGoogleLoading ? (
                <Loader2 className="w-4 h-4 animate-spin text-midnight-600" />
              ) : (
                <svg className="w-4 h-4" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                  />
                </svg>
              )}
              <span>Continue with Google</span>
            </button>
          </div>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-midnight-100" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="bg-white px-3 text-midnight-400 font-medium">
                Or sign in with email
              </span>
            </div>
          </div>

          {error && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 flex flex-col gap-1 text-xs text-rose-700">
              <div className="flex items-center gap-2 font-semibold">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>Authentication Notice</span>
              </div>
              <p className="text-[11px] leading-relaxed text-rose-600 pl-6">{error}</p>
            </div>
          )}

          {/* Traditional Email & Password Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-midnight-800 mb-1">
                Email address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your-name@company.com"
                className="w-full px-3.5 py-2.5 rounded-xl border border-midnight-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-all placeholder:text-midnight-300"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-midnight-800 mb-1">
                Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-3.5 py-2.5 rounded-xl border border-midnight-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-all placeholder:text-midnight-300"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 px-4 rounded-xl bg-midnight-900 hover:bg-midnight-800 text-white font-semibold text-sm shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Backend target diagnostic indicator */}
          <div className="pt-3 border-t border-midnight-100 flex items-center justify-between text-[11px] text-midnight-500">
            <div className="flex items-center gap-1.5">
              <Server className="w-3.5 h-3.5 text-midnight-400" />
              <span>Target Backend:</span>
            </div>
            <code className="text-[10px] font-mono px-2 py-0.5 rounded bg-midnight-50 text-midnight-700 max-w-[200px] truncate" title={apiBase}>
              {apiBase}
            </code>
          </div>

          <div className="text-center pt-1">
            <span className="text-xs text-midnight-500">
              Need an account?{" "}
              <Link
                href="/register"
                className="font-semibold text-brand-600 hover:text-brand-700 underline"
              >
                Create account
              </Link>
            </span>
          </div>
        </div>
      </div>

      {/* Google OAuth Setup / Simulation Modal */}
      {showGoogleModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-midnight-950/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-midnight-100 space-y-4">
            <div className="flex items-center justify-between border-b border-midnight-100 pb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                  <Info className="w-4 h-4" />
                </div>
                <h3 className="text-sm font-bold text-midnight-950">
                  Google Sign-In Configuration
                </h3>
              </div>
              <button
                onClick={() => setShowGoogleModal(false)}
                className="p-1 text-midnight-400 hover:text-midnight-600 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-midnight-600 leading-relaxed">
              Google OAuth backend endpoint is implemented and ready. To use real Google accounts on production:
            </p>

            <div className="p-3 bg-midnight-50 rounded-xl space-y-1.5 text-xs text-midnight-700">
              <p><strong>1.</strong> Create project in Google Cloud Console.</p>
              <p><strong>2.</strong> Add Authorized JavaScript Origin (e.g. your Vercel URL).</p>
              <p><strong>3.</strong> Set <code>GOOGLE_CLIENT_ID</code> in backend environment variables.</p>
            </div>

            <div className="pt-2 flex flex-col gap-2">
              <button
                type="button"
                onClick={simulateGoogleLogin}
                className="w-full py-2.5 px-4 rounded-xl bg-midnight-900 hover:bg-midnight-800 text-white font-bold text-xs shadow-md transition-all flex items-center justify-center gap-2"
              >
                <Sparkles className="w-3.5 h-3.5 text-brand-300" />
                <span>Simulate Google Authentication (Judge Test)</span>
              </button>

              <button
                type="button"
                onClick={() => setShowGoogleModal(false)}
                className="w-full py-2 px-4 rounded-xl border border-midnight-200 text-midnight-700 font-semibold text-xs hover:bg-midnight-50"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
