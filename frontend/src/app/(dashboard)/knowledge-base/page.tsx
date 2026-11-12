"use client";

import React, { useState, useEffect } from "react";
import { AppNavbar } from "@/components/layout/AppNavbar";
import { useAuth } from "@/context/AuthContext";
import {
  FileText,
  Upload,
  Trash2,
  Calendar,
  Layers,
  CheckCircle,
  AlertCircle,
  Clock,
  ShieldCheck,
  Loader2,
  Search,
  Plus,
  BookOpen,
  CheckSquare,
  AlertOctagon,
  Palette,
  X,
  ExternalLink,
  Info,
} from "lucide-react";
import { KnowledgeDocument } from "@/types";
import { api } from "@/lib/api";

interface BrandGuidelineItem {
  id: string;
  category: string;
  title: string;
  description: string;
  rules: string[];
  severity_level: string;
}

interface ApprovedFactItem {
  id: string;
  topic: string;
  statement: string;
  verified_numbers?: Record<string, any>;
  reference_url_or_doc?: string;
}

interface RestrictedTermItem {
  id: string;
  term: string;
  category: string;
  severity: string;
  suggested_alternative: string;
  reason: string;
}

interface BrandAssetItem {
  id: string;
  name: string;
  asset_type: string;
  primary_color_hex?: string;
  secondary_color_hex?: string;
  accent_color_hex?: string;
  neutral_color_hex?: string;
  wcag_min_contrast?: number;
  rules_json?: Record<string, any>;
}

