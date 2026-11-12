"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { AppNavbar } from "@/components/layout/AppNavbar";
import { EvidenceGraph } from "@/components/evidence/EvidenceGraph";
import { getScoreBadge } from "@/lib/utils";
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
  UserCheck
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
  const [publishedToken, setPublishedToken] = useState<string | null>(null);
  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
      return;
    }
    if (id) {
      loadSubmission();
    }
  }, [id, isAuthenticated, authLoading]);

  const loadSubmission = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/submissions/${id}`);
      setSubmission(res.data);
      if (res.data.status === "published") {
        // If already published, check if published token exists
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

      // 1. Submit review decision
      const decideRes = await api.post(`/reviews/${id}/decide`, {
        decision,
        comment,
      });

      // 2. If approved, automatically trigger publishing to create the public preview link
      if (decision === "approved") {
        const pubRes = await api.post(`/publishing/${id}/publish`);
        setPublishedToken(pubRes.data.public_preview_token);
        setNotification({
          type: "success",
          message: `Submission approved and published! Public read-only preview is now live.`
        });
      } else {
        setNotification({
          type: "success",
          message: `Decision recorded: status updated to '${decision.replace("_", " ")}'.`
        });
      }

      setSubmission(decideRes.data);
    } catch (err: any) {
      setNotification({
        type: "error",
        message: err.response?.data?.detail || "Failed to process decision."
      });
    } finally {
      setSubmitting(false);
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
  const score = submission?.latest_report?.compliance_score ?? 0;
  const badge = getScoreBadge(score);

  return (
    <div className="min-h-screen bg-lavender-50 flex flex-col">
      <AppNavbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Top Header */}
        <div className="mb-6">
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
          <div className={`mb-6 p-4 rounded-2xl border flex items-center gap-3 text-xs ${
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
          <div className="mb-6 p-4 rounded-2xl bg-white border border-purple-300 shadow-elevated flex flex-col sm:flex-row sm:items-center justify-between gap-4">
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
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
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

        {/* Evidence Verification Graph & Fact Grounding */}
        <div className="mb-6">
          <EvidenceGraph submissionId={id} submissionTitle={submission?.title} />
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
                  disabled={submitting}
                  className="px-4 py-2.5 rounded-xl text-xs font-semibold text-orange-700 bg-orange-50 border border-orange-200 hover:bg-orange-100 transition-colors disabled:opacity-50"
                >
                  Request Changes
                </button>

                <button
                  type="button"
                  onClick={() => handleDecision("rejected")}
                  disabled={submitting}
                  className="px-4 py-2.5 rounded-xl text-xs font-semibold text-rose-700 bg-rose-50 border border-rose-200 hover:bg-rose-100 transition-colors disabled:opacity-50"
                >
                  Reject Content
                </button>

                <button
                  type="button"
                  onClick={() => handleDecision("approved")}
                  disabled={submitting}
                  className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-semibold text-white bg-midnight-900 hover:bg-midnight-800 shadow-md hover:shadow-lg transition-all disabled:opacity-50"
                >
                  {submitting ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  )}
                  <span>Approve & Publish Immediately</span>
                </button>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
