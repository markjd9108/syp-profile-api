#!/usr/bin/env python3
"""
SYP Team Effectiveness Lab — PDF Profile API Server v1.3
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
from generate_manager_report import generate_manager_report_pdf

app = FastAPI(
    title="SYP Profile Generator API",
    description="Generates Team Effectiveness Lab PDFs — participant profiles and manager reports",
    version="1.3.0",
)

# Backward-compat aliases: old archetype keys → new keys
LEGACY_ALIAS = {
    "operator":  "navigator",
    "architect": "generalist",
    "connector": "anchor",
    "ember":     "developing",
}

# --- Individual profile models ---
class ProfileRequest(BaseModel):
    archetype: str          = Field(..., description="Archetype key: signal, navigator, anchor, generalist, full_spectrum, developing")
    participant_name: str   = Field(..., description="Participant's full name")
    company: str            = Field("",  description="Company name")
    comm_score: int         = Field(..., ge=0, description="Communication score 0-100")
    decision_score: int     = Field(..., ge=0, description="Decision Making score 0-100")
    collab_score: int       = Field(..., ge=0, description="Collaboration score 0-100")
    context_score: Optional[float] = Field(None, description="Session context quality 1–5 (challenge + representativeness avg)")
    state_score: Optional[float]   = Field(None, description="Session readiness state 1–5 (energy and focus)")
    response_format: Optional[str] = Field("binary", description="'binary' returns raw PDF, 'base64' returns JSON with base64-encoded PDF")

# --- Manager report models ---
class ManagerReportParticipant(BaseModel):
    name: str           = Field(..., description="Participant full name")
    archetype: str      = Field(..., description="Archetype: Signal, Navigator, Anchor, Generalist, Full Spectrum, Developing")
    comm_score: int     = Field(..., ge=0, le=100)
    decision_score: int = Field(..., ge=0, le=100)
    collab_score: int   = Field(..., ge=0, le=100)
    role: Optional[str] = Field(None)

class ManagerReportRequest(BaseModel):
    manager_name: str                            = Field(..., description="Manager's name")
    company: str                                 = Field("", description="Company name")
    workshop_date: Optional[str]                 = Field(None, description="Workshop date string e.g. 'May 2026'")
    folder_url: Optional[str]                    = Field(None, description="Google Drive folder URL (ignored by PDF generator)")
    participants: List[ManagerReportParticipant] = Field(..., description="List of participant data")
    response_format: Optional[str]               = Field("binary")

# --- Individual participant profile ---
@app.post("/generate")
def generate(req: ProfileRequest):
    key = req.archetype.lower().strip().replace(" ", "_")
    # Apply backward-compat alias if needed
    key = LEGACY_ALIAS.get(key, key)
    if key not in ARCHETYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown archetype '{req.archetype}'. Valid: {list(ARCHETYPES.keys())}"
        )
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
            context_score=req.context_score,
            state_score=req.state_score,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

    if req.response_format == "base64":
        return {
            "filename":     f"SYP_{req.participant_name.replace(' ', '_')}_Profile.pdf",
            "archetype":    ARCHETYPES[key]["name"],
            "content_type": "application/pdf",
            "data":         base64.b64encode(pdf_bytes).decode("utf-8"),
        }
    safe_name = req.participant_name.replace(" ", "_")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="SYP_{safe_name}_Profile.pdf"'},
    )

# --- Manager overview report ---
@app.post("/generate-manager-report")
def generate_manager_report(req: ManagerReportRequest):
    if not req.participants:
        raise HTTPException(status_code=400, detail="No participants provided.")
    try:
        pdf_bytes = generate_manager_report_pdf({
            "manager_name":  req.manager_name,
            "team_name":     req.company,
            "workshop_date": req.workshop_date or "",
            "participants": [
                {
                    "name":      p.name,
                    "archetype": p.archetype,
                    "c_score":   p.comm_score,
                    "d_score":   p.decision_score,
                    "co_score":  p.collab_score,
                }
                for p in req.participants
            ],
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

    if req.response_format == "base64":
        return {
            "filename":     f"SYP_Manager_Report_{req.manager_name.replace(' ', '_')}.pdf",
            "content_type": "application/pdf",
            "data":         base64.b64encode(pdf_bytes).decode("utf-8"),
        }
    safe_name = req.manager_name.replace(" ", "_")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="SYP_Manager_Report_{safe_name}.pdf"'},
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
