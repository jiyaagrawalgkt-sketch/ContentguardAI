"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { AppNavbar } from "@/components/layout/AppNavbar";
import {
  getScoreBadge,
  getSeverityStyle,
  getCategoryMeta,
  getActionMeta,
  maskSensitivePreview
} from "@/lib/utils";
import {
  ArrowLeft,
  Sparkles,
  RefreshCw,
  Send,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  FileCheck2,
  Check,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  ShieldAlert,
  Loader2,
  Info,
  X,
  Filter,
  Trash2,
  Cpu,
  Palette,
  Layers,
  BookOpen,
  Lock,
  GitCompare,
  FileCheck,
} from "lucide-react";
import { DetectedIssue, ContentSubmission, AnalysisReport } from "@/types";
import { EvidenceGraph } from "@/components/evidence/EvidenceGraph";
import { VisualAuditPanel } from "@/components/multimodal/VisualAuditPanel";
import { BrandRiskRadar } from "@/components/features/BrandRiskRadar";
import { ClaimProvenanceExplorer } from "@/components/features/ClaimProvenanceExplorer";
import { PrePublicationGate } from "@/components/features/PrePublicationGate";
import { VersionIntelligence } from "@/components/features/VersionIntelligence";

interface ExtendedReport extends Omit<AnalysisReport, "issues"> {
  issues: DetectedIssue[];
}

