"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { getScoreBadge } from "@/lib/utils";
import { ShieldCheck, CheckCircle2, Award, Calendar, ArrowLeft, Loader2, AlertCircle } from "lucide-react";

interface PublishedData {
  id: string;
  public_preview_token: string;
  published_by_name: string;
  published_at: string;
  final_content_snapshot: string;
  compliance_score: number;
  title: string;
  category: string;
}

export default function PublicPreviewPage() {
  const { token } = useParams<{ token: string }>();
  const [data, setData] = useState<PublishedData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (token) {
      api
        .get(`/publishing/preview/${token}`)
        .then((res) => setData(res.data))
        .catch((err) => {
          setError(
            err.response?.data?.detail || "Published content not found or preview link expired."
          );
        })
        .finally(() => setLoading(false));
    }
  }, [token]);

  if (loading) {
    return (
      <div className="min-h-screen bg-lavender-50 flex items-center justify-center text-midnight-500">
        <Loader2 className="w-8 h-8 animate-spin text-brand-600 mb-2" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-lavender-50 flex flex-col items-center justify-center px-4">
        <div className="p-8 max-w-md w-full bg-white rounded-3xl border border-rose-200 shadow-card text-center">
          <AlertCircle className="w-12 h-12 text-rose-500 mx-auto mb-3" />
          <h2 className="text-lg font-bold text-midnight-950 mb-1">
            Verification Notice
          </h2>
          <p className="text-xs text-midnight-600 mb-6 leading-relaxed">
            {error || "Content has not been approved and published."}
          </p>
          <Link
            href="/"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-midnight-900 hover:bg-midnight-800 transition-all"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to Homepage</span>
          </Link>
        </div>
      </div>
    );
  }

  const scoreBadge = getScoreBadge(data.compliance_score);

  return (
    <div className="min-h-screen bg-lavender-50 flex flex-col py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl w-full mx-auto">
        {/* Navigation back */}
        <div className="mb-6 flex items-center justify-between">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-midnight-600 hover:text-midnight-900 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>ContentGuard AI Home</span>
          </Link>
          <span className="text-[11px] font-mono text-midnight-400">
            Preview Token: {data.public_preview_token.slice(0, 16)}...
          </span>
        </div>

        {/* Certificate Card */}
        <div className="bg-white rounded-3xl border border-midnight-100 shadow-elevated overflow-hidden">
          {/* Certificate Header Banner */}
          <div className="bg-gradient-to-r from-midnight-950 via-midnight-900 to-midnight-800 text-white p-6 sm:p-8 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-midnight-800">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-2xl bg-white/10 border border-white/10 flex items-center justify-center text-brand-400">
                  <ShieldCheck className="w-7 h-7" />
                </div>
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-widest text-brand-300 block">
                    Official Verification Certificate
                  </span>
                  <h1 className="text-xl sm:text-2xl font-black text-white tracking-tight">
                    ContentGuard Verified Copy
                  </h1>
                </div>
              </div>

              {/* Compliance score seal */}
              <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-2xl bg-white/10 border border-white/15">
                <Award className="w-5 h-5 text-emerald-400" />
                <div>
                  <span className="text-[10px] text-midnight-300 block uppercase">Compliance Score</span>
                  <span className="text-sm font-extrabold font-mono text-white">
                    {data.compliance_score.toFixed(0)} / 100
                  </span>
                </div>
              </div>
            </div>

            {/* Governance metadata */}
            <div className="pt-4 grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs text-midnight-300">
              <div>
                <span className="text-[10px] text-midnight-400 block">Reviewed & Approved By</span>
                <strong className="text-white font-semibold">{data.published_by_name}</strong>
              </div>
              <div>
                <span className="text-[10px] text-midnight-400 block">Publication Date</span>
                <strong className="text-white font-semibold">
                  {new Date(data.published_at).toLocaleDateString()}
                </strong>
              </div>
              <div className="col-span-2 sm:col-span-1">
                <span className="text-[10px] text-midnight-400 block">Content Category</span>
                <strong className="text-white font-semibold capitalize">
                  {data.category.replace("_", " ")}
                </strong>
              </div>
            </div>
          </div>

          {/* Published Content Body */}
          <div className="p-6 sm:p-10">
            <h2 className="text-xl sm:text-2xl font-extrabold text-midnight-950 mb-4">
              {data.title}
            </h2>

            <div className="p-6 rounded-2xl bg-lavender-50/60 border border-midnight-100 font-mono text-xs sm:text-sm text-midnight-900 leading-relaxed whitespace-pre-wrap">
              {data.final_content_snapshot}
            </div>

            <div className="mt-8 pt-6 border-t border-midnight-100 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-midnight-500">
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Verified adherence to Acme brand guidelines and communication policy.</span>
              </div>
              <span className="font-semibold text-midnight-800">
                ContentGuard AI Governance Platform
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
