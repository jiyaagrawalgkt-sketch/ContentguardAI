"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { AppNavbar } from "@/components/layout/AppNavbar";
import { SAMPLE_CONTENT_LIBRARY, SampleContent } from "@/lib/sampleContent";
import {
  ArrowLeft,
  Sparkles,
  Send,
  Loader2,
  AlertCircle,
  BookOpen,
  CheckCircle2,
  ChevronDown,
  Layers,
  ShieldAlert,
  Info,
  X
} from "lucide-react";

function NewSubmissionForm() {
  const { user } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("marketing_email");
  const [targetPlatform, setTargetPlatform] = useState("Email Newsletter");
  const [campaignName, setCampaignName] = useState("");
  const [content, setContent] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sample Content Library Modal state
  const [showLibraryModal, setShowLibraryModal] = useState(false);
  const [showRulesDrawer, setShowRulesDrawer] = useState(false);
  const [brandKnowledge, setBrandKnowledge] = useState<any>(null);

  useEffect(() => {
    // Optionally prefetch brand knowledge rules summary
    api.get("/brand-knowledge/summary")
      .then((res) => setBrandKnowledge(res.data))
      .catch((err) => console.log("Brand knowledge load optional", err));

    // Auto load preset from query param if provided
    const sampleParam = searchParams?.get("sample");
    if (sampleParam) {
      const found = SAMPLE_CONTENT_LIBRARY.find((s) => s.id === sampleParam);
      if (found) {
        setTitle(found.title);
        setCategory(found.category);
        setTargetPlatform(found.targetPlatform);
        setCampaignName(found.campaignName);
        setContent(found.content);
      }
    }
  }, [searchParams]);

  const handleSelectSample = (sample: SampleContent) => {
    setTitle(sample.title);
    setCategory(sample.category);
    setTargetPlatform(sample.targetPlatform);
    setCampaignName(sample.campaignName);
    setContent(sample.content);
    setError(null);
    setShowLibraryModal(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!title.trim()) {
      setError("Please enter a submission title.");
      return;
    }
    if (content.trim().length < 10) {
      setError("Please enter draft content with at least 10 characters.");
      return;
    }

    try {
      setIsLoading(true);
      const res = await api.post("/submissions/", {
        title,
        category,
        target_platform: targetPlatform,
        campaign_name: campaignName,
        content,
      });

      // Navigate to the correction workspace
      router.push(`/creator/${res.data.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create submission. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-lavender-50 flex flex-col">
      <AppNavbar />

      <main className="flex-1 max-w-4xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <Link
            href="/creator"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-midnight-600 hover:text-midnight-950 transition-colors mb-3"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Creator Studio</span>
          </Link>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-extrabold text-midnight-950 tracking-tight">
                New Content Submission
              </h1>
              <p className="text-xs text-midnight-600 mt-0.5">
                Submit marketing copy, ad drafts, social posts, or press releases to run AI brand governance analysis.
              </p>
            </div>

            <div className="flex items-center gap-2 self-start sm:self-auto">
              {/* Rules summary pill */}
              <button
                type="button"
                onClick={() => setShowRulesDrawer(!showRulesDrawer)}
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-white border border-midnight-200 text-midnight-700 hover:bg-lavender-50 transition-all shadow-sm"
              >
                <BookOpen className="w-3.5 h-3.5 text-brand-600" />
                <span>Active Brand Rules</span>
              </button>

              {/* Sample Content Library Modal Trigger */}
              <button
                type="button"
                onClick={() => setShowLibraryModal(true)}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-brand-50 text-brand-700 border border-brand-200 hover:bg-brand-100 hover:border-brand-300 transition-all shadow-sm"
              >
                <Sparkles className="w-3.5 h-3.5 text-brand-500" />
                <span>Try Sample Content</span>
              </button>
            </div>
          </div>
        </div>

        {/* Collapsible Brand Rules Panel */}
        {showRulesDrawer && brandKnowledge && (
          <div className="mb-6 p-5 rounded-2xl bg-white border border-brand-200 shadow-card">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-brand-600" />
                <h3 className="text-xs font-bold text-midnight-900 uppercase tracking-wider">
                  Active Brand Governance Standards
                </h3>
              </div>
              <button
                onClick={() => setShowRulesDrawer(false)}
                className="text-midnight-400 hover:text-midnight-700 text-xs font-semibold"
              >
                Hide
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div className="p-3 rounded-xl bg-lavender-50/70 border border-midnight-100">
                <p className="font-bold text-midnight-900 mb-1">Tone & Voice</p>
                <p className="text-midnight-600 text-[11px]">
                  Authoritative, transparent, professional. Prohibits superlatives and buzzwords like &quot;game-changer&quot;.
                </p>
              </div>
              <div className="p-3 rounded-xl bg-lavender-50/70 border border-midnight-100">
                <p className="font-bold text-midnight-900 mb-1">Approved Facts Vault</p>
                <p className="text-midnight-600 text-[11px]">
                  99.9% uptime SLA (SOC-2 Type II), up to 12,000 evaluations/min capacity.
                </p>
              </div>
              <div className="p-3 rounded-xl bg-lavender-50/70 border border-midnight-100">
                <p className="font-bold text-midnight-900 mb-1">Zero Guarantees</p>
                <p className="text-midnight-600 text-[11px]">
                  Never promise 100% risk-free outcomes, unverified multipliers, or unprovable market superiority.
                </p>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="mb-6 p-4 rounded-2xl bg-rose-50 border border-rose-200 flex items-center gap-3 text-xs text-rose-700">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Content Submission Form */}
        <form onSubmit={handleSubmit} className="space-y-6 bg-white p-6 sm:p-8 rounded-3xl border border-midnight-100 shadow-card">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-midnight-800 mb-1">
                Content Title *
              </label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Q4 Global Product Launch Announcement"
                className="w-full rounded-xl border border-midnight-200 px-3.5 py-2.5 text-sm text-midnight-900 placeholder:text-midnight-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-midnight-800 mb-1">
                Campaign / Initiative Name
              </label>
              <input
                type="text"
                value={campaignName}
                onChange={(e) => setCampaignName(e.target.value)}
                placeholder="e.g. Enterprise Outreach 2026"
                className="w-full rounded-xl border border-midnight-200 px-3.5 py-2.5 text-sm text-midnight-900 placeholder:text-midnight-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-midnight-800 mb-1">
                Content Format / Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full rounded-xl border border-midnight-200 px-3.5 py-2.5 text-sm text-midnight-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              >
                <option value="marketing_email">Marketing Email / Newsletter</option>
                <option value="social_media">Social Media Post (LinkedIn / X)</option>
                <option value="advertisement">Paid Search / Display Ad Copy</option>
                <option value="landing_page">Website Landing Page Copy</option>
                <option value="press_release">Official Corporate Press Release</option>
                <option value="blog">Blog Article / Thought Leadership</option>
                <option value="business_document">Business Document / Specs</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-midnight-800 mb-1">
                Target Publication Channel
              </label>
              <input
                type="text"
                value={targetPlatform}
                onChange={(e) => setTargetPlatform(e.target.value)}
                placeholder="e.g. LinkedIn, Newsletter, Corporate Website, PR Newswire"
                className="w-full rounded-xl border border-midnight-200 px-3.5 py-2.5 text-sm text-midnight-900 placeholder:text-midnight-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-xs font-semibold text-midnight-800">
                Draft Content (Text Editor) *
              </label>
              <span className="text-[11px] text-midnight-400 font-mono">
                {content.length} characters
              </span>
            </div>
            <textarea
              required
              rows={12}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Paste or write any marketing, social, ad, or corporate content here to run real-time brand compliance analysis..."
              className="w-full rounded-xl border border-midnight-200 p-4 text-sm text-midnight-900 font-mono placeholder:text-midnight-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 leading-relaxed"
            />
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-midnight-100">
            <button
              type="button"
              onClick={() => setShowLibraryModal(true)}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-brand-600 hover:text-brand-800 transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Browse Sample Library</span>
            </button>

            <div className="flex items-center gap-3">
              <Link
                href="/creator"
                className="px-4 py-2.5 rounded-xl text-xs font-semibold text-midnight-600 hover:text-midnight-900 hover:bg-lavender-100 transition-colors"
              >
                Cancel
              </Link>
              <button
                type="submit"
                disabled={isLoading}
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold text-white bg-midnight-900 hover:bg-midnight-800 shadow-card hover:shadow-elevated transition-all disabled:opacity-50"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <Send className="w-4 h-4 text-brand-400" />
                    <span>Create & Run Analysis</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </form>

        {/* Sample Content Library Modal */}
        {showLibraryModal && (
          <div className="fixed inset-0 z-50 bg-midnight-950/40 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-white rounded-3xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-elevated border border-midnight-100 overflow-hidden">
              <div className="p-6 border-b border-midnight-100 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-brand-600" />
                    <h2 className="text-lg font-bold text-midnight-950">
                      Sample Content Library
                    </h2>
                  </div>
                  <p className="text-xs text-midnight-600 mt-0.5">
                    Select a realistic industry draft to evaluate how ContentGuard AI flags violations and guides corrections.
                  </p>
                </div>
                <button
                  onClick={() => setShowLibraryModal(false)}
                  className="p-1 rounded-lg text-midnight-400 hover:text-midnight-800 hover:bg-lavender-100 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="p-6 overflow-y-auto space-y-3.5 divide-y divide-midnight-50">
                {SAMPLE_CONTENT_LIBRARY.map((sample) => (
                  <div
                    key={sample.id}
                    onClick={() => handleSelectSample(sample)}
                    className="pt-3.5 first:pt-0 group p-3.5 rounded-2xl hover:bg-lavender-50 border border-transparent hover:border-brand-200 transition-all cursor-pointer text-left"
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-midnight-900 group-hover:text-brand-600 transition-colors">
                          {sample.name}
                        </span>
                        <span className="text-[10px] px-2 py-0.5 rounded-md bg-lavender-100 font-medium text-midnight-600">
                          {sample.targetPlatform}
                        </span>
                      </div>
                      <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full border ${sample.riskBadgeColor}`}>
                        {sample.riskTier}
                      </span>
                    </div>

                    <p className="text-xs text-midnight-600 mb-2">
                      {sample.description}
                    </p>

                    <div className="flex flex-wrap gap-1.5">
                      {sample.highlights.map((h, i) => (
                        <span
                          key={i}
                          className="text-[10px] font-medium bg-white px-2 py-0.5 rounded-md border border-midnight-100 text-midnight-500"
                        >
                          {h}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <div className="p-4 bg-lavender-50/50 border-t border-midnight-100 flex justify-end">
                <button
                  type="button"
                  onClick={() => setShowLibraryModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-midnight-600 hover:text-midnight-900 bg-white border border-midnight-200 transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default function NewSubmissionPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-lavender-50 flex items-center justify-center text-midnight-500">
          <Loader2 className="w-8 h-8 animate-spin text-brand-600 mb-2" />
        </div>
      }
    >
      <NewSubmissionForm />
    </Suspense>
  );
}
