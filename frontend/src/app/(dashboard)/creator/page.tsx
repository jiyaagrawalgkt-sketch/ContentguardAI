"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { AppNavbar } from "@/components/layout/AppNavbar";
import { getScoreBadge } from "@/lib/utils";
import { SAMPLE_CONTENT_LIBRARY, SampleContent } from "@/lib/sampleContent";
import {
  Plus,
  FileText,
  ArrowRight,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  Loader2,
  BarChart3,
  ShieldCheck,
  Search,
  Filter,
  Layers,
  BookOpen
} from "lucide-react";

interface SubmissionItem {
  id: string;
  title: string;
  category: string;
  target_platform?: string;
  campaign_name?: string;
  status: string;
  compliance_score?: number;
  compliance_rating?: string;
  version_count: number;
  created_at: string;
  updated_at: string;
}

export default function CreatorDashboardPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const [submissions, setSubmissions] = useState<SubmissionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState<string>("all");
  const router = useRouter();

  // Route guard & account switching: refetch whenever user?.id changes
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
      return;
    }

    if (isAuthenticated && user?.id) {
      fetchSubmissions();
    }
  }, [isAuthenticated, authLoading, user?.id, router]);

  const fetchSubmissions = async () => {
    try {
      setLoading(true);
      setSubmissions([]); // Clear previous user state immediately
      const res = await api.get("/submissions/");
      setSubmissions(res.data);
    } catch (err) {
      console.error("Failed to load submissions", err);
    } finally {
      setLoading(false);
    }
  };

  // Dashboard Metrics Calculation
  const metrics = useMemo(() => {
    const total = submissions.length;
    const scoredSubs = submissions.filter((s) => s.compliance_score !== undefined && s.compliance_score !== null);
    const avgScore = scoredSubs.length > 0
      ? scoredSubs.reduce((acc, curr) => acc + (curr.compliance_score || 0), 0) / scoredSubs.length
      : null;

    const pending = submissions.filter((s) => s.status === "pending_review").length;
    const changes = submissions.filter((s) => s.status === "changes_requested").length;
    const publishedOrApproved = submissions.filter((s) => ["approved", "published"].includes(s.status)).length;
    const drafts = submissions.filter((s) => ["draft", "analyzing"].includes(s.status)).length;

    return {
      total,
      avgScore,
      pending,
      changes,
      publishedOrApproved,
      drafts,
    };
  }, [submissions]);

  // Filtered submissions list
  const filteredSubmissions = useMemo(() => {
    return submissions.filter((sub) => {
      const matchesSearch =
        sub.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (sub.campaign_name && sub.campaign_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (sub.target_platform && sub.target_platform.toLowerCase().includes(searchQuery.toLowerCase()));

      if (!matchesSearch) return false;

      if (activeFilter === "pending") return sub.status === "pending_review";
      if (activeFilter === "changes") return sub.status === "changes_requested";
      if (activeFilter === "published") return ["approved", "published"].includes(sub.status);
      if (activeFilter === "drafts") return ["draft", "analyzing"].includes(sub.status);

      return true;
    });
  }, [submissions, searchQuery, activeFilter]);

  const getStatusBadge = (status: string) => {
    switch (status?.toLowerCase()) {
      case "approved":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">Approved</span>;
      case "published":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200">Published</span>;
      case "pending_review":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">Pending Review</span>;
      case "changes_requested":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-orange-50 text-orange-700 border border-orange-200">Changes Requested</span>;
      case "rejected":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">Rejected</span>;
      case "analyzing":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">Analyzing</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">Draft</span>;
    }
  };

  return (
    <div className="min-h-screen bg-lavender-50 flex flex-col">
      <AppNavbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header Section */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-midnight-950 tracking-tight">
              Creator Studio
            </h1>
            <p className="text-sm text-midnight-600 mt-1">
              Draft, analyze against brand guidelines, and correct copy before submitting for review.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href="/knowledge-base"
              className="inline-flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl text-xs font-semibold text-midnight-800 bg-white hover:bg-lavender-100 border border-midnight-200 shadow-sm transition-all"
            >
              <BookOpen className="w-3.5 h-3.5 text-brand-600" />
              <span>Knowledge Hub</span>
            </Link>

            <Link
              href="/creator/new"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white bg-midnight-900 hover:bg-midnight-800 shadow-card hover:shadow-elevated transition-all"
            >
              <Plus className="w-4 h-4 text-brand-400" />
              <span>New Submission</span>
            </Link>
          </div>
        </div>

        {/* Top Metrics Cards */}
        {!loading && submissions.length > 0 && (
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-3.5 mb-8">
            <div className="bg-white p-4 rounded-2xl border border-midnight-100 shadow-card">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-semibold text-midnight-500 uppercase tracking-wider">
                  Total Submissions
                </span>
                <FileText className="w-4 h-4 text-brand-600" />
              </div>
              <p className="text-2xl font-extrabold text-midnight-950">
                {metrics.total}
              </p>
              <p className="text-[11px] text-midnight-500 mt-0.5">
                Across your campaigns
              </p>
            </div>

            <div className="bg-white p-4 rounded-2xl border border-midnight-100 shadow-card">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-semibold text-midnight-500 uppercase tracking-wider">
                  Avg Compliance
                </span>
                <BarChart3 className="w-4 h-4 text-emerald-600" />
              </div>
              <p className="text-2xl font-extrabold text-midnight-950">
                {metrics.avgScore !== null ? `${metrics.avgScore.toFixed(0)}%` : "N/A"}
              </p>
              <p className="text-[11px] text-emerald-600 font-medium mt-0.5">
                Empirical scoring
              </p>
            </div>

            <div className="bg-white p-4 rounded-2xl border border-midnight-100 shadow-card">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-semibold text-midnight-500 uppercase tracking-wider">
                  Pending Review
                </span>
                <Clock className="w-4 h-4 text-amber-600" />
              </div>
              <p className="text-2xl font-extrabold text-amber-700">
                {metrics.pending}
              </p>
              <p className="text-[11px] text-midnight-500 mt-0.5">
                In reviewer queue
              </p>
            </div>

            <div className="bg-white p-4 rounded-2xl border border-midnight-100 shadow-card">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-semibold text-midnight-500 uppercase tracking-wider">
                  Drafts & Revisions
                </span>
                <AlertTriangle className="w-4 h-4 text-orange-600" />
              </div>
              <p className="text-2xl font-extrabold text-midnight-950">
                {metrics.drafts + metrics.changes}
              </p>
              <p className="text-[11px] text-midnight-500 mt-0.5">
                In progress
              </p>
            </div>

            <div className="bg-white p-4 rounded-2xl border border-midnight-100 shadow-card col-span-2 lg:col-span-1">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-semibold text-midnight-500 uppercase tracking-wider">
                  Published
                </span>
                <ShieldCheck className="w-4 h-4 text-purple-600" />
              </div>
              <p className="text-2xl font-extrabold text-purple-700">
                {metrics.publishedOrApproved}
              </p>
              <p className="text-[11px] text-midnight-500 mt-0.5">
                Certified & live
              </p>
            </div>
          </div>
        )}

        {/* Explore Real-World Sample Content Showcase */}
        <div className="mb-8 p-6 rounded-3xl bg-white border border-brand-100 shadow-card">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 pb-3 border-b border-midnight-100">
            <div>
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-brand-600" />
                <h2 className="text-sm font-bold text-midnight-950 uppercase tracking-wider">
                  Explore Real-World Sample Content
                </h2>
              </div>
              <p className="text-xs text-midnight-500 mt-0.5">
                Test ContentGuard AI against realistic industry copy with controlled compliance violations.
              </p>
            </div>
            <span className="text-[11px] px-2.5 py-1 rounded-full bg-lavender-100 text-midnight-600 font-medium">
              Fictional Product Presets
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
            {SAMPLE_CONTENT_LIBRARY.map((sample) => (
              <div
                key={sample.id}
                className="p-3.5 rounded-2xl border border-midnight-100 hover:border-brand-300 hover:bg-lavender-50/50 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] font-mono font-medium text-midnight-500">
                      {sample.targetPlatform}
                    </span>
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${sample.riskBadgeColor}`}>
                      {sample.riskTier.split(" ")[0]}
                    </span>
                  </div>
                  <h3 className="font-bold text-xs text-midnight-950 mb-1 leading-snug">
                    {sample.name}
                  </h3>
                  <p className="text-[11px] text-midnight-500 line-clamp-3 mb-3">
                    {sample.description}
                  </p>
                </div>

                <Link
                  href={`/creator/new?sample=${sample.id}`}
                  className="inline-flex items-center justify-center gap-1.5 w-full py-1.5 rounded-xl bg-white border border-brand-200 hover:border-brand-400 text-brand-700 font-semibold text-[11px] shadow-2xs hover:shadow-xs transition-all"
                >
                  <span>Load Into Studio</span>
                  <ArrowRight className="w-3 h-3 text-brand-500" />
                </Link>
              </div>
            ))}
          </div>
        </div>

        {/* Filter Bar & Search */}
        {!loading && submissions.length > 0 && (
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 mb-4">
            <div className="flex items-center gap-1.5 p-1 rounded-xl bg-white border border-midnight-100 shadow-sm w-full sm:w-auto overflow-x-auto">
              <button
                onClick={() => setActiveFilter("all")}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  activeFilter === "all"
                    ? "bg-midnight-900 text-white shadow-sm"
                    : "text-midnight-600 hover:text-midnight-950"
                }`}
              >
                All ({submissions.length})
              </button>
              <button
                onClick={() => setActiveFilter("pending")}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  activeFilter === "pending"
                    ? "bg-midnight-900 text-white shadow-sm"
                    : "text-midnight-600 hover:text-midnight-950"
                }`}
              >
                Pending ({metrics.pending})
              </button>
              <button
                onClick={() => setActiveFilter("drafts")}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  activeFilter === "drafts"
                    ? "bg-midnight-900 text-white shadow-sm"
                    : "text-midnight-600 hover:text-midnight-950"
                }`}
              >
                Drafts ({metrics.drafts})
              </button>
              <button
                onClick={() => setActiveFilter("published")}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  activeFilter === "published"
                    ? "bg-midnight-900 text-white shadow-sm"
                    : "text-midnight-600 hover:text-midnight-950"
                }`}
              >
                Published ({metrics.publishedOrApproved})
              </button>
            </div>

            <div className="relative w-full sm:w-64">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-midnight-400" />
              <input
                type="text"
                placeholder="Search your submissions..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 rounded-xl text-xs border border-midnight-200 bg-white focus:outline-none focus:border-brand-500 shadow-sm"
              />
            </div>
          </div>
        )}

        {/* Submissions List */}
        {loading ? (
          <div className="py-20 flex flex-col items-center justify-center text-midnight-500">
            <Loader2 className="w-8 h-8 animate-spin text-brand-500 mb-3" />
            <p className="text-sm">Loading your submissions...</p>
          </div>
        ) : submissions.length === 0 ? (
          <div className="p-12 text-center rounded-3xl bg-white border border-midnight-100 shadow-card">
            <div className="w-16 h-16 rounded-2xl bg-brand-50 flex items-center justify-center text-brand-600 mx-auto mb-4">
              <FileText className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-bold text-midnight-900">
              No submissions yet
            </h3>
            <p className="text-sm text-midnight-500 max-w-md mx-auto mt-1 mb-6">
              Create your first marketing draft or select a sample preset above to run automated brand voice and factual compliance analysis.
            </p>
            <Link
              href="/creator/new"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold text-white bg-midnight-900 hover:bg-midnight-800 shadow-sm transition-all"
            >
              <Sparkles className="w-4 h-4 text-brand-300" />
              <span>Create First Submission</span>
            </Link>
          </div>
        ) : (
          <div className="bg-white rounded-3xl border border-midnight-100 shadow-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-midnight-800">
                <thead className="bg-lavender-50/60 border-b border-midnight-100 text-[11px] uppercase tracking-wider font-bold text-midnight-500">
                  <tr>
                    <th scope="col" className="px-6 py-4">Submission Title</th>
                    <th scope="col" className="px-6 py-4">Category</th>
                    <th scope="col" className="px-6 py-4">Status</th>
                    <th scope="col" className="px-6 py-4">Compliance Score</th>
                    <th scope="col" className="px-6 py-4">Version</th>
                    <th scope="col" className="px-6 py-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-midnight-100">
                  {filteredSubmissions.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-6 py-8 text-center text-xs text-midnight-500">
                        No submissions match the current filter.
                      </td>
                    </tr>
                  ) : (
                    filteredSubmissions.map((sub) => {
                      const score = sub.compliance_score;
                      const badge = score !== undefined && score !== null ? getScoreBadge(score) : null;
                      return (
                        <tr key={sub.id} className="hover:bg-lavender-50/40 transition-colors">
                          <td className="px-6 py-4 font-semibold text-midnight-950">
                            <Link href={`/creator/${sub.id}`} className="hover:text-brand-600 transition-colors">
                              {sub.title}
                            </Link>
                            {sub.target_platform && (
                              <span className="block text-[11px] text-midnight-400 font-normal">
                                {sub.target_platform}
                              </span>
                            )}
                          </td>
                          <td className="px-6 py-4">
                            <span className="capitalize text-xs font-medium text-midnight-600">
                              {sub.category.replace("_", " ")}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            {getStatusBadge(sub.status)}
                          </td>
                          <td className="px-6 py-4">
                            {score !== undefined && score !== null && badge ? (
                              <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold font-mono border ${badge.borderColor} ${badge.bgColor} ${badge.textColor}`}>
                                <span>{score.toFixed(0)}</span>
                                <span className="text-[10px] opacity-75 font-sans font-medium">/ 100</span>
                              </div>
                            ) : (
                              <span className="text-xs text-midnight-400 font-mono">Not analyzed</span>
                            )}
                          </td>
                          <td className="px-6 py-4 text-xs font-mono text-midnight-600">
                            v{sub.version_count}
                          </td>
                          <td className="px-6 py-4 text-right">
                            <Link
                              href={`/creator/${sub.id}`}
                              className="inline-flex items-center gap-1.5 text-xs font-semibold text-brand-600 hover:text-brand-800 transition-colors"
                            >
                              <span>Open Workspace</span>
                              <ArrowRight className="w-3.5 h-3.5" />
                            </Link>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
