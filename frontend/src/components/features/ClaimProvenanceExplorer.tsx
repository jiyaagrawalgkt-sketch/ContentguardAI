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
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { ExtractedClaim } from "@/types";
import { api } from "@/lib/api";

interface ClaimProvenanceProps {
  submissionId: string;
}

export function ClaimProvenanceExplorer({ submissionId }: ClaimProvenanceProps) {
  const [claims, setClaims] = useState<ExtractedClaim[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [reverifying, setReverifying] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("all");
  const [search, setSearch] = useState<string>("");
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    if (submissionId) {
      fetchClaims();
    }

    const handleClaimsUpdated = (e: any) => {
      if (!e.detail || e.detail.submissionId === submissionId) {
        fetchClaims();
      }
    };
    window.addEventListener("claims-reverified", handleClaimsUpdated);
    return () => window.removeEventListener("claims-reverified", handleClaimsUpdated);
  }, [submissionId]);

  const fetchClaims = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get(`/evidence/claims/${submissionId}`);
      setClaims(res.data || []);
    } catch (e: any) {
      console.error(e);
      setError(e.response?.data?.detail || "Failed to retrieve claim provenance data.");
    } finally {
      setLoading(false);
    }
  };

  const handleReverify = async () => {
    try {
      setReverifying(true);
      setError(null);
      const res = await api.post(`/evidence/reverify/${submissionId}`);
      const updated = res.data.claims || [];
      setClaims(updated);
      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("claims-reverified", { detail: { submissionId } }));
      }
    } catch (e: any) {
      console.error(e);
      setError(e.response?.data?.detail || "Re-verification failed. Please try again.");
    } finally {
      setReverifying(false);
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

  if (error) {
    return (
      <div className="bg-white rounded-3xl border border-rose-200 shadow-card p-8 text-center space-y-3">
        <AlertTriangle className="w-8 h-8 text-rose-500 mx-auto" />
        <h4 className="text-sm font-bold text-rose-950">Claim Extraction Failed</h4>
        <p className="text-xs text-rose-700 max-w-md mx-auto leading-relaxed">{error}</p>
        <button
          onClick={fetchClaims}
          className="px-4 py-2 rounded-xl bg-midnight-950 text-white font-semibold text-xs shadow-md inline-flex items-center gap-2 hover:bg-midnight-900 transition-all"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Retry Evidence Extraction</span>
        </button>
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
              {claims.length} Verified Assertions
            </span>
          </div>
          <p className="text-xs text-midnight-500 mt-0.5">
            Trace every factual assertion directly back to its approved source passage and validity date.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleReverify}
            disabled={reverifying}
            className="px-3.5 py-1.5 rounded-xl border border-midnight-200 bg-white hover:bg-lavender-50 text-midnight-800 text-xs font-semibold inline-flex items-center gap-1.5 shadow-subtle transition-all disabled:opacity-50"
          >
            {reverifying ? <Loader2 className="w-3.5 h-3.5 animate-spin text-brand-600" /> : <RefreshCw className="w-3.5 h-3.5 text-brand-600" />}
            <span>Re-Verify Claims</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex flex-wrap items-center gap-1.5">
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
              {st} {st !== "all" && `(${claims.filter(c => c.verification_status.toLowerCase() === st).length})`}
            </button>
          ))}
        </div>

        <div className="relative min-w-[220px]">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search claims or citations..."
            className="w-full pl-8 pr-3 py-1.5 rounded-xl border border-midnight-200 text-xs text-midnight-950 placeholder:text-midnight-400 focus:outline-none focus:ring-1 focus:ring-brand-600"
          />
          <Search className="w-3.5 h-3.5 text-midnight-400 absolute left-2.5 top-2.5" />
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="py-12 text-center space-y-2">
          <FileText className="w-8 h-8 text-midnight-300 mx-auto" />
          <p className="text-sm font-bold text-midnight-800">
            {claims.length === 0
              ? "No factual claims detected"
              : "No claims match this filter"}
          </p>
          <p className="text-xs text-midnight-500 max-w-sm mx-auto leading-relaxed">
            {claims.length === 0
              ? "Claim extraction completed successfully. This draft contains general marketing, guidance, or creative copy without specific numerical, benchmark, or SLA assertions."
              : "Try switching status filters or clearing the search query to inspect other extracted assertions."}
          </p>
          {claims.length === 0 && (
            <div className="pt-2">
              <button
                onClick={handleReverify}
                disabled={reverifying}
                className="px-3.5 py-1.5 rounded-xl bg-brand-600 text-white text-xs font-semibold hover:bg-brand-700 inline-flex items-center gap-1.5 shadow-sm"
              >
                {reverifying ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                <span>Re-Scan Content for Claims</span>
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map((claim, idx) => (
            <div
              key={claim.id || idx}
              className={`p-5 rounded-2xl border transition-all shadow-subtle space-y-3 ${
                claim.verification_status === "supported"
                  ? "border-emerald-200 bg-emerald-50/20"
                  : claim.verification_status === "conflicting"
                  ? "border-amber-200 bg-amber-50/20"
                  : claim.verification_status === "outdated"
                  ? "border-purple-200 bg-purple-50/20"
                  : "border-rose-200 bg-rose-50/20"
              }`}
            >
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-midnight-100/60 pb-2.5">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-bold text-midnight-400">#{idx + 1}</span>
                  {getStatusBadge(claim.verification_status)}
                  <span className="text-[11px] font-semibold text-midnight-600 capitalize bg-white px-2 py-0.5 rounded border border-midnight-100">
                    {claim.claim_type.replace("_", " ")}
                  </span>
                </div>

                <div className="flex items-center gap-2 text-xs text-midnight-500 font-mono">
                  <span>Confidence: {Math.round((claim.confidence || 0.95) * 100)}%</span>
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
              <div className="text-xs font-mono font-bold text-midnight-950 bg-white p-3 rounded-xl border border-midnight-100">
                &ldquo;{claim.claim_text}&rdquo;
              </div>

              {/* Surrounding Context */}
              <div className="text-[11px] text-midnight-500 italic">
                From draft sentence: &ldquo;{claim.sentence || claim.claim_text}&rdquo;
              </div>

              {/* Audit Explanation */}
              <p className="text-xs text-midnight-800 leading-relaxed font-medium">
                {claim.explanation}
              </p>

              {/* Corroborating Passage or Source */}
              {claim.source_document_name ? (
                <div className="p-3 rounded-xl bg-white border border-midnight-200/80 text-xs space-y-1.5 shadow-sm">
                  <div className="flex items-center justify-between text-[11px] font-bold text-midnight-900">
                    <span className="flex items-center gap-1.5 text-brand-700">
                      <BookOpen className="w-3.5 h-3.5 text-brand-600" />
                      Approved Knowledge Source: {claim.source_document_name}
                    </span>
                    {claim.source_validity_date && (
                      <span className="text-[10px] text-midnight-500 font-mono">
                        Valid Until: {claim.source_validity_date}
                      </span>
                    )}
                  </div>
                  {claim.source_passage && (
                    <p className="font-mono text-[11px] text-midnight-800 leading-relaxed bg-lavender-50/50 p-2 rounded-lg border border-midnight-100 whitespace-pre-wrap">
                      {claim.source_passage}
                    </p>
                  )}
                </div>
              ) : (
                <div className="p-3 rounded-xl bg-white border border-rose-200 text-xs text-rose-800">
                  <span className="font-bold block mb-0.5">Evidence Deficit:</span>
                  <p className="leading-relaxed">No approved organizational evidence source was found for this assertion in the Knowledge Base.</p>
                </div>
              )}

              {/* Suggested Remediation */}
              {claim.suggested_correction && (
                <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-950">
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
