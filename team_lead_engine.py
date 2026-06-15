# -*- coding: utf-8 -*-
"""
Team-level narrative engine for The Performance Lens "Leadership Insight Report".

The sibling of lead_engine.py. Where lead_engine writes the per-participant
opening paragraph, this module writes the cohort-level prose: the Summary
headline + cards, the team-shape and structural-risk paragraphs, the working-
style summary, and the per-member focus openers.

Two layers, same hybrid pattern as lead_engine:
  1. compose_team_narrative() — deterministic, rules-based composer. Builds every
     narrative string from the cohort data (team averages vs benchmarks, the
     archetype mix, who sits below threshold, the structural pattern). Always
     available, always on-voice, uses the real numbers and names.
  2. build_team_narrative() — calls the Anthropic API (when ANTHROPIC_API_KEY is
     set) for fully written prose, returned as STRICT JSON, validates the output
     against voice + structure rules, and falls back to the deterministic
     composer on any failure. Never raises.

The output dict keys match exactly what generate_leader_report.py reads from
data["narrative"]: headline, strength, priority, what_this_means, team_shape,
structural_risk, working_style_summary, focus (object keyed by participant name),
and the optional page_dynamics / page_action_plan / page_whats_next.

Voice (The Performance Lens): confident not boastful, specific not vague,
diagnostic not motivational — a clinician, not a coach. Plain short sentences.
No contractions. At most one em dash per item. We are not performance coaches:
observations, risks, and OPTIONS only, never "do X to achieve Y".
"""
from __future__ import annotations

import json
import os
import re
import urllib.request

# ── Domain constants (kept in sync with generate_leader_report.py) ───────────────
_DIMS = ("Communication", "Decision Making", "Collaboration")

ALL_ARCHETYPES = ["Relay", "Navigator", "Signal", "Summit", "Anchor", "Compass"]

ARCHETYPE_NOTE = {
    "Relay":     "executes on clear briefs",
    "Navigator": "makes the call in ambiguity",
    "Signal":    "reads the room and connects people",
    "Summit":    "raises the team's standard",
    "Anchor":    "holds steady when the brief breaks down",
    "Compass":   "builds structure out of ambiguity",
}

DEFAULT_BENCHMARKS = {"Communication": 62, "Decision Making": 58, "Collaboration": 64}

# Report's band thresholds (mirror generate_leader_report._band).
_THRESHOLD = 60  # below this, a dimension is the area to watch for a member


def _band(score: float) -> str:
    if score >= 75:
        return "Strong"
    if score >= 60:
        return "Developing"
    if score >= 40:
        return "Emerging"
    return "Foundation"


