from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class AdminOverviewOut(BaseModel):
    total_users: int
    total_organizations: int
    total_submissions: int
    pending_reviews: int
    approved_publications: int
    rejected_submissions: int
    average_compliance_score: float


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    role: str
    organization_id: str
    organization_name: Optional[str] = None
    is_active: bool
    created_at: datetime


class AdminUserCreate(BaseModel):
    email: str
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2)
    role: str = Field("creator", description="Role: creator, reviewer, admin")
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None


class AdminUserRoleUpdate(BaseModel):
    role: str = Field(..., description="Role: creator, reviewer, admin")


class AdminUserStatusUpdate(BaseModel):
    is_active: bool


class AdminOrgOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    industry: Optional[str] = None
    user_count: int = 0
    submission_count: int = 0
    guidelines_count: int = 0
    created_at: datetime


class AdminOrgCreate(BaseModel):
    name: str = Field(..., min_length=2)
    industry: Optional[str] = "Enterprise Software"


class AdminActivityItem(BaseModel):
    id: str
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime


class AdminSystemHealth(BaseModel):
    database_connected: bool
    database_type: str
    total_records: Dict[str, int]
    environment: str
    version: str
