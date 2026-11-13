"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api, getApiBaseUrl } from "@/lib/api";
import { AppNavbar } from "@/components/layout/AppNavbar";
import { EvidenceGraph } from "@/components/evidence/EvidenceGraph";
import { ClaimProvenanceExplorer } from "@/components/features/ClaimProvenanceExplorer";
import { getScoreBadge } from "@/lib/utils";
import { VisualAnalysisReport } from "@/types";
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Send,
  ExternalLink,
  ShieldCheck,
  Sparkles,
  Loader2,
  FileText,
  UserCheck,
  Image as ImageIcon,
  Download,
  Eye,
  Layers,
  Sliders,
  Check,
  X,
} from "lucide-react";

interface Submission {
  id: string;
  title: string;
  category: string;
  target_platform?: string;
  campaign_name?: string;
  description?: string;
  status: string;
  current_content: string;
  creator_id?: string;
  creator_name?: string;
  versions: { id: string; version_number: number; content_body: string; change_summary?: string; created_at: string }[];
  latest_report?: {
    id: string;
    compliance_score: number;
    compliance_rating: string;
    total_issues: number;
    critical_count: number;
    high_count: number;
    medium_count: number;
    low_count: number;
    summary_verdict?: string;
    issues: any[];
  };
}

export default function ReviewerStationPage() {
  const { id } = useParams<{ id: string }>();
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();

  const [submission, setSubmission] = useState<Submission | null>(null);
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [publishedToken, setPublishedToken] = useState<string | null>(null);
  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // Visual Asset Governance State
  const [visualReports, setVisualReports] = useState<VisualAnalysisReport[]>([]);
  const [activeVisualIndex, setActiveVisualIndex] = useState(0);
  const [visualViewMode, setVisualViewMode] = useState<"side_by_side" | "original" | "corrected">("side_by_side");
  const [visualComment, setVisualComment] = useState("");
  const [visualSubmitting, setVisualSubmitting] = useState(false);
  const [visualPublishing, setVisualPublishing] = useState(false);

  const apiBase = getApiBaseUrl();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
      return;
    }
    if (id) {
      loadSubmission();
      loadVisualReports();
    }
  }, [id, isAuthenticated, authLoading]);

  const loadSubmission = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/submissions/${id}`);
      setSubmission(res.data);
      if (res.data.status === "published") {
        try {
          const pubRes = await api.get(`/publishing/preview/by-sub/${id}`);
          if (pubRes.data) setPublishedToken(pubRes.data.public_preview_token);
        } catch (e) {}
      }
    } catch (err: any) {
      setNotification({
        type: "error",
        message: err.response?.data?.detail || "Failed to load submission."
      });
    } finally {
      setLoading(false);
    }
  };

  const loadVisualReports = async () => {
    try {
      const res = await api.get(`/multimodal/submission/${id}`);
      setVisualReports(res.data || []);
    } catch (e) {
      console.error("No visual reports found or failed to load", e);
    }
  };

  const handleDecision = async (decision: "approved" | "rejected" | "changes_requested") => {
    if (!comment.trim()) {
      setNotification({
        type: "error",
        message: "Please enter feedback comments before submitting a decision."
      });
      return;
    }

    try {
      setSubmitting(true);
      setNotification(null);

      const decideRes = await api.post(`/reviews/${id}/decide`, {
        decision,
        comment,
      });

      setSubmission(decideRes.data);
      setComment("");

      if (decision === "approved") {
        setNotification({
          type: "success",
          message: `Submission approved by reviewer! It is now certified and ready for publication.`
        });
      } else {
        setNotification({
          type: "success",
          message: `Decision recorded: status updated to '${decision.replace("_", " ")}'.`
        });
      }
      loadVisualReports();
    } catch (err: any) {
      setNotification({
        type: "error",
        message: err.response?.data?.detail || "Failed to process decision."
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handlePublish = async () => {
    try {
      setPublishing(true);
      setNotification(null);
      const pubRes = await api.post(`/publishing/${id}/publish`);
      setPublishedToken(pubRes.data.public_preview_token);
      setNotification({
        type: "success",
        message: "Content officially published! Live public preview link is now generated."
      });
      loadSubmission();
      loadVisualReports();
    } catch (err: any) {
      setNotification({
        type: "error",
        message: err.response?.data?.detail || "Failed to publish content."
      });
    } finally {
      setPublishing(false);
    }
  };

  const handleVisualDecision = async (reportId: string, decision: "approved" | "rejected" | "changes_requested") => {
    try {
      setVisualSubmitting(true);
      const res = await api.post(`/multimodal/reports/${reportId}/review-decision`, {
        decision,
        comment: visualComment.trim() || undefined,
        comments: visualComment.trim() || undefined,
      });

      // Update local state
      setVisualReports((prev) =>
        prev.map((r) => ((r.id || r.report_id) === reportId ? res.data : r))
      );

      setNotification({
        type: "success",
        message: `Visual asset review decision recorded: ${decision.replace("_", " ").toUpperCase()}`,
      });
      setVisualComment("");
      loadSubmission();
    } catch (err: any) {
      setNotification({
        type: "error",
        message: err.response?.data?.detail || "Failed to record visual review decision.",
      });
    } finally {
      setVisualSubmitting(false);
    }
  };

  const handleVisualPublish = async (reportId: string) => {
    try {
      setVisualPublishing(true);
      setNotification(null);
      const res = await api.post(`/multimodal/reports/${reportId}/publish`);
      if (res.data.public_preview_token) {
        setPublishedToken(res.data.public_preview_token);
      }
      setNotification({
        type: "success",
        message: "Visual brand asset officially published and certified!",
      });
      loadVisualReports();
      loadSubmission();
    } catch (err: any) {
      setNotification({
        type: "error",
        message: err.response?.data?.detail || "Failed to publish visual asset.",
      });
    } finally {
      setVisualPublishing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-lavender-50 flex flex-col">
        <AppNavbar />
        <div className="flex-1 flex items-center justify-center text-midnight-500">
          <Loader2 className="w-8 h-8 animate-spin text-purple-600 mb-2" />
        </div>
      </div>
    );
  }

  const v1 = submission?.versions[0];
  const currentV = submission?.versions[submission.versions.length - 1];
  const visualScore = visualReports[0]?.visual_score ?? 0;
  const score = submission?.latest_report?.compliance_score ?? (visualReports.length > 0 ? visualScore : 0);
  const badge = getScoreBadge(score);
  const activeVisual = visualReports[activeVisualIndex];
  const activeVisualId = activeVisual ? (activeVisual.id || activeVisual.report_id) : "";

  return (
    <div className="min-h-screen bg-lavender-50 flex flex-col">
      <AppNavbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Top Header */}
        <div>
          <Link
            href="/reviewer"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-midnight-500 hover:text-midnight-900 transition-colors mb-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Review Queue</span>
          </Link>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200">
                  Review Station
                </span>
                <span className="text-xs text-midnight-500">
                  Author: <strong className="text-midnight-900">{submission?.creator_name}</strong>
                </span>
                {visualReports.length > 0 && (
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-brand-50 text-brand-700 border border-brand-200 flex items-center gap-1">
                    <ImageIcon className="w-3 h-3" />
                    <span>{visualReports.length} Visual Asset{visualReports.length > 1 ? "s" : ""} Attached</span>
                  </span>
                )}
              </div>
              <h1 className="text-2xl font-extrabold text-midnight-950">
                {submission?.title}
              </h1>
            </div>

            <div className="flex items-center gap-3">
              <span className="text-xs text-midnight-500">Score:</span>
              <div className={`px-3 py-1 rounded-full text-xs font-bold border font-mono ${badge.bgColor} ${badge.textColor} ${badge.borderColor}`}>
                {score.toFixed(0)} / 100 ({badge.label})
              </div>
            </div>
          </div>
        </div>

        {/* Notifications */}
        {notification && (
          <div className={`p-4 rounded-2xl border flex items-center gap-3 text-xs ${
            notification.type === "success"
              ? "bg-emerald-50 border-emerald-200 text-emerald-800"
              : "bg-rose-50 border-rose-200 text-rose-800"
          }`}>
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
            <span className="font-medium">{notification.message}</span>
          </div>
        )}

        {/* Published Link Banner */}
        {publishedToken && (
          <div className="p-4 rounded-2xl bg-white border border-purple-300 shadow-elevated flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-purple-100 flex items-center justify-center text-purple-700">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs font-bold text-midnight-900">
                  Content Verified & Officially Published
                </p>
                <p className="text-xs text-midnight-500">
                  The certified read-only public preview is available for executive and public verification.
                </p>
              </div>
            </div>

            <Link
              href={`/preview/${publishedToken}`}
              target="_blank"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-midnight-900 hover:bg-midnight-800 text-white font-semibold text-xs shadow-md transition-all shrink-0"
            >
              <span>Open Certified Public Preview</span>
              <ExternalLink className="w-3.5 h-3.5 text-brand-300" />
            </Link>
          </div>
        )}

        {/* Side-by-Side Version Diff & Inspection */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Version 1: Original Submitted Draft */}
          <div className="bg-white rounded-3xl border border-midnight-100 shadow-card p-6 flex flex-col">
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-midnight-100">
              <span className="text-xs font-bold text-midnight-700 uppercase tracking-wider">
                Original Draft (Version 1)
              </span>
              <span className="text-[11px] text-midnight-400 font-mono">
                {v1?.created_at ? new Date(v1.created_at).toLocaleTimeString() : ""}
              </span>
            </div>
            <div className="flex-1 p-4 rounded-2xl bg-lavender-50/50 border border-midnight-100 font-mono text-xs text-midnight-800 leading-relaxed whitespace-pre-wrap">
              {v1?.content_body}
            </div>
            <p className="mt-2 text-[11px] text-midnight-400">
              {v1?.change_summary || "Initial draft submitted by creator"}
            </p>
          </div>

          {/* Current Version: Corrected & Revised Copy */}
          <div className="bg-white rounded-3xl border border-midnight-100 shadow-card p-6 flex flex-col">
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-midnight-100">
              <span className="text-xs font-bold text-emerald-700 uppercase tracking-wider">
                Revised Copy (Version {currentV?.version_number || 1})
              </span>
              <span className="text-[11px] text-emerald-600 font-semibold px-2 py-0.5 rounded bg-emerald-50 border border-emerald-200">
                Ready for Publication
              </span>
            </div>
            <div className="flex-1 p-4 rounded-2xl bg-emerald-50/20 border border-emerald-100 font-mono text-xs text-midnight-900 leading-relaxed whitespace-pre-wrap">
              {currentV?.content_body}
            </div>
            <p className="mt-2 text-[11px] text-midnight-500">
              {currentV?.change_summary || "Latest corrected version"}
            </p>
          </div>
        </div>

        {/* ======================================================== */}
        {/* MULTIMODAL BRAND VISUAL REVIEW STATION                   */}
        {/* ======================================================== */}
        {activeVisual && (
          <div className="bg-white rounded-3xl border border-midnight-100 shadow-card p-6 sm:p-8 space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-midnight-100">
              <div>
                <div className="flex items-center gap-2">
                  <ImageIcon className="w-5 h-5 text-brand-600" />
                  <h3 className="text-base font-bold text-midnight-950">
                    Multimodal Visual Governance Station
                  </h3>
                  <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                    activeVisual.review_status === "approved"
                      ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                      : activeVisual.review_status === "rejected"
                      ? "bg-rose-50 text-rose-700 border border-rose-200"
                      : activeVisual.review_status === "changes_requested"
                      ? "bg-orange-50 text-orange-700 border border-orange-200"
                      : "bg-blue-50 text-blue-700 border border-blue-200"
                  }`}>
                    {activeVisual.review_status ? activeVisual.review_status.replace("_", " ") : "Pending Review"}
                  </span>
                </div>
                <p className="text-xs text-midnight-500 mt-1">
                  Inspect visual asset compliance, WCAG contrast corrections, logo protection, and OCR text.
                </p>
              </div>

              {/* View Mode Controls */}
              {activeVisual.has_corrected_image && (
                <div className="flex items-center gap-1 p-1 bg-midnight-50 rounded-xl border border-midnight-100 self-start sm:self-auto">
                  <button
                    onClick={() => setVisualViewMode("side_by_side")}
                    className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
                      visualViewMode === "side_by_side"
                        ? "bg-white text-midnight-950 shadow-sm"
                        : "text-midnight-600 hover:text-midnight-950"
                    }`}
                  >
                    Side-by-Side
                  </button>
                  <button
                    onClick={() => setVisualViewMode("original")}
                    className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
                      visualViewMode === "original"
                        ? "bg-white text-midnight-950 shadow-sm"
                        : "text-midnight-600 hover:text-midnight-950"
                    }`}
                  >
                    Original Only
                  </button>
                  <button
                    onClick={() => setVisualViewMode("corrected")}
                    className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
                      visualViewMode === "corrected"
                        ? "bg-white text-midnight-950 shadow-sm"
                        : "text-midnight-600 hover:text-midnight-950"
                    }`}
                  >
                    Corrected Only
                  </button>
                </div>
              )}
            </div>

            {/* Creator Notes Banner */}
            {activeVisual.creator_notes && (
              <div className="p-3.5 rounded-2xl bg-blue-50/60 border border-blue-200 text-xs text-blue-900 flex items-start gap-2.5">
                <Sparkles className="w-4 h-4 text-brand-600 shrink-0 mt-0.5" />
                <div>
                  <strong className="font-bold">Creator Submission Notes:</strong>
                  <p className="mt-0.5 text-blue-800">{activeVisual.creator_notes}</p>
                </div>
              </div>
            )}

            {/* Visual Canvas Display */}
            <div className={`grid gap-6 ${visualViewMode === "side_by_side" && activeVisual.has_corrected_image ? "grid-cols-1 md:grid-cols-2" : "grid-cols-1"}`}>
              {/* Original Asset */}
              {(visualViewMode === "side_by_side" || visualViewMode === "original" || !activeVisual.has_corrected_image) && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs font-semibold text-midnight-700">
                    <span className="flex items-center gap-1.5">
                      <Eye className="w-3.5 h-3.5 text-midnight-400" />
                      Original Asset (Draft Finding Layer)
                    </span>
                    <span className="text-[11px] text-midnight-400 font-mono">
                      Contrast: {activeVisual.contrast_ratio?.toFixed(2) || "N/A"}:1
                    </span>
                  </div>
                  <div className="relative rounded-2xl overflow-hidden border border-midnight-200 bg-midnight-950/5 flex items-center justify-center p-2 min-h-[260px]">
                    <img
                      src={`${apiBase}/multimodal/reports/${activeVisualId}/image/original`}
                      alt="Original Visual Asset"
                      className="max-h-[360px] w-auto object-contain rounded-xl shadow-sm"
                    />

                    {/* Bounding Box Highlights for Issues */}
                    {activeVisual.visual_issues?.map((iss, i) => {
                      if (!iss.region) return null;
                      return (
                        <div
                          key={i}
                          style={{
                            position: "absolute",
                            left: `${iss.region.x}%`,
                            top: `${iss.region.y}%`,
                            width: `${iss.region.width}%`,
                            height: `${iss.region.height}%`,
                          }}
                          className="border-2 border-rose-500 bg-rose-500/10 pointer-events-none rounded transition-all"
                        >
                          <span className="absolute -top-4 left-0 bg-rose-600 text-white text-[9px] font-bold px-1 rounded shadow">
                            {iss.title}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Corrected Asset */}
              {(visualViewMode === "side_by_side" || visualViewMode === "corrected") && activeVisual.has_corrected_image && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs font-semibold">
                    <span className={`flex items-center gap-1.5 ${
                      activeVisual.post_correction_verification?.passed
                        ? "text-emerald-800"
                        : activeVisual.post_correction_verification?.passed === false
                        ? "text-rose-800"
                        : "text-brand-800"
                    }`}>
                      {activeVisual.post_correction_verification?.passed ? (
                        <>
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                          <span>Corrected &amp; Verified Brand Asset</span>
                        </>
                      ) : activeVisual.post_correction_verification?.passed === false ? (
                        <>
                          <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                          <span>Correction Failed Independent Verification</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-3.5 h-3.5 text-brand-600" />
                          <span>Corrected Visual Asset</span>
                        </>
                      )}
                    </span>
                    {activeVisual.post_correction_verification ? (
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                        activeVisual.post_correction_verification.passed
                          ? "bg-emerald-50 text-emerald-700 border-emerald-300"
                          : "bg-rose-50 text-rose-700 border-rose-300"
                      }`}>
                        {activeVisual.post_correction_verification.status.toUpperCase()}
                      </span>
                    ) : (
                      <span className="text-[11px] text-emerald-600 font-mono bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                        WCAG 2.1 AA Compliant
                      </span>
                    )}
                  </div>
                  <div className={`relative rounded-2xl overflow-hidden border-2 flex items-center justify-center p-2 min-h-[260px] ${
                    activeVisual.post_correction_verification?.passed
                      ? "border-emerald-300 bg-emerald-50/10"
                      : activeVisual.post_correction_verification?.passed === false
                      ? "border-rose-300 bg-rose-50/10"
                      : "border-brand-200 bg-slate-50"
                  }`}>
                    <img
                      src={`${apiBase}/multimodal/reports/${activeVisualId}/image/corrected`}
                      alt="Corrected Visual Asset"
                      className="max-h-[360px] w-auto object-contain rounded-xl shadow-sm"
                    />
                  </div>
                  {activeVisual.post_correction_verification && (
                    <div className={`p-2.5 rounded-xl border text-[11px] leading-relaxed ${
                      activeVisual.post_correction_verification.passed
                        ? "bg-emerald-50/70 border-emerald-200 text-emerald-900"
                        : "bg-rose-50/70 border-rose-200 text-rose-900"
                    }`}>
                      <p className="font-bold text-[10.5px]">
                        {activeVisual.post_correction_verification.status_headline}
                      </p>
                      <p className="text-[10px] mt-0.5 opacity-90">
                        {activeVisual.post_correction_verification.summary}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Findings & Decisions Inspector */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-midnight-100">
              <div className="space-y-2">
                <span className="text-xs font-bold text-midnight-900 block">
                  Detected Optical & Accessibility Issues
                </span>
                <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                  {activeVisual.visual_issues?.map((iss, idx) => {
                    const isAccepted = activeVisual.accepted_corrections?.includes(iss.id || `issue_${idx}`);
                    const isRejected = activeVisual.rejected_corrections?.includes(iss.id || `issue_${idx}`);
                    return (
                      <div
                        key={idx}
                        className={`p-3 rounded-xl border text-xs flex items-start justify-between gap-2 ${
                          isAccepted
                            ? "bg-emerald-50/60 border-emerald-200 text-emerald-950"
                            : isRejected
                            ? "bg-slate-50 border-slate-200 text-slate-700"
                            : "bg-amber-50/60 border-amber-200 text-amber-950"
                        }`}
                      >
                        <div>
                          <div className="flex items-center gap-1.5 font-bold">
                            <span>{iss.title}</span>
                            <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 rounded bg-white/80 border border-slate-200">
                              {iss.severity}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-600 mt-0.5">{iss.explanation}</p>
                          <p className="text-[11px] text-brand-700 mt-1 font-medium">
                            <strong>Fix:</strong> {iss.suggestion}
                          </p>
                        </div>
                        <div className="shrink-0">
                          {isAccepted ? (
                            <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-700 bg-white px-2 py-0.5 rounded-full border border-emerald-300">
                              <Check className="w-3 h-3" /> Fixed
                            </span>
                          ) : isRejected ? (
                            <span className="inline-flex items-center gap-1 text-[10px] font-bold text-slate-500 bg-white px-2 py-0.5 rounded-full border border-slate-300">
                              <X className="w-3 h-3" /> Ignored
                            </span>
                          ) : (
                            <span className="text-[10px] text-amber-700 font-semibold">Pending</span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* OCR and Swatch Summary */}
              <div className="space-y-3">
                <span className="text-xs font-bold text-midnight-900 block">
                  OCR Text & Palette Compliance
                </span>
                <div className="p-3 rounded-xl bg-midnight-50/60 border border-midnight-100 text-xs space-y-2">
                  <div>
                    <span className="text-[11px] font-bold text-midnight-500 uppercase tracking-wider block">
                      OCR Extracted Copy:
                    </span>
                    <p className="font-mono text-midnight-900 bg-white p-2 rounded-lg border border-midnight-100 mt-1 line-clamp-3">
                      {activeVisual.ocr_extracted_text || "No text detected in asset."}
                    </p>
                  </div>

                  <div>
                    <span className="text-[11px] font-bold text-midnight-500 uppercase tracking-wider block">
                      Detected Palette Swatches:
                    </span>
                    <div className="flex items-center gap-1.5 mt-1">
                      {activeVisual.palette_colors?.map((c, i) => (
                        <div
                          key={i}
                          className="w-7 h-7 rounded-lg border border-midnight-200 shadow-xs flex items-center justify-center text-[9px] font-mono"
                          style={{ backgroundColor: c }}
                          title={c}
                        />
                      ))}
                    </div>
                  </div>
                </div>

                {/* Download Certified Asset Button if Approved */}
                {activeVisual.review_status === "approved" && (
                  <a
                    href={`${apiBase}/multimodal/reports/${activeVisualId}/download-asset`}
                    download
                    className="w-full py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs shadow-md transition-all flex items-center justify-center gap-2"
                  >
                    <Download className="w-4 h-4" />
                    <span>Download Certified Publication-Ready Asset</span>
                  </a>
                )}
              </div>
            </div>

            {/* Reviewer Decision Controls for Visual Asset */}
            <div className="pt-4 border-t border-midnight-100 space-y-3">
              <label className="block text-xs font-semibold text-midnight-800">
                Visual Brand Review Decision & Feedback
              </label>
              <textarea
                rows={2}
                value={visualComment}
                onChange={(e) => setVisualComment(e.target.value)}
                placeholder="Optional feedback comment on color contrast, logo clearspace, or typography..."
                className="w-full rounded-xl border border-midnight-200 p-2.5 text-xs text-midnight-900 focus:outline-none focus:ring-1 focus:ring-purple-600"
              />

              <div className="flex flex-wrap items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => handleVisualDecision(activeVisualId, "changes_requested")}
                  disabled={visualSubmitting}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-orange-700 bg-orange-50 border border-orange-200 hover:bg-orange-100 transition-colors disabled:opacity-50"
                >
                  Request Visual Changes
                </button>

                <button
                  type="button"
                  onClick={() => handleVisualDecision(activeVisualId, "rejected")}
                  disabled={visualSubmitting}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-rose-700 bg-rose-50 border border-rose-200 hover:bg-rose-100 transition-colors disabled:opacity-50"
                >
                  Reject Visual
                </button>

                <button
                  type="button"
                  onClick={() => handleVisualDecision(activeVisualId, "approved")}
                  disabled={visualSubmitting}
                  className="inline-flex items-center gap-2 px-5 py-2 rounded-xl text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 shadow-md transition-all disabled:opacity-50"
                >
                  {visualSubmitting ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <CheckCircle2 className="w-3.5 h-3.5" />
                  )}
                  <span>Approve Visual Draft</span>
                </button>

                {activeVisual.review_status === "approved" && !activeVisual.is_published && (
                  <button
                    type="button"
                    onClick={() => handleVisualPublish(activeVisualId)}
                    disabled={visualPublishing}
                    className="inline-flex items-center gap-2 px-5 py-2 rounded-xl text-xs font-semibold text-white bg-midnight-950 hover:bg-midnight-900 shadow-md transition-all disabled:opacity-50"
                  >
                    {visualPublishing ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <ShieldCheck className="w-3.5 h-3.5 text-brand-300" />
                    )}
                    <span>Publish Certified Asset</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Evidence Verification Graph & Fact Grounding */}
        <div className="space-y-6">
          <EvidenceGraph submissionId={id} submissionTitle={submission?.title} />
          <ClaimProvenanceExplorer submissionId={id} />
        </div>

        {/* Reviewer Decision Station */}
        <div className="bg-white rounded-3xl border border-midnight-100 shadow-card p-6 sm:p-8">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-midnight-100">
            <UserCheck className="w-5 h-5 text-purple-600" />
            <h3 className="text-sm font-bold text-midnight-950 uppercase tracking-wider">
              Governance Approval Station
            </h3>
            <span className="text-xs text-midnight-400">• Authenticated as {user?.full_name}</span>
          </div>

          {submission?.creator_id === user?.id && user?.role !== "admin" ? (
            <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 shrink-0 text-amber-600" />
              <div>
                <p className="font-bold">Governance Conflict of Interest Restricted</p>
                <p className="text-[11px] text-amber-700 mt-0.5">
                  As the original author of this draft, commercial compliance rules prohibit approving your own content. A peer reviewer must evaluate and clear this submission.
                </p>
              </div>
            </div>
          ) : (
            <>
              <div className="mb-4">
                <label className="block text-xs font-semibold text-midnight-800 mb-1">
                  Reviewer Notes / Feedback Comments *
                </label>
                <textarea
                  rows={3}
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="e.g. Revised copy removes prohibited guarantees and corrects SLA facts to 99.9%. Approved for production deployment."
                  className="w-full rounded-2xl border border-midnight-200 p-3 text-xs text-midnight-900 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                />
              </div>

              <div className="flex flex-wrap items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => handleDecision("changes_requested")}
                  disabled={submitting || publishing}
                  className="px-4 py-2.5 rounded-xl text-xs font-semibold text-orange-700 bg-orange-50 border border-orange-200 hover:bg-orange-100 transition-colors disabled:opacity-50"
                >
                  Request Changes
                </button>

                <button
                  type="button"
                  onClick={() => handleDecision("rejected")}
                  disabled={submitting || publishing}
                  className="px-4 py-2.5 rounded-xl text-xs font-semibold text-rose-700 bg-rose-50 border border-rose-200 hover:bg-rose-100 transition-colors disabled:opacity-50"
                >
                  Reject Content
                </button>

                <button
                  type="button"
                  onClick={() => handleDecision("approved")}
                  disabled={submitting || publishing}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 shadow-md transition-all disabled:opacity-50"
                >
                  {submitting ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <CheckCircle2 className="w-3.5 h-3.5 text-white" />
                  )}
                  <span>Approve Draft</span>
                </button>

                {submission?.status === "approved" && (
                  <button
                    type="button"
                    onClick={handlePublish}
                    disabled={publishing}
                    className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-semibold text-white bg-midnight-900 hover:bg-midnight-800 shadow-md hover:shadow-lg transition-all disabled:opacity-50"
                  >
                    {publishing ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <ShieldCheck className="w-3.5 h-3.5 text-brand-300" />
                    )}
                    <span>Publish Certified Content</span>
                  </button>
                )}
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
