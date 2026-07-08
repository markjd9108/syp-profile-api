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
    "leaderVerdict": 60, "firstMove": 45,
    "workingWell": 35, "needsSupport": 35, "teamRisk": 35, "teamOpportunity": 35,
    "patternLabel": 6, "patternTitle": 5,
    "definingPatternP1": 55, "definingPatternP2": 55,
    "prescription": 45, "closingVerdict": 50,
}

# Spec v2 §1/§2: maximum score references per block (None = no limit check)
SCORE_LIMITS = {
    "leaderVerdict": 1, "firstMove": 0,
    "workingWell": 0, "needsSupport": 0, "teamRisk": 0, "teamOpportunity": 0,
    "patternLabel": 0, "patternTitle": 0,
    "prescription": 1, "closingVerdict": 1,
}

RITUAL_JARGON = ["sprint", "retrospective", "retro", "stand-up", "standup",
                 "backlog", "scrum", "kanban", "okr"]
FOLKSY = ["wobble", "wobbles", "juggling", "juggle", "spinning plates",
          "drops the ball", "drop the ball", "dropped the ball"]
TENTATIVE = ["worth trying", "you might consider", "might consider", "maybe",
             "could be worth", "give this a go", "worth a try"]
CITATION_MARKERS = ["study", "studies", "research", "survey", "according to", "%"]

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

def _strip_exempt(text, member_names=()):
    """Remove tokens that legitimately carry digits: member names, '1:1',
    the product phrase '90-minute'."""
    clean = text
    for nm in sorted(member_names, key=len, reverse=True):
        clean = clean.replace(nm, " ")
    clean = clean.replace("1:1", " ")
    clean = re.sub(r"90[- ]minutes?", " ", clean, flags=re.I)
    return clean

