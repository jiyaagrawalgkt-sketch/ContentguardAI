"use client";

import React from "react";
import { AlertCircle, CheckCircle2, ShieldAlert, Sparkles, XCircle, Check } from "lucide-react";

export function ProblemSolution() {
  const problems = [
    "Brand voice drifts across disjointed marketing channels",
    "Outdated product statistics and unapproved pricing claims published",
    "Restricted terminology triggers costly legal and regulatory penalties",
    "Inconsistent visual palettes and unauthorized logo usage",
    "No centralized audit trail of who approved what and when",
  ];

  const solutions = [
    "Autonomous voice consistency scoring across tone, clarity, and style",
    "Automated factual grounding against official, verified fact repositories",
    "Deterministic detection of prohibited language with instant replacements",
    "Computer-vision color palette distance checks and logo verification",
    "Immutable audit trail and state machine recording every reviewer action",
  ];

  return (
    <section id="governance" className="py-20 bg-lavender-50/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <p className="text-xs font-bold text-brand-600 uppercase tracking-widest mb-2">
            The Governance Dilemma
          </p>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-midnight-950 tracking-tight">
            Publishing at Scale Without Compromising Brand Integrity
          </h2>
          <p className="text-base text-midnight-600 mt-3">
            Manual reviews are slow, inconsistent, and error-prone. ContentGuard AI provides an intelligent, automated safety net.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto">
          {/* Without ContentGuard */}
          <div className="p-8 rounded-3xl bg-white border border-rose-200 shadow-card">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-rose-50 flex items-center justify-center text-rose-600">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-lg text-midnight-900">
                  Without ContentGuard AI
                </h3>
                <p className="text-xs text-rose-600 font-medium">
                  High Risk • Friction • Compliance Breaches
                </p>
              </div>
            </div>

            <ul className="space-y-4">
              {problems.map((item, idx) => (
                <li key={idx} className="flex items-start gap-3">
                  <XCircle className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
                  <span className="text-sm text-midnight-700 leading-snug">
                    {item}
                  </span>
                </li>
              ))}
            </ul>
          </div>

          {/* With ContentGuard */}
          <div className="p-8 rounded-3xl bg-white border border-brand-300 shadow-elevated relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-brand-50 rounded-full blur-2xl pointer-events-none" />

            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-brand-50 flex items-center justify-center text-brand-600">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-lg text-midnight-900">
                  With ContentGuard AI
                </h3>
                <p className="text-xs text-brand-600 font-semibold">
                  Zero Drift • Verified Facts • Rapid Approvals
                </p>
              </div>
            </div>

            <ul className="space-y-4">
              {solutions.map((item, idx) => (
                <li key={idx} className="flex items-start gap-3">
                  <div className="w-5 h-5 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-700 shrink-0 mt-0.5">
                    <Check className="w-3.5 h-3.5" />
                  </div>
                  <span className="text-sm text-midnight-800 font-medium leading-snug">
                    {item}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
