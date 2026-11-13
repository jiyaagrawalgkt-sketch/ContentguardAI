"use client";

import React, { useState } from "react";
import {
  GitCommit,
  GitCompare,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Clock,
  Sparkles,
  FileText,
  TrendingUp,
} from "lucide-react";
import { ContentVersion, ContentSubmission } from "@/types";

interface VersionIntelligenceProps {
  submission: ContentSubmission;
}

export function VersionIntelligence({ submission }: VersionIntelligenceProps) {
  const versions = submission.versions || [];
  const [selectedVerIdx, setSelectedVerIdx] = useState<number>(
    Math.max(0, versions.length - 2)
  );
  const currentVer = versions[versions.length - 1];
  const compareVer = versions[selectedVerIdx] || versions[0];

  if (versions.length === 0) {
    return (
      <div className="bg-white rounded-3xl border border-midnight-100 shadow-card p-12 text-center text-midnight-500 text-xs">
        <GitCommit className="w-8 h-8 text-midnight-300 mx-auto mb-2" />
        <p className="font-bold text-midnight-800">No version history available</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-3xl border border-midnight-100 shadow-card p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between pb-4 border-b border-midnight-100 gap-3">
        <div>
          <div className="flex items-center gap-2">
            <GitCompare className="w-5 h-5 text-brand-600" />
            <h3 className="text-base font-extrabold text-midnight-950">
              Version Intelligence & Diff
            </h3>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-brand-50 text-brand-700 border border-brand-200 uppercase tracking-wider">
              Revision Analytics
            </span>
          </div>
          <p className="text-xs text-midnight-500 mt-0.5">
            Compare incremental copy revisions, view editorial change summaries, and track compliance evolution.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="text-midnight-500 font-semibold">Compare Base:</span>
          <select
            value={selectedVerIdx}
            onChange={(e) => setSelectedVerIdx(Number(e.target.value))}
            className="px-2.5 py-1 rounded-xl border border-midnight-200 bg-lavender-50 font-bold text-midnight-800 text-xs focus:outline-none"
          >
            {versions.map((v, i) => (
              <option key={v.id} value={i}>
                v{v.version_number} — {v.change_summary?.slice(0, 25) || `Revision ${v.version_number}`}
              </option>
            ))}
          </select>
          <span className="text-midnight-400">vs</span>
          <span className="px-2.5 py-1 rounded-xl bg-midnight-950 text-white font-bold text-xs">
            v{currentVer.version_number} (Latest)
          </span>
        </div>
      </div>

      {/* Version timeline cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {versions.map((v, idx) => {
          const isLatest = idx === versions.length - 1;
          const isBase = idx === selectedVerIdx;
          return (
            <div
              key={v.id}
              onClick={() => setSelectedVerIdx(idx)}
              className={`p-3.5 rounded-2xl border cursor-pointer transition-all ${
                isLatest
                  ? "bg-midnight-950 text-white border-midnight-950 shadow-md"
                  : isBase
                  ? "bg-brand-50 border-brand-400 ring-1 ring-brand-400"
                  : "bg-white border-midnight-100 hover:bg-lavender-50"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className={`text-xs font-bold font-mono ${isLatest ? "text-brand-300" : "text-brand-600"}`}>
                  Version {v.version_number}
                </span>
                {isLatest && (
                  <span className="text-[10px] bg-brand-500 text-white px-2 py-0.5 rounded-full font-bold">
                    ACTIVE DRAFT
                  </span>
                )}
              </div>
              <p className={`text-xs font-medium line-clamp-2 ${isLatest ? "text-midnight-200" : "text-midnight-700"}`}>
                {v.change_summary || "Initial draft creation"}
              </p>
              <span className={`text-[10px] font-mono mt-2 block ${isLatest ? "text-midnight-400" : "text-midnight-400"}`}>
                {v.content_body.length} characters • {v.content_body.split(/\s+/).filter(Boolean).length} words
              </span>
            </div>
          );
        })}
      </div>

      {/* Side by side comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Base Version */}
        <div className="p-4 rounded-2xl bg-lavender-50/50 border border-midnight-100 space-y-2">
          <div className="flex items-center justify-between border-b border-midnight-100 pb-2">
            <span className="text-xs font-bold text-midnight-800">
              Version {compareVer.version_number}: {compareVer.change_summary || "Base Copy"}
            </span>
            <span className="text-[10px] font-mono text-midnight-400">
              {compareVer.content_body.length} chars
            </span>
          </div>
          <div className="p-3 bg-white rounded-xl border border-midnight-100 text-xs font-mono text-midnight-900 leading-relaxed whitespace-pre-wrap min-h-[160px] max-h-[300px] overflow-y-auto">
            {compareVer.content_body}
          </div>
        </div>

        {/* Current Version */}
        <div className="p-4 rounded-2xl bg-brand-50/30 border border-brand-200 space-y-2">
          <div className="flex items-center justify-between border-b border-brand-100 pb-2">
            <span className="text-xs font-bold text-brand-950">
              Version {currentVer.version_number}: Current Draft
            </span>
            <span className="text-[10px] font-mono text-brand-700">
              {currentVer.content_body.length} chars
            </span>
          </div>
          <div className="p-3 bg-white rounded-xl border border-brand-200 text-xs font-mono text-midnight-950 leading-relaxed whitespace-pre-wrap min-h-[160px] max-h-[300px] overflow-y-auto">
            {currentVer.content_body}
          </div>
        </div>
      </div>
    </div>
  );
}
