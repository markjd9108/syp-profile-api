#!/usr/bin/env python3
"""
Leadership Insight Report — composition step.
Copy authority: LIR_Composition_Spec (shipped alongside as
lir_composition_spec.md and embedded in the system prompt).
One API call per report; validate; regenerate up to twice with the failure
named; after three failures raise CompositionHalt (flag for Mark, never ship
degraded output).
"""
import json, os, re, urllib.request

SESSION_MAP = {
    "Communication": "Communicating with Clarity",
    "Decision-Making": "Deciding with Conviction",
    "Collaboration": "Collaborating Under Pressure",
}

WORD_LIMITS = {
    "leaderVerdict": 60, "headline": 25, "priorityRead": 50, "firstMove": 45,
    "patternLabel": 6, "patternTitle": 5,
    "definingPatternP1": 55, "definingPatternP2": 55,
    "prescription": 45, "closingVerdict": 50,
}

BANNED_WORDS = ["actually", "rather than", "instead of", "manager", "diagnostic",
                "challenges", "transform", "unlock", "empower", "synergy",
                "game-changing"]
PRONOUNS = re.compile(r"\b(he|she|him|her|his|hers)\b", re.I)
CONTRAST = re.compile(r",\s*not\s+[a-z]", re.I)
ARCHETYPES = ["Summit", "Navigator", "Signal", "Anchor", "Compass", "Relay"]

class CompositionHalt(Exception):
    """Three failed generations. Halt and flag for Mark's review."""
    def __init__(self, failures):
        self.failures = failures
        super().__init__("composition halted after 3 failed generations: "
                         + " | ".join(failures[-1] if failures else []))

def _wc(s):
    return len([w for w in re.split(r"\s+", s.strip()) if w])

def _spec_text():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lir_composition_spec.md")
    return open(p).read()

def _walk_texts(composed):
    """Yield (fieldpath, text) for every composed string."""
    for k in WORD_LIMITS:
        yield k, composed.get(k, "")
    for i, c in enumerate(composed.get("patternCards", [])):
        yield f"patternCards[{i}].label", c.get("label", "")
        yield f"patternCards[{i}].name", c.get("name", "")
        yield f"patternCards[{i}].body", c.get("body", "")
    for i, c in enumerate(composed.get("missingCards", [])):
        yield f"missingCards[{i}].body", c.get("body", "")
    for i, r in enumerate(composed.get("risks", [])):
        yield f"risks[{i}].title", r.get("title", "")
        yield f"risks[{i}].statement", r.get("statement", "")
        for j, mv in enumerate(r.get("moves", [])):
            yield f"risks[{i}].moves[{j}]", mv
        yield f"risks[{i}].observable", r.get("observable", "")
    for name, t in composed.get("focusThemes", {}).items():
        yield f"focusThemes[{name}]", t
    for name, t in composed.get("stretchThemes", {}).items():
        yield f"stretchThemes[{name}]", t

THEME_OR_ACTION = re.compile(r"^(firstMove|risks\[\d+\]\.moves|focusThemes|stretchThemes)")

def _allowed_numbers(derived):
    base = set()
    for m in derived["members"]:
        base.update([m["comm"], m["dm"], m["collab"], m["avg"]])
    base.update([derived["avgComm"], derived["avgDm"], derived["avgCollab"],
                 derived["avgOverall"], derived["priorityScore"]])
    base.update([derived["teamSize"], derived["checkInCount"], derived["stretchCount"]])
    base.update([0, 40, 60, 70, 80, 100])
    base.update(range(0, derived["teamSize"] + 1))
    diffs = {abs(a - b) for a in base for b in base}
    return base | diffs

def _allowed_phrases(derived, team, leader_name):
    phrases = set()
    for m in derived["members"]:
        phrases.add(m["name"])
        parts = m["name"].split()
        for a in range(len(parts)):
            for b in range(a + 1, len(parts) + 1):
                phrases.add(" ".join(parts[a:b]))
    phrases.add(leader_name)
    for a_ in leader_name.split():
        phrases.add(a_)
    phrases.add(team)
    phrases.update(ARCHETYPES)
    phrases.update(["Team Effectiveness Workshop", "The Performance Lens",
                    "Leadership Insight Report", "Action Plan", "Focused Session",
                    "Communicating with Clarity", "Deciding with Conviction",
                    "Collaborating Under Pressure", "Communication",
                    "Decision-Making", "Collaboration", "Check-In", "Stretch",
                    "Steady", "What Is Missing", "One option", "One stretch",
                    "One structural option", "The data", "Worth exploring"])
    return phrases

