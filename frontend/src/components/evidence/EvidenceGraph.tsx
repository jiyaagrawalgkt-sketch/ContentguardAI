"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  ShieldCheck,
  AlertTriangle,
  XCircle,
  Clock,
  HelpCircle,
  FileText,
  Sparkles,
  Info,
  RefreshCw,
  Search,
  ZoomIn,
  ZoomOut,
  Maximize2,
  ExternalLink,
  ChevronRight,
  BookOpen,
  ArrowRight,
  CheckCircle2,
  Loader2,
} from "lucide-react";
import { ExtractedClaim, EvidenceGraphData } from "@/types";
import { api } from "@/lib/api";

interface EvidenceGraphProps {
  submissionId: string;
  submissionTitle?: string;
}

export function EvidenceGraph({ submissionId, submissionTitle }: EvidenceGraphProps) {
  const [claims, setClaims] = useState<ExtractedClaim[]>([]);
  const [selectedClaimId, setSelectedClaimId] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [loading, setLoading] = useState<boolean>(true);
  const [verifying, setVerifying] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [zoomLevel, setZoomLevel] = useState<number>(1);

  const fetchEvidence = async () => {
    setLoading(true);
    setError(null);
    try {
      const claimsRes = await api.get(`/evidence/claims/${submissionId}`);
      const fetched = claimsRes.data || [];
      setClaims(fetched);
      if (fetched.length > 0) {
        setSelectedClaimId(fetched[0].id);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Could not retrieve evidence data.");
    } finally {
      setLoading(false);
    }
  };

  const handleRunVerification = async () => {
    setVerifying(true);
    setError(null);
    try {
      const res = await api.post(`/evidence/verify/${submissionId}`);
      const newClaims = res.data.claims || [];
      setClaims(newClaims);
      if (newClaims.length > 0) {
        setSelectedClaimId(newClaims[0].id);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Evidence verification failed.");
    } finally {
      setVerifying(false);
    }
  };

  useEffect(() => {
    if (submissionId) {
      fetchEvidence();
    }
  }, [submissionId]);

  const filteredClaims = useMemo(() => {
    if (filterStatus === "all") return claims;
    return claims.filter((c) => c.verification_status.toLowerCase() === filterStatus.toLowerCase());
  }, [claims, filterStatus]);

  const selectedClaim = useMemo(() => {
    return claims.find((c) => c.id === selectedClaimId) || claims[0] || null;
  }, [claims, selectedClaimId]);

  // Statistics
  const stats = useMemo(() => {
    return {
      total: claims.length,
      supported: claims.filter((c) => c.verification_status.toLowerCase() === "supported").length,
      unsupported: claims.filter((c) => c.verification_status.toLowerCase() === "unsupported").length,
      conflicting: claims.filter((c) => c.verification_status.toLowerCase() === "conflicting").length,
      outdated: claims.filter((c) => c.verification_status.toLowerCase() === "outdated").length,
    };
  }, [claims]);

  const getStatusBadge = (status: string) => {
    const s = status.toLowerCase();
    switch (s) {
      case "supported":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
            <ShieldCheck className="w-3.5 h-3.5" />
            SUPPORTED
          </span>
        );
      case "unsupported":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-200">
            <XCircle className="w-3.5 h-3.5" />
            UNSUPPORTED
          </span>
        );
      case "conflicting":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-200">
            <AlertTriangle className="w-3.5 h-3.5" />
            CONFLICTING
          </span>
        );
      case "outdated":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-purple-100 text-purple-800 border border-purple-200">
            <Clock className="w-3.5 h-3.5" />
            OUTDATED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-midnight-100 text-midnight-800 border border-midnight-200">
            <HelpCircle className="w-3.5 h-3.5" />
            UNVERIFIED
          </span>
        );
    }
  };

  const getNodeColor = (status: string, isSelected: boolean) => {
    const s = status.toLowerCase();
    if (s === "supported") return isSelected ? "#10B981" : "#059669";
    if (s === "unsupported") return isSelected ? "#F43F5E" : "#E11D48";
    if (s === "conflicting") return isSelected ? "#F59E0B" : "#D97706";
    if (s === "outdated") return isSelected ? "#A855F7" : "#9333EA";
    return isSelected ? "#64748B" : "#475569";
  };

  // SVG Geometry Calculations
  const svgWidth = 840;
  const rowHeight = 70;
  const svgHeight = Math.max(280, filteredClaims.length * rowHeight + 60);
  const rootY = svgHeight / 2;

  return (
    <div className="bg-white rounded-3xl border border-midnight-100 shadow-card overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-midnight-100 flex flex-wrap items-center justify-between gap-4 bg-gradient-to-r from-brand-50/60 via-white to-purple-50/40">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-brand-600" />
            <h3 className="text-base font-extrabold text-midnight-950">
              Evidence Intelligence Graph
            </h3>
            <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-brand-100 text-brand-800 border border-brand-200">
              Provenance & Grounding
            </span>
          </div>
          <p className="text-xs text-midnight-500 mt-0.5">
            Real-time topology mapping claims to ingested knowledge base documents and verified facts.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRunVerification}
            disabled={verifying}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-midnight-900 hover:bg-midnight-800 text-white text-xs font-semibold shadow-sm transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${verifying ? "animate-spin" : ""}`} />
            <span>{verifying ? "Verifying..." : "Re-Verify Claims"}</span>
          </button>
        </div>
      </div>

      {/* Stats KPI Ribbon */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 p-4 bg-lavender-50/50 border-b border-midnight-100">
        <div className="p-3 rounded-xl bg-white border border-emerald-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-[11px] font-semibold text-emerald-700 block">Supported Claims</span>
            <span className="text-xl font-extrabold text-emerald-950">{stats.supported}</span>
          </div>
          <ShieldCheck className="w-6 h-6 text-emerald-500" />
        </div>

        <div className="p-3 rounded-xl bg-white border border-rose-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-[11px] font-semibold text-rose-700 block">Unsupported Claims</span>
            <span className="text-xl font-extrabold text-rose-950">{stats.unsupported}</span>
          </div>
          <XCircle className="w-6 h-6 text-rose-500" />
        </div>

        <div className="p-3 rounded-xl bg-white border border-amber-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-[11px] font-semibold text-amber-700 block">Conflicting Facts</span>
            <span className="text-xl font-extrabold text-amber-950">{stats.conflicting}</span>
          </div>
          <AlertTriangle className="w-6 h-6 text-amber-500" />
        </div>

        <div className="p-3 rounded-xl bg-white border border-purple-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-[11px] font-semibold text-purple-700 block">Outdated Citations</span>
            <span className="text-xl font-extrabold text-purple-950">{stats.outdated}</span>
          </div>
          <Clock className="w-6 h-6 text-purple-500" />
        </div>
      </div>

      {/* Filter and Zoom Controls */}
      <div className="px-6 py-2.5 bg-white border-b border-midnight-100 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-1.5">
          <span className="text-midnight-500 font-semibold mr-1">Status Filter:</span>
          {["all", "supported", "unsupported", "conflicting", "outdated"].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`px-2.5 py-1 rounded-lg font-semibold capitalize transition-all ${
                filterStatus === st
                  ? "bg-midnight-900 text-white"
                  : "bg-lavender-50 text-midnight-600 hover:bg-midnight-100"
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[11px] text-midnight-400">Zoom:</span>
          <button
            onClick={() => setZoomLevel((z) => Math.max(0.7, z - 0.1))}
            className="p-1 rounded-lg border border-midnight-200 hover:bg-lavender-50 text-midnight-700"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <span className="font-mono text-[11px] w-9 text-center font-bold text-midnight-800">
            {Math.round(zoomLevel * 100)}%
          </span>
          <button
            onClick={() => setZoomLevel((z) => Math.min(1.4, z + 0.1))}
            className="p-1 rounded-lg border border-midnight-200 hover:bg-lavender-50 text-midnight-700"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setZoomLevel(1)}
            className="p-1 rounded-lg border border-midnight-200 hover:bg-lavender-50 text-midnight-700"
            title="Reset Zoom"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main Split: Topology Graph (Left) + Selected Claim Provenance Drawer (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-midnight-100">

        {/* Graph Canvas */}
        <div className="lg:col-span-7 p-4 bg-midnight-950 text-white overflow-x-auto min-h-[360px] flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-midnight-400 mb-2">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="font-semibold text-white">Interactive Node-Link Map</span>
            </div>
            <span className="font-mono text-[11px]">
              {filteredClaims.length} Claims • {stats.total} Total Ingested
            </span>
          </div>

          {loading ? (
            <div className="py-24 text-center space-y-2">
              <Loader2 className="w-7 h-7 animate-spin text-brand-400 mx-auto" />
              <p className="text-xs text-midnight-400">Loading factual graph nodes...</p>
            </div>
          ) : filteredClaims.length === 0 ? (
            <div className="py-20 text-center space-y-3">
              <Sparkles className="w-8 h-8 text-midnight-500 mx-auto" />
              <p className="text-xs text-midnight-300 font-semibold">
                No factual claims detected for this filter.
              </p>
              <button
                onClick={handleRunVerification}
                disabled={verifying}
                className="px-3.5 py-1.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold"
              >
                {verifying ? "Verifying..." : "Scan & Extract Claims Now"}
              </button>
            </div>
          ) : (
            <div
              className="relative overflow-auto"
              style={{ transform: `scale(${zoomLevel})`, transformOrigin: "top left", transition: "transform 0.15s ease" }}
            >
              <svg width={svgWidth} height={svgHeight} className="overflow-visible select-none">
                {/* Column Headers */}
                <text x="50" y="25" fill="#94A3B8" fontSize="10" fontWeight="700" letterSpacing="0.05em">
                  CONTENT DRAFT
                </text>
                <text x="230" y="25" fill="#94A3B8" fontSize="10" fontWeight="700" letterSpacing="0.05em">
                  EXTRACTED CLAIMS
                </text>
                <text x="460" y="25" fill="#94A3B8" fontSize="10" fontWeight="700" letterSpacing="0.05em">
                  EVIDENCE CITATION
                </text>
                <text x="690" y="25" fill="#94A3B8" fontSize="10" fontWeight="700" letterSpacing="0.05em">
                  VERDICT
                </text>

                {/* Root Draft Node */}
                <g transform={`translate(20, ${rootY - 24})`}>
                  <rect
                    width="140"
                    height="48"
                    rx="12"
                    fill="#1E293B"
                    stroke="#475569"
                    strokeWidth="1.5"
                  />
                  <text x="70" y="22" fill="#FFFFFF" fontSize="11" fontWeight="700" textAnchor="middle">
                    Draft Submission
                  </text>
                  <text x="70" y="36" fill="#94A3B8" fontSize="9" textAnchor="middle">
                    {submissionTitle?.slice(0, 18) || "Current Copy"}
                  </text>
                </g>

                {/* Render Each Claim Row */}
                {filteredClaims.map((claim, idx) => {
                  const claimY = 60 + idx * rowHeight;
                  const isSelected = selectedClaim?.id === claim.id;
                  const nodeColor = getNodeColor(claim.verification_status, isSelected);

                  // Curve 1: Root -> Claim
                  const curve1Path = `M 160 ${rootY} C 190 ${rootY}, 200 ${claimY + 18}, 230 ${claimY + 18}`;
                  // Curve 2: Claim -> Evidence Source
                  const curve2Path = `M 410 ${claimY + 18} C 430 ${claimY + 18}, 440 ${claimY + 18}, 460 ${claimY + 18}`;
                  // Curve 3: Evidence Source -> Verdict
                  const curve3Path = `M 640 ${claimY + 18} C 660 ${claimY + 18}, 670 ${claimY + 18}, 690 ${claimY + 18}`;

                  return (
                    <g
                      key={claim.id || idx}
                      className="cursor-pointer transition-opacity"
                      onClick={() => setSelectedClaimId(claim.id)}
                    >
                      {/* Connection Curves */}
                      <path
                        d={curve1Path}
                        fill="none"
                        stroke={nodeColor}
                        strokeWidth={isSelected ? 2.5 : 1.2}
                        strokeOpacity={isSelected ? 0.9 : 0.4}
                      />
                      <path
                        d={curve2Path}
                        fill="none"
                        stroke={nodeColor}
                        strokeWidth={isSelected ? 2.5 : 1.2}
                        strokeOpacity={isSelected ? 0.9 : 0.4}
                      />
                      <path
                        d={curve3Path}
                        fill="none"
                        stroke={nodeColor}
                        strokeWidth={isSelected ? 2.5 : 1.2}
                        strokeOpacity={isSelected ? 0.9 : 0.4}
                      />

                      {/* Claim Node (Column 2) */}
                      <g transform={`translate(230, ${claimY})`}>
                        <rect
                          width="180"
                          height="36"
                          rx="8"
                          fill={isSelected ? "#1E1B4B" : "#0F172A"}
                          stroke={nodeColor}
                          strokeWidth={isSelected ? 2 : 1}
                        />
                        <text
                          x="12"
                          y="18"
                          fill="#FFFFFF"
                          fontSize="10"
                          fontWeight="700"
                        >
                          "{claim.claim_text.slice(0, 22)}{claim.claim_text.length > 22 ? "..." : ""}"
                        </text>
                        <text
                          x="12"
                          y="29"
                          fill="#94A3B8"
                          fontSize="8"
                        >
                          {claim.claim_type.replace("_", " ").toUpperCase()}
                        </text>
                      </g>

                      {/* Evidence Source Node (Column 3) */}
                      <g transform={`translate(460, ${claimY})`}>
                        <rect
                          width="180"
                          height="36"
                          rx="8"
                          fill="#0F172A"
                          stroke={claim.source_document_name ? "#334155" : "#475569"}
                          strokeDasharray={claim.source_document_name ? "none" : "3,3"}
                          strokeWidth="1"
                        />
                        <text
                          x="12"
                          y="18"
                          fill={claim.source_document_name ? "#E2E8F0" : "#64748B"}
                          fontSize="10"
                          fontWeight="600"
                        >
                          {claim.source_document_name
                            ? claim.source_document_name.slice(0, 20) + (claim.source_document_name.length > 20 ? "..." : "")
                            : "No Corroborating Source"}
                        </text>
                        <text
                          x="12"
                          y="29"
                          fill="#64748B"
                          fontSize="8"
                        >
                          {claim.source_validity_date ? `Exp: ${claim.source_validity_date}` : "Zero-Trust Verified"}
                        </text>
                      </g>

                      {/* Verdict Badge Node (Column 4) */}
                      <g transform={`translate(690, ${claimY})`}>
                        <rect
                          width="120"
                          height="36"
                          rx="8"
                          fill={nodeColor}
                          fillOpacity={0.2}
                          stroke={nodeColor}
                          strokeWidth="1.5"
                        />
                        <text
                          x="60"
                          y="22"
                          fill={nodeColor}
                          fontSize="10"
                          fontWeight="800"
                          textAnchor="middle"
                          letterSpacing="0.04em"
                        >
                          {claim.verification_status.toUpperCase()}
                        </text>
                      </g>
                    </g>
                  );
                })}
              </svg>
            </div>
          )}

          {/* Legend */}
          <div className="pt-3 border-t border-midnight-900 flex flex-wrap items-center gap-4 text-[11px] text-midnight-400">
            <span className="font-semibold text-white">Legend:</span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Supported
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500" /> Unsupported
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> Conflicting
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-purple-500" /> Outdated
            </span>
          </div>
        </div>

        {/* Selected Node Detail & Provenance Inspector (Right Column) */}
        <div className="lg:col-span-5 p-6 bg-white space-y-4">
          <div className="flex items-center justify-between border-b border-midnight-100 pb-3">
            <span className="text-xs font-bold text-midnight-800 uppercase tracking-wide">
              Evidence Citation Inspector
            </span>
            {selectedClaim && getStatusBadge(selectedClaim.verification_status)}
          </div>

          {!selectedClaim ? (
            <div className="py-12 text-center text-midnight-400 text-xs">
              Select any node in the graph to inspect evidence citations and audit reasoning.
            </div>
          ) : (
            <div className="space-y-4 text-xs">
              {/* Claim Statement */}
              <div>
                <span className="text-[11px] font-bold text-midnight-500 uppercase tracking-wider block mb-1">
                  Claim Under Audit:
                </span>
                <div className="p-3 bg-lavender-50 rounded-xl border border-midnight-100 font-semibold text-midnight-950">
                  "{selectedClaim.claim_text}"
                </div>
              </div>

              {/* Classification & Confidence */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-white border border-midnight-100">
                  <span className="text-[10px] text-midnight-400 block font-semibold">Claim Type</span>
                  <span className="font-bold text-midnight-800 capitalize text-xs">
                    {selectedClaim.claim_type.replace("_", " ")}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-white border border-midnight-100">
                  <span className="text-[10px] text-midnight-400 block font-semibold">Confidence Score</span>
                  <span className="font-bold text-midnight-800 text-xs font-mono">
                    {Math.round(selectedClaim.confidence * 100)}% Match
                  </span>
                </div>
              </div>

              {/* Rationale & Explanation */}
              <div>
                <span className="text-[11px] font-bold text-midnight-500 uppercase tracking-wider block mb-1">
                  Grounding Rationale:
                </span>
                <p className="text-midnight-700 leading-relaxed bg-white p-3 rounded-xl border border-midnight-100">
                  {selectedClaim.explanation}
                </p>
              </div>

              {/* Source Document Passage */}
              {selectedClaim.source_passage && (
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] font-bold text-midnight-500 uppercase tracking-wider">
                      Corroborating Document Passage:
                    </span>
                    {selectedClaim.source_document_name && (
                      <span className="text-[10px] font-mono text-brand-600 truncate max-w-[160px]">
                        {selectedClaim.source_document_name}
                      </span>
                    )}
                  </div>
                  <div className="p-3 bg-emerald-50/40 rounded-xl border border-emerald-100 font-mono text-[11px] text-emerald-950 leading-relaxed whitespace-pre-wrap">
                    {selectedClaim.source_passage}
                  </div>
                </div>
              )}

              {/* Suggested Remediation */}
              {selectedClaim.suggested_correction && (
                <div className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200 text-amber-900 space-y-1">
                  <div className="flex items-center gap-1.5 font-bold text-xs">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    <span>Recommended Remediation</span>
                  </div>
                  <p className="text-xs leading-relaxed">{selectedClaim.suggested_correction}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
