"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  XCircle,
  AlertTriangle,
  Clock,
  HelpCircle,
  BookOpen,
  ArrowRight,
  ExternalLink,
  Copy,
  Check,
  Loader2,
  FileText,
  Search,
} from "lucide-react";
import { ExtractedClaim } from "@/types";
import { api } from "@/lib/api";

interface ClaimProvenanceProps {
  submissionId: string;
}

export function ClaimProvenanceExplorer({ submissionId }: ClaimProvenanceProps) {
  const [claims, setClaims] = useState<ExtractedClaim[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [filter, setFilter] = useState<string>("all");
  const [search, setSearch] = useState<string>("");
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    fetchClaims();
  }, [submissionId]);

  const fetchClaims = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/evidence/claims/${submissionId}`);
      setClaims(res.data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filtered = claims.filter((c) => {
    if (filter !== "all" && c.verification_status.toLowerCase() !== filter) return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        c.claim_text.toLowerCase().includes(q) ||
        (c.source_document_name && c.source_document_name.toLowerCase().includes(q)) ||
        c.explanation.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "supported":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
            <ShieldCheck className="w-3 h-3 text-emerald-600" /> SUPPORTED
          </span>
        );
      case "unsupported":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200">
            <XCircle className="w-3 h-3 text-rose-600" /> UNSUPPORTED
          </span>
        );
      case "conflicting":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
            <AlertTriangle className="w-3 h-3 text-amber-600" /> CONFLICTING
          </span>
        );
      case "outdated":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-purple-100 text-purple-800 border border-purple-200">
            <Clock className="w-3 h-3 text-purple-600" /> OUTDATED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-800 border border-slate-200">
            <HelpCircle className="w-3 h-3 text-slate-600" /> UNVERIFIED
          </span>
        );
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-3xl border border-midnight-100 shadow-card p-12 text-center text-midnight-500 text-xs">
        <Loader2 className="w-6 h-6 animate-spin text-brand-600 mx-auto mb-2" />
        <p>Loading claim provenance records...</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-3xl border border-midnight-100 shadow-card p-6 space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between pb-4 border-b border-midnight-100 gap-3">
        <div>
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-brand-600" />
            <h3 className="text-base font-extrabold text-midnight-950">
              Claim Provenance Explorer
            </h3>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-brand-50 text-brand-700 border border-brand-200 uppercase tracking-wider">
              Traceability Engine
            </span>
          </div>
          <p className="text-xs text-midnight-500 mt-0.5">
            Trace every factual assertion directly back to its approved source passage and validity date.
          </p>
        </div>

        {/* Filter buttons */}
        <div className="flex flex-wrap items-center gap-1.5 text-xs">
          {["all", "supported", "unsupported", "conflicting", "outdated"].map((st) => (
            <button
              key={st}
              onClick={() => setFilter(st)}
              className={`px-2.5 py-1 rounded-lg capitalize font-semibold transition-all ${
                filter === st
                  ? "bg-midnight-950 text-white"
                  : "bg-lavender-50 text-midnight-600 hover:bg-midnight-100"
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="py-12 text-center space-y-2">
          <FileText className="w-8 h-8 text-midnight-300 mx-auto" />
          <p className="text-sm font-bold text-midnight-800">No matching claims found</p>
          <p className="text-xs text-midnight-500">
            {claims.length === 0
              ? "No factual claims were detected in this content submission."
              : "Try switching status filters to view other extracted assertions."}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map((claim, idx) => (
            <div
              key={claim.id || idx}
              className="p-5 rounded-2xl border border-midnight-100 bg-white hover:border-brand-300 transition-all shadow-subtle space-y-3"
            >
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-midnight-100/60 pb-2.5">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-bold text-midnight-400">#{idx + 1}</span>
                  {getStatusBadge(claim.verification_status)}
                  <span className="text-[11px] font-semibold text-midnight-600 capitalize bg-lavender-50 px-2 py-0.5 rounded border border-midnight-100">
                    {claim.claim_type.replace("_", " ")}
                  </span>
                </div>

                <div className="flex items-center gap-2 text-xs text-midnight-500 font-mono">
                  <span>Confidence: {Math.round((claim.confidence || 1) * 100)}%</span>
                  <button
                    onClick={() => handleCopy(claim.claim_text, claim.id)}
                    className="p-1 hover:text-midnight-900 rounded"
                    title="Copy claim text"
                  >
                    {copiedId === claim.id ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              {/* Claim Text */}
              <div className="text-xs font-mono font-bold text-midnight-950 bg-lavender-50/60 p-3 rounded-xl border border-midnight-100">
                &ldquo;{claim.claim_text}&rdquo;
              </div>

              {/* Audit Explanation */}
              <p className="text-xs text-midnight-700 leading-relaxed">
                {claim.explanation}
              </p>

              {/* Corroborating Passage */}
              {claim.source_passage && (
                <div className="p-3 rounded-xl bg-emerald-50/40 border border-emerald-100 text-xs space-y-1">
                  <div className="flex items-center justify-between text-[11px] font-semibold text-emerald-900">
                    <span className="flex items-center gap-1.5">
                      <BookOpen className="w-3.5 h-3.5 text-emerald-700" />
                      Approved Knowledge Source: {claim.source_document_name || "Official Fact Vault"}
                    </span>
                    {claim.source_validity_date && (
                      <span className="text-[10px] text-emerald-700 font-mono">
                        Valid Until: {claim.source_validity_date}
                      </span>
                    )}
                  </div>
                  <p className="font-mono text-[11px] text-emerald-950 leading-relaxed whitespace-pre-wrap">
                    {claim.source_passage}
                  </p>
                </div>
              )}

              {/* Suggested Remediation */}
              {claim.suggested_correction && (
                <div className="p-3 rounded-xl bg-amber-50/60 border border-amber-200 text-xs text-amber-950">
                  <span className="font-bold block mb-0.5">Recommended Remediation:</span>
                  <p className="leading-relaxed">{claim.suggested_correction}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
