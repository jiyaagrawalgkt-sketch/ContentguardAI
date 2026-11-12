import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import get_current_user, require_admin, require_any_authenticated
from app.models.user import User
from app.models.brand_knowledge import BrandGuideline, ApprovedFact, RestrictedTerm, BrandAsset
from app.models.audit import AuditLog

router = APIRouter()


@router.get("/summary", summary="Get Active Brand Knowledge Rules Summary")
def get_brand_knowledge_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the organization's active brand governance rules:
    - Official brand voice & style guidelines
    - Approved factual specifications
    - Restricted terminology dictionary
    """
    guidelines = db.query(BrandGuideline).filter(
        BrandGuideline.organization_id == current_user.organization_id,
        BrandGuideline.is_active == True
    ).all()

    facts = db.query(ApprovedFact).filter(
        ApprovedFact.organization_id == current_user.organization_id,
        ApprovedFact.is_active == True
    ).all()

    terms = db.query(RestrictedTerm).filter(
        RestrictedTerm.organization_id == current_user.organization_id,
        RestrictedTerm.is_active == True
    ).all()

    return {
        "organization_id": current_user.organization_id,
        "guidelines": [
            {
                "id": g.id,
                "category": g.category,
                "title": g.title,
                "description": g.description,
                "rules": g.rules,
                "severity_level": g.severity_level
            }
            for g in guidelines
        ],
        "approved_facts": [
            {
                "id": f.id,
                "topic": f.topic,
                "statement": f.statement,
                "verified_numbers": f.verified_numbers,
                "reference_url_or_doc": f.reference_url_or_doc
            }
            for f in facts
        ],
        "restricted_terms": [
            {
                "id": t.id,
                "term": t.term,
                "category": t.category,
                "severity": t.severity,
                "suggested_alternative": t.suggested_alternative,
                "reason": t.reason
            }
            for t in terms
        ]
    }


# -------------------------------------------------------------
# Brand Asset Library Endpoints (Multimodal Brand Intelligence)
# -------------------------------------------------------------
@router.get("/assets", summary="List Organization Brand Assets")
def list_brand_assets(
    current_user: User = Depends(require_any_authenticated),
    db: Session = Depends(get_db)
):
    """Retrieve official logos, color palettes, and typography assets for organization."""
    assets = db.query(BrandAsset).filter(
        BrandAsset.organization_id == current_user.organization_id,
        BrandAsset.is_active == True
    ).all()

    return [
        {
            "id": a.id,
            "name": a.name,
            "asset_type": a.asset_type,
            "primary_color_hex": a.primary_color_hex,
            "secondary_color_hex": a.secondary_color_hex,
            "accent_color_hex": a.accent_color_hex,
            "neutral_color_hex": a.neutral_color_hex,
            "color_palette_json": a.color_palette_json,
            "wcag_min_contrast": a.wcag_min_contrast,
            "file_path": a.file_path,
            "rules_json": a.rules_json,
            "is_active": a.is_active,
        }
        for a in assets
    ]


@router.post("/assets", status_code=status.HTTP_201_CREATED, summary="Create or Update Brand Asset")
def create_or_update_brand_asset(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Register official brand logo, color palette, or typography guidelines."""
    asset_id = payload.get("id") or str(uuid.uuid4())
    existing = None
    if payload.get("id"):
        existing = db.query(BrandAsset).filter(
            BrandAsset.id == payload.get("id"),
            BrandAsset.organization_id == current_user.organization_id
        ).first()

    if existing:
        existing.name = payload.get("name", existing.name)
        existing.asset_type = payload.get("asset_type", existing.asset_type)
        existing.primary_color_hex = payload.get("primary_color_hex", existing.primary_color_hex)
        existing.secondary_color_hex = payload.get("secondary_color_hex", existing.secondary_color_hex)
        existing.neutral_color_hex = payload.get("neutral_color_hex", existing.neutral_color_hex)
        existing.accent_color_hex = payload.get("accent_color_hex", existing.accent_color_hex)
        existing.color_palette_json = payload.get("color_palette_json", existing.color_palette_json)
        existing.wcag_min_contrast = payload.get("wcag_min_contrast", existing.wcag_min_contrast)
        existing.rules_json = payload.get("rules_json", existing.rules_json)
        db.commit()
        db.refresh(existing)
        target = existing
    else:
        new_asset = BrandAsset(
            id=asset_id,
            organization_id=current_user.organization_id,
            name=payload.get("name", "Brand Asset"),
            asset_type=payload.get("asset_type", "color_palette"),
            primary_color_hex=payload.get("primary_color_hex", "#0B0F19"),
            secondary_color_hex=payload.get("secondary_color_hex", "#6366F1"),
            neutral_color_hex=payload.get("neutral_color_hex", "#FFFFFF"),
            accent_color_hex=payload.get("accent_color_hex", "#FAF9FF"),
            color_palette_json=payload.get("color_palette_json", []),
            wcag_min_contrast=float(payload.get("wcag_min_contrast", 4.5)),
            rules_json=payload.get("rules_json", {}),
            is_active=True
        )
        db.add(new_asset)
        db.commit()
        db.refresh(new_asset)
        target = new_asset

    # Audit log
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="BRAND_ASSET_UPDATED",
        entity_type="brand_asset",
        entity_id=target.id,
        details={"name": target.name, "type": target.asset_type}
    )
    db.add(audit)
    db.commit()

    return {
        "id": target.id,
        "name": target.name,
        "asset_type": target.asset_type,
        "primary_color_hex": target.primary_color_hex,
        "secondary_color_hex": target.secondary_color_hex,
        "message": f"Brand asset '{target.name}' updated successfully."
    }
