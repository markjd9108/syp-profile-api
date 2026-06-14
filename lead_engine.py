# -*- coding: utf-8 -*-
"""
Personalized opening paragraph ("lead") for the TEW participant profile — hybrid.

Two layers:
  1. compose_lead()  — deterministic, rules-based composer. Builds the paragraph
     from the participant's bands + working style. Always available, always
     on-voice. Includes hash-seeded phrasing variants so two side-by-side
     profiles with the same pattern still read differently.
  2. generate_lead() — calls the Anthropic API (when ANTHROPIC_API_KEY is set)
     for fully written prose, validates the output against voice + safety
     rules, and falls back to compose_lead() on any failure.

The paragraph answers four things, in order: what the person is good at,
what that means / why it is valuable to a team, where the growth
opportunity is, and how their natural working style shapes it.

Voice (The Performance Lens): confident not boastful, specific not vague,
diagnostic not motivational. No "transform/unlock/empower" language.
"""
import hashlib
import json
import os
import re
import urllib.request

# ── Band helper (kept local to avoid circular imports) ──────────────────────────
def _band(score):
    s = int(score)
    if s >= 80: return "strong"
    if s >= 60: return "developing"
    if s >= 40: return "emerging"
    return "foundation"

_BAND_LABEL = {"strong": "Strong", "developing": "Developing",
               "emerging": "Emerging", "foundation": "Foundation"}

_DIMS = ("Communication", "Decision-Making", "Collaboration")

# ── Composer fragments ───────────────────────────────────────────────────────────
# Two variants per slot; selection is seeded by the participant's identity so
# the same person always gets the same paragraph (stable re-renders), while
# different people with identical patterns get different phrasing.

_STRENGTH = {
    "Communication": [
        "your communication: you put language to what was happening while others "
        "were still working out what to say",
        "your communication: when clarity went missing, you were the one who "
        "restored it",
    ],
    "Decision-Making": [
        "your decision-making: you committed to calls while others were still "
        "weighing options",
        "your decision-making: you were willing to decide, and to own the "
        "decision, when the moment asked for it",
    ],
    "Collaboration": [
        "your collaboration: you stayed functional under pressure and kept the "
        "people around you functional too",
        "your collaboration: when plans broke down, you held the team's "
        "structure together rather than retreating into your own task",
    ],
}

_VALUE = {
    "Communication": [
        "Teams run on clarity, and the person who provides it becomes the "
        "reference point in the room.",
        "Most team failures are communication failures; someone who names things "
        "plainly removes the most common point of breakdown.",
    ],
    "Decision-Making": [
        "Teams stall without someone willing to make the call, and that "
        "willingness is rarer than it looks.",
        "Momentum is a team's scarcest resource, and decisions are what create it.",
    ],
    "Collaboration": [
        "Under pressure most teams fragment; someone who holds them together is "
        "what stops that.",
        "Composure is contagious: a team borrows its steadiness from whoever "
        "has it.",
    ],
}

_GROWTH = {
    "foundation": [
        "The clearest opportunity is your {dim}. It is at the start of its "
        "curve, which means the fastest gains available to you are there.",
        "Your biggest room to grow is {dim}: early on the curve, where "
        "deliberate practice pays back quickest.",
    ],
    "emerging": [
        "The clearest opportunity is your {dim}. It is early-stage but moving, "
        "and deliberate reps in real meetings compound quickly from here.",
        "Your next gains are in {dim}. The foundations are visible; consistency "
        "in live situations is what builds on them.",
    ],
    "developing": [
        "The clearest opportunity is your {dim}. It is close to strong, and the "
        "gap is consistency under pressure rather than capability.",
        "Your {dim} is within reach of the top band. What remains is holding it "
        "when the pressure is highest, not learning it.",
    ],
    "all_strong": [
        "With all three dimensions above threshold, your next level is not your "
        "own performance. It is the performance you generate in the people "
        "around you.",
        "All three dimensions cleared the top threshold, so the question changes: "
        "not what to add, but how to use what you have to raise the people "
        "around you.",
    ],
}

_STYLE_SHORT = {
    "Direct & To-the-Point": "direct", "Considered & Thorough": "considered",
    "Warm & Attuned": "warm", "Curious & Questioning": "curious",
    "Measured & Analytical": "measured", "Decisive & Committed": "decisive",
    "Consultative & Inclusive": "consultative", "Adaptive & Iterative": "adaptive",
    "Self-Directed & Focused": "self-directed", "Close & Collaborative": "close-working",
    "Flexible & Versatile": "flexible", "Candid & Open": "candid",
}

_OPEN_TOP = [
    "The clearest signal in your data today was {strength}.",
    "One thing stood out in how you worked today: {strength}.",
]
_OPEN_BALANCED = [
    "Your three dimensions moved together today, all {band}. That is an "
    "unusually balanced starting point, and the strongest of them was {strength}.",
    "Today's read was even across the board, {band} in all three dimensions. "
    "The leading edge was {strength}.",
]
_STYLE_SENT = [
    "How you get there will look like you: {c} in how you communicate, {d} in "
    "how you decide, {co} in how you work with others.",
    "The way there will be your own: {c} in communication, {d} in how you "
    "decide, and {co} in how you collaborate.",
]


