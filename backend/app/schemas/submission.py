from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class SubmissionCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    category: str = Field("marketing_email", description="social_media, advertisement, marketing_email, blog, website, business_document")
    target_platform: Optional[str] = Field(None, max_length=100)
    campaign_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    content: str = Field(..., min_length=5, description="Initial draft content text")


class SubmissionUpdateContent(BaseModel):
    content: str = Field(..., min_length=5)
    change_summary: Optional[str] = Field("Manual content update", max_length=255)


class VersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    version_number: int
    content_body: str
    change_summary: Optional[str] = None
    created_at: datetime


class DetectedIssueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    module: str
    category: Optional[str] = "brand_voice"
    severity: str
    issue_type: str
    matched_text: str
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    explanation: str
    guideline_reference: str
    confidence: float
    recommended_action: Optional[str] = "Replace"
    detection_source: Optional[str] = "Rule Engine"
    suggested_replacement: Optional[str] = None
    rationale: Optional[str] = None
    is_resolved: bool = False
    is_dismissed: bool = False
    dismiss_reason: Optional[str] = None


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    version_id: str
    engine_mode: str
    compliance_score: float
    compliance_rating: str
    total_issues: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    summary_verdict: Optional[str] = None
    issues: List[DetectedIssueOut] = []
    created_at: datetime


class SubmissionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    category: str
    target_platform: Optional[str] = None
    campaign_name: Optional[str] = None
    status: str
    compliance_score: Optional[float] = None
    compliance_rating: Optional[str] = None
    creator_name: Optional[str] = None
    version_count: int = 1
    created_at: datetime
    updated_at: datetime


class SubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    category: str
    target_platform: Optional[str] = None
    campaign_name: Optional[str] = None
    description: Optional[str] = None
    status: str
    current_version_id: Optional[str] = None
    current_content: str = ""
    creator_id: Optional[str] = None
    creator_name: Optional[str] = None
    versions: List[VersionOut] = []
    latest_report: Optional[ReportOut] = None
    latest_review_feedback: Optional[str] = None
    latest_reviewer_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