_CAPSEQ = re.compile(r"(?<![.!?:]\s)(?<!^)\b([A-Z][a-zA-Z'-]*(?:[ ·]+[A-Z][a-zA-Z'-]*)+)")

def validate_composed(composed, derived, team, leader_name):
    fails = []
    # --- structure ---
    for k in list(WORD_LIMITS) + ["patternCards", "missingCards", "risks",
                                  "focusThemes", "stretchThemes"]:
        if k not in composed:
            fails.append(f"missing field {k}")
    if fails:
        return fails

    for k, lim in WORD_LIMITS.items():
        if not isinstance(composed[k], str) or not composed[k].strip():
            fails.append(f"{k} empty")
        elif _wc(composed[k]) > lim:
            fails.append(f"{k} over {lim} words ({_wc(composed[k])})")

    # patternCards
    pcs = composed["patternCards"]
    if len(pcs) != derived["patternCardCount"]:
        fails.append(f"patternCards count {len(pcs)} != required {derived['patternCardCount']}")
    by_name = {m["name"]: m for m in derived["members"]}
    for i, c in enumerate(pcs):
        nm = c.get("name", "")
        m2 = re.match(r"^(.*) · (Summit|Navigator|Signal|Anchor|Compass|Relay)$", nm)
        if not m2 or m2.group(1) not in by_name or by_name[m2.group(1)]["archetype"] != m2.group(2):
            fails.append(f"patternCards[{i}].name '{nm}' not '{{member}} · {{their archetype}}'")
        if _wc(c.get("body", "")) > 90:
            fails.append(f"patternCards[{i}].body over 90 words")
        if "One option:" not in c.get("body", ""):
            fails.append(f"patternCards[{i}].body missing 'One option:'")

    # missingCards
    mcs = composed["missingCards"]
    if len(mcs) != derived["missingCardCount"]:
        fails.append(f"missingCards count {len(mcs)} != required {derived['missingCardCount']}")
    for i, c in enumerate(mcs):
        nm = c.get("name", "")
        if nm not in derived["absentArchetypes"]:
            fails.append(f"missingCards[{i}].name '{nm}' not an absent archetype")
        if _wc(c.get("body", "")) > 55:
            fails.append(f"missingCards[{i}].body over 55 words")
        if f"No member fills the {nm} seat." not in c.get("body", ""):
            fails.append(f"missingCards[{i}].body missing 'No member fills the {nm} seat.'")
        if "One structural option:" not in c.get("body", ""):
            fails.append(f"missingCards[{i}].body missing 'One structural option:'")

    # risks
    risks = composed["risks"]
    if not 2 <= len(risks) <= 3:
        fails.append(f"risks count {len(risks)} not 2-3")
    for i, r in enumerate(risks):
        if _wc(r.get("title", "")) > 6:
            fails.append(f"risks[{i}].title over 6 words")
        if _wc(r.get("statement", "")) > 40:
            fails.append(f"risks[{i}].statement over 40 words")
        mvs = r.get("moves", [])
        if not 2 <= len(mvs) <= 3:
            fails.append(f"risks[{i}].moves count {len(mvs)} not 2-3")
        for j, mv in enumerate(mvs):
            if _wc(mv) > 35:
                fails.append(f"risks[{i}].moves[{j}] over 35 words")
        if _wc(r.get("observable", "")) > 25:
            fails.append(f"risks[{i}].observable over 25 words")
    if risks and derived["priorityDim"].lower() not in json.dumps(risks[:2]).lower():
        fails.append(f"neither risk 01 nor 02 addresses priority dimension {derived['priorityDim']}")

    # themes (only for the members code selected for page-5 focus)
    for nm in derived["themedCheckIn"]:
        t = composed["focusThemes"].get(nm, "")
        if not t:
            fails.append(f"focusThemes missing for {nm}")
        else:
            if _wc(t) > 45:
                fails.append(f"focusThemes[{nm}] over 45 words")
            if not t.startswith("The data:"):
                fails.append(f"focusThemes[{nm}] must start 'The data:'")
            if "Worth exploring in a 1:1" not in t:
                fails.append(f"focusThemes[{nm}] missing 'Worth exploring in a 1:1'")
    for nm in derived["themedStretch"]:
        t = composed["stretchThemes"].get(nm, "")
        if not t:
            fails.append(f"stretchThemes missing for {nm}")
        else:
            if _wc(t) > 40:
                fails.append(f"stretchThemes[{nm}] over 40 words")
            if not t.startswith("The data:"):
                fails.append(f"stretchThemes[{nm}] must start 'The data:'")
            if "One stretch:" not in t:
                fails.append(f"stretchThemes[{nm}] missing 'One stretch:'")

    # prescription
    p = composed["prescription"]
    if derived["priorityDim"] not in p:
        fails.append(f"prescription must contain '{derived['priorityDim']}' verbatim (exact spelling, hyphen included)")
    if str(derived["priorityScore"]) not in p:
        fails.append("prescription does not cite the priority score")
    if SESSION_MAP[derived["priorityDim"]] not in p:
        fails.append(f"prescription missing session '{SESSION_MAP[derived['priorityDim']]}'")
    for s in SESSION_MAP.values():
        if s != SESSION_MAP[derived["priorityDim"]] and s in p:
            fails.append(f"prescription prescribes wrong session '{s}'")

    # --- language rules, every field ---
    allowed_nums = _allowed_numbers(derived)
    allowed_phrases = _allowed_phrases(derived, team, leader_name)
    for path, text in _walk_texts(composed):
        if not isinstance(text, str):
            fails.append(f"{path} not a string")
            continue
        if "—" in text:
            fails.append(f"{path} contains an em dash")
        low = " " + text.lower() + " "
        for w in BANNED_WORDS:
            if re.search(r"\b" + re.escape(w) + r"\b", low):
                fails.append(f"{path} contains banned '{w}'")
        if PRONOUNS.search(text):
            fails.append(f"{path} contains a gendered pronoun")
        if CONTRAST.search(text):
            fails.append(f"{path} uses the 'X, not Y' contrast construction")
        if THEME_OR_ACTION.match(path) and re.search(r'["“”]', text):
            fails.append(f"{path} contains quotation marks in an action or theme")
        # number traceability (ignore the literal '1:1' shape and risk numbering)
        clean = text.replace("1:1", " ")
        for num in re.findall(r"\d+", clean):
            if int(num) not in allowed_nums:
                fails.append(f"{path} cites untraceable number {num}")
        # name traceability: capitalised multi-word sequences must be known
        for seq in _CAPSEQ.findall(text):
            s = re.sub(r"[’']s\b", "", seq).strip()  # possessives trace to the name
            if s in allowed_phrases:
                continue
            words = s.replace("·", " ").split()
            if all((w in allowed_phrases) or any(w in ph.split() for ph in allowed_phrases)
                   for w in words):
                continue
            fails.append(f"{path} contains untraceable name/phrase '{s}'")
    return fails

