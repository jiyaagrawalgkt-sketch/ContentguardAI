"use client";

import React from "react";
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  AlertCircle,
  FileText,
  Sparkles,
  Info,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { AnalysisReport, DetectedIssue } from "@/types";

interface BrandRiskRadarProps {
  report: AnalysisReport | null;
  submissionTitle?: string;
}

export function BrandRiskRadar({ report, submissionTitle }: BrandRiskRadarProps) {
  if (!report) {
    return (
      <div className="bg-white rounded-3xl border border-midnight-100 p-8 text-center text-midnight-500 text-xs">
        <Sparkles className="w-8 h-8 text-midnight-400 mx-auto mb-2" />
        <p className="font-bold text-midnight-800">No Risk Analysis Available</p>
        <p className="mt-1">Run content analysis to generate your multi-dimensional Brand Risk Radar.</p>
      </div>
    );
  }

  const issues = report.issues || [];

  // Calculate categorical risk levels (0-100 scale, where 100 = safe, 0 = critical risk)
  const factualDeduction = (100 - (report.evidence_confidence_score ?? 100));
  const factualScore = Math.max(0, 100 - factualDeduction);

  const brandVoiceIssues = issues.filter((i) => i.module === "brand_voice" || i.category === "brand_voice");
  const brandVoiceScore = Math.max(0, 100 - brandVoiceIssues.length * 15);

  const restrictedIssues = issues.filter((i) => i.module === "restricted_language" || i.category === "misleading_claim");
  const restrictedScore = Math.max(0, 100 - restrictedIssues.length * 20);

  const sensitiveIssues = issues.filter((i) => i.category === "confidentiality" || i.category === "privacy" || i.category === "security_technical");
  const sensitiveScore = Math.max(0, 100 - sensitiveIssues.length * 25);

  const qualityScore = report.content_quality_score ?? 95;

  const riskCategories = [
    {
      name: "Factual Accuracy",
      score: factualScore,
      violations: issues.filter((i) => i.module === "fact_checker").length,
      desc: "Grounding against Knowledge Hub whitepapers & approved facts",
    },
    {
      name: "Brand Voice & Tone",
      score: brandVoiceScore,
      violations: brandVoiceIssues.length,
      desc: "Confidence through facts rather than marketing superlatives",
    },
    {
      name: "Restricted Language",
      score: restrictedScore,
      violations: restrictedIssues.length,
      desc: "Absence of prohibited guarantees, false claims, and buzzwords",
    },
    {
      name: "Sensitive Data & Privacy",
      score: sensitiveScore,
      violations: sensitiveIssues.length,
      desc: "Confidentiality, client privacy, credentials, and PII protection",
    },
    {
      name: "Readability & Quality",
      score: qualityScore,
      violations: qualityScore < 85 ? 1 : 0,
      desc: "Sentence length, clarity, accessibility, and vocabulary repetition",
    },
  ];

  const getRiskPill = (score: number) => {
    if (score >= 90) return { label: "Low Risk", color: "bg-emerald-100 text-emerald-800 border-emerald-200" };
    if (score >= 70) return { label: "Moderate Risk", color: "bg-amber-100 text-amber-800 border-amber-200" };
    if (score >= 50) return { label: "Elevated Risk", color: "bg-orange-100 text-orange-800 border-orange-200" };
    return { label: "Critical Risk", color: "bg-rose-100 text-rose-800 border-rose-200" };
  };

  const overallRisk = report.publication_risk || (report.compliance_score >= 90 ? "low" : report.compliance_score >= 75 ? "medium" : "high");

  return (
    <div className="bg-white rounded-3xl border border-midnight-100 shadow-card p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between pb-4 border-b border-midnight-100 gap-3">
        <div>
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-brand-600" />
            <h3 className="text-base font-extrabold text-midnight-950">
              Brand Risk Radar
            </h3>
            <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-brand-50 text-brand-700 border border-brand-200 uppercase tracking-wider">
              Round 3 Intelligence
            </span>
          </div>
          <p className="text-xs text-midnight-500 mt-0.5">
            Holistic publication safety assessment across 5 core governance vectors.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-midnight-600">Publication Readiness:</span>
          <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${
            overallRisk === "low"
              ? "bg-emerald-50 text-emerald-700 border-emerald-200"
              : overallRisk === "medium"
              ? "bg-amber-50 text-amber-700 border-amber-200"
              : "bg-rose-50 text-rose-700 border-rose-200"
          }`}>
            {overallRisk.toUpperCase()} RISK
          </span>
        </div>
      </div>

      {/* Grid of 5 Risk Vectors */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
        {riskCategories.map((cat) => {
          const pill = getRiskPill(cat.score);
          return (
            <div
              key={cat.name}
              className="p-4 rounded-2xl bg-lavender-50/40 border border-midnight-100 flex flex-col justify-between space-y-3"
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${pill.color}`}>
                    {pill.label}
                  </span>
                  <span className="text-xs font-extrabold text-midnight-900 font-mono">
                    {Math.round(cat.score)}%
                  </span>
                </div>
                <h4 className="text-xs font-bold text-midnight-950 leading-tight">
                  {cat.name}
                </h4>
                <p className="text-[11px] text-midnight-500 mt-1 line-clamp-2">
                  {cat.desc}
                </p>
              </div>

              {/* Progress Track */}
              <div>
                <div className="w-full bg-midnight-100 h-1.5 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      cat.score >= 90
                        ? "bg-emerald-500"
                        : cat.score >= 70
                        ? "bg-amber-500"
                        : "bg-rose-500"
                    }`}
                    style={{ width: `${cat.score}%` }}
                  />
                </div>
                <span className="text-[10px] text-midnight-400 font-mono mt-1 block">
                  {cat.violations} flagged finding{cat.violations === 1 ? "" : "s"}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Strategic Remediation Advice */}
      <div className="p-4 rounded-2xl bg-gradient-to-r from-brand-50/60 via-lavender-50/40 to-white border border-brand-200 flex items-start gap-3 text-xs">
        <Info className="w-5 h-5 text-brand-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-bold text-midnight-950">
            Pre-Publication Governance Summary
          </p>
          <p className="text-midnight-600 leading-relaxed">
            {report.critical_count > 0
              ? `Resolve the ${report.critical_count} critical policy violation(s) before submitting to review. Content with critical issues cannot be published.`
              : (report.evidence_confidence_score ?? 100) < 90
              ? "Factual assertions require citation against official whitepapers. Inspect the Claim Provenance tab to attach approved evidence."
              : "All 5 brand risk vectors are within acceptable parameters. Content satisfies zero-trust brand governance standards."}
          </p>
        </div>
      </div>
    </div>
  );
}
