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
