#!/usr/bin/env python3
"""
SYP Team Effectiveness Lab — PDF Profile API Server
Accepts participant data via POST, generates a personalised PDF, returns it as binary.
Designed for deployment on Railway, Render, or any platform that runs Python.
"""

import os, base64, json
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Optional

# Import the PDF generator
from generate_syp_profiles_improved import generate_profile_bytes, ARCHETYPES

app = FastAPI(
    title="SYP Profile Generator API",
    description="Generates personalised Team Effectiveness Lab PDF profiles",
    version="1.0.0",
)

# ─── Request model ────────────────────────────────────────────────────────────
class ProfileRequest(BaseModel):
    archetype: str = Field(..., description="Archetype key: operator, architect, navigator, signal, anchor, ember")
    participant_name: str = Field(..., description="Participant's full name")
    company: str = Field("", description="Company name")
    comm_score: int = Field(..., ge=0, le=100, description="Communication score 0-100")
    decision_score: int = Field(..., ge=0, le=100, description="Decision Making score 0-100")
    collab_score: int = Field(..., ge=0, le=100, description="Collaboration score 0-100")
    response_format: Optional[str] = Field("binary", description="'binary' returns raw PDF, 'base64' returns JSON with base64-encoded PDF")

# ─── Health check ─────────────────────────────────────────────────────────────
@app.get("/")
def health():
    return {"status": "ok", "service": "SYP Profile Generator", "archetypes": list(ARCHETYPES.keys())}

# ─── Generate profile ─────────────────────────────────────────────────────────
@app.post("/generate")
def generate(req: ProfileRequest):
    key = req.archetype.lower().strip()
    if key not in ARCHETYPES:
        raise HTTPException(status_code=400, detail=f"Unknown archetype '{key}'. Valid: {list(ARCHETYPES.keys())}")

    try:
        pdf_bytes = generate_profile_bytes(
            archetype_key=key,
            participant_name=req.participant_name,
            company=req.company,
            comm_score=req.comm_score,
            decision_score=req.decision_score,
            collab_score=req.collab_score,
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

    # Default: return raw PDF binary
    safe_name = req.participant_name.replace(" ", "_")
    filename = f"SYP_{safe_name}_Profile.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
