"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Image as ImageIcon,
  Upload,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Eye,
  Type,
  Palette,
  FileCheck,
  Loader2,
  Sparkles,
  Info,
  Check,
  X,
  Sliders,
  Send,
  Download,
  ShieldCheck,
  Building2,
  AlertCircle,
  Maximize2,
  RefreshCw,
  RotateCcw,
} from "lucide-react";
import { VisualAnalysisReport } from "@/types";
import { api, getApiBaseUrl } from "@/lib/api";

interface SamplePreset {
  id: string;
  title: string;
  badge: string;
  icon: string;
  brand: string;
  description: string;
  violations_preview: string[];
}

const SAMPLE_PRESETS: SamplePreset[] = [
  {
    id: "pepsi-campaign-poster",
    title: "Pepsi Multimodal Poster",
    badge: "All 4 Categories",
    icon: "🥤",
    brand: "Pepsi",
    description: "Outdated/Purple Logo + Off-Brand Colors + #1 Claim + Low Contrast",
    violations_preview: [
      "Logo Mismatch: Purple Pepsi Globe (#9C27B0) instead of official Pepsi Blue (#004B93)",
      "Off-brand color palette (#9C27B0 & cream #FFFDE7)",
      "Unsupported promotional claim (#1 in the world with 100% guarantee)",
      "WCAG 2.1 AA contrast failure (< 4.5:1)",
      "Typo: 'revalutionary'",
    ],
  },
  {
    id: "apple-certified-card",
    title: "Apple Partner Card",
    badge: "Card Framing & Proportions",
    icon: "🍎",
    brand: "Apple",
    description: "Container framing & horizontally stretched Apple logo (0.82:1 canonical)",
    violations_preview: [
      "Distorted logo proportions (stretched horizontally)",
      "Container card preservation without wiping canvas",
    ],
  },
  {
    id: "lg-display-banner",
    title: "LG UltraWide Banner",
    badge: "16:9 Standardization",
    icon: "📺",
    brand: "LG",
    description: "2.79:1 banner non-destructively standardized to 16:9 marketing format",
    violations_preview: [
      "Non-standard canvas ratio (2.79:1)",
      "Standardize to 16:9 landscape without distorting artwork",
    ],
  },
  {
    id: "enterprise-launch-poster",
    title: "Enterprise Launch Poster",
    badge: "Casing & Claims",
    icon: "🛡️",
    brand: "Enterprise",
    description: "Brand casing ('Linkedin'), typo ('unlimitted'), claim & microscopic disclaimer",
    violations_preview: [
      "Brand name casing error ('Linkedin' -> 'LinkedIn')",
      "Promotional typo ('unlimitted' -> 'unlimited')",
      "Unqualified claim ('100% risk-free')",
      "Microscopic disclaimer text hazard",
    ],
  },
];

interface VisualAuditPanelProps {
  submissionId?: string;
  onAnalysisComplete?: (report: VisualAnalysisReport) => void;
  onReviewSubmitted?: () => void;
}

