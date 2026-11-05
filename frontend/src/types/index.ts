export type UserRole = "creator" | "reviewer" | "admin";

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
  created_at: string;
  updated_at: string;
}
