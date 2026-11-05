"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { AppNavbar } from "@/components/layout/AppNavbar";
import { getScoreBadge } from "@/lib/utils";
import {
  ClipboardCheck,
  ArrowRight,
  Loader2,
  ShieldCheck,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  ShieldAlert,
  Building2,
  User,
  Filter
} from "lucide-react";

interface QueueItem {
  id: string;
  title: string;
  category: string;
  target_platform?: string;
  status: string;
  compliance_score?: number;
  creator_name?: string;
  version_count: number;
  created_at: string;
  updated_at: string;
}

export default function ReviewerQueuePage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("pending_review");
  const [accessDenied, setAccessDenied] = useState(false);
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
      return;
    }

    if (isAuthenticated && user) {
      if (user.role !== "reviewer" && user.role !== "admin") {
        setAccessDenied(true);
        setLoading(false);
        return;
      }
      fetchQueue(statusFilter);
    }
  }, [isAuthenticated, authLoading, user?.id, statusFilter, router]);

  const fetchQueue = async (filter: string) => {
    try {
      setLoading(true);
      setQueue([]);
      const res = await api.get(`/reviews/queue?status_filter=${filter}`);
      setQueue(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (accessDenied) {
    return (
      <div className="min-h-screen bg-lavender-50 flex flex-col">
        <AppNavbar />
        <main className="flex-1 max-w-md w-full mx-auto p-8 flex flex-col justify-center items-center text-center">
          <div className="p-8 bg-white rounded-3xl border border-rose-200 shadow-card">
            <ShieldAlert className="w-12 h-12 text-rose-500 mx-auto mb-3" />
            <h2 className="text-xl font-bold text-midnight-950 mb-2">Reviewer Access Restricted</h2>
            <p className="text-xs text-midnight-600 mb-6 leading-relaxed">
              Your account is registered with the <strong>{user?.role}</strong> role. Only authorized Brand Governance Reviewers and Administrators can access the review queue.
            </p>
            <Link
              href="/creator"
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-semibold text-white bg-midnight-900 hover:bg-midnight-800 transition-all shadow-md"
            >
              <span>Go to Creator Studio</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-lavender-50 flex flex-col">
      <AppNavbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-1">
            <ClipboardCheck className="w-6 h-6 text-purple-600" />
            <h1 className="text-2xl sm:text-3xl font-extrabold text-midnight-950 tracking-tight">
              Reviewer Governance Station
            </h1>
          </div>
          <p className="text-sm text-midnight-600">
            Inspect submissions for organization <strong className="text-midnight-900">{user?.organization_name || "Enterprise"}</strong>, compare version diffs, and authorize publication.
          </p>
        </div>

        {/* Status Filter Tabs */}
        <div className="flex items-center gap-1.5 p-1 rounded-2xl bg-white border border-midnight-100 shadow-sm mb-6 w-full sm:w-auto overflow-x-auto">
          <button
            onClick={() => setStatusFilter("pending_review")}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              statusFilter === "pending_review"
                ? "bg-purple-900 text-white shadow-sm"
                : "text-midnight-600 hover:text-midnight-950"
            }`}
          >
            Pending Reviews
          </button>

          <button
            onClick={() => setStatusFilter("changes_requested")}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              statusFilter === "changes_requested"
                ? "bg-purple-900 text-white shadow-sm"
                : "text-midnight-600 hover:text-midnight-950"
            }`}
          >
            Changes Requested
          </button>

          <button
            onClick={() => setStatusFilter("approved")}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              statusFilter === "approved"
                ? "bg-purple-900 text-white shadow-sm"
                : "text-midnight-600 hover:text-midnight-950"
            }`}
          >
            Approved Content
          </button>

          <button
            onClick={() => setStatusFilter("rejected")}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              statusFilter === "rejected"
                ? "bg-purple-900 text-white shadow-sm"
                : "text-midnight-600 hover:text-midnight-950"
            }`}
          >
            Rejected
          </button>

          <button
            onClick={() => setStatusFilter("all")}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              statusFilter === "all"
                ? "bg-purple-900 text-white shadow-sm"
                : "text-midnight-600 hover:text-midnight-950"
            }`}
          >
            All Submissions
          </button>
        </div>

        {loading ? (
          <div className="py-20 flex flex-col items-center justify-center text-midnight-500">
            <Loader2 className="w-8 h-8 animate-spin text-purple-600 mb-3" />
            <p className="text-sm">Loading review queue...</p>
          </div>
        ) : queue.length === 0 ? (
          <div className="p-12 text-center rounded-3xl bg-white border border-midnight-100 shadow-card">
            <div className="w-16 h-16 rounded-2xl bg-purple-50 flex items-center justify-center text-purple-600 mx-auto mb-4">
              <CheckCircle className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-bold text-midnight-900">
              No Submissions Found
            </h3>
            <p className="text-sm text-midnight-500 max-w-md mx-auto mt-1">
              There are currently no items matching the status &apos;{statusFilter.replace("_", " ")}&apos;.
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-3xl border border-midnight-100 shadow-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-midnight-800">
                <thead className="bg-lavender-50/60 border-b border-midnight-100 text-[11px] uppercase tracking-wider font-bold text-midnight-500">
                  <tr>
                    <th scope="col" className="px-6 py-4">Submission</th>
                    <th scope="col" className="px-6 py-4">Creator Information</th>
                    <th scope="col" className="px-6 py-4">Status</th>
                    <th scope="col" className="px-6 py-4">Compliance Score</th>
                    <th scope="col" className="px-6 py-4">Versions</th>
                    <th scope="col" className="px-6 py-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-midnight-100">
                  {queue.map((item) => {
                    const score = item.compliance_score;
                    const badge = score !== undefined && score !== null ? getScoreBadge(score) : null;
                    return (
                      <tr key={item.id} className="hover:bg-lavender-50/40 transition-colors">
                        <td className="px-6 py-4 font-semibold text-midnight-950">
                          <Link href={`/reviewer/${item.id}`} className="hover:text-purple-600 transition-colors">
                            {item.title}
                          </Link>
                          <span className="block text-[11px] text-midnight-400 font-normal capitalize">
                            {item.category.replace("_", " ")} {item.target_platform ? `• ${item.target_platform}` : ""}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-xs">
                          <p className="font-semibold text-midnight-900">{item.creator_name || "Unknown Author"}</p>
                          <p className="text-[11px] text-midnight-400">{user?.organization_name || "Organization Member"}</p>
                        </td>
                        <td className="px-6 py-4">
                          <span
                            className={`px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider ${
                              item.status === "pending_review"
                                ? "bg-amber-50 text-amber-700 border border-amber-200"
                                : item.status === "approved"
                                ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                                : item.status === "rejected"
                                ? "bg-rose-50 text-rose-700 border border-rose-200"
                                : item.status === "changes_requested"
                                ? "bg-orange-50 text-orange-700 border border-orange-200"
                                : "bg-slate-100 text-slate-700 border border-slate-200"
                            }`}
                          >
                            {item.status.replace("_", " ")}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          {score !== undefined && score !== null && badge ? (
                            <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold font-mono border ${badge.borderColor} ${badge.bgColor} ${badge.textColor}`}>
                              <span>{score.toFixed(0)}</span>
                              <span className="text-[10px] opacity-75 font-sans font-medium">/ 100</span>
                            </div>
                          ) : (
                            <span className="text-xs text-midnight-400">N/A</span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-xs font-mono text-midnight-600">
                          v{item.version_count}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <Link
                            href={`/reviewer/${item.id}`}
                            className="inline-flex items-center gap-1.5 text-xs font-semibold text-purple-600 hover:text-purple-800 transition-colors"
                          >
                            <span>Inspect & Review</span>
                            <ArrowRight className="w-3.5 h-3.5" />
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