def _num(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _i(v) -> int:
    return int(round(_num(v)))


def _join(names) -> str:
    names = list(names)
    if not names:
        return "no members"
    if len(names) == 1:
        return str(names[0])
    return ", ".join(str(n) for n in names[:-1]) + " and " + str(names[-1])


# ── Cohort derivation ────────────────────────────────────────────────────────────

def _member(p: dict) -> dict:
    m = dict(p)
    m["c"] = _num(p.get("c_score", p.get("communication")))
    m["d"] = _num(p.get("d_score", p.get("decision")))
    m["co"] = _num(p.get("co_score", p.get("collaboration")))
    m["avg"] = round((m["c"] + m["d"] + m["co"]) / 3)
    m["archetype"] = p.get("archetype") or "Relay"
    m["name"] = p.get("name") or "Member"
    flag = p.get("focus")
    if not flag:
        if all(s >= 60 for s in (m["c"], m["d"], m["co"])) and m["avg"] >= 70:
            flag = "Stretch"
        elif any(s < 60 for s in (m["c"], m["d"], m["co"])):
            flag = "Check-In"
        else:
            flag = "Stretch"
    m["focus"] = flag
    return m


def _dim_value(m: dict, dim: str) -> float:
    return {"Communication": m["c"], "Decision Making": m["d"], "Collaboration": m["co"]}[dim]


def _derive(data: dict) -> dict:
    """Reduce the raw cohort `data` into the facts the composer and prompt need."""
    company = data.get("company") or data.get("team_name") or "the team"
    members = [_member(p) for p in data.get("participants", [])]
    n = len(members)

    benchmarks = dict(DEFAULT_BENCHMARKS)
    benchmarks.update(data.get("benchmarks", {}) or {})

    if n:
        dims = {
            "Communication": round(sum(m["c"] for m in members) / n),
            "Decision Making": round(sum(m["d"] for m in members) / n),
            "Collaboration": round(sum(m["co"] for m in members) / n),
        }
    else:
        dims = {d: 0 for d in _DIMS}
    overall = round(sum(dims.values()) / 3) if n else 0

    ranked = sorted(_DIMS, key=lambda d: dims[d], reverse=True)
    strength = ranked[0]
    second = ranked[1] if len(ranked) > 1 else ranked[0]
    priority = ranked[-1]

    # archetype mix
    counts = {}
    for m in members:
        counts[m["archetype"]] = counts.get(m["archetype"], 0) + 1
    mix = [(a, counts[a]) for a in ALL_ARCHETYPES if counts.get(a)]
    dominant = max(mix, key=lambda t: t[1])[0] if mix else None
    navigators = counts.get("Navigator", 0)

    # focus groups
    check_ins = [m for m in members if m["focus"] == "Check-In"]
    stretches = [m for m in members if m["focus"] == "Stretch"]

    # per-dimension spread + who is below threshold on each dimension
    below = {d: [m for m in members if _dim_value(m, d) < _THRESHOLD] for d in _DIMS}
    leader_on = {d: (max(members, key=lambda m: _dim_value(m, d)) if members else None) for d in _DIMS}
    spread = {}
    for d in _DIMS:
        if members:
            vals = [_dim_value(m, d) for m in members]
            spread[d] = _i(max(vals) - min(vals))
        else:
            spread[d] = 0

    return {
        "company": company,
        "members": members,
        "n": n,
        "benchmarks": benchmarks,
        "dims": dims,
        "overall": overall,
        "strength": strength,
        "second": second,
        "priority": priority,
        "mix": mix,
        "counts": counts,
        "dominant": dominant,
        "navigators": navigators,
        "check_ins": check_ins,
        "stretches": stretches,
        "below": below,
        "leader_on": leader_on,
        "spread": spread,
    }


# ── Deterministic composer ───────────────────────────────────────────────────────

def _compose_headline(f: dict) -> str:
    co, dims = f["company"], f["dims"]
    s, p = f["strength"], f["priority"]
    return (f"{co} averages {f['overall']} across the three dimensions. "
            f"{s} ({dims[s]}) is the strongest signal and {p} ({dims[p]}) is the area to watch.")


def _compose_strength(f: dict) -> str:
    s, dims, bm = f["strength"], f["dims"], f["benchmarks"]
    lead = f["leader_on"][s]
    gap = dims[s] - bm.get(s, 0)
    rel = "above" if gap > 0 else ("at" if gap == 0 else "below")
    body = (f"{s} is the team's highest dimension at {dims[s]}, {rel} the industry benchmark "
            f"of {bm.get(s, 0)}.")
    if lead is not None:
        body += f" {lead['name']} leads it at {_i(_dim_value(lead, s))}."
    return body


def _compose_priority(f: dict) -> str:
    p, dims, bm = f["priority"], f["dims"], f["benchmarks"]
    below = f["below"][p]
    lead = f["leader_on"][p]
    body = f"{p} is the lowest at {dims[p]}, against a benchmark of {bm.get(p, 0)}."
    if f["spread"][p] >= 20 and lead is not None and below:
        body += (f" Spread is wide: {lead['name']} leads at {_i(_dim_value(lead, p))} while "
                 f"{_join(m['name'] for m in below)} sit below the line.")
    elif below:
        body += f" {_join(m['name'] for m in below)} sit below 60."
    return body


def _compose_what_this_means(f: dict) -> str:
    s2, dims, bm = f["second"], f["dims"], f["benchmarks"]
    gap = dims[s2] - bm.get(s2, 0)
    if gap > 0:
        return f"{s2} also sits above benchmark at {dims[s2]}, a second team-level asset."
    return f"{s2} sits near benchmark at {dims[s2]}, steady rather than a standout."


def _compose_team_shape(f: dict) -> str:
    n, overall = f["n"], f["overall"]
    mix_txt = ", ".join(f"{cnt} {a}" for a, cnt in f["mix"]) if f["mix"] else "a mixed set of archetypes"
    note = ""
    if f["dominant"]:
        share = round(f["counts"][f["dominant"]] / n * 100) if n else 0
        if share >= 50:
            note = (f" The mix leans {f['dominant']}, the profile that "
                    f"{ARCHETYPE_NOTE.get(f['dominant'], 'sets the team baseline')}.")
    return f"{n} members, average {overall}. The mix is {mix_txt}.{note}"


def _compose_structural_risk(f: dict) -> str:
    dom, counts, n = f["dominant"], f["counts"], f["n"]
    navs = f["navigators"]
    decisive = counts.get("Navigator", 0) + counts.get("Summit", 0)

    # A single decision-maker becomes a bottleneck.
    if navs == 1 and n >= 4:
        nav = next((m for m in f["members"] if m["archetype"] == "Navigator"), None)
        who = f" {nav['name']} holds it alone." if nav else ""
        return (f"With one Navigator on a team of {n}, decision ownership sits with one person.{who} "
                "The risk is a bottleneck if that person is absent. One option is to name a second owner.")

    # A Relay-heavy base funnels decisions to the few decisive members.
    if dom == "Relay" and counts.get("Relay", 0) >= max(3, n // 2) and decisive <= 2:
        names = [m["name"] for m in f["members"] if m["archetype"] in ("Navigator", "Summit")]
        tail = f" toward {_join(names)}" if names else ""
        return ("A Relay-heavy base executes well but leans on a few to set direction. "
                f"The risk is decisions stacking{tail}. One option is to widen who makes the call.")

    # Decision Making is the weak dimension across the board.
    if f["priority"] == "Decision Making" and len(f["below"]["Decision Making"]) >= max(2, n // 2):
        names = [m["name"] for m in f["below"]["Decision Making"]]
        return (f"Decision Making is the thinnest dimension, with {_join(names)} below the line. "
                "The risk is hesitation under time pressure.")

    # No clear single risk: name the dimension to watch.
    p = f["priority"]
    return (f"No single fault dominates. Watch {p} at {f['dims'][p]}: it can thin out under pressure. "
            "One option is to track it next round.")


def _compose_working_style_summary(f: dict) -> str:
    # Summarise the dominant working-style flavour from member blocks, if present.
    style_names = []
    for m in f["members"]:
        ws = m.get("working_style") or {}
        for dim in _DIMS:
            v = ws.get(dim)
            if isinstance(v, dict) and v.get("name"):
                style_names.append(v["name"])
            elif isinstance(v, str) and v:
                style_names.append(v)
    decisive = [m["name"] for m in f["members"] if m["archetype"] in ("Navigator", "Summit")]

    base = (f"{f['company']} works from a clear brief before it commits.")
    if style_names:
        # surface the most common style word, lowercased, without inventing labels
        from collections import Counter
        common = [s for s, _ in Counter(style_names).most_common(2)]
        flavour = _join([s.lower() for s in common])
        base = (f"{f['company']} leans {flavour} in how it works, preferring a clear brief "
                "before it commits.")
    if decisive:
        base += f" {_join(decisive)} set direction when the brief runs out."
    return base


def _compose_focus(f: dict) -> dict:
    out = {}
    for m in f["members"]:
        if m["focus"] == "Check-In":
            # lowest dimension as the constraint
            low_dim = min(_DIMS, key=lambda d: _dim_value(m, d))
            low_val = _i(_dim_value(m, low_dim))
            opener = (f"{low_dim} ({low_val}) was the constraint. "
                      '<span style="color:#0D2A66;font-style:italic;">An opener: '
                      f'&ldquo;On {low_dim.lower()}, what would have helped you move sooner?&rdquo;</span>')
        else:
            opener = (f"Steady at an average of {_i(m['avg'])}. "
                      '<span style="color:#0D2A66;font-style:italic;">An opener: '
                      '&ldquo;Where could you lead a call you would normally wait on?&rdquo;</span>')
        out[m["name"]] = opener
    return out


def compose_team_narrative(data: dict) -> dict:
    """Deterministic cohort narrative. Always on-voice, uses the real numbers and
    names. Returns the full narrative dict (no LLM)."""
    f = _derive(data)
    return {
        "headline": _compose_headline(f),
        "strength": _compose_strength(f),
        "priority": _compose_priority(f),
        "what_this_means": _compose_what_this_means(f),
        "team_shape": _compose_team_shape(f),
        "structural_risk": _compose_structural_risk(f),
        "working_style_summary": _compose_working_style_summary(f),
        "focus": _compose_focus(f),
    }


# ── LLM layer ────────────────────────────────────────────────────────────────────

_BANNED = ("transform", "unlock", "empower", "journey", "synergy", "holistic",
           "game-chang", "revolutionary", "soft skills", "superpower", "elevate",
           "simulation")

# contractions we will not accept in the prose
_CONTRACTIONS = ("don't", "doesn't", "isn't", "aren't", "wasn't", "weren't",
                 "won't", "can't", "couldn't", "shouldn't", "wouldn't", "it's",
                 "that's", "there's", "they're", "we're", "you're", "i'm",
                 "let's", "who's", "what's", "haven't", "hasn't", "hadn't",
                 "didn't", "they've", "we've", "you've", "they'll", "we'll")

_REQUIRED_KEYS = ("headline", "strength", "priority", "what_this_means",
                  "team_shape", "structural_risk", "working_style_summary", "focus")

# Hard word caps per field (mirror the prompt). Validation rejects output that runs
# long so a rambling LLM response falls back to the concise composer rather than
# overflowing the fixed-height report page.
_WORD_CAPS = {
    "headline": 22, "strength": 28, "priority": 34, "what_this_means": 24,
    "team_shape": 26, "structural_risk": 40, "working_style_summary": 28,
    "focus": 30,
}
_CAP_TOLERANCE = 1.3  # allow a little slack before rejecting

def _word_count(text: str) -> int:
    # strip HTML tags/entities so the cap reflects visible words, not markup
    plain = re.sub(r"<[^>]+>", " ", str(text))
    plain = re.sub(r"&[a-zA-Z]+;", " ", plain)
    return len(plain.split())

def _too_long(text: str, cap: int) -> bool:
    return _word_count(text) > cap * _CAP_TOLERANCE

_PROMPT = """You write the cohort-level narrative for The Performance Lens \
"Leadership Insight Report", the team layer of a team-effectiveness assessment. \
The reader is the team's leader.

VOICE (strict):
- Confident, specific, diagnostic. A clinician, not a coach.
- Plain, short sentences. NO contractions (write "do not", never "don't").
- At most ONE em dash in any single value. Prefer periods, commas, semicolons.
- You are NOT a performance coach. State observations, risks, and OPTIONS only. \
Never write "do X to achieve Y". Use framings like "one option", "a risk worth \
watching", "some teams in this position".
- Never use these words: transform, unlock, empower, journey, synergy, holistic, \
game-changing, revolutionary, soft skills, superpower, elevate. Never write \
"simulation" or "simulations"; call them "the exercises".
- No exclamation marks. Do not invent any data that is not in the cohort facts below.

BREVITY (strict): This is a one-glance report. Be terse. Cut every word that does \
not carry information. The word limits below are HARD MAXIMUMS, not targets — \
shorter is better. Prefer one tight sentence over two loose ones. Do not restate \
the data twice or explain what a score "means" in general terms.

WRITE these fields, each a short HTML-safe string, using the real numbers and \
names. Stay within the word cap on each:
- headline: ONE sentence, max 22 words. Team average, strongest dimension, \
dimension to watch.
- strength: max 28 words. Strongest dimension, score vs benchmark, who leads it.
- priority: max 34 words. Lowest dimension, score vs benchmark, who sits below \
the 60 line, and whether the average hides a wide spread.
- what_this_means: ONE sentence, max 24 words. What the second dimension adds.
- team_shape: max 26 words. Member count, average, archetype mix in plain words.
- structural_risk: max 40 words. The one structural pattern in the mix (e.g. a \
Relay-heavy base funnelling decisions to a few, or a single Navigator becoming a \
bottleneck): name it, name the risk, offer one option. Do NOT prefix with "The \
structural risk:"; the report adds that label. Write only the sentence(s).
- working_style_summary: max 28 words, drawn only from the working-style data given.
- focus: an OBJECT keyed by participant name (use exactly the names listed). Each \
value max 30 words: for a member below threshold name the constraining dimension \
and its score, then one short question the leader could ask (you may wrap the \
question in a short italic span). For a steady performer, one line plus a question.

Cohort facts (do not contradict or exceed these):
{data}

Return ONLY a JSON object with exactly these keys: headline, strength, priority, \
what_this_means, team_shape, structural_risk, working_style_summary, focus. \
No preamble, no code fences, no commentary."""


def _llm_payload(f: dict) -> dict:
    """Compact, fact-only payload for the prompt (no invented data)."""
    return {
        "company": f["company"],
        "members": f["n"],
        "team_average": f["overall"],
        "dimension_averages": f["dims"],
        "benchmarks": f["benchmarks"],
        "strongest_dimension": f["strength"],
        "second_dimension": f["second"],
        "lowest_dimension": f["priority"],
        "dimension_spread": f["spread"],
        "archetype_mix": {a: c for a, c in f["mix"]},
        "members_below_60_by_dimension": {
            d: [m["name"] for m in f["below"][d]] for d in _DIMS
        },
        "leader_per_dimension": {
            d: (f["leader_on"][d]["name"] if f["leader_on"][d] else None) for d in _DIMS
        },
        "participants": [
            {
                "name": m["name"],
                "archetype": m["archetype"],
                "Communication": _i(m["c"]),
                "Decision Making": _i(m["d"]),
                "Collaboration": _i(m["co"]),
                "average": _i(m["avg"]),
                "focus_group": m["focus"],
                "working_style": {
                    dim: (
                        (m.get("working_style") or {}).get(dim, {}).get("name")
                        if isinstance((m.get("working_style") or {}).get(dim), dict)
                        else (m.get("working_style") or {}).get(dim)
                    )
                    for dim in _DIMS
                },
            }
            for m in f["members"]
        ],
    }


def _violates_voice(text: str) -> bool:
    if not isinstance(text, str) or not text.strip():
        return True
    low = text.lower()
    if any(b in low for b in _BANNED):
        return True
    if any(c in low for c in _CONTRACTIONS):
        return True
    if "!" in text:
        return True
    if text.count("—") + text.count("–") > 1:  # one em/en dash per value
        return True
    return False


def _validate(narrative, member_names) -> bool:
    if not isinstance(narrative, dict):
        return False
    for k in _REQUIRED_KEYS:
        if k not in narrative:
            return False
    for k in ("headline", "strength", "priority", "what_this_means",
              "team_shape", "structural_risk", "working_style_summary"):
        if _violates_voice(narrative.get(k, "")):
            return False
        if _too_long(narrative.get(k, ""), _WORD_CAPS[k]):
            return False
    focus = narrative.get("focus")
    if not isinstance(focus, dict) or not focus:
        return False
    for name in member_names:
        v = focus.get(name)
        if not isinstance(v, str) or not v.strip():
            return False
        if _violates_voice(v):
            return False
        if _too_long(v, _WORD_CAPS["focus"]):
            return False
    return True


def _llm_narrative(payload: dict, api_key: str, timeout: int = 40) -> dict:
    body = json.dumps({
        "model": os.environ.get("LEAD_MODEL", "claude-sonnet-4-6"),
        "max_tokens": 1600,
        "temperature": 0.6,
        "messages": [{"role": "user",
                      "content": _PROMPT.format(data=json.dumps(payload, indent=2))}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        out = json.loads(r.read())
    text = "".join(blk.get("text", "") for blk in out.get("content", [])).strip()
    # strip code fences if the model wrapped the JSON
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    return json.loads(text)


def build_team_narrative(data: dict) -> dict:
    """Hybrid entry point. LLM when ANTHROPIC_API_KEY is set and the output passes
    validation; deterministic composer otherwise. Never raises.

    Returns the narrative dict consumed by generate_leader_report.build_leader_report_html
    via data["narrative"]: headline, strength, priority, what_this_means, team_shape,
    structural_risk, working_style_summary, focus (object keyed by participant name).
    """
    f = _derive(data)
    fallback = compose_team_narrative(data)

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key or os.environ.get("LEAD_DISABLE_LLM"):
        return fallback

    try:
        payload = _llm_payload(f)
        narrative = _llm_narrative(payload, api_key)
        member_names = [m["name"] for m in f["members"]]
        if _validate(narrative, member_names):
            # keep only the keys the report expects; preserve any optional pages
            keep = dict(narrative)
            for opt in ("page_dynamics", "page_action_plan", "page_whats_next"):
                if opt in data.get("narrative", {}) and opt not in keep:
                    keep[opt] = data["narrative"][opt]
            return keep
        print("[team_lead] LLM output failed validation — using composer fallback")
    except Exception as e:
        print(f"[team_lead] LLM call failed ({e}) — using composer fallback")
    return fallback


# ──────────────────────────────────────────────────────────────────────────────
# Test harness
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.environ["LEAD_DISABLE_LLM"] = "1"  # force the deterministic path

    WS = lambda nm, dn: {"name": nm, "description": dn}

    fake = {
        "company": "Atlas",
        "cohort_code": "ATL-2026-06",
        "workshop_date": "June 2026",
        "leader_name": "Dana Reyes",
        "benchmarks": {"Communication": 62, "Decision Making": 58, "Collaboration": 64},
        "participants": [
            {"name": "Harmony", "archetype": "Relay", "c_score": 75, "d_score": 66, "co_score": 76,
             "working_style": {
                 "Communication": WS("Considered & Thorough", "Confirms before acting."),
                 "Decision Making": WS("Considered & Thorough", "Commits once direction is set."),
                 "Collaboration": WS("Close & Collaborative", "A steady contributor.")}},
            {"name": "Mia", "archetype": "Relay", "c_score": 73, "d_score": 56, "co_score": 76,
             "working_style": {
                 "Communication": WS("Warm & Attuned", "Reads tone and adjusts."),
                 "Decision Making": WS("Consultative & Inclusive", "Aligns before committing."),
                 "Collaboration": WS("Close & Collaborative", "Keeps the group cohesive.")}},
            {"name": "Phuong", "archetype": "Navigator", "c_score": 63, "d_score": 85, "co_score": 63,
             "working_style": {
                 "Communication": WS("Direct & To-the-Point", "Says the essential thing."),
                 "Decision Making": WS("Decisive & Committed", "Commits early."),
                 "Collaboration": WS("Self-Directed & Focused", "Carries a call alone when needed.")}},
            {"name": "Rose", "archetype": "Relay", "c_score": 75, "d_score": 63, "co_score": 78,
             "working_style": {
                 "Communication": WS("Considered & Thorough", "Clarifies the brief first."),
                 "Decision Making": WS("Considered & Thorough", "Weighs options."),
                 "Collaboration": WS("Close & Collaborative", "A connector across workstreams.")}},
            {"name": "Snow", "archetype": "Signal", "c_score": 87, "d_score": 58, "co_score": 73,
             "working_style": {
                 "Communication": WS("Warm & Attuned", "Notices what is unsaid."),
                 "Decision Making": WS("Consultative & Inclusive", "Checks the room first."),
                 "Collaboration": WS("Close & Collaborative", "An informal connector.")}},
            {"name": "Tuong Vy", "archetype": "Summit", "c_score": 70, "d_score": 79, "co_score": 88,
             "working_style": {
                 "Communication": WS("Direct & To-the-Point", "States the standard plainly."),
                 "Decision Making": WS("Decisive & Committed", "Pushes for the better answer."),
                 "Collaboration": WS("Close & Collaborative", "Lifts the group's bar.")}},
        ],
    }

    result = build_team_narrative(fake)

    print("=" * 78)
    print("RETURNED KEYS:", sorted(result.keys()))
    print("=" * 78)
    for k, v in result.items():
        if k == "focus":
            print("\n[focus] keys:", sorted(v.keys()))
            for name, txt in v.items():
                print(f"  - {name}: {txt}")
        else:
            print(f"\n[{k}]\n  {v}")

    # 1. every required key present and non-empty
    print("\n" + "=" * 78)
    missing = [k for k in _REQUIRED_KEYS if not result.get(k)]
    print("MISSING/EMPTY required keys:", missing or "NONE")
    member_names = [p["name"] for p in fake["participants"]]
    focus_missing = [n for n in member_names if not result.get("focus", {}).get(n)]
    print("MISSING focus entries:", focus_missing or "NONE")

    # 2. banned-word scan over ALL values (strings + focus dict)
    def _scan(text):
        low = str(text).lower()
        hits = [b for b in _BANNED if b in low]
        contr = [c for c in _CONTRACTIONS if c in low]
        return hits, contr

    all_strings = []
    for k, v in result.items():
        if isinstance(v, dict):
            all_strings.extend(v.values())
        else:
            all_strings.append(v)

    banned_hits, contraction_hits = [], []
    for s in all_strings:
        b, c = _scan(s)
        banned_hits += b
        contraction_hits += c
    print("BANNED-WORD HITS:", banned_hits or "NONE")
    print("CONTRACTION HITS:", contraction_hits or "NONE")
    clean = not banned_hits and not contraction_hits and not missing and not focus_missing
    print("\nSCAN RESULT:", "CLEAN" if clean else "FAILED")