def _score_refs(text, member_names=()):
    """Count digit-bearing score references after exemptions."""
    return len(re.findall(r"\d+", _strip_exempt(text, member_names)))

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
    # v2: risk-01/priority alignment is thematic (insight-first copy no longer
    # names dimensions verbatim); enforced through the prompt, checked in review.

    # themes: every flagged member, v2 shape (insight sentence + fixed lead-in),
    # length per group size, ZERO scores (the row's columns already show them)
    member_names = [m["name"] for m in derived["members"]]
    ci_lim = derived["themeWordsCi"]
    st_lim = derived["themeWordsSt"]
    for nm in derived["themedCheckIn"]:
        t = composed["focusThemes"].get(nm, "")
        if not t:
            fails.append(f"focusThemes missing for {nm}")
        else:
            if _wc(t) > ci_lim:
                fails.append(f"focusThemes[{nm}] over {ci_lim} words")
            if "Worth exploring in a 1:1" not in t:
                fails.append(f"focusThemes[{nm}] missing 'Worth exploring in a 1:1'")
            if _score_refs(t, member_names) > 0:
                fails.append(f"focusThemes[{nm}] contains a score; themes carry no numbers")
    for nm in derived["themedStretch"]:
        t = composed["stretchThemes"].get(nm, "")
        if not t:
            fails.append(f"stretchThemes missing for {nm}")
        else:
            if _wc(t) > st_lim:
                fails.append(f"stretchThemes[{nm}] over {st_lim} words")
            if "One stretch:" not in t:
                fails.append(f"stretchThemes[{nm}] missing 'One stretch:'")
            if _score_refs(t, member_names) > 0:
                fails.append(f"stretchThemes[{nm}] contains a score; themes carry no numbers")

    # prescription (Spec v2: priority area in plain words; score optional)
    p = composed["prescription"]
    dim_plain = derived["priorityDim"].lower().replace("-", " ")
    if dim_plain not in p.lower().replace("-", " "):
        fails.append(f"prescription must name the priority area ('{dim_plain}' in plain words)")
    if SESSION_MAP[derived["priorityDim"]] not in p:
        fails.append(f"prescription missing session '{SESSION_MAP[derived['priorityDim']]}'")
    for s in SESSION_MAP.values():
        if s != SESSION_MAP[derived["priorityDim"]] and s in p:
            fails.append(f"prescription prescribes wrong session '{s}'")
    if not re.search(r"90[- ]minute", p, re.I):
        fails.append("prescription must describe the Focused Session as a 90-minute development session")
    if re.search(r"\bworkshop\b", p, re.I):
        fails.append("prescription must not contain the word 'workshop'")
    if re.search(r"half[- ]day", p, re.I):
        fails.append("prescription must not contain 'half-day'")

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
        for w in RITUAL_JARGON:
            if re.search(r"\b" + re.escape(w) + r"s?\b", low):
                fails.append(f"{path} contains workplace-ritual jargon '{w}'")
        for w in FOLKSY:
            if w in low:
                fails.append(f"{path} contains colloquial imagery '{w}'")
        for w in TENTATIVE:
            if re.search(r"\b" + re.escape(w) + r"\b", low):
                fails.append(f"{path} uses tentative framing '{w}'")
        if THEME_OR_ACTION.match(path):
            for w in CITATION_MARKERS:
                if (w in low) if w == "%" else re.search(r"\b" + re.escape(w) + r"\b", low):
                    fails.append(f"{path} cites a study/statistic ('{w}'); moves never cite sources")
        # Spec v2 score-frequency scan (member names exempted; they may carry digits)
        mnames = [m["name"] for m in derived["members"]]
        sr = _score_refs(text, mnames)
        base_field = path.split("[")[0]
        if base_field in SCORE_LIMITS and sr > SCORE_LIMITS[base_field]:
            fails.append(f"{path} has {sr} score references; maximum {SCORE_LIMITS[base_field]}")
        if path.startswith("patternCards") and path.endswith(".body") and sr > 1:
            fails.append(f"{path} has more than one score reference")
        if path.startswith("missingCards") and sr > 0:
            fails.append(f"{path} contains a score; missing cards carry no numbers")
        if re.search(r"\.title$|\.observable$", path) and sr > 0:
            fails.append(f"{path} contains a number; titles and observables carry none")
        if re.search(r"\.statement$", path) and sr > 1:
            fails.append(f"{path} has more than one score reference")
        if re.search(r"\.moves\[\d+\]$", path) and sr > 0:
            fails.append(f"{path} contains a score; moves carry no numbers")
        # number traceability (names, '1:1' and '90-minute' exempted)
        clean = _strip_exempt(text, [m["name"] for m in derived["members"]])
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

    combined = (_score_refs(composed.get("definingPatternP1", ""), member_names)
                + _score_refs(composed.get("definingPatternP2", ""), member_names))
    if combined > 2:
        fails.append(f"definingPatternP1+P2 carry {combined} score references; maximum 2 combined")
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
        "leaderVerdict": "string, max 60 words, addressed to the leader by first name once; "
                         "what the team is good at, what holds it back, the shape of the work "
                         "ahead; maximum ONE number, trailing",
        "workingWell": "string, max 35 words, ZERO numbers: what the team does well as observed behaviour",
        "needsSupport": "string, max 35 words, ZERO numbers: where the team underperforms, behaviour and consequence",
        "teamRisk": "string, max 35 words, ZERO numbers: the single most important risk and what it costs",
        "teamOpportunity": "string, max 35 words, ZERO numbers: the growth opening, what becomes possible",
        "firstMove": "string, max 45 words, ZERO numbers: need stated as a declarative, then one "
                     "established practice the leader can start this week",
        "patternLabel": "string, max 6 words",
        "patternTitle": "string, max 5 words",
        "definingPatternP1": "string, max 55 words: the structural fact of this team",
        "definingPatternP2": "string, max 55 words: the risk that follows and the direction. "
                             "Maximum TWO numbers across P1+P2 combined, trailing only",
        "patternCards": f"array of EXACTLY {derived['patternCardCount']} objects "
                        "{label: small-caps kicker, name: '{{Member name}} · {{Their archetype}}', "
                        "body: max 90 words, three beats: what this person GIVES, what they NEED, "
                        "one way to USE them better introduced 'One option:'. Maximum ONE score, "
                        "trailing or parenthetical; zero is often better}",
        "missingCards": (f"array of EXACTLY {derived['missingCardCount']} objects "
                         "{name: an ABSENT archetype from absentArchetypes, body: max 55 words, "
                         "ZERO numbers, opens 'No member fills the {{Archetype}} seat.' and includes "
                         "'One structural option:'}") if derived["missingCardCount"] else "empty array []",
        "risks": "array of 2 or 3 objects {title: max 6 words, no numbers; statement: max 40 words, "
                 "behavioural terms, maximum ONE number trailing; moves: 2-3 strings max 35 words each, "
                 "need-then-practice shape, ZERO numbers, no schedules; observable: max 25 words "
                 "completing 'You will know this is moving when', visible behaviour, no numbers} "
                 "ordered by severity; risk 1 aligns with the priority dimension unless a sharper "
                 "structural risk exists",
        "focusThemes": f"object mapping EACH name in themedCheckIn (exactly those, no others) to a "
                       f"string, max {derived['themeWordsCi']} words: one sentence of insight about "
                       "this person's pattern in plain words, then 'Worth exploring in a 1:1,' plus "
                       "the theme as a subject. ZERO numbers",
        "stretchThemes": f"object mapping EACH name in themedStretch (exactly those, no others) to a "
                         f"string, max {derived['themeWordsSt']} words: one sentence naming the "
                         "strength in plain words, then 'One stretch:' plus a concrete extension. "
                         "ZERO numbers, strength framing",
        "prescription": f"string, max 45 words: names the priority area in plain words "
                        f"('{derived['priorityDim']}' verbatim; the score {derived['priorityScore']} "
                        f"may appear once, trailing) and the session "
                        f"'{SESSION_MAP[derived['priorityDim']]}', described as a 90-minute "
                        "development session. NEVER the words workshop or half-day",
        "closingVerdict": "string, max 50 words: what strong looks like and the two or three moves "
                          "that get there; maximum one number",
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
        "1. INSIGHT FIRST, NUMBER LAST. Never open a sentence with a score. The four "
        "at-a-glance blocks, firstMove, all themes, all moves, missingCards, titles and "
        "observables carry ZERO numbers. Verdicts, statements, prescription: at most ONE "
        "number, trailing. P1+P2: at most two combined. Never list a member's scores in prose.\n"
        "2. NEVER write he, she, him, her, his or hers. Use the member's name or "
        "they, them, their.\n"
        "3. Word limits are hard maximums; target roughly 70 percent of each. Count words "
        "including fixed openings like 'One stretch:'.\n"
        "4. No em dashes. NEVER write the two-word sequence ', not'. British English.\n"
        "5. No workplace-ritual jargon: sprint, retrospective, retro, stand-up, backlog, "
        "scrum, kanban, OKR. Use neutral forms: weekly team meeting, project review, "
        "regular check-in.\n"
        "6. No colloquial imagery (wobbles, juggling, spinning plates, drops the ball) and "
        "no tentative framing (worth trying, you might consider, maybe, could be worth). "
        "State the need as a declarative, then name the practice.\n"
        "7. A Focused Session is a 90-minute development session. Never call it a workshop "
        "or a half-day.\n"
        "8. Never cite a study, author, firm, statistic or percentage.\n"
        "9. Characterise archetypes ONLY per the canonical definitions in the spec: "
        "Relay executes to clear briefs; Navigator makes the call in ambiguity; Signal "
        "reads the room, the informal connector; Summit raises the standard; Anchor is "
        "the steadying force under pressure; Compass builds structure out of ambiguity.\n"
        "10. Any number you do use must be a payload number or a difference of two "
        "payload numbers. Never invent or re-round."
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

def compose(derived, team, date_str, leader_name, model=None, api_key=None,
            extra_rules=None):
    """Returns validated composed dict. Raises CompositionHalt after 3 failures.
    extra_rules: additional hard constraints (e.g. page-overflow feedback from
    a previous render round)."""
    system = ("You are the composition engine for The Performance Lens "
              "Leadership Insight Report. The following specification governs "
              "every field you produce. Violations are rejected.\n\n" + _spec_text())
    base_user = _build_prompt(derived, team, date_str, leader_name)
    if extra_rules:
        base_user += "\n\nADDITIONAL HARD CONSTRAINT FOR THIS GENERATION:\n" + extra_rules
    user = base_user
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
        user = (base_user
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
