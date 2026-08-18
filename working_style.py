# -*- coding: utf-8 -*-
"""
The Performance Lens — Working Style resolver & renderer (single source of truth).

This module is consumed by BOTH the ReportLab PDF generator and the HTML profile
so the two formats can never drift. Participant-facing copy lives in
working_style_content.py (TEW, verbatim from the Word doc) and
working_style_content_lead.py (Leadership Workshop / TLW variant). Nothing here
paraphrases either.

Every public function takes an optional `family` argument ('tew' default, or
'lead') that selects which content module drives the resolution. Existing
callers that don't pass `family` get identical TEW behaviour to before.

Public API:
    resolve_dimension(dimension, a1, a2, a3, family='tew') -> dict(pattern, primary, secondary, third)
    resolve_all(answers, family='tew')                     -> flat dict of the 12 output variables
    build_blocks(answers, family='tew')                    -> list of 3 render-ready blocks (one per dimension)
"""

from collections import Counter
import re
import working_style_content as _tew
import working_style_content_lead as _lead

# --- Family registry -------------------------------------------------------
# Each family bundles the dimension-keyed content sets that everything below
# looks up by name. Dimension names never collide between families
# (Communication/Decision-Making/Collaboration vs Leadership/Change
# Management/Conflict Management), but ws_q1..ws_q9 keys DO collide (both
# families reuse the same question-key namespace with different text), so the
# option-text lookup must stay keyed by family too.
_FAMILIES = {
    "tew": {
        "KEYED": _tew.KEYED,
        "TIEBREAK": _tew.TIEBREAK,
        "DIMENSION_QUESTIONS": _tew.DIMENSION_QUESTIONS,
        "DIMENSION_PREFIX": _tew.DIMENSION_PREFIX,
        "WORKING_STYLE_CONTENT": _tew.WORKING_STYLE_CONTENT,
        "OPTION_TEXTS": _tew.OPTION_TEXTS,
        "COMPLEMENTS": _tew.COMPLEMENTS,
        "DIMENSIONS": ("Communication", "Decision-Making", "Collaboration"),
    },
    "lead": {
        "KEYED": _lead.KEYED,
        "TIEBREAK": _lead.TIEBREAK,
        "DIMENSION_QUESTIONS": _lead.DIMENSION_QUESTIONS,
        "DIMENSION_PREFIX": _lead.DIMENSION_PREFIX,
        "WORKING_STYLE_CONTENT": _lead.WORKING_STYLE_CONTENT,
        "OPTION_TEXTS": _lead.OPTION_TEXTS,
        "COMPLEMENTS": _lead.COMPLEMENTS,
        "DIMENSIONS": ("Leadership", "Change Management", "Conflict Management"),
    },
}

DIMENSIONS_BY_FAMILY = {fam: d["DIMENSIONS"] for fam, d in _FAMILIES.items()}

# --- Backward-compatible module-level names (TEW defaults) -----------------
# Kept so any existing code importing these symbols directly from
# working_style keeps working unchanged.
KEYED = _tew.KEYED
TIEBREAK = _tew.TIEBREAK
DIMENSION_QUESTIONS = _tew.DIMENSION_QUESTIONS
DIMENSION_PREFIX = _tew.DIMENSION_PREFIX
WORKING_STYLE_CONTENT = _tew.WORKING_STYLE_CONTENT
OPTION_TEXTS = _tew.OPTION_TEXTS
COMPLEMENTS = _tew.COMPLEMENTS
DIMENSIONS = _FAMILIES["tew"]["DIMENSIONS"]


def _norm_text(s):
    """Lowercase, straighten smart quotes, collapse whitespace — for robust matching."""
    s = str(s).strip()
    for a, b in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'), ("—", "-"), ("–", "-")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).lower()


def _build_opt_to_letter(option_texts):
    return {
        q: {_norm_text(t): "ABCD"[i] for i, t in enumerate(texts)}
        for q, texts in option_texts.items()
    }


_OPT_TO_LETTER_BY_FAMILY = {
    fam: _build_opt_to_letter(d["OPTION_TEXTS"]) for fam, d in _FAMILIES.items()
}
# Backward-compat name (TEW default table).
_OPT_TO_LETTER = _OPT_TO_LETTER_BY_FAMILY["tew"]


