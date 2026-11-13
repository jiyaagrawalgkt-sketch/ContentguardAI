import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import get_current_user, require_admin, require_any_authenticated
from app.models.user import User
from app.models.brand_knowledge import BrandGuideline, ApprovedFact, RestrictedTerm, BrandAsset, BrandMemory
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
# Admin Management Endpoints for Guidelines, Facts & Terms
# -------------------------------------------------------------
@router.post("/guidelines", status_code=status.HTTP_201_CREATED, summary="Create Brand Guideline")
def create_brand_guideline(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    guideline = BrandGuideline(
        id=str(uuid.uuid4()),
        organization_id=current_user.organization_id,
        category=payload.get("category", "tone_voice"),
        title=payload.get("title", "Brand Guideline"),
        description=payload.get("description", ""),
        rules=payload.get("rules", []),
        severity_level=payload.get("severity_level", "medium"),
        is_active=True
    )
    db.add(guideline)
    db.commit()
    db.refresh(guideline)
    return {"id": guideline.id, "title": guideline.title, "message": "Guideline created successfully."}


@router.delete("/guidelines/{guideline_id}", summary="Delete Brand Guideline")
def delete_brand_guideline(
    guideline_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    g = db.query(BrandGuideline).filter(
        BrandGuideline.id == guideline_id,
        BrandGuideline.organization_id == current_user.organization_id
    ).first()
    if not g:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guideline not found")
    db.delete(g)
    db.commit()
    return {"message": "Guideline deleted successfully."}


@router.post("/facts", status_code=status.HTTP_201_CREATED, summary="Create Approved Fact")
def create_approved_fact(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    fact = ApprovedFact(
        id=str(uuid.uuid4()),
        organization_id=current_user.organization_id,
        topic=payload.get("topic", "Company Fact"),
        statement=payload.get("statement", ""),
        verified_numbers=payload.get("verified_numbers", {}),
        reference_url_or_doc=payload.get("reference_url_or_doc", ""),
        is_active=True
    )
    db.add(fact)
    db.commit()
    db.refresh(fact)
    return {"id": fact.id, "statement": fact.statement, "message": "Fact registered successfully."}


@router.delete("/facts/{fact_id}", summary="Delete Approved Fact")
def delete_approved_fact(
    fact_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    f = db.query(ApprovedFact).filter(
        ApprovedFact.id == fact_id,
        ApprovedFact.organization_id == current_user.organization_id
    ).first()
    if not f:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approved fact not found")
    db.delete(f)
    db.commit()
    return {"message": "Fact deleted successfully."}


@router.post("/terms", status_code=status.HTTP_201_CREATED, summary="Create Restricted Term")
def create_restricted_term(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    term = RestrictedTerm(
        id=str(uuid.uuid4()),
        organization_id=current_user.organization_id,
        term=payload.get("term", ""),
        category=payload.get("category", "unverified_superlative"),
        severity=payload.get("severity", "high"),
        suggested_alternative=payload.get("suggested_alternative", ""),
        reason=payload.get("reason", "Violates brand communication policy"),
        is_active=True
    )
    db.add(term)
    db.commit()
    db.refresh(term)
    return {"id": term.id, "term": term.term, "message": "Restricted term saved successfully."}


@router.delete("/terms/{term_id}", summary="Delete Restricted Term")
def delete_restricted_term(
    term_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    t = db.query(RestrictedTerm).filter(
        RestrictedTerm.id == term_id,
        RestrictedTerm.organization_id == current_user.organization_id
    ).first()
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restricted term not found")
    db.delete(t)
    db.commit()
    return {"message": "Restricted term deleted successfully."}


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


@router.delete("/assets/{asset_id}", summary="Delete Brand Asset")
def delete_brand_asset(
    asset_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    a = db.query(BrandAsset).filter(
        BrandAsset.id == asset_id,
        BrandAsset.organization_id == current_user.organization_id
    ).first()
    if not a:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand asset not found")
    db.delete(a)
    db.commit()
    return {"message": "Brand asset deleted successfully."}


@router.get("/memory", summary="Get Organization Brand Memory & Learning")
def get_brand_memory(
    current_user: User = Depends(require_any_authenticated),
    db: Session = Depends(get_db)
):
    """Retrieves accumulated reviewer feedback, preferred phrases, and false-positive exemptions."""
    records = db.query(BrandMemory).filter(
        BrandMemory.organization_id == current_user.organization_id
    ).order_by(BrandMemory.created_at.desc()).all()

    return [
        {
            "id": r.id,
            "feedback_type": r.feedback_type,
            "original_phrase": r.original_phrase,
            "preferred_phrase": r.preferred_phrase,
            "notes": r.notes,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]


@router.post("/memory", summary="Record Reviewer Feedback / Custom Preference")
def record_brand_memory(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(require_any_authenticated),
    db: Session = Depends(get_db)
):
    """Saves reviewer feedback (e.g. false positive, preferred wording) into organization brand memory."""
    mem = BrandMemory(
        id=str(uuid.uuid4()),
        organization_id=current_user.organization_id,
        feedback_type=payload.get("feedback_type", "preferred_wording"),
        original_phrase=payload.get("original_phrase", "").strip(),
        preferred_phrase=payload.get("preferred_phrase", "").strip() or None,
        notes=payload.get("notes", "").strip() or None,
        created_by_user_id=current_user.id
    )
    db.add(mem)
    db.commit()
    db.refresh(mem)

    return {
        "id": mem.id,
        "message": "Feedback recorded in brand memory successfully.",
        "feedback_type": mem.feedback_type
    }


@router.delete("/memory/{memory_id}", summary="Delete Brand Memory Entry")
def delete_brand_memory(
    memory_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    mem = db.query(BrandMemory).filter(
        BrandMemory.id == memory_id,
        BrandMemory.organization_id == current_user.organization_id
    ).first()
    if not mem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    db.delete(mem)
    db.commit()
    return {"message": "Memory entry deleted successfully."}