export default function CorrectionWorkspacePage() {
  const { id } = useParams<{ id: string }>();
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();

  const [submission, setSubmission] = useState<ContentSubmission | null>(null);
  const [editorContent, setEditorContent] = useState("");
  const [report, setReport] = useState<ExtendedReport | null>(null);
  const [workspaceTab, setWorkspaceTab] = useState<"text" | "evidence" | "provenance" | "radar" | "gate" | "versions" | "multimodal">("text");
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [submittingReview, setSubmittingReview] = useState(false);
  const [appliedIssues, setAppliedIssues] = useState<Set<string>>(new Set());
  const [notification, setNotification] = useState<{ type: "success" | "info" | "error"; message: string } | null>(null);

  // Filter states
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [hideDismissed, setHideDismissed] = useState<boolean>(false);

  // Card expansion & dismiss state
  const [expandedIssueId, setExpandedIssueId] = useState<string | null>(null);
  const [dismissingIssueId, setDismissingIssueId] = useState<string | null>(null);
  const [dismissReason, setDismissReason] = useState<string>("");
  const [isDismissing, setIsDismissing] = useState<boolean>(false);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
      return;
    }
    if (id) {
      loadSubmission();
    }
  }, [id, isAuthenticated, authLoading, user?.id, router]);

  const loadSubmission = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/submissions/${id}`);
      setSubmission(res.data);
      setEditorContent(res.data.current_content || "");
      if (res.data.latest_report) {
        setReport(res.data.latest_report);
      } else {
        runAutoAnalysis();
      }
    } catch (err: any) {
      setNotification({
        type: "error",
        message: err.response?.data?.detail || "Failed to load submission details."
      });
    } finally {
      setLoading(false);
    }
  };

  const runAutoAnalysis = async () => {
    try {
      setAnalyzing(true);
      const res = await api.post(`/analysis/analyze/${id}`);
      setReport(res.data);
    } catch (e: any) {
      console.error(e);
      setNotification({
        type: "error",
        message: e.response?.data?.detail || "Initial automated analysis failed. Please click 'Re-Analyze Content' to retry."
      });
    } finally {
      setAnalyzing(false);
    }
  };

  const handleManualAnalyze = async () => {
    try {
      setAnalyzing(true);
      setNotification(null);
      if (editorContent !== submission?.current_content) {
        await api.put(`/submissions/${id}/content`, {
          content: editorContent,
          change_summary: "Updated copy before re-analysis"
        });
      }
      const res = await api.post(`/analysis/analyze/${id}`);
      setReport(res.data);
      setAppliedIssues(new Set());
      setNotification({
        type: "success",
        message: `Analysis complete! Detected ${res.data.total_issues} issues. Compliance Score: ${res.data.compliance_score.toFixed(0)}/100.`
      });
      const subRes = await api.get(`/submissions/${id}`);
      setSubmission(subRes.data);
    } catch (err: any) {
      setNotification({
        type: "error",
        message: err.response?.data?.detail || "Analysis failed."
      });
    } finally {
      setAnalyzing(false);
    }
  };

  const handleApplyFix = async (issue: DetectedIssue) => {
    const original = issue.matched_text;
    const replacement = issue.suggested_replacement ?? "";
    const isRemove = (issue.recommended_action || "").toLowerCase() === "remove" && !issue.suggested_replacement;

    if (!editorContent.includes(original)) {
      setNotification({
        type: "error",
        message: `Phrase "${original.slice(0, 35)}..." was not found in the editor (it may have already been changed).`
      });
      return;
    }

    const updatedText = isRemove
      ? editorContent.replace(original, "").replace(/\s{2,}/g, " ")
      : editorContent.replace(original, replacement);

    setEditorContent(updatedText);

    try {
      setSaving(true);
      // 1. Save new version to backend
      const saveRes = await api.put(`/submissions/${id}/content`, {
        content: updatedText,
        change_summary: isRemove
          ? `Removed risk phrase: '${original.slice(0, 30)}...'`
          : `Applied fix: replaced '${original.slice(0, 30)}...' with '${replacement.slice(0, 30)}...'`
      });
      setSubmission(saveRes.data);
      setAppliedIssues((prev) => new Set(prev).add(issue.id));

      // 2. Immediately trigger re-analysis so the score recalculates and resolved issue is cleared
      setAnalyzing(true);
      const analysisRes = await api.post(`/analysis/analyze/${id}`);
      setReport(analysisRes.data);
      setNotification({
        type: "success",
        message: `Applied fix and re-analyzed! Updated Compliance Score: ${analysisRes.data.compliance_score.toFixed(0)}/100.`
      });
    } catch (err: any) {
      setNotification({
        type: "error",
        message: err.response?.data?.detail || "Failed to save revision and re-analyze."
      });
    } finally {
      setSaving(false);
      setAnalyzing(false);
    }
  };

  const handleDismissIssue = async (issueId: string) => {
    if (!dismissReason.trim()) {
      setNotification({
        type: "error",
        message: "Please provide a reason to dismiss this finding."
      });
      return;
    }

    try {
      setIsDismissing(true);
      await api.post(`/analysis/issues/${issueId}/dismiss`, {
        reason: dismissReason.trim()
      });

      // Update local report state
      if (report) {
        const updatedIssues = report.issues.map((iss) =>
          iss.id === issueId
            ? { ...iss, is_dismissed: true, dismiss_reason: dismissReason.trim() }
            : iss
        );
        setReport({ ...report, issues: updatedIssues });
      }

      setDismissingIssueId(null);
      setDismissReason("");
      setNotification({
        type: "info",
        message: "Finding marked as dismissed with compliance rationale note."
      });
    } catch (err: any) {
      setNotification({
        type: "error",
        message: err.response?.data?.detail || "Failed to dismiss issue."
      });
    } finally {
      setIsDismissing(false);
    }
  };

  const handleSubmitForReview = async () => {
    try {
      setSubmittingReview(true);
      setNotification(null);
      const res = await api.post(`/submissions/${id}/submit-review`);
      setSubmission(res.data);
      setNotification({
        type: "success",
        message: "Submission pushed to Reviewer queue! Brand reviewers can now inspect and approve."
      });
    } catch (err: any) {
      setNotification({
        type: "error",
        message: err.response?.data?.detail || "Failed to submit for review."
      });
    } finally {
      setSubmittingReview(false);
    }
  };

  // Category counts and filtering
  const allIssues = report?.issues || [];
  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = {
      all: allIssues.length,
      confidentiality: 0,
      privacy: 0,
      misleading_claim: 0,
      unnecessary_content: 0,
      brand_voice: 0,
      security_technical: 0
    };
    allIssues.forEach((iss) => {
      const cat = (iss.category || "brand_voice").toLowerCase();
      if (counts[cat] !== undefined) {
        counts[cat]++;
      }
    });
    return counts;
  }, [allIssues]);

  const filteredIssues = useMemo(() => {
    return allIssues.filter((iss) => {
      if (categoryFilter !== "all") {
        const cat = (iss.category || "brand_voice").toLowerCase();
        if (cat !== categoryFilter) return false;
      }
      if (severityFilter !== "all") {
        if (iss.severity.toLowerCase() !== severityFilter.toLowerCase()) return false;
      }
      if (hideDismissed && iss.is_dismissed) {
        return false;
      }
      return true;
    });
  }, [allIssues, categoryFilter, severityFilter, hideDismissed]);

  if (loading) {
    return (
      <div className="min-h-screen bg-lavender-50 flex flex-col">
        <AppNavbar />
        <div className="flex-1 flex items-center justify-center text-midnight-500">
          <Loader2 className="w-8 h-8 animate-spin text-brand-500 mb-2" />
        </div>
      </div>
    );
  }

  const score = report?.compliance_score ?? 0;
  const scoreBadge = getScoreBadge(score);

  const categories = [
    { key: "all", label: "All Violations", count: categoryCounts.all },
    { key: "confidentiality", label: "Confidentiality", count: categoryCounts.confidentiality },
    { key: "privacy", label: "Privacy & PII", count: categoryCounts.privacy },
    { key: "misleading_claim", label: "Unsupported Claims", count: categoryCounts.misleading_claim },
    { key: "unnecessary_content", label: "Excessive / Redundant", count: categoryCounts.unnecessary_content },
    { key: "brand_voice", label: "Brand Voice", count: categoryCounts.brand_voice },
    { key: "security_technical", label: "Security & Creds", count: categoryCounts.security_technical }
  ];

  return (
    <div className="min-h-screen bg-lavender-50 flex flex-col">
      <AppNavbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Top Header Bar */}
        <div className="mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <Link
              href="/creator"
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-midnight-500 hover:text-midnight-900 transition-colors mb-2"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Submissions</span>
            </Link>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-xl sm:text-2xl font-extrabold text-midnight-950">
                {submission?.title}
              </h1>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider bg-white border border-midnight-200 text-midnight-600">
                {submission?.category.replace("_", " ")}
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-brand-50 text-brand-700 border border-brand-200 font-mono">
                v{submission?.versions?.length || 1}
              </span>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider ${
                submission?.status === "approved"
                  ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                  : submission?.status === "published"
                  ? "bg-purple-50 text-purple-700 border border-purple-200"
                  : submission?.status === "pending_review"
                  ? "bg-amber-50 text-amber-700 border border-amber-200"
                  : "bg-slate-100 text-slate-700 border border-slate-200"
              }`}>
                {submission?.status.replace("_", " ")}
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2.5">
            <button
              onClick={handleManualAnalyze}
              disabled={analyzing}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold text-midnight-800 bg-white hover:bg-lavender-100 border border-midnight-200 shadow-subtle transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-brand-600 ${analyzing ? "animate-spin" : ""}`} />
              <span>{analyzing ? "Analyzing Draft..." : "Re-Analyze Content"}</span>
            </button>

            <button
              onClick={handleSubmitForReview}
              disabled={submittingReview || submission?.status === "pending_review" || submission?.status === "approved"}
              className="inline-flex items-center gap-2 px-5 py-2 rounded-xl text-xs font-semibold text-white bg-midnight-900 hover:bg-midnight-800 shadow-card hover:shadow-elevated transition-all disabled:opacity-50"
            >
              {submittingReview ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Send className="w-3.5 h-3.5 text-brand-400" />
              )}
              <span>
                {submission?.status === "pending_review"
                  ? "Awaiting Review"
                  : submission?.status === "approved"
                  ? "Approved"
                  : "Submit for Review"}
              </span>
            </button>
          </div>
        </div>

        {/* Notifications */}
        {notification && (
          <div className={`mb-6 p-4 rounded-2xl border flex items-center justify-between gap-3 text-xs ${
            notification.type === "success"
              ? "bg-emerald-50 border-emerald-200 text-emerald-800"
              : notification.type === "info"
              ? "bg-blue-50 border-blue-200 text-blue-800"
              : "bg-rose-50 border-rose-200 text-rose-800"
          }`}>
            <div className="flex items-center gap-2.5">
              {notification.type === "success" ? (
                <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
              ) : (
                <Info className="w-4 h-4 shrink-0" />
              )}
              <span className="font-medium">{notification.message}</span>
            </div>
            <button
              onClick={() => setNotification(null)}
              className="p-1 hover:bg-black/5 rounded-lg transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Reviewer Feedback & Changes Requested Banner */}
        {submission?.status === "changes_requested" && (
          <div className="mb-6 p-4 rounded-2xl bg-gradient-to-r from-orange-50 via-white to-amber-50 border-2 border-orange-300 shadow-sm flex items-start gap-3 text-xs">
            <div className="w-8 h-8 rounded-xl bg-orange-100 text-orange-700 flex items-center justify-center shrink-0 mt-0.5">
              <AlertTriangle className="w-4 h-4" />
            </div>
            <div className="flex-1 space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-bold text-orange-950 uppercase tracking-wide">
                  Reviewer Feedback — Changes Requested
                </span>
                {submission.latest_reviewer_name && (
                  <span className="text-[11px] text-orange-700 font-semibold">
                    • Reviewed by {submission.latest_reviewer_name}
                  </span>
                )}
              </div>
              <p className="text-orange-900 bg-white/80 p-2.5 rounded-xl border border-orange-200/80 font-mono text-[11px] leading-relaxed">
                "{submission.latest_review_feedback || "Please revise flagged compliance issues and update the copy before requesting approval."}"
              </p>
              <p className="text-[11px] text-orange-700 pt-0.5">
                Apply the fixes below or edit the editor text directly. When done, click <strong>"Submit for Review"</strong> to return this draft to the reviewer station.
              </p>
            </div>
          </div>
        )}

        {/* Workspace Feature Mode Selector (Round 3) */}
        <div className="mb-6 flex flex-wrap items-center gap-1.5 p-1 rounded-2xl bg-white border border-midnight-200/80 shadow-sm">
          <button
            onClick={() => setWorkspaceTab("text")}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
              workspaceTab === "text"
                ? "bg-midnight-950 text-white shadow-sm"
                : "text-midnight-600 hover:text-midnight-950 hover:bg-lavender-50"
            }`}
          >
            <FileCheck2 className="w-3.5 h-3.5" />
            <span>Editor & Violations</span>
          </button>

          <button
            onClick={() => setWorkspaceTab("evidence")}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
              workspaceTab === "evidence"
                ? "bg-brand-600 text-white shadow-sm"
                : "text-midnight-600 hover:text-midnight-950 hover:bg-lavender-50"
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Evidence Graph</span>
          </button>

          <button
            onClick={() => setWorkspaceTab("provenance")}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
              workspaceTab === "provenance"
                ? "bg-brand-600 text-white shadow-sm"
                : "text-midnight-600 hover:text-midnight-950 hover:bg-lavender-50"
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Claim Provenance</span>
          </button>

          <button
            onClick={() => setWorkspaceTab("radar")}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
              workspaceTab === "radar"
                ? "bg-brand-600 text-white shadow-sm"
                : "text-midnight-600 hover:text-midnight-950 hover:bg-lavender-50"
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>Brand Risk Radar</span>
          </button>

          <button
            onClick={() => setWorkspaceTab("gate")}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
              workspaceTab === "gate"
                ? "bg-brand-600 text-white shadow-sm"
                : "text-midnight-600 hover:text-midnight-950 hover:bg-lavender-50"
            }`}
          >
            <Lock className="w-3.5 h-3.5" />
            <span>Publication Gate</span>
          </button>

          <button
            onClick={() => setWorkspaceTab("versions")}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
              workspaceTab === "versions"
                ? "bg-brand-600 text-white shadow-sm"
                : "text-midnight-600 hover:text-midnight-950 hover:bg-lavender-50"
            }`}
          >
            <GitCompare className="w-3.5 h-3.5" />
            <span>Version Intelligence</span>
          </button>

          <button
            onClick={() => setWorkspaceTab("multimodal")}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
              workspaceTab === "multimodal"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-midnight-600 hover:text-midnight-950 hover:bg-lavender-50"
            }`}
          >
            <Palette className="w-3.5 h-3.5" />
            <span>Visual Intelligence</span>
          </button>
        </div>

        {workspaceTab === "evidence" && (
          <div className="mb-8">
            <EvidenceGraph submissionId={id} submissionTitle={submission?.title} />
          </div>
        )}

        {workspaceTab === "provenance" && (
          <div className="mb-8">
            <ClaimProvenanceExplorer submissionId={id} />
          </div>
        )}

        {workspaceTab === "radar" && (
          <div className="mb-8">
            <BrandRiskRadar report={report} submissionTitle={submission?.title} />
          </div>
        )}

        {workspaceTab === "gate" && (
          <div className="mb-8">
            <PrePublicationGate submissionId={id} submissionStatus={submission?.status} onRefresh={loadSubmission} />
          </div>
        )}

        {workspaceTab === "versions" && submission && (
          <div className="mb-8">
            <VersionIntelligence submission={submission} />
          </div>
        )}

        {workspaceTab === "multimodal" && (
          <div className="mb-8">
            <VisualAuditPanel submissionId={id} onReviewSubmitted={loadSubmission} />
          </div>
        )}

        {/* Side-by-Side Correction Workspace */}
        {workspaceTab === "text" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Pane: Content Editor (6 Cols) */}
          <div className="lg:col-span-6 bg-white rounded-3xl border border-midnight-100 shadow-card p-6 flex flex-col">
            <div className="flex flex-wrap items-center justify-between pb-3 mb-3 border-b border-midnight-100 gap-2">
              <div className="flex items-center gap-2">
                <FileCheck2 className="w-4 h-4 text-brand-600" />
                <h3 className="text-sm font-bold text-midnight-950">
                  Content Draft Workspace
                </h3>
              </div>
              <div className="flex items-center gap-2 text-[11px] text-midnight-500 font-mono">
                <span>{editorContent.length} chars</span>
                <span>•</span>
                <span>{editorContent.trim() ? editorContent.trim().split(/\s+/).length : 0} words</span>
                <span>•</span>
                <span>~{Math.max(1, Math.ceil((editorContent.trim().split(/\s+/).length || 1) / 200))} min read</span>
              </div>
            </div>

            {/* Outdated Analysis Warning if Copy was Modified */}
            {editorContent !== submission?.current_content && (
              <div className="mb-3 p-2.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-center justify-between">
                <span className="flex items-center gap-1.5 font-medium">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                  Copy modified in editor — analysis scores below reflect prior version.
                </span>
                <button
                  type="button"
                  onClick={handleManualAnalyze}
                  disabled={analyzing}
                  className="font-bold underline text-amber-900 hover:text-black ml-2 text-[11px]"
                >
                  Re-Analyze
                </button>
              </div>
            )}

            <textarea
              rows={18}
              value={editorContent}
              onChange={(e) => setEditorContent(e.target.value)}
              placeholder="Paste or write your content copy here..."
              className="w-full flex-1 rounded-2xl border border-midnight-100 p-4 text-sm text-midnight-900 font-mono leading-relaxed focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 resize-y"
            />

            <div className="mt-4 pt-4 border-t border-midnight-100 flex items-center justify-between">
              <p className="text-[11px] text-midnight-400">
                1-click fixes update this editor automatically. Save and run analysis anytime.
              </p>
              <button
                onClick={handleManualAnalyze}
                disabled={analyzing || saving}
                className="text-xs font-semibold text-brand-600 hover:text-brand-800 transition-colors"
              >
                Save & Run Analysis →
              </button>
            </div>
          </div>

          {/* Right Pane: AI Report & Correction Cards (6 Cols) */}
          <div className="lg:col-span-6 space-y-4">
            {/* Score Card: 4-Dimensional Metrics */}
            <div className="bg-white rounded-3xl border border-midnight-100 shadow-card p-6">
              <div className="flex items-center justify-between pb-3 mb-3 border-b border-midnight-100">
                <p className="text-xs font-bold text-midnight-500 uppercase tracking-wider">
                  Governance & Compliance Radar
                </p>
                <span className="text-[10px] font-mono font-semibold px-2.5 py-1 rounded bg-lavender-100 text-midnight-700 flex items-center gap-1.5">
                  <Cpu className="w-3 h-3 text-brand-600" />
                  Engine: {analyzing
                    ? "Running Governance Scan..."
                    : report?.engine_mode === "hybrid_gemini"
                    ? "Hybrid (Gemini + Rules)"
                    : report?.engine_mode === "deterministic_fallback"
                    ? "Deterministic Rules"
                    : "Awaiting Analysis"}
                </span>
              </div>

              {/* Top Score & Publication Risk */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-extrabold text-midnight-950 font-mono">
                    {analyzing || !report ? "--" : score.toFixed(0)}
                  </span>
                  <span className="text-sm text-midnight-400 font-semibold font-mono">/ 100</span>
                </div>

                <div className="flex items-center gap-2">
                  {report?.publication_risk && (
                    <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                      report.publication_risk === "low"
                        ? "bg-emerald-100 text-emerald-800 border-emerald-200"
                        : report.publication_risk === "medium"
                        ? "bg-amber-100 text-amber-800 border-amber-200"
                        : "bg-rose-100 text-rose-800 border-rose-200"
                    }`}>
                      {report.publication_risk} RISK
                    </span>
                  )}
                  {analyzing ? (
                    <div className="px-3 py-1 rounded-full text-xs font-bold border bg-blue-50 text-blue-700 border-blue-200 flex items-center gap-1.5">
                      <Loader2 className="w-3 h-3 animate-spin" />
                      <span>Analyzing...</span>
                    </div>
                  ) : !report ? (
                    <div className="px-3 py-1 rounded-full text-xs font-bold border bg-slate-100 text-slate-700 border-slate-200">
                      Awaiting Analysis
                    </div>
                  ) : (
                    <div className={`px-3 py-1 rounded-full text-xs font-bold border ${scoreBadge.bgColor} ${scoreBadge.textColor} ${scoreBadge.borderColor}`}>
                      {scoreBadge.label}
                    </div>
                  )}
                </div>
              </div>

              {/* 3 Separated Pillar Scores (Part 2.2) */}
              <div className="grid grid-cols-3 gap-2.5 mb-4 text-xs">
                <div className="p-3 rounded-2xl bg-lavender-50/70 border border-midnight-100">
                  <span className="text-[10px] text-midnight-500 font-semibold block">Brand Voice</span>
                  <span className="text-base font-extrabold text-midnight-950 font-mono">
                    {report?.brand_compliance_score !== undefined ? `${report.brand_compliance_score.toFixed(0)}%` : "100%"}
                  </span>
                </div>
                <div className="p-3 rounded-2xl bg-lavender-50/70 border border-midnight-100">
                  <span className="text-[10px] text-midnight-500 font-semibold block">Evidence Confidence</span>
                  <span className="text-base font-extrabold text-midnight-950 font-mono">
                    {report?.evidence_confidence_score !== undefined ? `${report.evidence_confidence_score.toFixed(0)}%` : "100%"}
                  </span>
                </div>
                <div className="p-3 rounded-2xl bg-lavender-50/70 border border-midnight-100">
                  <span className="text-[10px] text-midnight-500 font-semibold block">Content Quality</span>
                  <span className="text-base font-extrabold text-midnight-950 font-mono">
                    {report?.content_quality_score !== undefined ? `${report.content_quality_score.toFixed(0)}%` : "95%"}
                  </span>
                </div>
              </div>

              {/* Severity Breakdown Bar */}
              <div className="grid grid-cols-4 gap-2 text-center text-xs">
                <div className="p-2 rounded-xl bg-rose-50 border border-rose-100">
                  <span className="block text-sm font-extrabold text-rose-700 font-mono">{report?.critical_count || 0}</span>
                  <span className="text-[10px] font-semibold text-rose-600 uppercase">Critical</span>
                </div>
                <div className="p-2 rounded-xl bg-orange-50 border border-orange-100">
                  <span className="block text-sm font-extrabold text-orange-700 font-mono">{report?.high_count || 0}</span>
                  <span className="text-[10px] font-semibold text-orange-600 uppercase">High</span>
                </div>
                <div className="p-2 rounded-xl bg-amber-50 border border-amber-100">
                  <span className="block text-sm font-extrabold text-amber-700 font-mono">{report?.medium_count || 0}</span>
                  <span className="text-[10px] font-semibold text-amber-600 uppercase">Medium</span>
                </div>
                <div className="p-2 rounded-xl bg-blue-50 border border-blue-100">
                  <span className="block text-sm font-extrabold text-blue-700 font-mono">{report?.low_count || 0}</span>
                  <span className="text-[10px] font-semibold text-blue-600 uppercase">Low</span>
                </div>
              </div>

              {report?.summary_verdict && (
                <p className="mt-4 text-xs text-midnight-600 leading-relaxed bg-lavender-50/60 p-3 rounded-xl border border-midnight-100/60">
                  {report.summary_verdict}
                </p>
              )}
            </div>

            {/* Findings Filter Bar & List */}
            <div className="bg-white rounded-3xl border border-midnight-100 shadow-card p-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 mb-3 border-b border-midnight-100 gap-2">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-brand-600" />
                  <h4 className="text-xs font-bold text-midnight-950 uppercase tracking-wider">
                    Detected Violations ({filteredIssues.length} of {allIssues.length})
                  </h4>
                </div>
                <div className="flex items-center gap-3">
                  <label className="inline-flex items-center gap-1.5 text-[11px] text-midnight-500 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={hideDismissed}
                      onChange={(e) => setHideDismissed(e.target.checked)}
                      className="rounded border-midnight-300 text-brand-600 focus:ring-brand-500 h-3.5 w-3.5"
                    />
                    <span>Hide Dismissed</span>
                  </label>
                  <span className="text-[11px] text-emerald-600 font-medium">
                    {appliedIssues.size} applied
                  </span>
                </div>
              </div>

              {/* Category Filter Pills */}
              <div className="flex items-center gap-1.5 overflow-x-auto pb-2 mb-3 scrollbar-none text-xs">
                {categories.map((cat) => {
                  if (cat.key !== "all" && cat.count === 0) return null;
                  const isActive = categoryFilter === cat.key;
                  return (
                    <button
                      key={cat.key}
                      onClick={() => setCategoryFilter(cat.key)}
                      className={`shrink-0 px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all flex items-center gap-1.5 ${
                        isActive
                          ? "bg-midnight-900 text-white shadow-sm"
                          : "bg-lavender-50 hover:bg-lavender-100 text-midnight-700 border border-midnight-100"
                      }`}
                    >
                      <span>{cat.label}</span>
                      <span className={`px-1.5 py-0.2 rounded-full text-[10px] ${
                        isActive ? "bg-white/20 text-white" : "bg-white text-midnight-500"
                      }`}>
                        {cat.count}
                      </span>
                    </button>
                  );
                })}
              </div>

              {/* Severity Filter Pills */}
              <div className="flex items-center gap-1.5 pb-2 mb-4 text-[11px]">
                <span className="text-midnight-400 font-medium mr-1 flex items-center gap-1">
                  <Filter className="w-3 h-3" /> Severity:
                </span>
                {["all", "critical", "high", "medium", "low"].map((sev) => {
                  const isActive = severityFilter === sev;
                  return (
                    <button
                      key={sev}
                      onClick={() => setSeverityFilter(sev)}
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold capitalize transition-all ${
                        isActive
                          ? "bg-brand-600 text-white"
                          : "bg-lavender-50 hover:bg-lavender-100 text-midnight-600 border border-midnight-100"
                      }`}
                    >
                      {sev}
                    </button>
                  );
                })}
              </div>

              {/* Issues List */}
              {filteredIssues.length === 0 ? (
                <div className="text-center py-8">
                  <div className="w-10 h-10 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto mb-2">
                    <Check className="w-5 h-5" />
                  </div>
                  <p className="text-xs font-bold text-midnight-900">No violations matching filter!</p>
                  <p className="text-[11px] text-midnight-500 mt-0.5">
                    {allIssues.length === 0
                      ? "Your content fully satisfies compliance guidelines."
                      : "Try switching category or severity filters to view other findings."}
                  </p>
                </div>
              ) : (
                <div className="space-y-3 max-h-[560px] overflow-y-auto pr-1">
                  {filteredIssues.map((issue) => {
                    const isApplied = appliedIssues.has(issue.id) || !editorContent.includes(issue.matched_text);
                    const isDismissed = Boolean(issue.is_dismissed);
                    const isExpanded = expandedIssueId === issue.id;
                    const sevStyle = getSeverityStyle(issue.severity);
                    const catMeta = getCategoryMeta(issue.category);
                    const actMeta = getActionMeta(issue.recommended_action);
                    const isAiSource = (issue.detection_source || "").toLowerCase().includes("ai");
                    const maskedMatchedText = maskSensitivePreview(issue.matched_text, issue.category);

                    return (
                      <div
                        key={issue.id}
                        className={`p-4 rounded-2xl border transition-all ${
                          isDismissed
                            ? "bg-slate-50 border-slate-200 opacity-60"
                            : isApplied
                            ? "bg-emerald-50/40 border-emerald-200 opacity-70"
                            : "bg-white border-midnight-100 shadow-subtle hover:border-brand-300"
                        }`}
                      >
                        {/* Header: Badges & Source */}
                        <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                          <div className="flex flex-wrap items-center gap-1.5">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${sevStyle.badge}`}>
                              {issue.severity}
                            </span>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${catMeta.badge}`}>
                              {catMeta.label}
                            </span>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${actMeta.badge}`}>
                              Action: {actMeta.label}
                            </span>
                          </div>

                          <div className="flex items-center gap-1.5 text-[10px] text-midnight-500">
                            <span className="font-mono bg-lavender-100 px-1.5 py-0.5 rounded text-midnight-700 flex items-center gap-1">
                              {isAiSource ? (
                                <>
                                  <Sparkles className="w-2.5 h-2.5 text-brand-600" />
                                  <span>AI Contextual</span>
                                </>
                              ) : (
                                <>
                                  <ShieldCheck className="w-2.5 h-2.5 text-emerald-600" />
                                  <span>Rule Engine</span>
                                </>
                              )}
                            </span>
                          </div>
                        </div>

                        {/* Title */}
                        <div className="text-xs font-bold text-midnight-900 mb-1.5">
                          {issue.issue_type}
                        </div>

                        {/* Matched text quote */}
                        <div className="my-1.5 text-xs font-mono bg-rose-50/60 p-2.5 rounded-xl text-rose-950 border border-rose-100">
                          &ldquo;{maskedMatchedText}&rdquo;
                        </div>

                        {/* Explanation */}
                        <p className="text-xs text-midnight-700 leading-relaxed my-1.5">
                          {issue.explanation}
                        </p>

                        <div className="flex items-center justify-between text-[10px] text-midnight-400 mt-1 mb-2">
                          <span>
                            Guideline: <strong className="text-midnight-600">{issue.guideline_reference}</strong>
                          </span>
                          <button
                            type="button"
                            onClick={() => setExpandedIssueId(isExpanded ? null : issue.id)}
                            className="text-brand-600 hover:text-brand-800 font-medium inline-flex items-center gap-0.5"
                          >
                            <span>{isExpanded ? "Less Details" : "More Details"}</span>
                            {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                          </button>
                        </div>

                        {/* Expandable Details Area */}
                        {isExpanded && (
                          <div className="mt-2 pt-2 border-t border-midnight-100 text-[11px] text-midnight-600 space-y-1 bg-lavender-50/50 p-2.5 rounded-xl">
                            <div>
                              <span className="font-semibold text-midnight-800">Confidence Score: </span>
                              <span>{((issue.confidence || 1) * 100).toFixed(0)}%</span>
                            </div>
                            {issue.rationale && (
                              <div>
                                <span className="font-semibold text-midnight-800">Compliance Rationale: </span>
                                <span>{issue.rationale}</span>
                              </div>
                            )}
                            <div>
                              <span className="font-semibold text-midnight-800">Detection Layer: </span>
                              <span>{issue.detection_source || "Deterministic Regex & Pattern Heuristics"}</span>
                            </div>
                          </div>
                        )}

                        {/* Dismissed indicator or inline dismiss bar */}
                        {isDismissed ? (
                          <div className="mt-2.5 pt-2 border-t border-slate-200 flex items-center justify-between text-[11px] text-slate-500">
                            <span className="font-medium">
                              ✓ Dismissed: &ldquo;{issue.dismiss_reason || "Approved exception"}&rdquo;
                            </span>
                            <span className="px-2 py-0.5 rounded bg-slate-200 text-slate-700 text-[10px] font-bold">
                              DISMISSED
                            </span>
                          </div>
                        ) : dismissingIssueId === issue.id ? (
                          <div className="mt-3 p-3 rounded-xl bg-lavender-50 border border-brand-200 space-y-2">
                            <p className="text-[11px] font-bold text-midnight-900">
                              Dismiss Finding Reason:
                            </p>
                            <div className="flex flex-wrap gap-1.5">
                              {["Approved by Legal", "Client authorized", "Internal mock data", "Public entity"].map((pre) => (
                                <button
                                  key={pre}
                                  type="button"
                                  onClick={() => setDismissReason(pre)}
                                  className="px-2 py-0.5 rounded text-[10px] bg-white border border-midnight-200 text-midnight-700 hover:bg-brand-50 hover:border-brand-300"
                                >
                                  {pre}
                                </button>
                              ))}
                            </div>
                            <input
                              type="text"
                              value={dismissReason}
                              onChange={(e) => setDismissReason(e.target.value)}
                              placeholder="Or type custom compliance reason..."
                              className="w-full text-xs p-2 rounded-lg border border-midnight-200 focus:outline-none focus:border-brand-500"
                            />
                            <div className="flex items-center justify-end gap-2 pt-1">
                              <button
                                type="button"
                                onClick={() => {
                                  setDismissingIssueId(null);
                                  setDismissReason("");
                                }}
                                className="px-3 py-1 rounded-lg text-[11px] text-midnight-600 hover:bg-midnight-100"
                              >
                                Cancel
                              </button>
                              <button
                                type="button"
                                disabled={isDismissing || !dismissReason.trim()}
                                onClick={() => handleDismissIssue(issue.id)}
                                className="px-3 py-1 rounded-lg text-[11px] font-semibold bg-midnight-900 hover:bg-midnight-800 text-white disabled:opacity-50"
                              >
                                {isDismissing ? "Saving..." : "Confirm Dismiss"}
                              </button>
                            </div>
                          </div>
                        ) : (
                          /* Replacement & Action Area */
                          <div className="mt-3 pt-2.5 border-t border-midnight-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                            <div className="min-w-0 flex-1">
                              {issue.suggested_replacement ? (
                                <>
                                  <span className="text-[10px] font-semibold text-emerald-800 block">Recommended fix:</span>
                                  <span className="text-xs font-mono text-emerald-700 font-medium truncate block">
                                    &ldquo;{issue.suggested_replacement}&rdquo;
                                  </span>
                                </>
                              ) : (issue.recommended_action || "").toLowerCase() === "remove" ? (
                                <span className="text-[11px] text-rose-700 font-medium">
                                  Recommended fix: Remove sensitive text from copy.
                                </span>
                              ) : (
                                <span className="text-[11px] text-midnight-500 font-medium">
                                  Recommended fix: Review or verify against policy.
                                </span>
                              )}
                            </div>

                            <div className="shrink-0 flex items-center gap-1.5">
                              {/* Dismiss Button */}
                              <button
                                type="button"
                                onClick={() => {
                                  setDismissingIssueId(issue.id);
                                  setDismissReason("");
                                }}
                                className="px-2.5 py-1.5 rounded-xl text-xs font-medium text-midnight-500 hover:text-midnight-800 hover:bg-lavender-100 transition-colors"
                              >
                                Dismiss
                              </button>

                              {/* Apply Fix Button */}
                              {(issue.suggested_replacement || (issue.recommended_action || "").toLowerCase() === "remove") && (
                                <button
                                  type="button"
                                  onClick={() => handleApplyFix(issue)}
                                  disabled={isApplied || saving}
                                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                                    isApplied
                                      ? "bg-emerald-100 text-emerald-800 cursor-default"
                                      : "bg-brand-500 hover:bg-brand-600 text-white shadow-sm"
                                  }`}
                                >
                                  {isApplied ? (
                                    <>
                                      <Check className="w-3 h-3 text-emerald-700" />
                                      <span>Applied</span>
                                    </>
                                  ) : (
                                    <>
                                      <Sparkles className="w-3 h-3 text-brand-200" />
                                      <span>Apply Fix</span>
                                    </>
                                  )}
                                </button>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
        )}
      </main>
    </div>
  );
}
