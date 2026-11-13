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
  Maximize2,
  RefreshCw,
} from "lucide-react";
import { VisualAnalysisReport } from "@/types";
import { api, getApiBaseUrl } from "@/lib/api";

interface VisualAuditPanelProps {
  submissionId?: string;
  onAnalysisComplete?: (report: VisualAnalysisReport) => void;
}

export function VisualAuditPanel({ submissionId, onAnalysisComplete }: VisualAuditPanelProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [altText, setAltText] = useState<string>("");
  const [report, setReport] = useState<VisualAnalysisReport | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [isGeneratingFix, setIsGeneratingFix] = useState<boolean>(false);
  const [isSubmittingReview, setIsSubmittingReview] = useState<boolean>(false);
  const [activeFindingId, setActiveFindingId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"side_by_side" | "original" | "corrected">("side_by_side");
  const [creatorNotes, setCreatorNotes] = useState<string>("");
  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error" | "info"; text: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const replaceFileInputRef = useRef<HTMLInputElement>(null);

  const apiBase = getApiBaseUrl();

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
      await api.post(`/multimodal/reports/${report.report_id}/generate-corrected`, {});
      // Refresh report
      const repRes = await api.get(`/multimodal/reports/${report.report_id}`);
      setReport(repRes.data);
      setViewMode("side_by_side");
      setStatusMessage({
        type: "success",
        text: "Applied accepted corrections and generated publication-ready visual!"
      });
    } catch (e: any) {
      console.error(e);
      setStatusMessage({ type: "error", text: e.response?.data?.detail || "Failed to generate corrected visual." });
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

      <div className="p-6 space-y-6">
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
              Supports PNG, JPG, JPEG, WEBP up to 15MB
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
                      <span className="text-[10px] font-bold text-emerald-700 uppercase tracking-wider block flex items-center gap-1">
                        <Check className="w-3 h-3" /> Corrected & Verified
                      </span>
                      <div className="relative rounded-2xl overflow-hidden border border-emerald-300 bg-midnight-950 flex items-center justify-center min-h-[220px]">
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
                              ? "border-amber-400 bg-amber-400/20 ring-2 ring-amber-300 shadow-lg"
                              : "border-rose-400/80 bg-rose-400/10 hover:border-amber-400 hover:bg-amber-400/20"
                          }`}
                          title={iss.title}
                        >
                          <span className="absolute -top-5 left-1 text-[9px] font-bold px-1.5 py-0.5 rounded bg-midnight-900/90 text-white shadow-sm border border-midnight-700">
                            #{i + 1} {iss.type.replace(/_/g, " ")}
                          </span>
                        </div>
                      );
                    })}
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
                                <div className="flex items-center gap-1.5">
                                  <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                                  <span className="font-bold text-midnight-950">{iss.title}</span>
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

                              <p className="text-midnight-700 text-[11px] leading-relaxed">
                                {iss.explanation}
                              </p>

                              <div className="p-2.5 rounded-xl bg-amber-50/70 border border-amber-200 text-amber-950 text-[11px]">
                                <strong>Recommended Fix:</strong> {iss.suggestion}
                              </div>

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
                              <span>Submit Visual for Reviewer Approval</span>
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