export function VisualAuditPanel({ submissionId, onAnalysisComplete, onReviewSubmitted }: VisualAuditPanelProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [altText, setAltText] = useState<string>("");
  const [report, setReport] = useState<VisualAnalysisReport | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [isGeneratingFix, setIsGeneratingFix] = useState<boolean>(false);
  const [loadingPresetId, setLoadingPresetId] = useState<string | null>(null);
  const [isSubmittingReview, setIsSubmittingReview] = useState<boolean>(false);
  const [activeFindingId, setActiveFindingId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"side_by_side" | "original" | "corrected">("side_by_side");
  const [creatorNotes, setCreatorNotes] = useState<string>("");
  const [selectedVariants, setSelectedVariants] = useState<Record<string, string>>({});
  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error" | "info"; text: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const replaceFileInputRef = useRef<HTMLInputElement>(null);

  const apiBase = getApiBaseUrl();

  const handleLoadPreset = async (presetId: string) => {
    try {
      setLoadingPresetId(presetId);
      setStatusMessage({ type: "info", text: `Synthesizing test graphic and executing Multimodal Brand Intelligence inspection...` });
      const res = await api.post(`/multimodal/sample-presets/${presetId}/load`);
      const newReport = res.data;
      setReport(newReport);
      setPreviewUrl(`${apiBase}/multimodal/reports/${newReport.report_id}/image/original`);
      setSelectedFile(null);
      setViewMode("side_by_side");
      setStatusMessage({
        type: "success",
        text: `Loaded test preset '${newReport.title || presetId}'. ${newReport.visual_issues?.length || 0} multimodal brand governance findings detected.`
      });
      if (onAnalysisComplete) onAnalysisComplete(newReport);
    } catch (err: any) {
      setStatusMessage({
        type: "error",
        text: err?.response?.data?.detail || "Failed to load sample preset test case."
      });
    } finally {
      setLoadingPresetId(null);
    }
  };

  // Load existing visual reports for this submission if available
  useEffect(() => {
    if (submissionId) {
      loadExistingReport();
    }
  }, [submissionId]);

  const loadExistingReport = async () => {
    try {
      const res = await api.get(`/multimodal/submission/${submissionId}`);
      if (res.data && res.data.length > 0) {
        const latest = res.data[res.data.length - 1];
        setReport(latest);
        setPreviewUrl(`${apiBase}/multimodal/reports/${latest.report_id}/image/original`);
        if (onAnalysisComplete) onAnalysisComplete(latest);
      }
    } catch (e) {
      console.warn("Could not load existing visual report", e);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setReport(null);
      setStatusMessage(null);
    }
  };

  const runVisualAnalysis = async () => {
    if (!selectedFile) return;

    setIsAnalyzing(true);
    setStatusMessage(null);

    const formData = new FormData();
    formData.append("file", selectedFile);
    if (submissionId) {
      formData.append("submission_id", submissionId);
    }
    if (altText) {
      formData.append("alt_text", altText);
    }
    formData.append("title", selectedFile.name);

    try {
      const res = await api.post("/multimodal/analyze", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setReport(res.data);
      setStatusMessage({ type: "success", text: "Visual brand audit completed successfully!" });
      if (onAnalysisComplete) {
        onAnalysisComplete(res.data);
      }
    } catch (err: any) {
      console.error("Visual analysis error:", err);
      setStatusMessage({
        type: "error",
        text: err.response?.data?.detail || "Failed to analyze image. Please ensure file format is PNG/JPG."
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleCorrectionDecision = async (findingId: string, decision: "accept" | "reject") => {
    if (!report) return;
    try {
      const res = await api.post(`/multimodal/reports/${report.report_id}/findings/${findingId}/decision`, {
        decision
      });
      setReport({
        ...report,
        accepted_corrections: res.data.accepted_corrections,
        rejected_corrections: res.data.rejected_corrections,
      });
      setStatusMessage({
        type: "info",
        text: `Correction ${decision === "accept" ? "accepted" : "rejected"}.`
      });
    } catch (e: any) {
      console.error(e);
      setStatusMessage({ type: "error", text: "Failed to record correction decision." });
    }
  };

  const handleGenerateCorrected = async () => {
    if (!report) return;
    try {
      setIsGeneratingFix(true);
      setStatusMessage(null);

      // Check if user selected an official variant for any logo finding
      const logoIssue = report.visual_issues?.find(
        (iss) => iss.category === "logo_integrity" || iss.brand_key
      );
      const chosenVariant = logoIssue
        ? (selectedVariants[logoIssue.id || ""] || logoIssue.recommended_variant || "primary")
        : undefined;

      await api.post(`/multimodal/reports/${report.report_id}/generate-corrected`, {
        selected_variant: chosenVariant,
      });

      // Refresh report
      const repRes = await api.get(`/multimodal/reports/${report.report_id}`);
      setReport(repRes.data);
      setViewMode("side_by_side");

      const ver = repRes.data.post_correction_verification;
      if (ver?.passed) {
        setStatusMessage({
          type: "success",
          text: `Applied official brand asset (${chosenVariant || "primary"}). Post-correction audit PASSED.`,
        });
      } else if (ver && !ver.passed) {
        setStatusMessage({
          type: "error",
          text: `Applied correction, but post-correction audit flagged: ${ver.summary}`,
        });
      } else {
        setStatusMessage({
          type: "success",
          text: "Applied accepted corrections and generated publication-ready visual!",
        });
      }
    } catch (e: any) {
      console.error(e);
      setStatusMessage({ type: "error", text: e.response?.data?.detail || "Failed to generate corrected visual." });
    } finally {
      setIsGeneratingFix(false);
    }
  };

  const handleUndoCorrection = async () => {
    if (!report) return;
    try {
      setIsGeneratingFix(true);
      setStatusMessage(null);
      await api.post(`/multimodal/reports/${report.report_id}/undo-correction`);
      const repRes = await api.get(`/multimodal/reports/${report.report_id}`);
      setReport(repRes.data);
      setViewMode("original");
      setStatusMessage({
        type: "info",
        text: "Applied replacement undone. Restored original visual asset.",
      });
    } catch (e: any) {
      console.error(e);
      setStatusMessage({
        type: "error",
        text: e.response?.data?.detail || "Failed to undo corrections.",
      });
    } finally {
      setIsGeneratingFix(false);
    }
  };

  const handleUploadReplacement = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!report || !e.target.files || !e.target.files[0]) return;
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append("file", file);

    try {
      setIsGeneratingFix(true);
      await api.post(`/multimodal/reports/${report.report_id}/upload-corrected`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      const repRes = await api.get(`/multimodal/reports/${report.report_id}`);
      setReport(repRes.data);
      setViewMode("side_by_side");
      setStatusMessage({ type: "success", text: "Uploaded replacement corrected visual!" });
    } catch (err: any) {
      console.error(err);
      setStatusMessage({ type: "error", text: "Failed to upload replacement image." });
    } finally {
      setIsGeneratingFix(false);
    }
  };

  const handleSubmitForReview = async () => {
    if (!report) return;
    try {
      setIsSubmittingReview(true);
      await api.post(`/multimodal/reports/${report.report_id}/submit-review`, {
        notes: creatorNotes.trim()
      });
      setReport({ ...report, review_status: "pending_review", creator_notes: creatorNotes.trim() });
      setStatusMessage({
        type: "success",
        text: "Visual asset and analysis submitted to the Reviewer Station!"
      });
      if (onReviewSubmitted) {
        onReviewSubmitted();
      }
    } catch (e: any) {
      console.error(e);
      setStatusMessage({ type: "error", text: e.response?.data?.detail || "Failed to submit visual for review." });
    } finally {
      setIsSubmittingReview(false);
    }
  };

  const getStatusBadge = (st?: string) => {
    switch (st?.toLowerCase()) {
      case "approved":
        return (
          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            Approved for Publication
          </span>
        );
      case "pending_review":
        return (
          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-purple-100 text-purple-800 border border-purple-300">
            <Loader2 className="w-3.5 h-3.5 animate-spin text-purple-600" />
            Pending Reviewer Approval
          </span>
        );
      case "changes_requested":
        return (
          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            Changes Requested
          </span>
        );
      case "rejected":
        return (
          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-300">
            <XCircle className="w-3.5 h-3.5 text-rose-600" />
            Rejected
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-800 border border-slate-300">
            Draft Asset
          </span>
        );
    }
  };

  return (
    <div className="bg-white rounded-3xl border border-midnight-100 shadow-card overflow-hidden space-y-0">
      {/* Header */}
      <div className="px-6 py-4 border-b border-midnight-100 flex flex-wrap items-center justify-between gap-4 bg-gradient-to-r from-indigo-50/60 via-white to-brand-50/40">
        <div>
          <div className="flex items-center gap-2">
            <Palette className="w-5 h-5 text-indigo-600" />
            <h3 className="text-base font-extrabold text-midnight-950">
              Multimodal Brand Intelligence & Visual Audit
            </h3>
            {getStatusBadge(report?.review_status)}
          </div>
          <p className="text-xs text-midnight-500 mt-0.5">
            Evaluate brand colors, WCAG 2.1 contrast, OCR typography, and generate publication-approved assets.
          </p>
        </div>

        {report?.is_published && (
          <a
            href={`${apiBase}/multimodal/reports/${report.report_id}/download-asset`}
            target="_blank"
            download
            className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs shadow-md transition-all inline-flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            <span>Download Certified Final Asset</span>
          </a>
        )}
      </div>

      {statusMessage && (
        <div className={`px-6 py-3 text-xs flex items-center gap-2 border-b ${
          statusMessage.type === "success"
            ? "bg-emerald-50 text-emerald-800 border-emerald-200"
            : statusMessage.type === "error"
            ? "bg-rose-50 text-rose-800 border-rose-200"
            : "bg-brand-50 text-brand-800 border-brand-200"
        }`}>
          {statusMessage.type === "success" ? <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /> : <Info className="w-4 h-4 shrink-0" />}
          <span className="font-medium">{statusMessage.text}</span>
        </div>
      )}

      {/* Reviewer Feedback Banner */}
      {report?.reviewer_comments && (
        <div className="mx-6 mt-4 p-4 rounded-2xl bg-amber-50 border border-amber-200 text-xs text-amber-950 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="font-bold">
              Reviewer Governance Feedback ({report.review_status ? report.review_status.replace("_", " ").toUpperCase() : "NOTES"}):
            </p>
            <p className="text-amber-900 leading-relaxed font-sans">{report.reviewer_comments}</p>
            {report.review_status === "changes_requested" && (
              <p className="text-[11px] text-amber-700 font-medium">
                Please review the optical findings, apply suggested fixes or upload a corrected graphic, then resubmit below.
              </p>
            )}
          </div>
        </div>
      )}

      <div className="p-6 space-y-6">
        {/* Sample Presets Quick-Launch Bar */}
        <div className="p-4 rounded-2xl bg-lavender-50/70 border border-midnight-100 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <span className="text-xs font-bold text-midnight-950 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-brand-600" />
                Interactive Brand Governance Test Presets (1-Click Verification)
              </span>
              <p className="text-[11px] text-midnight-600 mt-0.5">
                Load authentic multimodal test cases demonstrating real-world brand violations &amp; surgical corrections:
              </p>
            </div>
            {previewUrl && (
              <button
                onClick={() => {
                  setPreviewUrl(null);
                  setSelectedFile(null);
                  setReport(null);
                  setStatusMessage(null);
                }}
                className="text-[11px] font-semibold text-brand-600 hover:text-brand-700 hover:underline flex items-center gap-1"
              >
                <Upload className="w-3 h-3" />
                Upload Custom Asset Instead
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
            {SAMPLE_PRESETS.map((preset) => {
              const isLoading = loadingPresetId === preset.id;
              return (
                <button
                  key={preset.id}
                  onClick={() => handleLoadPreset(preset.id)}
                  disabled={Boolean(loadingPresetId)}
                  className={`p-3 rounded-xl border text-left transition-all relative flex flex-col justify-between group ${
                    report?.preset_id === preset.id
                      ? "border-brand-500 bg-white ring-1 ring-brand-500 shadow-xs"
                      : "border-midnight-100 bg-white/90 hover:bg-white hover:border-brand-300 hover:shadow-xs"
                  }`}
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between gap-1">
                      <span className="text-base">{preset.icon}</span>
                      <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-brand-50 text-brand-700 border border-brand-200">
                        {preset.badge}
                      </span>
                    </div>
                    <div>
                      <span className="font-bold text-xs text-midnight-950 block group-hover:text-brand-600 transition-colors">
                        {preset.title}
                      </span>
                      <p className="text-[10.5px] text-midnight-600 mt-0.5 line-clamp-2">
                        {preset.description}
                      </p>
                    </div>
                  </div>

                  <div className="mt-2.5 pt-2 border-t border-midnight-100/60 flex items-center justify-between text-[10px]">
                    <span className="font-semibold text-brand-600 group-hover:underline flex items-center gap-1">
                      {isLoading ? (
                        <>
                          <Loader2 className="w-3 h-3 animate-spin text-brand-600" />
                          <span>Auditing...</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-3 h-3 text-brand-600" />
                          <span>1-Click Test</span>
                        </>
                      )}
                    </span>
                    <span className="text-[9px] text-midnight-400 font-mono">
                      {preset.brand}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Upload State */}
        {!previewUrl ? (
          <div
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-midnight-200 hover:border-brand-500 rounded-2xl p-10 text-center cursor-pointer transition-all hover:bg-brand-50/20 group"
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept="image/png,image/jpeg,image/webp,image/svg+xml"
              className="hidden"
            />
            <div className="w-14 h-14 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center mx-auto mb-3 group-hover:scale-105 transition-transform">
              <Upload className="w-7 h-7" />
            </div>
            <p className="text-sm font-bold text-midnight-950">
              Upload marketing visual, social banner, or branded graphic
            </p>
            <p className="text-xs text-midnight-500 mt-1">
              Supports PNG, JPG, JPEG, WEBP up to 15MB (or test with 1-click sample presets above)
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Visual Workspace Canvas */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
              {/* Left Column: Image Canvas with Interactive Bounding Boxes */}
              <div className="lg:col-span-6 space-y-3">
                <div className="flex items-center justify-between pb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-midnight-800">Visual Asset Inspection</span>
                    {report?.has_corrected_image && (
                      <div className="flex items-center gap-1 bg-lavender-50 p-1 rounded-lg border border-midnight-100 text-[11px] font-semibold">
                        <button
                          onClick={() => setViewMode("original")}
                          className={`px-2 py-0.5 rounded ${viewMode === "original" ? "bg-white shadow-xs text-midnight-950" : "text-midnight-500"}`}
                        >
                          Original
                        </button>
                        <button
                          onClick={() => setViewMode("corrected")}
                          className={`px-2 py-0.5 rounded ${viewMode === "corrected" ? "bg-white shadow-xs text-midnight-950" : "text-midnight-500"}`}
                        >
                          Corrected
                        </button>
                        <button
                          onClick={() => setViewMode("side_by_side")}
                          className={`px-2 py-0.5 rounded ${viewMode === "side_by_side" ? "bg-white shadow-xs text-midnight-950" : "text-midnight-500"}`}
                        >
                          Side-by-Side
                        </button>
                        <div className="h-3 w-px bg-midnight-200 mx-0.5" />
                        <button
                          type="button"
                          onClick={handleUndoCorrection}
                          disabled={isGeneratingFix}
                          title="Undo applied replacement and restore original asset"
                          className="px-2 py-0.5 rounded text-rose-600 hover:bg-rose-50 inline-flex items-center gap-1 font-semibold transition-colors disabled:opacity-50"
                        >
                          <RotateCcw className="w-3 h-3" />
                          <span>Undo</span>
                        </button>
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => {
                      setSelectedFile(null);
                      setPreviewUrl(null);
                      setReport(null);
                    }}
                    className="text-xs font-semibold text-rose-600 hover:underline"
                  >
                    Change Image
                  </button>
                </div>

                {/* Main Interactive Image Frame */}
                {viewMode === "side_by_side" && report?.has_corrected_image ? (
                  <div className="grid grid-cols-2 gap-3">
                    {/* Original */}
                    <div className="space-y-1">
                      <span className="text-[10px] font-bold text-midnight-500 uppercase tracking-wider block">
                        Original Asset
                      </span>
                      <div className="relative rounded-2xl overflow-hidden border border-midnight-200 bg-midnight-950 flex items-center justify-center min-h-[220px]">
                        <img
                          src={report ? `${apiBase}/multimodal/reports/${report.report_id}/image/original` : previewUrl}
                          alt="Original"
                          className="max-h-[220px] w-auto object-contain"
                        />
                      </div>
                    </div>
                    {/* Corrected */}
                    <div className="space-y-1">
                      <div className="flex items-center justify-between">
                        <span className={`text-[10px] font-bold uppercase tracking-wider block flex items-center gap-1 ${
                          report.post_correction_verification?.passed
                            ? "text-emerald-700"
                            : report.post_correction_verification?.passed === false
                            ? "text-rose-700"
                            : "text-brand-700"
                        }`}>
                          {report.post_correction_verification?.passed ? (
                            <>
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Corrected &amp; Verified
                            </>
                          ) : report.post_correction_verification?.passed === false ? (
                            <>
                              <AlertCircle className="w-3.5 h-3.5 text-rose-600" /> Correction Audit Failed
                            </>
                          ) : (
                            <>
                              <Sparkles className="w-3.5 h-3.5 text-brand-600" /> Corrected Visual
                            </>
                          )}
                        </span>
                        {report.post_correction_verification && (
                          <span className={`text-[9px] font-extrabold px-1.5 py-0.5 rounded uppercase tracking-wider ${
                            report.post_correction_verification.passed
                              ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                              : "bg-rose-100 text-rose-800 border border-rose-300"
                          }`}>
                            {report.post_correction_verification.status}
                          </span>
                        )}
                      </div>
                      <div className={`relative rounded-2xl overflow-hidden border bg-midnight-950 flex items-center justify-center min-h-[220px] ${
                        report.post_correction_verification?.passed
                          ? "border-emerald-400"
                          : report.post_correction_verification?.passed === false
                          ? "border-rose-400"
                          : "border-brand-300"
                      }`}>
                        <img
                          src={`${apiBase}/multimodal/reports/${report.report_id}/image/corrected`}
                          alt="Corrected"
                          className="max-h-[220px] w-auto object-contain"
                        />
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="relative rounded-2xl overflow-hidden border border-midnight-200 bg-midnight-950 flex items-center justify-center min-h-[260px] max-h-[360px]">
                    <img
                      src={
                        viewMode === "corrected" && report?.has_corrected_image
                          ? `${apiBase}/multimodal/reports/${report.report_id}/image/corrected`
                          : (report ? `${apiBase}/multimodal/reports/${report.report_id}/image/original` : previewUrl)
                      }
                      alt="Visual Preview"
                      className="max-h-[360px] w-auto object-contain"
                    />

                    {/* Bounding Box Highlights for Detected Visual Issues */}
                    {report?.visual_issues?.map((iss, i) => {
                      if (!iss.region) return null;
                      const isHighlighted = activeFindingId === (iss.id || `iss-${i}`);
                      const isCrit = iss.severity === "critical";
                      return (
                        <div
                          key={iss.id || i}
                          onClick={() => setActiveFindingId(iss.id || `iss-${i}`)}
                          style={{
                            left: `${iss.region.x}%`,
                            top: `${iss.region.y}%`,
                            width: `${iss.region.width}%`,
                            height: `${iss.region.height}%`,
                          }}
                          className={`absolute border-2 rounded transition-all cursor-pointer ${
                            isHighlighted
                              ? "border-amber-400 bg-amber-400/25 ring-2 ring-amber-300 shadow-xl z-20"
                              : isCrit
                              ? "border-rose-500/90 bg-rose-500/15 hover:border-amber-400 hover:bg-amber-400/20 z-10"
                              : "border-brand-500/80 bg-brand-500/10 hover:border-amber-400 hover:bg-amber-400/20"
                          }`}
                          title={iss.title}
                        >
                          <span className="absolute -top-5 left-1 text-[9px] font-bold px-1.5 py-0.5 rounded bg-midnight-950 text-white shadow-md border border-midnight-700 whitespace-nowrap">
                            #{i + 1} {iss.category ? iss.category.replace(/_/g, " ").toUpperCase() : iss.type.replace(/_/g, " ")}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Independent Post-Correction Verification Audit Card */}
                {report?.has_corrected_image && report.post_correction_verification && (
                  <div
                    className={`p-4 rounded-2xl border text-xs space-y-2.5 transition-all shadow-xs ${
                      report.post_correction_verification.passed
                        ? "bg-emerald-50/70 border-emerald-300 text-emerald-950"
                        : "bg-rose-50/80 border-rose-300 text-rose-950"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {report.post_correction_verification.passed ? (
                          <div className="w-6 h-6 rounded-lg bg-emerald-600 text-white flex items-center justify-center shadow-xs shrink-0">
                            <Check className="w-4 h-4" />
                          </div>
                        ) : (
                          <div className="w-6 h-6 rounded-lg bg-rose-600 text-white flex items-center justify-center shadow-xs shrink-0">
                            <X className="w-4 h-4" />
                          </div>
                        )}
                        <div>
                          <p className="font-extrabold text-xs tracking-tight">
                            {report.post_correction_verification.status_headline ||
                              (report.post_correction_verification.passed
                                ? "CORRECTED & VERIFIED BY AUDIT"
                                : "POST-CORRECTION AUDIT FAILED")}
                          </p>
                          <p className="text-[10.5px] opacity-80">
                            Independent brand integrity &amp; pixel-level verification
                          </p>
                        </div>
                      </div>
                      <span
                        className={`text-[9.5px] font-black px-2 py-0.5 rounded-full uppercase tracking-wider ${
                          report.post_correction_verification.passed
                            ? "bg-emerald-200/90 text-emerald-900 border border-emerald-300"
                            : "bg-rose-200/90 text-rose-900 border border-rose-300"
                        }`}
                      >
                        {report.post_correction_verification.status}
                      </span>
                    </div>

                    <p className="text-[11.5px] leading-relaxed font-sans">
                      {report.post_correction_verification.summary}
                    </p>

                    {report.post_correction_verification.checks &&
                      report.post_correction_verification.checks.length > 0 && (
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1 border-t border-black/5">
                          {report.post_correction_verification.checks.map((chk, i) => (
                            <div
                              key={i}
                              className={`p-2 rounded-xl flex items-start gap-2 border text-[11px] ${
                                chk.passed
                                  ? "bg-white/90 border-emerald-200 text-emerald-950"
                                  : "bg-white/90 border-rose-200 text-rose-950"
                              }`}
                            >
                              {chk.passed ? (
                                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                              ) : (
                                <AlertCircle className="w-3.5 h-3.5 text-rose-600 shrink-0 mt-0.5" />
                              )}
                              <div className="space-y-0.5 leading-tight overflow-hidden">
                                <span className="font-bold block text-midnight-950 truncate">
                                  {chk.name}
                                </span>
                                <span className="text-[10px] text-midnight-700 block line-clamp-2">
                                  {chk.detail}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                  </div>
                )}

                {/* Alt-text and Run Audit Button */}
                {!report && (
                  <div className="space-y-3 pt-2">
                    <div>
                      <label className="block text-xs font-semibold text-midnight-800 mb-1">
                        Image Alt-Text (Accessibility Verification)
                      </label>
                      <input
                        type="text"
                        value={altText}
                        onChange={(e) => setAltText(e.target.value)}
                        placeholder="Describe key visual message for screen readers..."
                        className="w-full px-3.5 py-2.5 rounded-xl border border-midnight-200 text-xs text-midnight-900 focus:outline-none focus:ring-1 focus:ring-brand-600"
                      />
                    </div>

                    <button
                      onClick={runVisualAnalysis}
                      disabled={isAnalyzing}
                      className="w-full py-2.5 px-4 rounded-xl bg-midnight-950 hover:bg-midnight-900 text-white font-semibold text-xs shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      {isAnalyzing ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin text-brand-400" />
                          <span>Analyzing Color Palette & Accessibility...</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-4 h-4 text-brand-400" />
                          <span>Run Complete Visual Brand Audit</span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>

              {/* Right Column: Score Breakdown & Findings with Accept/Reject Actions */}
              <div className="lg:col-span-6 space-y-4">
                {report ? (
                  <>
                    {/* Metrics Bar */}
                    <div className="grid grid-cols-3 gap-3">
                      <div className="p-3.5 rounded-2xl bg-lavender-50/60 border border-midnight-100">
                        <span className="text-[10px] font-bold text-midnight-500 uppercase tracking-wider">
                          Visual Score
                        </span>
                        <p className="text-xl font-extrabold text-midnight-950 mt-0.5">
                          {report.visual_score}/100
                        </p>
                      </div>

                      <div className="p-3.5 rounded-2xl bg-lavender-50/60 border border-midnight-100">
                        <span className="text-[10px] font-bold text-midnight-500 uppercase tracking-wider">
                          WCAG 2.1 Contrast
                        </span>
                        <div className="flex items-center gap-1.5 mt-0.5">
                          <span className="text-lg font-extrabold text-midnight-950">
                            {report.contrast_ratio}:1
                          </span>
                          <span
                            className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                              report.wcag_compliance === "AAA_PASS" || report.wcag_compliance === "AA_PASS"
                                ? "bg-emerald-100 text-emerald-800"
                                : "bg-rose-100 text-rose-800"
                            }`}
                          >
                            {report.wcag_compliance}
                          </span>
                        </div>
                      </div>

                      <div className="p-3.5 rounded-2xl bg-lavender-50/60 border border-midnight-100">
                        <span className="text-[10px] font-bold text-midnight-500 uppercase tracking-wider">
                          Palette Match
                        </span>
                        <p className="text-xl font-extrabold text-brand-700 mt-0.5">
                          {report.palette_match_score}%
                        </p>
                      </div>
                    </div>

                    {/* Dominant Color Swatches */}
                    <div className="p-3.5 rounded-2xl border border-midnight-100 bg-white">
                      <span className="text-[10px] font-bold text-midnight-600 uppercase tracking-wider block mb-2">
                        Extracted Dominant Color Swatches
                      </span>
                      <div className="flex flex-wrap items-center gap-2">
                        {report.dominant_colors.map((c, i) => (
                          <div key={i} className="flex items-center gap-1.5 bg-lavender-50/60 px-2 py-1 rounded-lg border border-midnight-100">
                            <div
                              className="w-4 h-4 rounded shadow-xs border border-midnight-200"
                              style={{ backgroundColor: c.hex }}
                            />
                            <span className="text-[11px] font-mono font-bold text-midnight-900">{c.hex}</span>
                            <span className="text-[10px] text-midnight-500">{c.percent}%</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* OCR Text */}
                    {report.ocr_extracted_text && (
                      <div className="p-3 rounded-xl border border-midnight-100 bg-lavender-50/40 text-xs">
                        <span className="text-[10px] font-bold text-midnight-500 uppercase tracking-wider block mb-1">
                          OCR Extracted Copy
                        </span>
                        <p className="font-mono text-midnight-800 text-[11px]">
                          &ldquo;{report.ocr_extracted_text}&rdquo;
                        </p>
                      </div>
                    )}

                    {/* Detected Visual Findings with Accept/Reject Actions */}
                    <div className="space-y-3 pt-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-midnight-900">
                          Detected Visual Findings ({report.visual_issues?.length || 0})
                        </span>
                        <span className="text-[11px] text-midnight-500">
                          Click to highlight affected region
                        </span>
                      </div>

                      {report.visual_issues && report.visual_issues.length > 0 ? (
                        report.visual_issues.map((iss, idx) => {
                          const fid = iss.id || `iss-${idx}`;
                          const isAccepted = report.accepted_corrections?.includes(fid);
                          const isRejected = report.rejected_corrections?.includes(fid);
                          const isSelected = activeFindingId === fid;

                          return (
                            <div
                              key={fid}
                              onClick={() => setActiveFindingId(fid)}
                              className={`p-3.5 rounded-2xl border transition-all text-xs space-y-2 cursor-pointer ${
                                isSelected
                                  ? "border-brand-500 bg-brand-50/30 ring-1 ring-brand-500"
                                  : "border-midnight-100 bg-white hover:border-midnight-300"
                              }`}
                            >
                              <div className="flex items-start justify-between gap-2">
                                <div className="space-y-1">
                                  <div className="flex flex-wrap items-center gap-1.5">
                                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider ${
                                      iss.severity === "critical"
                                        ? "bg-rose-100 text-rose-800 border border-rose-300"
                                        : iss.severity === "high"
                                        ? "bg-amber-100 text-amber-800 border border-amber-300"
                                        : iss.severity === "medium"
                                        ? "bg-indigo-100 text-indigo-800 border border-indigo-200"
                                        : "bg-slate-100 text-slate-700 border border-slate-200"
                                    }`}>
                                      {iss.severity}
                                    </span>
                                    {iss.category && (
                                      <span className="text-[9px] font-semibold text-midnight-500 uppercase tracking-wider">
                                        • {iss.category.replace(/_/g, " ")}
                                      </span>
                                    )}
                                  </div>
                                  <div className="flex items-center gap-1.5">
                                    <AlertTriangle className={`w-4 h-4 shrink-0 ${iss.severity === "critical" ? "text-rose-600" : "text-amber-600"}`} />
                                    <span className="font-bold text-midnight-950">{iss.title}</span>
                                  </div>
                                </div>

                                <div className="flex items-center gap-1 shrink-0">
                                  {isAccepted ? (
                                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
                                      Accepted
                                    </span>
                                  ) : isRejected ? (
                                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-100 text-rose-800 border border-rose-200">
                                      Rejected
                                    </span>
                                  ) : (
                                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                                      Pending Decision
                                    </span>
                                  )}
                                </div>
                              </div>

                              {/* Detected Element vs Expected Reference Comparison */}
                              {iss.detected_element && iss.expected_reference && (
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] p-2.5 rounded-xl bg-lavender-50/70 border border-midnight-100">
                                  <div>
                                    <span className="font-bold text-rose-800 block text-[10px] uppercase tracking-wider">
                                      Detected Visual Element
                                    </span>
                                    <span className="text-midnight-900 font-mono text-[10.5px] leading-tight block mt-0.5">
                                      {iss.detected_element}
                                    </span>
                                  </div>
                                  <div>
                                    <span className="font-bold text-emerald-800 block text-[10px] uppercase tracking-wider">
                                      Expected Reference Standard
                                    </span>
                                    <span className="text-midnight-900 font-mono text-[10.5px] leading-tight block mt-0.5">
                                      {iss.expected_reference}
                                    </span>
                                  </div>
                                </div>
                              )}

                              {/* Policy Violation Explanation: What's Wrong */}
                              <div className="p-2.5 rounded-xl bg-rose-50/70 border border-rose-200/80 text-[11px] space-y-1">
                                <div className="flex items-center gap-1.5 font-bold text-rose-900">
                                  <AlertCircle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
                                  <span>Policy Violation: What&apos;s Wrong</span>
                                </div>
                                <p className="text-rose-950 leading-relaxed font-sans pl-5">
                                  {iss.explanation}
                                </p>
                              </div>

                              {/* Verification Status & Reference Source */}
                              <div className="flex flex-wrap items-center justify-between gap-2 text-[10px] pt-0.5">
                                <div>
                                  {iss.verification_status === "verified_official_reference" ? (
                                    <span className="inline-flex items-center gap-1 font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                                      <ShieldCheck className="w-3 h-3 text-emerald-600" />
                                      Verified Official Reference
                                    </span>
                                  ) : iss.verification_status === "verified_organization_asset" ? (
                                    <span className="inline-flex items-center gap-1 font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                                      <Building2 className="w-3 h-3 text-indigo-600" />
                                      Verified Org Asset
                                    </span>
                                  ) : (
                                    <span className="inline-flex items-center gap-1 font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                                      <AlertCircle className="w-3 h-3 text-amber-600" />
                                      Unverified Brand Reference
                                    </span>
                                  )}
                                </div>
                                {iss.reference_source && (
                                  <span className="text-midnight-500 font-medium truncate max-w-xs">
                                    Ref: {iss.reference_source}
                                  </span>
                                )}
                              </div>

                              <div className="p-2.5 rounded-xl bg-amber-50/70 border border-amber-200 text-amber-950 text-[11px]">
                                <strong>Recommended Fix:</strong> {iss.suggestion}
                              </div>

                              {/* Official Brand Variant Selector */}
                              {iss.available_variants && iss.available_variants.length > 0 && (
                                <div className="p-2.5 rounded-xl bg-lavender-50/80 border border-midnight-100 space-y-1.5">
                                  <div className="flex items-center justify-between">
                                    <span className="text-[10px] font-bold text-midnight-800 uppercase tracking-wider">
                                      Official Asset Variant for Replacement
                                    </span>
                                    {iss.recommended_variant && (
                                      <span className="text-[9px] text-brand-600 font-semibold">
                                        Recommended: {iss.recommended_variant.replace(/_/g, " ")}
                                      </span>
                                    )}
                                  </div>
                                  <div className="flex flex-wrap gap-1.5">
                                    {iss.available_variants.map((vKey) => {
                                      const isChosen =
                                        (selectedVariants[fid] || iss.recommended_variant || "primary") === vKey;
                                      const label =
                                        vKey === "primary"
                                          ? "Primary (Official)"
                                          : vKey === "monochrome_white"
                                          ? "Monochrome White"
                                          : vKey === "monochrome_black"
                                          ? "Monochrome Black"
                                          : vKey === "wordmark"
                                          ? "Wordmark"
                                          : vKey.replace(/_/g, " ");

                                      return (
                                        <button
                                          key={vKey}
                                          type="button"
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            setSelectedVariants((prev) => ({ ...prev, [fid]: vKey }));
                                          }}
                                          className={`px-2 py-1 rounded-lg text-[10px] font-bold border transition-all ${
                                            isChosen
                                              ? "bg-midnight-950 text-white border-midnight-950 shadow-xs ring-1 ring-midnight-950"
                                              : "bg-white text-midnight-700 border-midnight-200 hover:border-midnight-400"
                                          }`}
                                        >
                                          {label}
                                        </button>
                                      );
                                    })}
                                  </div>
                                </div>
                              )}

                              {/* Action Buttons: Accept or Reject */}
                              <div className="flex items-center justify-end gap-2 pt-1 border-t border-midnight-100/60">
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleCorrectionDecision(fid, "reject");
                                  }}
                                  className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold inline-flex items-center gap-1 border transition-all ${
                                    isRejected
                                      ? "bg-rose-600 text-white border-rose-600"
                                      : "bg-white text-rose-700 border-rose-200 hover:bg-rose-50"
                                  }`}
                                >
                                  <X className="w-3 h-3" />
                                  <span>Reject</span>
                                </button>

                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleCorrectionDecision(fid, "accept");
                                  }}
                                  className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold inline-flex items-center gap-1 border transition-all ${
                                    isAccepted
                                      ? "bg-emerald-600 text-white border-emerald-600"
                                      : "bg-white text-emerald-700 border-emerald-200 hover:bg-emerald-50"
                                  }`}
                                >
                                  <Check className="w-3 h-3" />
                                  <span>Accept Fix</span>
                                </button>
                              </div>
                            </div>
                          );
                        })
                      ) : (
                        <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs flex items-center gap-2">
                          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                          <span>No visual brand violations detected! Graphic complies with organization palette and contrast standards.</span>
                        </div>
                      )}
                    </div>

                    {/* Correction Actions Bar */}
                    <div className="p-4 rounded-2xl bg-lavender-50/60 border border-midnight-100 space-y-3 pt-3">
                      <div className="flex items-center justify-between text-xs font-bold text-midnight-950">
                        <span>Correction & Output Engine</span>
                        <input
                          type="file"
                          ref={replaceFileInputRef}
                          onChange={handleUploadReplacement}
                          accept="image/png,image/jpeg"
                          className="hidden"
                        />
                        <button
                          onClick={() => replaceFileInputRef.current?.click()}
                          className="text-[11px] text-brand-600 hover:underline font-semibold"
                        >
                          Upload Custom Corrected Visual
                        </button>
                      </div>

                      <button
                        onClick={handleGenerateCorrected}
                        disabled={isGeneratingFix}
                        className="w-full py-2.5 px-4 rounded-xl bg-midnight-950 hover:bg-midnight-900 text-white font-semibold text-xs shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                      >
                        {isGeneratingFix ? (
                          <>
                            <Loader2 className="w-3.5 h-3.5 animate-spin text-brand-400" />
                            <span>Generating Corrected Visual Asset...</span>
                          </>
                        ) : (
                          <>
                            <Sliders className="w-3.5 h-3.5 text-brand-400" />
                            <span>Apply Accepted Fixes & Generate Corrected Visual</span>
                          </>
                        )}
                      </button>

                      {report?.has_corrected_image && (
                        <button
                          type="button"
                          onClick={handleUndoCorrection}
                          disabled={isGeneratingFix}
                          className="w-full py-2 px-3 rounded-xl bg-white hover:bg-slate-50 text-midnight-700 border border-midnight-200 font-semibold text-xs transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                        >
                          <RotateCcw className="w-3.5 h-3.5 text-midnight-500" />
                          <span>Revert to Original (Undo Applied Replacement)</span>
                        </button>
                      )}

                      {/* Submit for Review Section */}
                      <div className="pt-2 border-t border-midnight-200/60 space-y-2">
                        <textarea
                          rows={2}
                          value={creatorNotes}
                          onChange={(e) => setCreatorNotes(e.target.value)}
                          placeholder="Optional notes for brand governance reviewer..."
                          className="w-full px-3 py-2 rounded-xl border border-midnight-200 text-xs text-midnight-900 placeholder:text-midnight-400 focus:outline-none focus:ring-1 focus:ring-brand-600"
                        />

                        <button
                          onClick={handleSubmitForReview}
                          disabled={isSubmittingReview}
                          className="w-full py-2.5 px-4 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                        >
                          {isSubmittingReview ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin text-white" />
                          ) : (
                            <>
                              <Send className="w-3.5 h-3.5" />
                              <span>
                                {report.review_status === "changes_requested"
                                  ? "Resubmit Visual with Revisions"
                                  : report.review_status === "approved"
                                  ? "Resubmit Visual for Re-Approval"
                                  : "Submit Visual for Reviewer Approval"}
                              </span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="py-20 text-center border-2 border-dashed border-midnight-100 rounded-3xl text-xs text-midnight-400">
                    Click &ldquo;Run Complete Visual Brand Audit&rdquo; to evaluate color swatches, optical contrast, and OCR text.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
