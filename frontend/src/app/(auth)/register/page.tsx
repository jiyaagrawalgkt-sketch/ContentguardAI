"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { ShieldCheck, ArrowRight, AlertCircle, Loader2 } from "lucide-react";

export default function RegisterPage() {
  const { register, isLoading } = useAuth();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [organizationName, setOrganizationName] = useState("");
  const [role, setRole] = useState("creator");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await register({
        full_name: fullName,
        email,
        password,
        organization_name: organizationName || undefined,
        role,
      });
    } catch (err: any) {
      if (!err.response || err.code === "ERR_NETWORK" || err.message?.includes("Network Error")) {
        setError("Cannot connect to backend server. Please verify the backend window is running on http://127.0.0.1:8000.");
      } else {
        setError(err.response?.data?.detail || "Registration failed. Please check your information.");
      }
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
          Create your account
        </h2>
        <p className="mt-1 text-center text-xs text-midnight-600">
          Join the Brand Governance & Compliance Platform
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow-card sm:rounded-3xl sm:px-10 border border-midnight-100">
          {error && (
            <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 flex items-center gap-2 text-xs text-rose-700">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Google Sign In option */}
          <div className="mb-4">
            <Link
              href="/login"
              className="w-full py-2.5 px-4 rounded-xl border border-midnight-200 bg-white hover:bg-midnight-50 text-midnight-800 font-semibold text-xs shadow-sm transition-all flex items-center justify-center gap-2.5"
            >
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
              <span>Continue with Google</span>
            </Link>
          </div>

          <div className="relative mb-4">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-midnight-100" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="bg-white px-2 text-midnight-400 font-medium">Or register with email</span>
            </div>
          </div>

          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs font-semibold text-midnight-700">
                Full Name
              </label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Alex Rivera"
                className="mt-1 block w-full rounded-xl border border-midnight-200 px-3.5 py-2.5 text-sm text-midnight-900 placeholder:text-midnight-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-midnight-700">
                Work Email
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="alex@acme.com"
                className="mt-1 block w-full rounded-xl border border-midnight-200 px-3.5 py-2.5 text-sm text-midnight-900 placeholder:text-midnight-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-midnight-700">
                Organization / Company
              </label>
              <input
                type="text"
                value={organizationName}
                onChange={(e) => setOrganizationName(e.target.value)}
                placeholder="Acme Corporation"
                className="mt-1 block w-full rounded-xl border border-midnight-200 px-3.5 py-2.5 text-sm text-midnight-900 placeholder:text-midnight-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-midnight-700">
                Role
              </label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="mt-1 block w-full rounded-xl border border-midnight-200 px-3.5 py-2.5 text-sm text-midnight-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              >
                <option value="creator">Content Creator (Drafts & corrections)</option>
                <option value="reviewer">Brand Reviewer (Governance & approvals)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-midnight-700">
                Password
              </label>
              <input
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="mt-1 block w-full rounded-xl border border-midnight-200 px-3.5 py-2.5 text-sm text-midnight-900 placeholder:text-midnight-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-sm font-semibold text-white bg-midnight-900 hover:bg-midnight-800 shadow-md hover:shadow-lg transition-all disabled:opacity-50"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <span>Create Account</span>
                  <ArrowRight className="w-4 h-4 text-brand-400" />
                </>
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-xs text-midnight-500">
            Already have an account?{" "}
            <Link href="/login" className="font-semibold text-brand-600 hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