export default function KnowledgeBasePage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const isCompliance = user?.role === "compliance_officer";
  const canManage = isAdmin || isCompliance;

  // Tabs
  const [activeTab, setActiveTab] = useState<"documents" | "guidelines" | "facts" | "terms" | "assets">("documents");

  // Data states
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [guidelines, setGuidelines] = useState<BrandGuidelineItem[]>([]);
  const [facts, setFacts] = useState<ApprovedFactItem[]>([]);
  const [terms, setTerms] = useState<RestrictedTermItem[]>([]);
  const [assets, setAssets] = useState<BrandAssetItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Modals & Forms
  const [inspectDoc, setInspectDoc] = useState<any | null>(null);
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Form inputs for document upload
  const [docTitle, setDocTitle] = useState("");
  const [docSourceType, setDocSourceType] = useState("company_stats");
  const [docVersion, setDocVersion] = useState("1.0");
  const [docValidity, setDocValidity] = useState("");
  const [docFile, setDocFile] = useState<File | null>(null);

  // Form inputs for new guideline
  const [glCategory, setGlCategory] = useState("tone_voice");
  const [glTitle, setGlTitle] = useState("");
  const [glDesc, setGlDesc] = useState("");
  const [glRules, setGlRules] = useState("");
  const [glSeverity, setGlSeverity] = useState("high");

  // Form inputs for new fact
  const [factTopic, setFactTopic] = useState("");
  const [factStatement, setFactStatement] = useState("");
  const [factRef, setFactRef] = useState("");

  // Form inputs for new restricted term
  const [termWord, setTermWord] = useState("");
  const [termCategory, setTermCategory] = useState("unverified_superlative");
  const [termSeverity, setTermSeverity] = useState("high");
  const [termAlt, setTermAlt] = useState("");
  const [termReason, setTermReason] = useState("");

  const loadAllKnowledge = async () => {
    setLoading(true);
    setMessage(null);

    // 1. Fetch ingested documents
    try {
      const docRes = await api.get("/knowledge-base/");
      setDocuments(docRes.data || []);
    } catch {
      setDocuments([]);
    }

    // 2. Fetch guidelines, facts, and restricted terms
    try {
      const summaryRes = await api.get("/brand-knowledge/summary");
      if (summaryRes.data) {
        setGuidelines(summaryRes.data.guidelines || []);
        setFacts(summaryRes.data.approved_facts || []);
        setTerms(summaryRes.data.restricted_terms || []);
      }
    } catch {
      // pass
    }

    // 3. Fetch brand assets
    try {
      const assetRes = await api.get("/brand-knowledge/assets");
      setAssets(assetRes.data || []);
    } catch {
      // pass
    }

    setLoading(false);
  };

  useEffect(() => {
    loadAllKnowledge();
  }, []);

  // Handlers for Document Ingestion
  const handleDocUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!docFile || !docTitle.trim()) return;

    setUploading(true);
    setMessage(null);

    const formData = new FormData();
    formData.append("file", docFile);
    formData.append("title", docTitle.trim());
    formData.append("source_type", docSourceType);
    formData.append("version", docVersion);
    if (docValidity) {
      formData.append("validity_date", docValidity);
    }

    try {
      const res = await api.post("/knowledge-base/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setMessage({ type: "success", text: res.data.message || "Document successfully ingested and indexed!" });
      setDocTitle("");
      setDocFile(null);
      setDocValidity("");
      setShowAddModal(false);
      await loadAllKnowledge();
    } catch (err: any) {
      setMessage({
        type: "error",
        text: err.response?.data?.detail || "Failed to upload document. Please verify format and size.",
      });
    } finally {
      setUploading(false);
    }
  };

  const handleDocDelete = async (docId: string) => {
    if (!confirm("Remove this document and cascade delete its vector embeddings?")) return;
    try {
      await api.delete(`/knowledge-base/${docId}`);
      setMessage({ type: "success", text: "Document removed from knowledge base." });
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    } catch (err: any) {
      setMessage({ type: "error", text: err.response?.data?.detail || "Failed to delete document." });
    }
  };

  const handleInspectDoc = async (docId: string) => {
    try {
      const res = await api.get(`/knowledge-base/${docId}`);
      setInspectDoc(res.data);
    } catch {
      setMessage({ type: "error", text: "Could not retrieve document passages." });
    }
  };

  // Handlers for Brand Guideline Creation
  const handleAddGuideline = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!glTitle.trim()) return;
    try {
      setUploading(true);
      await api.post("/brand-knowledge/guidelines", {
        category: glCategory,
        title: glTitle.trim(),
        description: glDesc.trim(),
        rules: glRules.split("\n").map((r) => r.trim()).filter(Boolean),
        severity_level: glSeverity,
      });
      setMessage({ type: "success", text: "Brand guideline registered successfully." });
      setGlTitle("");
      setGlDesc("");
      setGlRules("");
      setShowAddModal(false);
      await loadAllKnowledge();
    } catch (err: any) {
      setMessage({ type: "error", text: err.response?.data?.detail || "Failed to create guideline." });
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteGuideline = async (id: string) => {
    if (!confirm("Delete this brand guideline?")) return;
    try {
      await api.delete(`/brand-knowledge/guidelines/${id}`);
      setGuidelines((prev) => prev.filter((g) => g.id !== id));
      setMessage({ type: "success", text: "Guideline removed." });
    } catch (err: any) {
      setMessage({ type: "error", text: err.response?.data?.detail || "Failed to delete guideline." });
    }
  };

  // Handlers for Approved Facts
  const handleAddFact = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!factStatement.trim()) return;
    try {
      setUploading(true);
      await api.post("/brand-knowledge/facts", {
        topic: factTopic.trim() || "General",
        statement: factStatement.trim(),
        reference_url_or_doc: factRef.trim(),
      });
      setMessage({ type: "success", text: "Approved fact recorded." });
      setFactTopic("");
      setFactStatement("");
      setFactRef("");
      setShowAddModal(false);
      await loadAllKnowledge();
    } catch (err: any) {
      setMessage({ type: "error", text: err.response?.data?.detail || "Failed to add fact." });
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteFact = async (id: string) => {
    if (!confirm("Delete this approved fact?")) return;
    try {
      await api.delete(`/brand-knowledge/facts/${id}`);
      setFacts((prev) => prev.filter((f) => f.id !== id));
      setMessage({ type: "success", text: "Approved fact removed." });
    } catch (err: any) {
      setMessage({ type: "error", text: err.response?.data?.detail || "Failed to delete fact." });
    }
  };

  // Handlers for Restricted Terms
  const handleAddTerm = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!termWord.trim()) return;
    try {
      setUploading(true);
      await api.post("/brand-knowledge/terms", {
        term: termWord.trim(),
        category: termCategory,
        severity: termSeverity,
        suggested_alternative: termAlt.trim(),
        reason: termReason.trim() || "Violates communication guidelines",
      });
      setMessage({ type: "success", text: "Restricted term added to dictionary." });
      setTermWord("");
      setTermAlt("");
      setTermReason("");
      setShowAddModal(false);
      await loadAllKnowledge();
    } catch (err: any) {
      setMessage({ type: "error", text: err.response?.data?.detail || "Failed to add term." });
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteTerm = async (id: string) => {
    if (!confirm("Remove this restricted term?")) return;
    try {
      await api.delete(`/brand-knowledge/terms/${id}`);
      setTerms((prev) => prev.filter((t) => t.id !== id));
      setMessage({ type: "success", text: "Term removed." });
    } catch (err: any) {
      setMessage({ type: "error", text: err.response?.data?.detail || "Failed to delete term." });
    }
  };

  // Filtering
  const q = searchQuery.toLowerCase();
  const filteredDocs = documents.filter((d) => d.title.toLowerCase().includes(q) || d.file_name.toLowerCase().includes(q));
  const filteredGuidelines = guidelines.filter((g) => g.title.toLowerCase().includes(q) || g.description.toLowerCase().includes(q));
  const filteredFacts = facts.filter((f) => f.statement.toLowerCase().includes(q) || f.topic.toLowerCase().includes(q));
  const filteredTerms = terms.filter((t) => t.term.toLowerCase().includes(q) || t.reason.toLowerCase().includes(q));
  const filteredAssets = assets.filter((a) => a.name.toLowerCase().includes(q));

  return (
    <div className="min-h-screen bg-lavender-50 flex flex-col">
      <AppNavbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Header & Role Capabilities Bar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-brand-600 text-white flex items-center justify-center shadow-sm">
                <Layers className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-2xl font-extrabold text-midnight-950">
                  Brand Knowledge & Evidence Hub
                </h1>
                <p className="text-xs text-midnight-500">
                  {canManage
                    ? "Manage official guidelines, approved facts, restricted dictionary, and source documents."
                    : "Official organizational knowledge vault. Use this as your reference guide for compliant writing."}
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span
              className={`text-xs font-bold px-3 py-1 rounded-full border ${
                canManage
                  ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                  : "bg-brand-50 text-brand-800 border-brand-200"
              }`}
            >
              {user?.role === "admin"
                ? "Admin Management Mode"
                : user?.role === "compliance_officer"
                ? "Compliance Reviewer Mode"
                : "Read-Only Reference Vault"}
            </span>

            {canManage && (
              <button
                onClick={() => setShowAddModal(true)}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-midnight-900 hover:bg-midnight-800 text-white text-xs font-semibold shadow-sm transition-all"
              >
                <Plus className="w-4 h-4" />
                <span>
                  {activeTab === "documents"
                    ? "Ingest Document"
                    : activeTab === "guidelines"
                    ? "New Guideline"
                    : activeTab === "facts"
                    ? "Add Approved Fact"
                    : activeTab === "terms"
                    ? "Add Restricted Term"
                    : "Add Asset"}
                </span>
              </button>
            )}
          </div>
        </div>

        {/* Status Notification */}
        {message && (
          <div
            className={`p-4 rounded-2xl border flex items-center justify-between gap-2 text-xs font-semibold ${
              message.type === "success"
                ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                : "bg-rose-50 border-rose-200 text-rose-800"
            }`}
          >
            <div className="flex items-center gap-2">
              {message.type === "success" ? (
                <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
              ) : (
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              )}
              <span>{message.text}</span>
            </div>
            <button onClick={() => setMessage(null)} className="text-midnight-400 hover:text-midnight-800">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Tab Controls & Search Filter Bar */}
        <div className="bg-white p-3 rounded-2xl border border-midnight-100 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto p-1 bg-lavender-50 rounded-xl">
            <button
              onClick={() => setActiveTab("documents")}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                activeTab === "documents"
                  ? "bg-white text-midnight-950 shadow-sm"
                  : "text-midnight-600 hover:text-midnight-950"
              }`}
            >
              <FileText className="w-3.5 h-3.5 text-brand-600" />
              <span>Evidence Documents ({documents.length})</span>
            </button>

            <button
              onClick={() => setActiveTab("guidelines")}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                activeTab === "guidelines"
                  ? "bg-white text-midnight-950 shadow-sm"
                  : "text-midnight-600 hover:text-midnight-950"
              }`}
            >
              <BookOpen className="w-3.5 h-3.5 text-purple-600" />
              <span>Brand Guidelines ({guidelines.length})</span>
            </button>

            <button
              onClick={() => setActiveTab("facts")}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                activeTab === "facts"
                  ? "bg-white text-midnight-950 shadow-sm"
                  : "text-midnight-600 hover:text-midnight-950"
              }`}
            >
              <CheckSquare className="w-3.5 h-3.5 text-emerald-600" />
              <span>Approved Facts ({facts.length})</span>
            </button>

            <button
              onClick={() => setActiveTab("terms")}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                activeTab === "terms"
                  ? "bg-white text-midnight-950 shadow-sm"
                  : "text-midnight-600 hover:text-midnight-950"
              }`}
            >
              <AlertOctagon className="w-3.5 h-3.5 text-rose-600" />
              <span>Restricted Terms ({terms.length})</span>
            </button>

            <button
              onClick={() => setActiveTab("assets")}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                activeTab === "assets"
                  ? "bg-white text-midnight-950 shadow-sm"
                  : "text-midnight-600 hover:text-midnight-950"
              }`}
            >
              <Palette className="w-3.5 h-3.5 text-indigo-600" />
              <span>Visual Standards ({assets.length})</span>
            </button>
          </div>

          <div className="relative w-full md:w-72">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search knowledge records..."
              className="w-full pl-9 pr-3 py-1.5 rounded-xl border border-midnight-200 text-xs text-midnight-900 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
            <Search className="w-3.5 h-3.5 text-midnight-400 absolute left-3 top-2.5" />
          </div>
        </div>

        {/* Content Loading State */}
        {loading ? (
          <div className="py-20 flex flex-col items-center justify-center text-midnight-400">
            <Loader2 className="w-8 h-8 animate-spin text-brand-600 mb-2" />
            <p className="text-xs">Loading verified organizational knowledge...</p>
          </div>
        ) : (
          <div>
            {/* ======================================================== */}
            {/* TAB 1: EVIDENCE SOURCE DOCUMENTS                         */}
            {/* ======================================================== */}
            {activeTab === "documents" && (
              <div className="space-y-4">
                {filteredDocs.length === 0 ? (
                  <div className="bg-white p-12 rounded-3xl border border-midnight-100 text-center space-y-3">
                    <FileText className="w-10 h-10 text-midnight-300 mx-auto" />
                    <h3 className="text-sm font-bold text-midnight-800">No Evidence Documents Found</h3>
                    <p className="text-xs text-midnight-500 max-w-sm mx-auto">
                      {canManage
                        ? "Click 'Ingest Document' to upload PDF, DOCX, or TXT whitepapers to power zero-trust evidence verification."
                        : "No documents match your query in this workspace."}
                    </p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {filteredDocs.map((doc) => (
                      <div
                        key={doc.id}
                        className="bg-white p-5 rounded-2xl border border-midnight-100 shadow-card hover:border-brand-200 transition-all flex flex-col justify-between"
                      >
                        <div>
                          <div className="flex items-start justify-between gap-2 mb-2">
                            <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-brand-50 text-brand-700 border border-brand-100">
                              {doc.source_type.replace("_", " ")}
                            </span>
                            <span
                              className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                                doc.is_expired
                                  ? "bg-rose-50 text-rose-700 border border-rose-200"
                                  : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                              }`}
                            >
                              {doc.is_expired ? "OUTDATED" : "VALID & INDEXED"}
                            </span>
                          </div>

                          <h3 className="font-bold text-sm text-midnight-950 mb-1">{doc.title}</h3>
                          <p className="text-xs text-midnight-500 font-mono mb-3">{doc.file_name}</p>

                          <div className="space-y-1 text-xs text-midnight-600 bg-lavender-50/60 p-2.5 rounded-xl border border-midnight-100/60">
                            <div className="flex justify-between">
                              <span className="text-midnight-400">Indexed Chunks:</span>
                              <span className="font-bold text-midnight-800">{doc.chunks_count} segments</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-midnight-400">File Size:</span>
                              <span className="font-mono text-[11px] text-midnight-700">
                                {((doc.file_size_bytes || 0) / 1024).toFixed(0)} KB
                              </span>
                            </div>
                            {doc.validity_date && (
                              <div className="flex justify-between">
                                <span className="text-midnight-400">Validity Expiry:</span>
                                <span className="font-mono text-[11px] text-midnight-700">{doc.validity_date}</span>
                              </div>
                            )}
                          </div>
                        </div>

                        <div className="mt-4 pt-3 border-t border-midnight-100 flex items-center justify-between gap-2">
                          <button
                            onClick={() => handleInspectDoc(doc.id)}
                            className="text-xs font-semibold text-brand-600 hover:text-brand-800 inline-flex items-center gap-1"
                          >
                            <span>Inspect Passages</span>
                            <ExternalLink className="w-3 h-3" />
                          </button>

                          {canManage && (
                            <button
                              onClick={() => handleDocDelete(doc.id)}
                              className="p-1.5 text-midnight-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                              title="Delete Document"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* ======================================================== */}
            {/* TAB 2: BRAND GUIDELINES                                  */}
            {/* ======================================================== */}
            {activeTab === "guidelines" && (
              <div className="space-y-4">
                {filteredGuidelines.length === 0 ? (
                  <div className="bg-white p-12 rounded-3xl border border-midnight-100 text-center space-y-2">
                    <BookOpen className="w-10 h-10 text-midnight-300 mx-auto" />
                    <h3 className="text-sm font-bold text-midnight-800">No Brand Guidelines Registered</h3>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {filteredGuidelines.map((gl) => (
                      <div key={gl.id} className="bg-white p-6 rounded-2xl border border-midnight-100 shadow-card space-y-3">
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200">
                            {gl.category.replace("_", " ")}
                          </span>
                          <div className="flex items-center gap-2">
                            <span
                              className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                                gl.severity_level === "critical"
                                  ? "bg-rose-100 text-rose-800"
                                  : "bg-amber-100 text-amber-800"
                              }`}
                            >
                              {gl.severity_level}
                            </span>
                            {canManage && (
                              <button
                                onClick={() => handleDeleteGuideline(gl.id)}
                                className="text-midnight-400 hover:text-rose-600 p-1"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </div>
                        </div>

                        <h3 className="font-bold text-sm text-midnight-950">{gl.title}</h3>
                        <p className="text-xs text-midnight-600 leading-relaxed">{gl.description}</p>

                        {gl.rules && gl.rules.length > 0 && (
                          <div className="pt-2 border-t border-midnight-100/60">
                            <p className="text-[11px] font-bold text-midnight-700 uppercase tracking-wider mb-1.5">
                              Enforced Rules:
                            </p>
                            <ul className="space-y-1 text-xs text-midnight-700">
                              {gl.rules.map((r, i) => (
                                <li key={i} className="flex items-start gap-1.5">
                                  <span className="text-brand-500 font-bold">•</span>
                                  <span>{r}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* ======================================================== */}
            {/* TAB 3: APPROVED FACTS & METRICS                          */}
            {/* ======================================================== */}
            {activeTab === "facts" && (
              <div className="space-y-4">
                {filteredFacts.length === 0 ? (
                  <div className="bg-white p-12 rounded-3xl border border-midnight-100 text-center space-y-2">
                    <CheckSquare className="w-10 h-10 text-midnight-300 mx-auto" />
                    <h3 className="text-sm font-bold text-midnight-800">No Approved Facts Registered</h3>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {filteredFacts.map((fact) => (
                      <div key={fact.id} className="bg-white p-5 rounded-2xl border border-midnight-100 shadow-card flex flex-col justify-between">
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200">
                              {fact.topic}
                            </span>
                            {canManage && (
                              <button onClick={() => handleDeleteFact(fact.id)} className="text-midnight-400 hover:text-rose-600 p-1">
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </div>
                          <p className="text-xs font-semibold text-midnight-900 leading-relaxed mb-3">
                            "{fact.statement}"
                          </p>
                        </div>
                        {fact.reference_url_or_doc && (
                          <div className="pt-2 border-t border-midnight-100 text-[11px] text-midnight-500 flex items-center justify-between">
                            <span>Reference Source:</span>
                            <span className="font-mono text-midnight-700 truncate max-w-[150px]">
                              {fact.reference_url_or_doc}
                            </span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* ======================================================== */}
            {/* TAB 4: RESTRICTED TERMINOLOGY                            */}
            {/* ======================================================== */}
            {activeTab === "terms" && (
              <div className="bg-white rounded-2xl border border-midnight-100 shadow-card overflow-hidden">
                <div className="px-6 py-3 border-b border-midnight-100 bg-lavender-50/50 flex items-center justify-between">
                  <span className="text-xs font-bold text-midnight-800 uppercase tracking-wide">
                    Restricted Terminology Dictionary ({filteredTerms.length})
                  </span>
                  <span className="text-[11px] text-midnight-500">
                    Prohibited phrasing flagged during automated compliance scans
                  </span>
                </div>

                <div className="divide-y divide-midnight-100">
                  {filteredTerms.map((term) => (
                    <div key={term.id} className="p-4 sm:px-6 hover:bg-lavender-50/30 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-xs text-rose-700 bg-rose-50 px-2 py-0.5 rounded-lg border border-rose-200">
                            {term.term}
                          </span>
                          <span className="text-[10px] uppercase font-bold text-midnight-400">
                            [{term.category.replace("_", " ")}]
                          </span>
                        </div>
                        <p className="text-xs text-midnight-600">{term.reason}</p>
                      </div>

                      <div className="flex items-center gap-3 shrink-0">
                        {term.suggested_alternative && (
                          <div className="text-right">
                            <span className="text-[10px] text-midnight-400 block">Recommended Alternative:</span>
                            <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-lg border border-emerald-200 inline-block">
                              {term.suggested_alternative}
                            </span>
                          </div>
                        )}

                        {canManage && (
                          <button
                            onClick={() => handleDeleteTerm(term.id)}
                            className="p-1.5 text-midnight-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg"
                            title="Delete Term"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ======================================================== */}
            {/* TAB 5: BRAND ASSETS & VISUAL STANDARDS                    */}
            {/* ======================================================== */}
            {activeTab === "assets" && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredAssets.map((asset) => (
                  <div key={asset.id} className="bg-white p-6 rounded-2xl border border-midnight-100 shadow-card space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-midnight-950 uppercase tracking-wide">{asset.name}</span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 uppercase">
                        {asset.asset_type.replace("_", " ")}
                      </span>
                    </div>

                    <div className="space-y-2">
                      <span className="text-[11px] font-semibold text-midnight-500 block">Approved Color Palette:</span>
                      <div className="grid grid-cols-4 gap-2">
                        {asset.primary_color_hex && (
                          <div className="text-center">
                            <div className="w-full h-10 rounded-xl shadow-inner border border-midnight-200" style={{ backgroundColor: asset.primary_color_hex }} />
                            <span className="text-[10px] font-mono text-midnight-700 mt-1 block">{asset.primary_color_hex}</span>
                          </div>
                        )}
                        {asset.secondary_color_hex && (
                          <div className="text-center">
                            <div className="w-full h-10 rounded-xl shadow-inner border border-midnight-200" style={{ backgroundColor: asset.secondary_color_hex }} />
                            <span className="text-[10px] font-mono text-midnight-700 mt-1 block">{asset.secondary_color_hex}</span>
                          </div>
                        )}
                        {asset.accent_color_hex && (
                          <div className="text-center">
                            <div className="w-full h-10 rounded-xl shadow-inner border border-midnight-200" style={{ backgroundColor: asset.accent_color_hex }} />
                            <span className="text-[10px] font-mono text-midnight-700 mt-1 block">{asset.accent_color_hex}</span>
                          </div>
                        )}
                        {asset.neutral_color_hex && (
                          <div className="text-center">
                            <div className="w-full h-10 rounded-xl shadow-inner border border-midnight-200" style={{ backgroundColor: asset.neutral_color_hex }} />
                            <span className="text-[10px] font-mono text-midnight-700 mt-1 block">{asset.neutral_color_hex}</span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="pt-3 border-t border-midnight-100 flex items-center justify-between text-xs text-midnight-600">
                      <span>WCAG Contrast Threshold:</span>
                      <span className="font-bold font-mono text-midnight-900">&ge; {asset.wcag_min_contrast || 4.5}:1 (AA)</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      {/* ======================================================== */}
      {/* MODAL: DOCUMENT EXCERPT & CHUNK INSPECTION               */}
      {/* ======================================================== */}
      {inspectDoc && (
        <div className="fixed inset-0 z-50 bg-midnight-950/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-2xl border border-midnight-100 overflow-hidden">
            <div className="px-6 py-4 border-b border-midnight-100 flex items-center justify-between bg-lavender-50/50">
              <div>
                <h3 className="font-bold text-sm text-midnight-950">{inspectDoc.title}</h3>
                <span className="text-[11px] text-midnight-500 font-mono">{inspectDoc.file_name}</span>
              </div>
              <button onClick={() => setInspectDoc(null)} className="p-1 text-midnight-400 hover:text-midnight-900 rounded-lg">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4 text-xs">
              <div>
                <span className="font-bold text-midnight-800 uppercase tracking-wide block mb-1">
                  Extracted Document Text Preview:
                </span>
                <div className="p-3 bg-lavender-50/70 rounded-xl font-mono text-[11px] text-midnight-800 whitespace-pre-wrap max-h-48 overflow-y-auto border border-midnight-100">
                  {inspectDoc.extracted_text_preview || "No preview available."}
                </div>
              </div>

              <div>
                <span className="font-bold text-midnight-800 uppercase tracking-wide block mb-1">
                  Vector Chunks ({inspectDoc.chunks?.length || 0}):
                </span>
                <div className="space-y-2 max-h-56 overflow-y-auto">
                  {inspectDoc.chunks?.map((c: any) => (
                    <div key={c.id} className="p-2.5 rounded-lg border border-midnight-100 bg-white text-[11px]">
                      <span className="font-bold text-brand-600 block mb-0.5">Chunk #{c.chunk_index}:</span>
                      <p className="text-midnight-700">{c.chunk_text}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="px-6 py-3 border-t border-midnight-100 bg-lavender-50/30 flex justify-end">
              <button
                onClick={() => setInspectDoc(null)}
                className="px-4 py-1.5 rounded-xl bg-midnight-900 text-white text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* MODAL: ADD / INGEST KNOWLEDGE ITEM (ADMIN ONLY)          */}
      {/* ======================================================== */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-midnight-950/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-lg w-full shadow-2xl border border-midnight-100 overflow-hidden">
            <div className="px-6 py-4 border-b border-midnight-100 flex items-center justify-between bg-lavender-50/50">
              <h3 className="font-bold text-sm text-midnight-950">
                {activeTab === "documents"
                  ? "Ingest Verified Document"
                  : activeTab === "guidelines"
                  ? "Register Brand Guideline"
                  : activeTab === "facts"
                  ? "Register Approved Fact"
                  : "Add Restricted Term"}
              </h3>
              <button onClick={() => setShowAddModal(false)} className="p-1 text-midnight-400 hover:text-midnight-900">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6">
              {activeTab === "documents" && (
                <form onSubmit={handleDocUpload} className="space-y-4 text-xs">
                  <div>
                    <label className="block font-semibold text-midnight-800 mb-1">Document Title *</label>
                    <input
                      type="text"
                      required
                      value={docTitle}
                      onChange={(e) => setDocTitle(e.target.value)}
                      placeholder="e.g. Acme 2026 Enterprise Security Whitepaper"
                      className="w-full px-3 py-2 rounded-xl border border-midnight-200 text-xs focus:ring-1 focus:ring-brand-500"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block font-semibold text-midnight-800 mb-1">Source Type</label>
                      <select
                        value={docSourceType}
                        onChange={(e) => setDocSourceType(e.target.value)}
                        className="w-full px-3 py-2 rounded-xl border border-midnight-200 text-xs capitalize"
                      >
                        <option value="company_stats">Company Stats</option>
                        <option value="research_report">Research Report</option>
                        <option value="product_spec">Product Spec</option>
                        <option value="policy">Security & Policy</option>
                      </select>
                    </div>

                    <div>
                      <label className="block font-semibold text-midnight-800 mb-1">Version</label>
                      <input
                        type="text"
                        value={docVersion}
                        onChange={(e) => setDocVersion(e.target.value)}
                        className="w-full px-3 py-2 rounded-xl border border-midnight-200 text-xs"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block font-semibold text-midnight-800 mb-1">Validity Expiry Date (Optional)</label>
                    <input
                      type="date"
                      value={docValidity}
                      onChange={(e) => setDocValidity(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl border border-midnight-200 text-xs"
                    />
                  </div>

                  <div>
                    <label className="block font-semibold text-midnight-800 mb-1">Select File (PDF, DOCX, TXT) *</label>
                    <input
                      type="file"
                      required
                      accept=".pdf,.docx,.doc,.txt,.md"
                      onChange={(e) => setDocFile(e.target.files?.[0] || null)}
                      className="w-full text-xs text-midnight-700 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-brand-50 file:text-brand-700 hover:file:bg-brand-100"
                    />
                  </div>

                  <div className="pt-2 flex justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => setShowAddModal(false)}
                      className="px-4 py-2 rounded-xl border border-midnight-200 text-midnight-700 font-semibold text-xs"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={uploading}
                      className="px-4 py-2 rounded-xl bg-midnight-900 text-white font-semibold text-xs flex items-center gap-1.5 disabled:opacity-50"
                    >
                      {uploading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                      <span>{uploading ? "Ingesting..." : "Ingest & Index"}</span>
                    </button>
                  </div>
                </form>
              )}

              {activeTab === "guidelines" && (
                <form onSubmit={handleAddGuideline} className="space-y-4 text-xs">
                  <div>
                    <label className="block font-semibold text-midnight-800 mb-1">Guideline Title *</label>
                    <input
                      type="text"
                      required
                      value={glTitle}
                      onChange={(e) => setGlTitle(e.target.value)}
                      placeholder="e.g. Professional and Direct Tone"
                      className="w-full px-3 py-2 rounded-xl border border-midnight-200 text-xs"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block font-semibold text-midnight-800 mb-1">Category</label>
                      <select
                        value={glCategory}
                        onChange={(e) => setGlCategory(e.target.value)}
                        className="w-full px-3 py-2 rounded-xl border border-midnight-200 text-xs"
                      >
                        <option value="tone_voice">Tone & Voice</option>
                        <option value="policy">Policy & Legal</option>
                        <option value="writing_rules">Writing Rules</option>
                      </select>
                    </div>

                    <div>
                      <label className="block font-semibold text-midnight-800 mb-1">Severity</label>
                      <select
                        value={glSeverity}
                        onChange={(e) => setGlSeverity(e.target.value)}
                        className="w-full px-3 py-2 rounded-xl border border-midnight-200 text-xs"
                      >
                        <option value="critical">Critical</option>
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block font-semibold text-midnight-800 mb-1">Description</label>
                    <textarea
                      rows={2}
                      value={glDesc}
                      onChange={(e) => setGlDesc(e.target.value)}
                      placeholder="Guideline objective and business reasoning..."
                      className="w-full px-3 py-2 rounded-xl border border-midnight-200 text-xs"
                    />
                  </div>

                  <div>
                    <label className="block font-semibold text-midnight-800 mb-1">Specific Rules (One per line)</label>
                    <textarea
                      rows={3}
                      value={glRules}
                      onChange={(e) => setGlRules(e.target.value)}
                      placeholder="Avoid buzzwords&#10;Never guarantee double returns"
                      className="w-full px-3 py-2 rounded-xl border border-midnight-200 text-xs font-mono"
                    />
                  </div>

                  <div className="pt-2 flex justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => setShowAddModal(false)}
                      className="px-4 py-2 rounded-xl border border-midnight-200 text-midnight-700 font-semibold"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={uploading}
                      className="px-4 py-2 rounded-xl bg-midnight-900 text-white font-semibold flex items-center gap-1.5"
                    >
                      {uploading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                      <span>Save Guideline</span>
                    </button>
                  </div>
                </form>
              )}

              {activeTab === "facts" && (
                <form onSubmit={handleAddFact} className="space-y-4 text-xs">
                  <div>
                    <label className="block font-semibold text-midnight-800 mb-1">Topic *</label>
                    <input
                      type="text"
                      required
                      value={factTopic}
                      onChange={(e) => setFactTopic(e.target.value)}
                      placeholder="e.g. Infrastructure, Security, Uptime"
                      className="w-full px-3 py-2 rounded-xl border border-midnight-200 text-xs"
                    />
                  </div>

                  <div>
                    <label className="block font-semibold text-midnight-800 mb-1">Approved Statement *</label>
                    <textarea
                      rows={3}
                      required
                      value={factStatement}
                      onChange={(e) => setFactStatement(e.target.value)}
                      placeholder="e.g. Acme Cloud guarantees 99.99% monthly availability for enterprise tiers."
                      className="w-full px-3 py-2 rounded-xl border border-midnight-200 text-xs"
                    />
                  </div>

                  <div>
                    <label className="block font-semibold text-midnight-800 mb-1">Reference Document / URL</label>
                    <input
                      type="text"
                      value={factRef}
                      onChange={(e) => setFactRef(e.target.value)}
                      placeholder="e.g. SLA Terms 2026.pdf"
                      className="w-full px-3 py-2 rounded-xl border border-midnight-200 text-xs"
                    />
                  </div>

                  <div className="pt-2 flex justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => setShowAddModal(false)}
                      className="px-4 py-2 rounded-xl border border-midnight-200 text-midnight-700 font-semibold"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={uploading}
                      className="px-4 py-2 rounded-xl bg-midnight-900 text-white font-semibold flex items-center gap-1.5"
                    >
                      {uploading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                      <span>Save Fact</span>
                    </button>
                  </div>
                </form>
              )}

              {activeTab === "terms" && (
                <form onSubmit={handleAddTerm} className="space-y-4 text-xs">
                  <div>
                    <label className="block font-semibold text-midnight-800 mb-1">Restricted Term / Phrase *</label>
                    <input
                      type="text"
                      required
                      value={termWord}
                      onChange={(e) => setTermWord(e.target.value)}
                      placeholder="e.g. game-changer, 100% risk-free"
                      className="w-full px-3 py-2 rounded-xl border border-midnight-200 text-xs"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block font-semibold text-midnight-800 mb-1">Category</label>
                      <select
                        value={termCategory}
                        onChange={(e) => setTermCategory(e.target.value)}
                        className="w-full px-3 py-2 rounded-xl border border-midnight-200 text-xs"
                      >
                        <option value="unverified_superlative">Unverified Superlative</option>
                        <option value="false_guarantee">False Guarantee</option>
                        <option value="prohibited_slogan">Prohibited Slogan</option>
                        <option value="buzzword">Buzzword</option>
                      </select>
                    </div>

                    <div>
                      <label className="block font-semibold text-midnight-800 mb-1">Severity</label>
                      <select
                        value={termSeverity}
                        onChange={(e) => setTermSeverity(e.target.value)}
                        className="w-full px-3 py-2 rounded-xl border border-midnight-200 text-xs"
                      >
                        <option value="critical">Critical</option>
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block font-semibold text-midnight-800 mb-1">Suggested Compliant Alternative</label>
                    <input
                      type="text"
                      value={termAlt}
                      onChange={(e) => setTermAlt(e.target.value)}
                      placeholder="e.g. industry-leading, verified by SLA"
                      className="w-full px-3 py-2 rounded-xl border border-midnight-200 text-xs"
                    />
                  </div>

                  <div>
                    <label className="block font-semibold text-midnight-800 mb-1">Reason / Policy Reference</label>
                    <input
                      type="text"
                      value={termReason}
                      onChange={(e) => setTermReason(e.target.value)}
                      placeholder="e.g. Creates legal exposure without proof"
                      className="w-full px-3 py-2 rounded-xl border border-midnight-200 text-xs"
                    />
                  </div>

                  <div className="pt-2 flex justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => setShowAddModal(false)}
                      className="px-4 py-2 rounded-xl border border-midnight-200 text-midnight-700 font-semibold"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={uploading}
                      className="px-4 py-2 rounded-xl bg-midnight-900 text-white font-semibold flex items-center gap-1.5"
                    >
                      {uploading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                      <span>Save Restricted Term</span>
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
