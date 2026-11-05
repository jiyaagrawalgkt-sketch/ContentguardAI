"use client";

import React from "react";
import { Mic, FileSearch, ShieldBan, Sparkles, Image, CheckCheck } from "lucide-react";

export function FeatureHighlights() {
  const features = [
    {
      icon: Mic,
      title: "Module A: Brand Voice Analyzer",
      description: "Evaluates tone consistency, vocabulary, audience appropriateness, and brand style across all content channels.",
      tag: "Tone & Voice",
    },
    {
      icon: FileSearch,
      title: "Module B: Factual Consistency Checker",
      description: "Cross-checks submitted claims, numbers, dates, and specifications against your organization's approved facts vault.",
      tag: "Ground Truth",
    },
    {
      icon: ShieldBan,
      title: "Module C: Restricted Language Detector",
      description: "Instantly flags prohibited terminology, misleading marketing phrases, and outdated trademarks with approved alternatives.",
      tag: "Deterministic Rules",
    },
    {
      icon: Sparkles,
      title: "Module D: Marketing Claim Analyzer",
      description: "Detects unverified guarantees, absolute promises, and unsupported numerical superiority claims before publication.",
      tag: "Legal Compliance",
    },
    {
      icon: Image,
      title: "Module E: Visual Brand Checker",
      description: "Analyzes uploaded images for brand color palette adherence (Delta-E calculation), dimensions, logo placement, and text OCR.",
      tag: "Visual Identity",
    },
    {
      icon: CheckCheck,
      title: "Module F: Accessibility & Readability",
      description: "Measures readability ease scores, detects missing image alt-text, and flags text contrast concerns.",
      tag: "Accessibility",
    },
  ];

  return (
    <section id="features" className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <p className="text-xs font-bold text-brand-600 uppercase tracking-widest mb-2">
            Multi-Modular Governance Engine
          </p>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-midnight-950 tracking-tight">
            Six Specialized Compliance Analyzers
          </h2>
          <p className="text-base text-midnight-600 mt-3">
            Every piece of submitted content is thoroughly vetted by our hybrid rule-based and AI compliance pipeline.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f, i) => {
            const Icon = f.icon;
            return (
              <div
                key={i}
                className="p-6 rounded-2xl bg-lavender-50/50 border border-midnight-100 hover:border-brand-300 hover:bg-white hover:shadow-card transition-all group"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="w-10 h-10 rounded-xl bg-white border border-midnight-100 flex items-center justify-center text-brand-600 group-hover:bg-brand-50 transition-colors">
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full bg-white border border-midnight-100 text-midnight-600">
                    {f.tag}
                  </span>
                </div>
                <h3 className="text-base font-bold text-midnight-900 mb-2">
                  {f.title}
                </h3>
                <p className="text-sm text-midnight-600 leading-relaxed">
                  {f.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
