"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import {
  ShieldCheck,
  LogOut,
  LayoutDashboard,
  FileText,
  ClipboardCheck,
  ShieldAlert,
  Layers,
  Sparkles,
} from "lucide-react";

export function AppNavbar() {
  const { user, isDemoMode, logout } = useAuth();
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 w-full border-b border-midnight-100 bg-white/95 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo & Product Identity */}
        <div className="flex items-center gap-3">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-midnight-900 flex items-center justify-center shadow-sm">
              <ShieldCheck className="w-5 h-5 text-brand-400" />
            </div>
            <span className="font-extrabold text-lg tracking-tight text-midnight-950">
              ContentGuard<span className="text-brand-500">.ai</span>
            </span>
          </Link>
          <span className="text-xs text-midnight-400 hidden sm:inline">•</span>
          <span className="text-xs text-midnight-600 font-medium hidden sm:inline">
            Review it before it ships.
          </span>
          {isDemoMode && (
            <span className="ml-2 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300 flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-amber-600" />
              Judge Sandbox Mode
            </span>
          )}
        </div>

        {/* Authorized Workspace Navigation & User Profile */}
        <div className="flex items-center gap-4">
          {/* Workspace Links based on assigned role */}
          <div className="hidden md:flex items-center gap-1.5 p-1 rounded-xl bg-lavender-100/70 border border-midnight-100 text-xs">
            {user?.role === "admin" && (
              <>
                <Link
                  href="/admin"
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
                    pathname?.startsWith("/admin")
                      ? "bg-white text-emerald-700 shadow-sm"
                      : "text-midnight-600 hover:text-midnight-950"
                  }`}
                >
                  <LayoutDashboard className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Admin</span>
                </Link>

                <Link
                  href="/knowledge-base"
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
                    pathname?.startsWith("/knowledge-base")
                      ? "bg-white text-brand-700 shadow-sm"
                      : "text-midnight-600 hover:text-midnight-950"
                  }`}
                >
                  <Layers className="w-3.5 h-3.5 text-brand-600" />
                  <span>Knowledge Hub</span>
                </Link>

                <Link
                  href="/compliance"
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
                    pathname?.startsWith("/compliance")
                      ? "bg-white text-amber-700 shadow-sm"
                      : "text-midnight-600 hover:text-midnight-950"
                  }`}
                >
                  <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
                  <span>Compliance</span>
                </Link>

                <Link
                  href="/creator"
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
                    pathname?.startsWith("/creator")
                      ? "bg-white text-brand-700 shadow-sm"
                      : "text-midnight-600 hover:text-midnight-950"
                  }`}
                >
                  <FileText className="w-3.5 h-3.5 text-brand-600" />
                  <span>Creator</span>
                </Link>

                <Link
                  href="/reviewer"
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
                    pathname?.startsWith("/reviewer")
                      ? "bg-white text-purple-700 shadow-sm"
                      : "text-midnight-600 hover:text-midnight-950"
                  }`}
                >
                  <ClipboardCheck className="w-3.5 h-3.5 text-purple-600" />
                  <span>Reviewer</span>
                </Link>
              </>
            )}

            {user?.role === "compliance_officer" && (
              <>
                <Link
                  href="/compliance"
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
                    pathname?.startsWith("/compliance")
                      ? "bg-white text-amber-700 shadow-sm"
                      : "text-midnight-600 hover:text-midnight-950"
                  }`}
                >
                  <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
                  <span>Compliance Queue</span>
                </Link>

                <Link
                  href="/knowledge-base"
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
                    pathname?.startsWith("/knowledge-base")
                      ? "bg-white text-brand-700 shadow-sm"
                      : "text-midnight-600 hover:text-midnight-950"
                  }`}
                >
                  <Layers className="w-3.5 h-3.5 text-brand-600" />
                  <span>Knowledge Base</span>
                </Link>
              </>
            )}

            {user?.role === "reviewer" && (
              <>
                <Link
                  href="/reviewer"
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
                    pathname?.startsWith("/reviewer")
                      ? "bg-white text-purple-700 shadow-sm"
                      : "text-midnight-600 hover:text-midnight-950"
                  }`}
                >
                  <ClipboardCheck className="w-3.5 h-3.5 text-purple-600" />
                  <span>Reviewer Station</span>
                </Link>

                <Link
                  href="/knowledge-base"
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
                    pathname?.startsWith("/knowledge-base")
                      ? "bg-white text-brand-700 shadow-sm"
                      : "text-midnight-600 hover:text-midnight-950"
                  }`}
                >
                  <Layers className="w-3.5 h-3.5 text-brand-600" />
                  <span>Knowledge Base</span>
                </Link>
              </>
            )}

            {user?.role === "creator" && (
              <>
                <Link
                  href="/creator"
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
                    pathname?.startsWith("/creator")
                      ? "bg-white text-brand-700 shadow-sm"
                      : "text-midnight-600 hover:text-midnight-950"
                  }`}
                >
                  <FileText className="w-3.5 h-3.5 text-brand-600" />
                  <span>Creator Studio</span>
                </Link>

                <Link
                  href="/knowledge-base"
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
                    pathname?.startsWith("/knowledge-base")
                      ? "bg-white text-brand-700 shadow-sm"
                      : "text-midnight-600 hover:text-midnight-950"
                  }`}
                >
                  <Layers className="w-3.5 h-3.5 text-brand-600" />
                  <span>Knowledge Base</span>
                </Link>
              </>
            )}
          </div>

          {/* Current Authenticated User Identity */}
          <div className="flex items-center gap-2.5 pl-2 border-l border-midnight-100">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs ${
                user?.role === "admin"
                  ? "bg-emerald-100 text-emerald-800"
                  : user?.role === "compliance_officer"
                  ? "bg-amber-100 text-amber-800"
                  : user?.role === "reviewer"
                  ? "bg-purple-100 text-purple-800"
                  : "bg-brand-100 text-brand-800"
              }`}
            >
              {user?.full_name?.charAt(0) || "U"}
            </div>
            <div className="hidden sm:block text-left">
              <p className="text-xs font-semibold text-midnight-900 leading-tight">
                {user?.full_name || "User"}
              </p>
              <div className="flex items-center gap-1.5">
                <span
                  className={`inline-block text-[10px] font-bold uppercase tracking-wider ${
                    user?.role === "admin"
                      ? "text-emerald-700"
                      : user?.role === "compliance_officer"
                      ? "text-amber-700"
                      : user?.role === "reviewer"
                      ? "text-purple-700"
                      : "text-brand-700"
                  }`}
                >
                  {user?.role?.replace("_", " ") || "Creator"}
                </span>
                {user?.organization_name && (
                  <span className="text-[10px] text-midnight-400 font-normal truncate max-w-[120px]">
                    • {user.organization_name}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Sign Out Button */}
          <button
            onClick={logout}
            title="Sign out of account"
            className="p-2 text-midnight-500 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-all"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