def _build_prompt(derived, team, date_str, leader_name):
    input_payload = {
        "team": team, "date": date_str, "leaderName": leader_name,
        "members": derived["members"],
        "avgComm": derived["avgComm"], "avgDm": derived["avgDm"],
        "avgCollab": derived["avgCollab"], "avgOverall": derived["avgOverall"],
        "priorityDim": derived["priorityDim"], "priorityScore": derived["priorityScore"],
        "checkInMembers": derived["checkInNames"], "stretchMembers": derived["stretchNames"],
        "themedCheckIn": derived["themedCheckIn"], "themedStretch": derived["themedStretch"],
        "teamSize": derived["teamSize"],
        "absentArchetypes": derived["absentArchetypes"],
    }
    schema = {
        "leaderVerdict": "string, max 60 words",
        "headline": "string, max 25 words",
        "priorityRead": "string, max 50 words",
        "firstMove": "string, max 45 words",
        "patternLabel": "string, max 6 words",
        "patternTitle": "string, max 5 words",
        "definingPatternP1": "string, max 55 words",
        "definingPatternP2": "string, max 55 words",
        "patternCards": f"array of EXACTLY {derived['patternCardCount']} objects "
                        "{label: string (small-caps kicker, e.g. 'The connector'), "
                        "name: '{{Member name}} · {{Their archetype}}', body: max 90 words, "
                        "must include 'One option:'}",
        "missingCards": (f"array of EXACTLY {derived['missingCardCount']} objects "
                         "{name: an ABSENT archetype from absentArchetypes, body: max 55 words, "
                         "must open 'No member fills the {{Archetype}} seat.' and include "
                         "'One structural option:'}") if derived["missingCardCount"] else "empty array []",
        "risks": "array of 2 or 3 objects {title: max 6 words, statement: max 40 words, "
                 "moves: array of 2-3 strings max 35 words each, observable: max 25 words "
                 "completing 'You will know this is moving when'} ordered by severity; "
                 "risk 1 must align with the priority dimension unless a sharper structural "
                 "risk exists, in which case priority appears as risk 2",
        "focusThemes": "object mapping EACH name in themedCheckIn (exactly those, no others) "
                       "to a string, max 45 words, shaped 'The data: ... Worth exploring in a 1:1, ...'",
        "stretchThemes": "object mapping EACH name in themedStretch (exactly those, no others) "
                         "to a string, max 40 words, shaped 'The data: ... One stretch: ...'",
        "prescription": f"string, max 45 words, must name {derived['priorityDim']} with score "
                        f"{derived['priorityScore']} and the session "
                        f"'{SESSION_MAP[derived['priorityDim']]}'",
        "closingVerdict": "string, max 50 words",
    }
    return (
        "Compose the Leadership Insight Report fields for the team below. "
        "Follow the Composition Spec in the system prompt exactly.\n\n"
        "INPUT PAYLOAD (the only source of truth; every name, number, count and "
        "archetype you write must trace to it):\n"
        + json.dumps(input_payload, indent=2)
        + "\n\nOUTPUT: respond with ONE strict JSON object and nothing else, "
        "with exactly these fields:\n" + json.dumps(schema, indent=2)
        + "\n\nHARD RULES — any single violation rejects the whole output:\n"
        "1. NEVER write the words he, she, him, her, his or hers anywhere. Refer to "
        "members by name, or with they, them, their. The spec's register examples "
        "predate this rule; copy their tone but NEVER their pronouns.\n"
        "2. Word limits are hard maximums. Target roughly 80 percent of each limit. "
        "Count the words of every field before you finish it, including the fixed "
        "openings like 'The data:' and 'One stretch:'.\n"
        "3. No em dashes. NEVER write the two-word sequence ', not' anywhere: no "
        "'X, not Y' constructions of any kind. British English.\n"
        "4. Every number you cite must be a payload number or a difference between "
        "two payload numbers. Never invent or re-round a number.\n"
        "5. missingCards bodies must stay under 55 words INCLUDING the required "
        "opening sentence and 'One structural option:'.\n"
        "6. The prescription must contain the priority dimension EXACTLY as spelled "
        f"in the payload ('{derived['priorityDim']}', hyphen included), the score "
        f"{derived['priorityScore']}, and the session name verbatim."
    )