def compose_lead(comm_score, dec_score, collab_score, ws_blocks=None, seed=""):
    """Deterministic personalized lead. `seed` (e.g. profile_id or name) picks
    phrasing variants so identical patterns don't produce identical text."""
    scores = {"Communication": int(comm_score), "Decision-Making": int(dec_score),
              "Collaboration": int(collab_score)}
    bands = {d: _band(s) for d, s in scores.items()}
    h = int(hashlib.sha256(str(seed).encode()).hexdigest(), 16)
    pick = lambda options, slot: options[(h >> slot) % len(options)]

    top = max(_DIMS, key=lambda d: scores[d])
    low = min(_DIMS, key=lambda d: scores[d])
    balanced = len(set(bands.values())) == 1

    if balanced:
        opening = pick(_OPEN_BALANCED, 0).format(
            band=_BAND_LABEL[bands[top]], strength=pick(_STRENGTH[top], 2))
    else:
        opening = pick(_OPEN_TOP, 0).format(strength=pick(_STRENGTH[top], 2))

    value = pick(_VALUE[top], 4)

    if all(b == "strong" for b in bands.values()):
        growth = pick(_GROWTH["all_strong"], 6)
    else:
        growth = pick(_GROWTH[bands[low]], 6).format(dim=low.lower())

    parts = [opening, value, growth]

    if ws_blocks:
        styles = {b["dimension"]: b.get("style_name") for b in ws_blocks}
        if all(styles.get(d) for d in _DIMS):
            parts.append(pick(_STYLE_SENT, 8).format(
                c=_STYLE_SHORT.get(styles["Communication"], "your own"),
                d=_STYLE_SHORT.get(styles["Decision-Making"], "your own"),
                co=_STYLE_SHORT.get(styles["Collaboration"], "your own")))

    return " ".join(parts)


# ── LLM layer ────────────────────────────────────────────────────────────────────
_BANNED = ("transform", "unlock", "empower", "journey", "synergy", "holistic",
           "game-chang", "revolutionary", "soft skills", "superpower", "elevate")

_PROMPT = """You write the opening paragraph of a professional development profile \
for The Performance Lens, a team-effectiveness assessment. The reader is the participant.

Voice rules (strict): confident not boastful; specific not vague; diagnostic not \
motivational — a clinician, not a coach. Second person ("you"). Plain, short \
sentences. Never use: transform, unlock, empower, journey, synergy, holistic, \
game-changing, revolutionary, soft skills. No exclamation marks. No numbers or \
scores; refer to bands by name only (Foundation, Emerging, Developing, Strong). \
Use at most ONE em dash in the entire paragraph; prefer periods, commas, colons, \
and semicolons.

Write ONE paragraph of 70–100 words covering, in this order:
1. What this person is genuinely good at (their strongest dimension, named concretely \
through behaviour, not adjectives).
2. Why that matters to a team.
3. Where their clearest growth opportunity is and why it is reachable.
4. How their natural working style will shape the way they grow (weave the style \
names in naturally, lowercase, not as labels).

Participant data:
{data}

Return ONLY the paragraph, no preamble, no quotes."""


def _validate(text, scores):
    words = text.split()
    if not (55 <= len(words) <= 130):
        return False
    low = text.lower()
    if any(b in low for b in _BANNED):
        return False
    if "\n" in text.strip() or "*" in text or "#" in text:
        return False
    if text.count("—") + text.count("–") > 1:   # em/en dash budget
        return False
    if any(str(s) in text for s in scores):   # raw score leakage
        return False
    if " you" not in " " + low:
        return False
    return True


def _llm_lead(payload, api_key, timeout=25):
    body = json.dumps({
        "model": os.environ.get("LEAD_MODEL", "claude-sonnet-4-6"),
        "max_tokens": 400,
        "temperature": 0.7,
        "messages": [{"role": "user",
                      "content": _PROMPT.format(data=json.dumps(payload, indent=2))}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        out = json.loads(r.read())
    return "".join(blk.get("text", "") for blk in out.get("content", [])).strip()


def generate_lead(archetype_key, comm_score, dec_score, collab_score,
                  ws_blocks=None, seed=""):
    """Hybrid entry point: LLM when ANTHROPIC_API_KEY is set and output passes
    validation; deterministic composer otherwise. Never raises."""
    fallback = compose_lead(comm_score, dec_score, collab_score, ws_blocks, seed)
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key or os.environ.get("LEAD_DISABLE_LLM"):
        return fallback
    try:
        payload = {
            "archetype": archetype_key.title(),
            "bands": {d: _BAND_LABEL[_band(s)] for d, s in
                      zip(_DIMS, (comm_score, dec_score, collab_score))},
            "strongest_dimension": max(_DIMS, key=lambda d: dict(zip(_DIMS,
                (comm_score, dec_score, collab_score)))[d]),
        }
        if ws_blocks:
            payload["working_style"] = {
                b["dimension"]: {"style": b.get("style_name"),
                                 "pattern": b.get("pattern"),
                                 "secondary": (b.get("resolved") or {}).get("secondary")}
                for b in ws_blocks}
        text = _llm_lead(payload, api_key)
        text = re.sub(r"\s+", " ", text).strip().strip('"')
        if _validate(text, (comm_score, dec_score, collab_score)):
            return text
        print("[lead] LLM output failed validation — using composer fallback")
    except Exception as e:
        print(f"[lead] LLM call failed ({e}) — using composer fallback")
    return fallback
