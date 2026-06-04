# -*- coding: utf-8 -*-
"""
The Performance Lens — Working Style resolver & renderer (single source of truth).

This module is consumed by BOTH the ReportLab PDF generator and the HTML profile
so the two formats can never drift. Participant-facing copy lives in
working_style_content.py (verbatim from the Word doc). Nothing here paraphrases it.

Public API:
    resolve_dimension(dimension, a1, a2, a3) -> dict(pattern, primary, secondary, third)
    resolve_all(answers)                     -> flat dict of the 12 output variables
    build_blocks(answers)                    -> list of 3 render-ready blocks (one per dimension)
"""

from collections import Counter
import re
from working_style_content import (
    KEYED, TIEBREAK, DIMENSION_QUESTIONS, DIMENSION_PREFIX, WORKING_STYLE_CONTENT,
    OPTION_TEXTS, COMPLEMENTS,
)

DIMENSIONS = ('Communication', 'Decision-Making', 'Collaboration')


def _norm_text(s):
    """Lowercase, straighten smart quotes, collapse whitespace — for robust matching."""
    s = str(s).strip()
    for a, b in (("\u2019", "'"), ("\u2018", "'"), ("\u201c", '"'), ("\u201d", '"'), ("\u2014", "-"), ("\u2013", "-")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).lower()


_OPT_TO_LETTER = {
    q: {_norm_text(t): "ABCD"[i] for i, t in enumerate(texts)}
    for q, texts in OPTION_TEXTS.items()
}


def normalize_answer(qkey, value):
    """Accept either a letter (A-D) or the participant-facing option text and
    return the A-D letter. Unknown values pass through unchanged."""
    if value is None:
        return value
    v = str(value).strip()
    if v.upper() in ("A", "B", "C", "D"):
        return v.upper()
    return _OPT_TO_LETTER.get(qkey, {}).get(_norm_text(v), v)


def normalize_answers(answers):
    """Map every ws_q* value (letter or option text) to its A-D letter."""
    return {k: (normalize_answer(k, v) if k.startswith("ws_q") else v)
            for k, v in answers.items()}


def resolve_dimension(dimension, a1, a2, a3):
    """Resolve one dimension's three answers (letters A-D, in question order) to a
    Pattern + Primary/Secondary/Third style names, exactly as the logic table does."""
    keyed = KEYED[dimension]
    answers = [a.strip().upper() for a in (a1, a2, a3)]
    for a in answers:
        if a not in keyed:
            raise ValueError(f"{dimension}: invalid answer {a!r} (expected A-D)")
    counts = Counter(answers)

    if len(counts) == 1:                                   # Pure — all three the same
        return {"pattern": "Pure", "primary": keyed[answers[0]],
                "secondary": None, "third": None}

    if len(counts) == 2:                                   # Blend — 2 + 1
        primary_letter = next(l for l, n in counts.items() if n == 2)
        secondary_letter = next(l for l, n in counts.items() if n == 1)
        return {"pattern": "Blend", "primary": keyed[primary_letter],
                "secondary": keyed[secondary_letter], "third": None}

    # Tiebreak — all three different; question weighting sets the order
    p, s, t = TIEBREAK[dimension]
    return {"pattern": "Tiebreak", "primary": keyed[answers[p]],
            "secondary": keyed[answers[s]], "third": keyed[answers[t]]}


def resolve_all(answers):
    """answers: dict with keys ws_q1..ws_q9 (values A-D).
    Returns the flat 12-variable output:
        comm_pattern, comm_primary, comm_secondary, comm_third,
        decision_pattern, ...,  collab_pattern, ...
    Empty values are '' (Pure -> no secondary/third; Blend -> no third).
    Values may be letters A-D or the option text; both are accepted."""
    answers = normalize_answers(answers)
    out = {}
    for dim in DIMENSIONS:
        q1, q2, q3 = DIMENSION_QUESTIONS[dim]
        r = resolve_dimension(dim, answers[q1], answers[q2], answers[q3])
        pre = DIMENSION_PREFIX[dim]
        out[f"{pre}_pattern"] = r["pattern"]
        out[f"{pre}_primary"] = r["primary"] or ""
        out[f"{pre}_secondary"] = r["secondary"] or ""
        out[f"{pre}_third"] = r["third"] or ""
    return out


# --- Canonical closer templates (exact sentence shapes from the master doc, Section 4) ---

PURE_CLOSER = "Your answers pointed consistently to this style — a clear and settled preference."


def _phrase(style_name):
    return WORKING_STYLE_CONTENT[style_name]["third_preference_phrase"]


def closer_lines(resolved):
    """Return the list of closer sentence(s) for a resolved dimension."""
    pat = resolved["pattern"]
    if pat == "Pure":
        return [PURE_CLOSER]
    if pat == "Blend":
        sec = resolved["secondary"]
        return [f"You also bring a shade of {sec} — {_phrase(sec)}."]
    # Tiebreak
    sec, third = resolved["secondary"], resolved["third"]
    return [
        f"You also bring a shade of {sec} — {_phrase(sec)}.",
        f"And there's a thread of {third} in how you answered — {_phrase(third)}.",
    ]


def build_blocks(answers):
    """Render-ready structure for the profile: one block per dimension, in
    profile order (Communication, Decision-Making, Collaboration).
    Values may be letters A-D or the option text; both are accepted."""
    answers = normalize_answers(answers)
    blocks = []
    for dim in DIMENSIONS:
        q1, q2, q3 = DIMENSION_QUESTIONS[dim]
        r = resolve_dimension(dim, answers[q1], answers[q2], answers[q3])
        c = WORKING_STYLE_CONTENT[r["primary"]]
        blocks.append({
            "dimension": dim,
            "pattern": r["pattern"],
            "style_name": r["primary"],
            "summary": c["summary"],
            "bullets": c["bullets"],
            "closer_lines": closer_lines(r),
            "complement": COMPLEMENTS.get(r["primary"]),
            "resolved": r,
        })
    return blocks
