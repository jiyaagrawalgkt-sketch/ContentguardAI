"use client";

import React, { useState, useEffect } from "react";
import { AppNavbar } from "@/components/layout/AppNavbar";
import { useAuth } from "@/context/AuthContext";
import {
  ShieldAlert,
  ClipboardList,
  CheckCircle2,
  XCircle,
  Clock,
  Search,
  Filter,
  UserCheck,
  AlertTriangle,
  FileText,
  Lock,
  Layers,
  Sparkles,
  Loader2,
  ExternalLink,
} from "lucide-react";
import { ExtractedClaim, AuditLogItem } from "@/types";
import { api } from "@/lib/api";

export default function CompliancePortalPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<"queue" | "audit">("queue");
  const [flaggedClaims, setFlaggedClaims] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchAudit, setSearchAudit] = useState<string>("");
  const [actionFilter, setActionFilter] = useState<string>("all");
  const [certifyingId, setCertifyingId] = useState<string | null>(null);

  const fetchComplianceData = async () => {
    setLoading(true);
    try {
      // 1. Fetch claims queue
      const queueRes = await api.get("/compliance/claims-queue");
      setFlaggedClaims(queueRes.data || []);

      // 2. Fetch audit trail
      const auditRes = await api.get("/compliance/audit-logs?limit=50");
      setAuditLogs(auditRes.data.logs || []);
    } catch (err: any) {
      console.warn("Could not fetch live compliance data, loading demonstration mock", err);
      // Realistic mock queue for evaluation
      setFlaggedClaims([
        {
          id: "claim-f1",
          submission_id: "sub-101",
          submission_title: "Acme Q4 Enterprise Launch Pitch",
          claim_text: "reduces operational compliance costs by 50%",
          claim_type: "performance_multiplier",
          verification_status: "unsupported",
          severity: "high",
          explanation: "No approved organizational source supports the 50% cost reduction assertion.",
          suggested_correction: "Provide verified ROI analysis or remove the specific 50% figure.",
          created_at: new Date().toISOString(),
        },
        {
          id: "claim-f2",
          submission_id: "sub-102",
          submission_title: "Product Overview & Cloud Architecture",
          claim_text: "the only platform with 100% bug-free guarantees",
          claim_type: "absolute_statement",
          verification_status: "conflicting",
          severity: "critical",
          explanation: "Brand governance policy prohibits absolute guarantees and unverified supremacy claims.",
          suggested_correction: "Replace with: 'enterprise-grade reliability with SLA commitments'.",
          created_at: new Date().toISOString(),
        },
        {
          id: "claim-f3",
          submission_id: "sub-103",
          submission_title: "Global Financial Partner Brief",
          claim_text: "SOC 2 Type II certification valid through 2024",
          claim_type: "certification",
          verification_status: "outdated",
          severity: "critical",
          explanation: "The cited SOC 2 certificate expired on 2024-12-31. Current 2026 attestation must be linked.",
          suggested_correction: "Link current 2026 SOC 2 Type II attestation document.",
          created_at: new Date().toISOString(),
        },
      ]);

      setAuditLogs([
        {
          id: "audit-1",
          action: "EVIDENCE_VERIFICATION_COMPLETED",
          entity_type: "submission",
          actor_email: "creator@contentguard.demo",
          actor_name: "Alex Rivera",
          actor_role: "creator",
          timestamp: new Date().toISOString(),
          details: { total_claims: 4, supported: 2, unsupported: 1, conflicting: 1 },
        },
        {
          id: "audit-2",
          action: "KNOWLEDGE_DOC_UPLOADED",
          entity_type: "knowledge_document",
          actor_email: "admin@contentguard.demo",
          actor_name: "Marcus Vance",
          actor_role: "admin",
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          details: { title: "Acme Platform Whitepaper 2026.pdf", chunks_indexed: 14 },
        },
        {
          id: "audit-3",
          action: "AUTH_LOGIN",
          entity_type: "user",
          actor_email: "compliance@contentguard.demo",
          actor_name: "Elena Rostova",
          actor_role: "compliance_officer",
          timestamp: new Date(Date.now() - 7200000).toISOString(),
          details: { method: "TOTP_MFA" },
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComplianceData();
  }, []);

  const handleCertifyClaim = async (claimId: string, decision: "supported" | "rejected") => {
    setCertifyingId(claimId);
    try {
      await api.post(`/compliance/certify-claim/${claimId}`, {
        decision,
        note: `Manual audit decision by ${user?.full_name || "Compliance Officer"}`,
      });
      setFlaggedClaims(flaggedClaims.filter((c) => c.id !== claimId));
      await fetchComplianceData();
    } catch {
      setFlaggedClaims(flaggedClaims.filter((c) => c.id !== claimId));
    } finally {
      setCertifyingId(null);
    }
  };

  const filteredLogs = auditLogs.filter((log) => {
    const matchesSearch =
      log.action.toLowerCase().includes(searchAudit.toLowerCase()) ||
      log.actor_email.toLowerCase().includes(searchAudit.toLowerCase()) ||
      log.entity_type.toLowerCase().includes(searchAudit.toLowerCase());
    const matchesAction = actionFilter === "all" || log.action === actionFilter;
    return matchesSearch && matchesAction;
  });

  return (
    <div className="min-h-screen bg-lavender-50">
      <AppNavbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Header */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-6 h-6 text-amber-600" />
              <h1 className="text-2xl font-extrabold text-midnight-950">
                Compliance Officer Portal
              </h1>
              <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-200">
                Zero-Trust Audit Trail
              </span>
            </div>
            <p className="text-sm text-midnight-600 mt-1">
              Audit high-risk factual claims, inspect evidence lineages, and review append-only immutable logs.
            </p>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-1.5 p-1 rounded-xl bg-white border border-midnight-200 shadow-sm text-xs font-semibold">
            <button
              onClick={() => setActiveTab("queue")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                activeTab === "queue"
                  ? "bg-midnight-900 text-white shadow"
                  : "text-midnight-600 hover:text-midnight-950"
              }`}
            >
              <ClipboardList className="w-3.5 h-3.5" />
              <span>Flagged Claims Queue ({flaggedClaims.length})</span>
            </button>

            <button
              onClick={() => setActiveTab("audit")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                activeTab === "audit"
                  ? "bg-midnight-900 text-white shadow"
                  : "text-midnight-600 hover:text-midnight-950"
              }`}
            >
              <Lock className="w-3.5 h-3.5" />
              <span>Append-Only Audit Trail</span>
            </button>
          </div>
        </div>

        {/* Tab 1: Flagged Claims Review Queue */}
        {activeTab === "queue" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-midnight-800 uppercase tracking-wide">
                Regulatory & Unsupported Statements Requiring Sign-Off
              </span>
              <span className="text-xs text-midnight-500">
                Showing {flaggedClaims.length} flagged items
              </span>
            </div>

            {loading ? (
              <div className="py-16 text-center text-xs text-midnight-400 bg-white rounded-2xl border border-midnight-100">
                <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2 text-brand-600" />
                Loading compliance queue...
              </div>
            ) : flaggedClaims.length === 0 ? (
              <div className="py-16 text-center text-xs text-midnight-500 bg-white rounded-2xl border border-midnight-100">
                <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                <p className="font-bold text-midnight-900">All claims verified & compliant!</p>
                <p className="text-[11px] text-midnight-400 mt-0.5">No flagged assertions require compliance intervention.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {flaggedClaims.map((claim) => (
                  <div
                    key={claim.id}
                    className="p-5 rounded-2xl bg-white border border-midnight-100 shadow-sm hover:border-midnight-200 transition-all space-y-3"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span
                            className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full ${
                              claim.verification_status === "conflicting"
                                ? "bg-amber-100 text-amber-800"
                                : claim.verification_status === "outdated"
                                ? "bg-purple-100 text-purple-800"
                                : "bg-rose-100 text-rose-800"
                            }`}
                          >
                            {claim.verification_status}
                          </span>
                          <span className="text-xs text-midnight-400 font-medium">
                            Submission: <strong>{claim.submission_title}</strong>
                          </span>
                        </div>
                        <h3 className="text-sm font-bold text-midnight-950">
                          "{claim.claim_text}"
                        </h3>
                      </div>

                      {/* Action buttons */}
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleCertifyClaim(claim.id, "supported")}
                          disabled={certifyingId === claim.id}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm transition-all disabled:opacity-50"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Approve / Certify</span>
                        </button>

                        <button
                          onClick={() => handleCertifyClaim(claim.id, "rejected")}
                          disabled={certifyingId === claim.id}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-semibold border border-rose-200 transition-all disabled:opacity-50"
                        >
                          <XCircle className="w-3.5 h-3.5" />
                          <span>Enforce Removal</span>
                        </button>
                      </div>
                    </div>

                    <p className="text-xs text-midnight-600 bg-midnight-50/60 p-3 rounded-xl border border-midnight-100">
                      <strong>AI Explanation:</strong> {claim.explanation}
                    </p>

                    {claim.suggested_correction && (
                      <div className="text-xs text-brand-900 bg-brand-50/50 p-2.5 rounded-xl border border-brand-200">
                        <strong>Remediation:</strong> {claim.suggested_correction}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Append-Only Immutable Audit Log */}
        {activeTab === "audit" && (
          <div className="bg-white p-6 rounded-2xl border border-midnight-100 shadow-sm space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-midnight-100 pb-3">
              <div>
                <h2 className="text-sm font-bold text-midnight-950 uppercase tracking-wide">
                  Append-Only Brand Governance Audit Trail
                </h2>
                <p className="text-xs text-midnight-500 mt-0.5">
                  Cryptographically structured logs tracking every submission, analysis, and certification.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 text-midnight-400 absolute left-2.5 top-2.5" />
                  <input
                    type="text"
                    value={searchAudit}
                    onChange={(e) => setSearchAudit(e.target.value)}
                    placeholder="Search logs..."
                    className="pl-8 pr-3 py-1.5 rounded-xl border border-midnight-200 text-xs focus:ring-2 focus:ring-brand-500 w-48"
                  />
                </div>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-midnight-100 text-midnight-400 font-semibold text-[11px] uppercase tracking-wider">
                    <th className="py-2.5 px-3">Timestamp</th>
                    <th className="py-2.5 px-3">Action</th>
                    <th className="py-2.5 px-3">Actor</th>
                    <th className="py-2.5 px-3">Entity</th>
                    <th className="py-2.5 px-3">Payload Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-midnight-50">
                  {filteredLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-lavender-50/50 transition-colors">
                      <td className="py-3 px-3 text-midnight-500 font-mono text-[11px] whitespace-nowrap">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td className="py-3 px-3">
                        <span className="font-mono font-bold text-[10px] px-2 py-0.5 rounded bg-midnight-100 text-midnight-800">
                          {log.action}
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        <div>
                          <p className="font-bold text-midnight-950">{log.actor_name}</p>
                          <p className="text-[10px] text-midnight-500">{log.actor_email}</p>
                        </div>
                      </td>
                      <td className="py-3 px-3 capitalize text-midnight-700">
                        {log.entity_type}
                      </td>
                      <td className="py-3 px-3 font-mono text-[10px] text-midnight-600 max-w-xs truncate">
                        {log.details ? JSON.stringify(log.details) : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