def normalize_answer(qkey, value, family="tew"):
    """Accept either a letter (A-D) or the participant-facing option text and
    return the A-D letter. Unknown values pass through unchanged."""
    if value is None:
        return value
    v = str(value).strip()
    if v.upper() in ("A", "B", "C", "D"):
        return v.upper()
    return _OPT_TO_LETTER_BY_FAMILY.get(family, _OPT_TO_LETTER).get(qkey, {}).get(_norm_text(v), v)


def normalize_answers(answers, family="tew"):
    """Map every ws_q* value (letter or option text) to its A-D letter."""
    return {k: (normalize_answer(k, v, family) if k.startswith("ws_q") else v)
            for k, v in answers.items()}


def resolve_dimension(dimension, a1, a2, a3, family="tew"):
    """Resolve one dimension's three answers (letters A-D, in question order) to a
    Pattern + Primary/Secondary/Third style names, exactly as the logic table does."""
    fd = _FAMILIES[family]
    keyed = fd["KEYED"][dimension]
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
    p, s, t = fd["TIEBREAK"][dimension]
    return {"pattern": "Tiebreak", "primary": keyed[answers[p]],
            "secondary": keyed[answers[s]], "third": keyed[answers[t]]}


def resolve_all(answers, family="tew"):
    """answers: dict with keys ws_q1..ws_q9 (values A-D).
    Returns the flat 12-variable output. For family='tew':
        comm_pattern, comm_primary, comm_secondary, comm_third,
        decision_pattern, ...,  collab_pattern, ...
    For family='lead':
        lead_pattern, lead_primary, lead_secondary, lead_third,
        change_pattern, ...,  conflict_pattern, ...
    Empty values are '' (Pure -> no secondary/third; Blend -> no third).
    Values may be letters A-D or the option text; both are accepted."""
    fd = _FAMILIES[family]
    answers = normalize_answers(answers, family)
    out = {}
    for dim in fd["DIMENSIONS"]:
        q1, q2, q3 = fd["DIMENSION_QUESTIONS"][dim]
        r = resolve_dimension(dim, answers[q1], answers[q2], answers[q3], family)
        pre = fd["DIMENSION_PREFIX"][dim]
        out[f"{pre}_pattern"] = r["pattern"]
        out[f"{pre}_primary"] = r["primary"] or ""
        out[f"{pre}_secondary"] = r["secondary"] or ""
        out[f"{pre}_third"] = r["third"] or ""
    return out


# --- Canonical closer templates (exact sentence shapes from the master doc, Section 4) ---

PURE_CLOSER = "Your answers pointed consistently to this style — a clear and settled preference."


def _phrase(style_name, family="tew"):
    return _FAMILIES[family]["WORKING_STYLE_CONTENT"][style_name]["third_preference_phrase"]


def closer_lines(resolved, family="tew"):
    """Return the list of closer sentence(s) for a resolved dimension."""
    pat = resolved["pattern"]
    if pat == "Pure":
        return [PURE_CLOSER]
    if pat == "Blend":
        sec = resolved["secondary"]
        return [f"You also bring a shade of {sec} — {_phrase(sec, family)}."]
    # Tiebreak
    sec, third = resolved["secondary"], resolved["third"]
    return [
        f"You also bring a shade of {sec} — {_phrase(sec, family)}.",
        f"And there's a thread of {third} in how you answered — {_phrase(third, family)}.",
    ]


def build_blocks(answers, family="tew"):
    """Render-ready structure for the profile: one block per dimension, in
    profile order. For family='tew': Communication, Decision-Making,
    Collaboration. For family='lead': Leadership, Change Management,
    Conflict Management.
    Values may be letters A-D or the option text; both are accepted."""
    fd = _FAMILIES[family]
    answers = normalize_answers(answers, family)
    blocks = []
    for dim in fd["DIMENSIONS"]:
        q1, q2, q3 = fd["DIMENSION_QUESTIONS"][dim]
        r = resolve_dimension(dim, answers[q1], answers[q2], answers[q3], family)
        c = fd["WORKING_STYLE_CONTENT"][r["primary"]]
        blocks.append({
            "dimension": dim,
            "pattern": r["pattern"],
            "style_name": r["primary"],
            "summary": c["summary"],
            "bullets": c["bullets"],
            "closer_lines": closer_lines(r, family),
            "complement": fd["COMPLEMENTS"].get(r["primary"]),
            "resolved": r,
        })
    return blocks
