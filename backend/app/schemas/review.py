from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class ReviewDecisionRequest(BaseModel):
    decision: str = Field(..., description="approved, rejected, or changes_requested")
    comment: str = Field(..., min_length=2, description="Review feedback or modification instructions")


class ReviewCommentCreate(BaseModel):
    comment_text: str = Field(..., min_length=2)


class ReviewCommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    reviewer_name: str
    comment_text: str
    created_at: datetime


class ApprovalRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    reviewer_name: str
    decision: str
    feedback_reason: str
    compliance_score_at_approval: Optional[float] = None
    created_at: datetime


class PublishedContentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    public_preview_token: str
    published_by_name: str
    published_at: datetime
    final_content_snapshot: str
    compliance_score: float
    title: str
    category: str