def _call_api(system, user, model=None, api_key=None):
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise CompositionHalt([["ANTHROPIC_API_KEY not configured"]])
    body = json.dumps({
        "model": model or os.environ.get("LIR_COMPOSE_MODEL", "claude-sonnet-4-5"),
        "max_tokens": 8000,
        "temperature": 0.2,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        resp = json.load(r)
    return "".join(b.get("text", "") for b in resp.get("content", []))

def _extract_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.S)
    i, j = text.find("{"), text.rfind("}")
    return json.loads(text[i:j + 1])

def compose(derived, team, date_str, leader_name, model=None, api_key=None):
    """Returns validated composed dict. Raises CompositionHalt after 3 failures."""
    system = ("You are the composition engine for The Performance Lens "
              "Leadership Insight Report. The following specification governs "
              "every field you produce. Violations are rejected.\n\n" + _spec_text())
    user = _build_prompt(derived, team, date_str, leader_name)
    all_failures = []
    for attempt in range(3):
        try:
            raw = _call_api(system, user, model=model, api_key=api_key)
            composed = _extract_json(raw)
        except CompositionHalt:
            raise
        except Exception as e:
            all_failures.append([f"attempt {attempt + 1}: output not valid JSON ({type(e).__name__})"])
            user_retry = user + "\n\nYour previous output was not valid JSON. Respond with strict JSON only."
            user = user_retry
            continue
        fails = validate_composed(composed, derived, team, leader_name)
        if not fails:
            # assign risk numbering in code
            for i, r in enumerate(composed["risks"]):
                r["num"] = f"{i + 1:02d}"
            return composed
        all_failures.append(fails)
        # Repair mode: hand back the previous output and fix ONLY what failed.
        # Regenerating from scratch tends to reproduce similar violations.
        user = (_build_prompt(derived, team, date_str, leader_name)
                + "\n\nYOUR PREVIOUS OUTPUT (failed validation):\n"
                + json.dumps(composed, ensure_ascii=False)
                + "\n\nIt failed ONLY these checks:\n- " + "\n- ".join(fails[:25])
                + "\n\nReturn the FULL corrected JSON. Keep every passing field "
                "unchanged and rewrite only the failing fields. If a failure says "
                "'gendered pronoun', use the member's name or they/them/their. If it "
                "says 'over N words', cut that field to well under the limit. If it "
                "says a phrase must appear verbatim, include that exact phrase. If it "
                "says 'X, not Y', remove the ', not' construction entirely.")
    raise CompositionHalt(all_failures)
