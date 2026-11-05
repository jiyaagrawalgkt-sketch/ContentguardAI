"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ShieldAlert, CheckCircle, ArrowRight, Sparkles, RefreshCw } from "lucide-react";

export function LiveAuditDemo() {
  const sampleViolation = {
    original: "Our platform offers a 100% risk-free guarantee to double your leads within 24 hours. No other competitor can match our industry-first proprietary AI engine.",
    score: 48,
    issues: [
      {
        type: "Absolute Guarantee",
        severity: "Critical",
        evidence: "100% risk-free guarantee",
        explanation: "Violates Marketing Policy Rule 4.2 prohibiting absolute financial or performance guarantees.",
        fix: "reliable, high-performing lead generation pipeline",
      },
      {
        type: "Unverified Superiority Claim",
        severity: "High",
        evidence: "No other competitor can match",
        explanation: "Unsupported superiority claim requires empirical third-party verification.",
        fix: "designed to outperform standard legacy workflows",
      },
      {
        type: "Restricted Buzzword",
        severity: "Medium",
        evidence: "proprietary AI engine",
        explanation: "Restricted term under Brand Guidelines: replace with verified technical architecture.",
        fix: "ContentGuard Hybrid Governance Architecture",
      },
    ],
  };

  const [activeTab, setActiveTab] = useState<"findings" | "corrected">("findings");

  return (
    <section id="compliance" className="py-20 bg-midnight-950 text-white relative overflow-hidden">
      <div className="absolute top-0 right-1/4 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="text-center max-w-3xl mx-auto mb-14">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-white/10 text-brand-300 border border-white/10 mb-3">
            <Sparkles className="w-3.5 h-3.5" />
            Live Governance Playground
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
            See the AI Engine in Action
          </h2>
          <p className="text-midnight-400 text-sm sm:text-base mt-2">
            Every finding provides exact character quotes, rule citations, and verified 1-click replacements.
          </p>
        </div>

        <div className="max-w-4xl mx-auto bg-midnight-900 border border-midnight-800 rounded-3xl p-6 sm:p-8 shadow-2xl">
          {/* Header Bar */}
          <div className="flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-midnight-800">
            <div>
              <p className="text-xs text-midnight-400 font-mono">SAMPLE INPUT • MARKETING EMAIL DRAFT</p>
              <h4 className="text-base font-semibold text-white mt-0.5">Q4 Product Launch Announcement</h4>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-midnight-400">Compliance Score:</span>
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-bold font-mono">
                <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                48 / 100 (High Risk)
              </div>
            </div>
          </div>

          {/* Sample Text */}
          <div className="my-6 p-4 rounded-xl bg-midnight-950/80 border border-midnight-800/80 text-sm text-midnight-200 leading-relaxed font-mono">
            &ldquo;Our platform offers a{" "}
            <span className="bg-rose-500/20 text-rose-300 border-b-2 border-rose-500 px-1 py-0.5 rounded">
              100% risk-free guarantee
            </span>{" "}
            to double your leads within 24 hours.{" "}
            <span className="bg-amber-500/20 text-amber-300 border-b-2 border-amber-500 px-1 py-0.5 rounded">
              No other competitor can match
            </span>{" "}
            our industry-first{" "}
            <span className="bg-blue-500/20 text-blue-300 border-b-2 border-blue-500 px-1 py-0.5 rounded">
              proprietary AI engine
            </span>
            .&rdquo;
          </div>

          {/* Findings List */}
          <div className="space-y-3">
            {sampleViolation.issues.map((issue, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-midnight-950/50 border border-midnight-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                        issue.severity === "Critical"
                          ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                          : issue.severity === "High"
                          ? "bg-orange-500/20 text-orange-400 border border-orange-500/30"
                          : "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                      }`}
                    >
                      {issue.severity}
                    </span>
                    <span className="font-semibold text-white">{issue.type}</span>
                  </div>
                  <p className="text-midnight-400">{issue.explanation}</p>
                </div>
                <div className="sm:text-right shrink-0">
                  <span className="text-[10px] text-midnight-400 block mb-0.5">Recommended Fix</span>
                  <span className="font-mono text-emerald-400 font-medium">
                    &ldquo;{issue.fix}&rdquo;
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* CTA within Demo */}
          <div className="mt-8 pt-6 border-t border-midnight-800 flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-xs text-midnight-400 text-center sm:text-left">
              Accepting these 3 corrections elevates compliance score to{" "}
              <strong className="text-emerald-400">96 / 100 (Compliant)</strong>.
            </p>
            <Link
              href="/login?role=creator"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-medium text-xs shadow-glow transition-all"
            >
              <span>Test in Creator Studio</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
