#!/usr/bin/env python3
"""
SYP Team Effectiveness Lab — PDF Profile API Server
Endpoints:
  POST /generate               — individual participant PDF
  POST /generate-manager-report — team manager diagnostic report PDF
"""

import os, base64, json
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Optional, List

from generate_syp_profiles_improved import generate_profile_bytes, ARCHETYPES
from generate_manager_report import generate_manager_report_bytes

app = FastAPI(
    title="SYP Profile Generator API",
    description="Generates Team Effectiveness Lab PDFs — participant profiles and manager reports",
    version="1.1.0",
)

# ─── Individual profile models ───────────────────────────────────────────────────

class ProfileRequest(BaseModel):
    archetype: str = Field(..., description="Archetype key: operator, architect, navigator, signal, anchor, ember")
    participant_name: str = Field(..., description="Participant's full name")
    company: str = Field("", description="Company name")
    comm_score: int = Field(..., ge=0, description="Communication score 0-100")
    decision_score: int = Field(..., ge=0, description="Decision Making score 0-100")
    collab_score: int = Field(..., ge=0, description="Collaboration score 0-100")
    response_format: Optional[str] = Field("binary", description="'binary' returns raw PDF, 'base64' returns JSON with base64-encoded PDF")

# ─── Manager report models ────────────────────────────────────────────────────────

class ManagerReportParticipant(BaseModel):
    name: str = Field(..., description="Participant full name")
    archetype: str = Field(..., description="Archetype: Architect, Navigator, Anchor, Signal, Operator, Ember")
    comm_score: int = Field(..., ge=0, le=100, description="Communication score 0-100")
    decision_score: int = Field(..., ge=0, le=100, description="Decision Making score 0-100")
    collab_score: int = Field(..., ge=0, le=100, description="Collaboration score 0-100")

class ManagerReportRequest(BaseModel):
    manager_name: str = Field(..., description="Manager's full name (e.g. Sarah Mitchell)")
    company: str = Field(..., description="Company name (e.g. AED Global)")
    workshop_date: str = Field(..., description="Workshop date string (e.g. 6 May 2026)")
    participants: List[ManagerReportParticipant] = Field(..., description="Array of participant results")

# ─── Health check ────────────────────────────────────────────────────────────────

@app.get("/")
def health():
    return {
        "status": "ok",
        "service": "SYP Profile Generator",
        "archetypes": list(ARCHETYPES.keys()),
        "endpoints": ["/generate", "/generate-manager-report"],
    }

# ─── Individual participant profile ──────────────────────────────────────────────

@app.post("/generate")
def generate(req: ProfileRequest):
    key = req.archetype.lower().strip()
    if key not in ARCHETYPES:
        raise HTTPException(status_code=400, detail=f"Unknown archetype '{key}'. Valid: {list(ARCHETYPES.keys())}")

    comm     = min(max(req.comm_score,     0), 100)
    decision = min(max(req.decision_score, 0), 100)
    collab   = min(max(req.collab_score,   0), 100)

    try:
        pdf_bytes = generate_profile_bytes(
            archetype_key=key,
            participant_name=req.participant_name,
            company=req.company,
            comm_score=comm,
            decision_score=decision,
            collab_score=collab,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

    if req.response_format == "base64":
        return {
            "filename": f"SYP_{req.participant_name.replace(' ', '_')}_Profile.pdf",
            "archetype": ARCHETYPES[key]["name"],
            "content_type": "application/pdf",
            "data": base64.b64encode(pdf_bytes).decode("utf-8"),
        }

    safe_name = req.participant_name.replace(" ", "_")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="SYP_{safe_name}_Profile.pdf"'},
    )

# ─── Manager team diagnostic report ──────────────────────────────────────────────

@app.post("/generate-manager-report")
def generate_manager_report(req: ManagerReportRequest):
    if not req.participants:
        raise HTTPException(status_code=400, detail="participants array must not be empty")

    participants = [p.model_dump() for p in req.participants]

    try:
        pdf_bytes = generate_manager_report_bytes(
            manager_name=req.manager_name,
            company=req.company,
            workshop_date=req.workshop_date,
            participants=participants,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Manager report generation failed: {str(e)}")

    safe_company = req.company.replace(" ", "_")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="SYP_Team_Report_{safe_company}.pdf"'},
    )

# ─── Entry point ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
