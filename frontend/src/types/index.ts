export type UserRole = "creator" | "reviewer" | "admin" | "compliance_officer";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  organization_id: string;
  organization_name?: string;
  is_active: boolean;
  created_at: string;
}

export interface KnowledgeDocument {
  id: string;
  title: string;
  source_type: string;
  file_name: string;
  file_size_bytes?: number;
  version: string;
  approval_status: string;
  effective_date?: string;
  validity_date?: string;
  is_expired?: boolean;
  chunks_count: number;
  created_at: string;
}

export interface ExtractedClaim {
  id: string;
  claim_text: string;
  claim_type: string;
  verification_status: "supported" | "unsupported" | "conflicting" | "outdated" | "unverified";
  severity: "critical" | "high" | "medium" | "low";
  confidence: number;
  explanation: string;
  source_document_name?: string;
  source_passage?: string;
  source_validity_date?: string;
  suggested_correction?: string;
  recommended_action?: string;
}

export interface EvidenceGraphData {
  nodes: Array<{
    id: string;
    type: "submission" | "claim" | "knowledge_source";
    label: string;
    status: string;
    severity?: string;
    data?: any;
  }>;
  links: Array<{
    id: string;
    source: string;
    target: string;
    relationship: string;
    status?: string;
  }>;
  stats: {
    total_nodes: number;
    total_links: number;
    supported_claims: number;
    unsupported_claims: number;
    conflicting_claims: number;
    outdated_claims: number;
  };
}

export interface VisualAnalysisReport {
  report_id: string;
  submission_id?: string;
  filename?: string;
  dimensions: string;
  aspect_ratio: string;
  visual_score: number;
  wcag_compliance: "AAA_PASS" | "AA_PASS" | "FAIL";
  contrast_ratio: number;
  contrast_details?: {
    ratio: number;
    min_required: number;
    primary_bg: string;
    primary_fg: string;
  };
  palette_match_score: number;
  dominant_colors: Array<{
    hex: string;
    rgb: [number, number, number];
    percent: number;
  }>;
  palette_deviations: Array<{
    detected_hex: string;
    coverage_percent: number;
    closest_distance: number;
    severity: string;
    message: string;
  }>;
  alt_text_evaluation: {
    score: number;
    verdict: string;
    provided_alt?: string;
    issues: string[];
    suggestion: string;
  };
  logo_status: string;
  ocr_extracted_text?: string;
  visual_issues: Array<{
    type: string;
    severity: string;
    title: string;
    explanation: string;
    suggestion: string;
  }>;
  created_at?: string;
}

export interface AuditLogItem {
  id: string;
  action: string;
  entity_type: string;
  entity_id?: string;
  actor_id?: string;
  actor_email: string;
  actor_name: string;
  actor_role: string;
  details?: Record<string, any>;
  timestamp: string;
}

export type SubmissionStatus =
  | "draft"
  | "submitted"
  | "analyzing"
  | "analysis_complete"
  | "pending_review"
  | "changes_requested"
  | "rejected"
  | "approved"
  | "published";

export type ContentCategory =
  | "social_media"
  | "advertisement"
  | "marketing_email"
  | "blog"
  | "website"
  | "business_document";

export type IssueSeverity = "critical" | "high" | "medium" | "low";

export type IssueModule =
  | "brand_voice"
  | "fact_checker"
  | "restricted_language"
  | "marketing_claim"
  | "visual_brand"
  | "accessibility";

export type IssueCategory =
  | "confidentiality"
  | "privacy"
  | "misleading_claim"
  | "unnecessary_content"
  | "brand_voice"
  | "security_technical";

export type RecommendedAction = "Replace" | "Remove" | "Shorten" | "Verify" | "Review";

export interface DetectedIssue {
  id: string;
  module: IssueModule | string;
  category?: IssueCategory | string;
  severity: IssueSeverity;
  issue_type: string;
  matched_text: string;
  char_start?: number;
  char_end?: number;
  explanation: string;
  guideline_reference: string;
  confidence: number;
  recommended_action?: RecommendedAction | string;
  detection_source?: string;
  suggested_replacement?: string;
  rationale?: string;
  is_resolved?: boolean;
  is_dismissed?: boolean;
  dismiss_reason?: string;
}

export interface AnalysisReport {
  id: string;
  submission_id: string;
  version_id: string;
  engine_mode: "hybrid_gemini" | "deterministic_fallback";
  compliance_score: number;
  compliance_rating: "compliant" | "needs_review" | "high_risk" | "critical_violations";
  brand_compliance_score?: number;
  evidence_confidence_score?: number;
  content_quality_score?: number;
  publication_risk?: "low" | "medium" | "high" | "critical";
  score_breakdown?: {
    brand_deductions?: Array<{ issue: string; severity: string; penalty: number; reason: string }>;
    evidence_deductions?: Array<{ claim: string; status: string; penalty: number; reason: string }>;
    quality_deductions?: Array<{ metric: string; penalty: number; reason: string }>;
    formula?: string;
  };
  total_issues: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  summary_verdict: string;
  issues: DetectedIssue[];
  execution_duration_ms: number;
  created_at: string;
}

export interface ContentVersion {
  id: string;
  submission_id?: string;
  version_number: number;
  content_body: string;
  change_summary?: string;
  created_at?: string;
}

export interface ContentSubmission {
  id: string;
  title: string;
  category: ContentCategory;
  target_platform?: string;
  campaign_name?: string;
  description?: string;
  status: SubmissionStatus;
  current_version_id?: string;
  current_content?: string;
  creator_id: string;
  creator_name?: string;
  versions?: ContentVersion[];
  latest_report?: AnalysisReport;
  latest_review_feedback?: string;
  latest_reviewer_name?: string;
  created_at: string;
  updated_at: string;
}
