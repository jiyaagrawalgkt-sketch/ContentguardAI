"use client";

import React from "react";
import { UploadCloud, Cpu, CheckCheck, Send, FileCheck2, ArrowRight } from "lucide-react";

export function WorkflowVisualizer() {
  const steps = [
    {
      num: "01",
      icon: UploadCloud,
      title: "Content Ingestion",
      desc: "Upload documents (PDF, DOCX, TXT) or paste rich marketing drafts with target audience metadata.",
      color: "bg-blue-50 text-blue-600 border-blue-200",
    },
    {
      num: "02",
      icon: Cpu,
      title: "Hybrid AI Analysis",
      desc: "Deterministic rule matching + Gemini 2.5 evaluate brand voice, approved facts, prohibited words, and visual identity.",
      color: "bg-purple-50 text-purple-600 border-purple-200",
    },
    {
      num: "03",
      icon: FileCheck2,
      title: "Correction Workspace",
      desc: "Creators review explainable findings with exact text offsets, apply 1-click suggested fixes, and track score improvements.",
      color: "bg-amber-50 text-amber-600 border-amber-200",
    },
    {
      num: "04",
      icon: CheckCheck,
      title: "Human Governance & Approval",
      desc: "Authorized brand reviewers inspect side-by-side version diffs, annotate changes, or issue final publication approval.",
      color: "bg-emerald-50 text-emerald-600 border-emerald-200",
    },
  ];

  return (
    <section id="how-it-works" className="py-20 bg-white border-y border-midnight-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <p className="text-xs font-bold text-brand-600 uppercase tracking-widest mb-2">
            End-to-End Governance Lifecycle
          </p>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-midnight-950 tracking-tight">
            From Draft to Verified Publication
          </h2>
          <p className="text-base text-midnight-600 mt-3">
            An explainable, reliable 4-stage pipeline that bridges content creators and brand guardians.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            return (
              <div
                key={step.num}
                className="relative p-6 rounded-2xl bg-lavender-50/70 border border-midnight-100 hover:border-brand-200 hover:bg-white hover:shadow-card transition-all group"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center border ${step.color}`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <span className="text-2xl font-black text-midnight-200 group-hover:text-brand-300 transition-colors">
                    {step.num}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-midnight-900 mb-2">
                  {step.title}
                </h3>
                <p className="text-sm text-midnight-600 leading-relaxed">
                  {step.desc}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
