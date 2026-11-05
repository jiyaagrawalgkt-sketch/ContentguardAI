"use client";

import React from "react";
import Link from "next/link";
import { ShieldCheck, CheckCircle2, ArrowRight, AlertTriangle, Sparkles, Building2, Eye, UserCheck } from "lucide-react";

export function Hero() {
  return (
    <section className="relative overflow-hidden pt-12 pb-20 lg:pt-20 lg:pb-28">
      {/* Background radial gradient accent */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-96 bg-gradient-to-b from-brand-100/40 via-lavender-100/20 to-transparent pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto space-y-6">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold bg-white border border-brand-200/80 shadow-subtle text-midnight-900">
            <span className="w-2 h-2 rounded-full bg-brand-500 animate-pulse" />
            <span>AI Brand Governance & Content Compliance</span>
            <span className="text-midnight-400">•</span>
            <span className="text-brand-600 font-medium">Enterprise Edition</span>
          </div>

          {/* Main Headline */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-midnight-950 leading-[1.15]">
            Review it before <br className="hidden sm:inline" />
            <span className="bg-gradient-to-r from-brand-600 to-brand-500 bg-clip-text text-transparent">
              it ships.
            </span>
          </h1>

          {/* Subtitle */}
          <p className="text-lg sm:text-xl text-midnight-700 leading-relaxed max-w-2xl mx-auto font-normal">
            ContentGuard AI empowers marketing, legal, and brand governance teams to enforce tone, factual accuracy, restricted language, and visual identity across all content before publication.
          </p>

          {/* Call to Actions */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2">
            <Link
              href="/login"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-6 py-3.5 text-base font-medium text-white bg-midnight-900 hover:bg-midnight-800 rounded-xl shadow-card hover:shadow-elevated transition-all"
            >
              <span>Explore Demo Accounts</span>
              <ArrowRight className="w-4 h-4 text-brand-300" />
            </Link>
            <a
              href="#how-it-works"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 text-base font-medium text-midnight-800 bg-white hover:bg-lavender-50 border border-midnight-200/80 rounded-xl shadow-subtle transition-all"
            >
              <Eye className="w-4 h-4 text-brand-600" />
              <span>See Workflow</span>
            </a>
          </div>

          {/* Interactive Role Access Bar */}
          <div className="pt-6">
            <div className="p-4 rounded-2xl bg-white/90 border border-midnight-100 shadow-card max-w-2xl mx-auto">
              <p className="text-xs font-semibold text-midnight-500 uppercase tracking-wider mb-3">
                Experience Interactive Role Workspaces
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-left">
                <Link
                  href="/login?role=creator"
                  className="flex items-center gap-2.5 p-2.5 rounded-lg border border-midnight-100 hover:border-brand-300 hover:bg-brand-50/50 transition-all group"
                >
                  <div className="w-7 h-7 rounded-md bg-blue-100 flex items-center justify-center text-blue-700 font-semibold text-xs">
                    C
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-semibold text-midnight-900 group-hover:text-brand-600">
                      Creator
                    </p>
                    <p className="text-[10px] text-midnight-500 truncate">
                      Draft, analyze & fix
                    </p>
                  </div>
                </Link>

                <Link
                  href="/login?role=reviewer"
                  className="flex items-center gap-2.5 p-2.5 rounded-lg border border-midnight-100 hover:border-purple-300 hover:bg-purple-50/50 transition-all group"
                >
                  <div className="w-7 h-7 rounded-md bg-purple-100 flex items-center justify-center text-purple-700 font-semibold text-xs">
                    R
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-semibold text-midnight-900 group-hover:text-purple-600">
                      Reviewer
                    </p>
                    <p className="text-[10px] text-midnight-500 truncate">
                      Inspect & approve
                    </p>
                  </div>
                </Link>

                <Link
                  href="/login?role=admin"
                  className="flex items-center gap-2.5 p-2.5 rounded-lg border border-midnight-100 hover:border-emerald-300 hover:bg-emerald-50/50 transition-all group"
                >
                  <div className="w-7 h-7 rounded-md bg-emerald-100 flex items-center justify-center text-emerald-700 font-semibold text-xs">
                    A
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-semibold text-midnight-900 group-hover:text-emerald-600">
                      Admin
                    </p>
                    <p className="text-[10px] text-midnight-500 truncate">
                      Brand Hub & audit
                    </p>
                  </div>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
