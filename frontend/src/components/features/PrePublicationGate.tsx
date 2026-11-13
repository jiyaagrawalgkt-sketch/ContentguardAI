"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  AlertCircle,
  Clock,
  ArrowRight,
  Send,
  Loader2,
  Sparkles,
  Lock,
  Unlock,
} from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

interface PrePublicationGateProps {
  submissionId: string;
  submissionStatus?: string;
  onRefresh?: () => void;
}

export function PrePublicationGate({ submissionId, submissionStatus, onRefresh }: PrePublicationGateProps) {
  const { user } = useAuth();
  const [gateData, setGateData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [publishing, setPublishing] = useState<boolean>(false);
  const [publishResult, setPublishResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchGateStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get(`/publishing/${submissionId}/gate-status`);
      setGateData(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Could not retrieve publication gate status.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGateStatus();
  }, [submissionId, submissionStatus]);

  const handlePublish = async () => {
    try {
      setPublishing(true);
      setError(null);
      const res = await api.post(`/publishing/${submissionId}/publish`);
      setPublishResult(res.data);
      if (onRefresh) onRefresh();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to publish content.");
    } finally {
      setPublishing(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-3xl border border-midnight-100 shadow-card p-12 text-center text-midnight-500 text-xs">
        <Loader2 className="w-6 h-6 animate-spin text-brand-600 mx-auto mb-2" />
        <p>Evaluating pre-publication gates...</p>
      </div>
    );
  }

  const checks = gateData?.checks || {};
  const isApproved = gateData?.gate_status === "approved_for_publication";
  const canPublish = gateData?.can_publish;

  const gateItems = [
    {
      title: "Automated Governance Analysis",
      desc: "Deterministic rule check & AI contextual compliance completed",
      passed: Boolean(checks.analysis_completed),
    },
    {
      title: "Zero Critical Violations",
      desc: "No critical policy breaches, unapproved financial guarantees, or data leaks",
      passed: Boolean(checks.zero_critical_violations),
    },
    {
      title: "Zero High-Risk Violations",
      desc: "No severe brand tone or unverified superlative violations",
      passed: Boolean(checks.zero_high_risk_violations),
    },
    {
      title: "Evidence Grounding Verification",
      desc: "All factual and statistical assertions verified in Knowledge Hub",
      passed: Boolean(checks.evidence_verified),
    },
    {
      title: "Authorized Reviewer Sign-Off",
      desc: "Formal approval by certified reviewer (separation of duties enforced)",
      passed: Boolean(checks.reviewer_approved),
    },
  ];

  return (
    <div className="bg-white rounded-3xl border border-midnight-100 shadow-card p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between pb-4 border-b border-midnight-100 gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Lock className="w-5 h-5 text-brand-600" />
            <h3 className="text-base font-extrabold text-midnight-950">
              Smart Pre-Publication Gate
            </h3>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-brand-50 text-brand-700 border border-brand-200 uppercase tracking-wider">
              Release Gatekeeper
            </span>
          </div>
          <p className="text-xs text-midnight-500 mt-0.5">
            Strict enterprise publication gatekeeper preventing unapproved or non-compliant content from shipping.
          </p>
        </div>

        <div>
          <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${
            isApproved
              ? "bg-emerald-100 text-emerald-800 border-emerald-200"
              : gateData?.gate_status === "changes_requested"
              ? "bg-orange-100 text-orange-800 border-orange-200"
              : gateData?.gate_status === "awaiting_review"
              ? "bg-amber-100 text-amber-800 border-amber-200"
              : "bg-rose-100 text-rose-800 border-rose-200"
          }`}>
            {isApproved ? <CheckCircle2 className="w-3.5 h-3.5" /> : <ShieldAlert className="w-3.5 h-3.5" />}
            <span>{gateData?.status_label || "Needs Attention"}</span>
          </span>
        </div>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {publishResult && (
        <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-950 text-xs space-y-2">
          <div className="flex items-center gap-2 font-bold">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>Content Successfully Published & Certified!</span>
          </div>
          <p>
            Public Preview Token: <code className="font-mono bg-white px-2 py-0.5 rounded border border-emerald-200">{publishResult.public_preview_token}</code>
          </p>
        </div>
      )}

      {/* 5 Gate Checklist */}
      <div className="space-y-3">
        {gateItems.map((g, idx) => (
          <div
            key={g.title}
            className={`p-4 rounded-2xl border transition-all flex items-start justify-between gap-4 ${
              g.passed
                ? "bg-emerald-50/30 border-emerald-200"
                : "bg-white border-midnight-100 shadow-subtle"
            }`}
          >
            <div className="flex items-start gap-3">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-0.5 text-xs font-bold ${
                g.passed ? "bg-emerald-100 text-emerald-700" : "bg-midnight-100 text-midnight-500"
              }`}>
                {idx + 1}
              </div>
              <div>
                <h4 className="text-xs font-bold text-midnight-950">{g.title}</h4>
                <p className="text-[11px] text-midnight-500 mt-0.5">{g.desc}</p>
              </div>
            </div>

            <div className="shrink-0">
              {g.passed ? (
                <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                  <CheckCircle2 className="w-3.5 h-3.5" /> PASSED
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-[11px] font-bold text-rose-700 bg-rose-100 px-2 py-0.5 rounded-full">
                  <XCircle className="w-3.5 h-3.5" /> REQUIRED
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Blockers list if any */}
      {gateData?.blockers && gateData.blockers.length > 0 && (
        <div className="p-4 rounded-2xl bg-amber-50/70 border border-amber-200 text-xs space-y-2">
          <div className="flex items-center gap-1.5 font-bold text-amber-900">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <span>Outstanding Publication Blockers ({gateData.blockers.length})</span>
          </div>
          <ul className="list-disc list-inside space-y-1 text-amber-950 font-medium text-[11px]">
            {gateData.blockers.map((b: string, i: number) => (
              <li key={i}>{b}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Action footer */}
      <div className="pt-2 flex items-center justify-between border-t border-midnight-100">
        <span className="text-[11px] text-midnight-500">
          Zero-Trust Policy: Content is strictly immutable once certified and published.
        </span>

        {user?.role === "reviewer" || user?.role === "admin" ? (
          <button
            onClick={handlePublish}
            disabled={!canPublish || publishing}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-midnight-950 hover:bg-midnight-900 disabled:opacity-50 transition-all shadow-md"
          >
            {publishing ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Unlock className="w-3.5 h-3.5 text-emerald-400" />
            )}
            <span>Publish & Issue Cryptographic Seal</span>
          </button>
        ) : (
          <span className="text-xs font-semibold text-midnight-600">
            {canPublish ? "Ready for Reviewer Release" : "Resolve Blockers to Proceed"}
          </span>
        )}
      </div>
    </div>
  );
}
