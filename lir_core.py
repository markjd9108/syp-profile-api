#!/usr/bin/env python3
"""
Leadership Insight Report — deterministic core.
Data authority: LIR_Data_Contract (Section 3 derivations, Section 4 guards,
Section 5 input validation). No composed copy is produced here.
"""
import json, re, os
from fractions import Fraction
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

ARCHETYPES = ["Summit", "Navigator", "Signal", "Anchor", "Compass", "Relay"]
DIMS = [("Communication", "comm"), ("Decision-Making", "dm"), ("Collaboration", "collab")]

# Band scheme (single source: Foundation/Emerging/Developing/Strong @40/60/80)
def band(score) -> str:
    if score >= 80: return "Strong"
    if score >= 60: return "Developing"
    if score >= 40: return "Emerging"
    return "Foundation"

class LIRInputError(ValueError):
    pass

def rnd(x) -> int:
    """Round-half-up on an exact Fraction/number."""
    if isinstance(x, Fraction):
        d = Decimal(x.numerator) / Decimal(x.denominator)
    else:
        d = Decimal(str(x))
    return int(d.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

def validate_input(team, date_str, leader_name, members):
    errors, warnings = [], []
    if not team or not str(team).strip():
        errors.append("team is empty")
    if not leader_name or not str(leader_name).strip():
        errors.append("leaderName is empty")
    try:
        d = datetime.strptime(date_str, "%d %B %Y")
        canonical = f"{d.day} {d.strftime('%B %Y')}"
        if canonical != date_str:
            errors.append(f"date must be 'D Month YYYY' (got '{date_str}', expected '{canonical}')")
    except (ValueError, TypeError):
        errors.append(f"date must be 'D Month YYYY' (got '{date_str}')")
    if not isinstance(members, list) or len(members) == 0:
        errors.append("members missing")
        return errors, warnings
    n = len(members)
    if n < 4:
        warnings.append(f"teamSize {n} below product minimum of 4")
    if n > 30:
        warnings.append(f"teamSize {n} above 30; layout tested to 30 rows")
    names = []
    for i, m in enumerate(members):
        nm = str(m.get("name", "")).strip()
        if not nm:
            errors.append(f"member {i}: empty name")
        names.append(nm)
        if m.get("archetype") not in ARCHETYPES:
            errors.append(f"member {nm or i}: archetype '{m.get('archetype')}' not one of the six")
        for _, key in DIMS:
            v = m.get(key)
            if not isinstance(v, int) or isinstance(v, bool) or not (0 <= v <= 100):
                errors.append(f"member {nm or i}: {key} must be an integer 0-100 (got {v!r})")
    if len(set(names)) != len(names):
        errors.append("member names are not unique")
    return errors, warnings

def derive(members):
    """Recompute ALL derived fields from raw scores. Never trust upstream averages."""
    out_members = []
    for m in members:
        comm, dm, collab = m["comm"], m["dm"], m["collab"]
        avg = rnd(Fraction(comm + dm + collab, 3))
        if min(comm, dm, collab) <= 59:
            flag = "Check-In"
        else:
            flag = "Steady"  # Stretch retired (CO3, Mark 10 Jul 2026)
        out_members.append({
            "name": m["name"], "archetype": m["archetype"],
            "comm": comm, "dm": dm, "collab": collab,
            "bandComm": band(comm), "bandDm": band(dm), "bandCollab": band(collab),
            "avg": avg, "flag": flag,
        })

    n = len(out_members)
    dim_means = {}   # exact Fractions
    dim_spread = {}
    for label, key in DIMS:
        vals = [m[key] for m in out_members]
        dim_means[label] = Fraction(sum(vals), n)
        dim_spread[label] = max(vals) - min(vals)

    avgComm = rnd(dim_means["Communication"])
    avgDm = rnd(dim_means["Decision-Making"])
    avgCollab = rnd(dim_means["Collaboration"])
    avgOverall = rnd(sum(dim_means.values(), Fraction(0)) / 3)

    # Priority: lowest exact team average; tie-break widest spread; then fixed order.
    order = ["Communication", "Decision-Making", "Collaboration"]
    priorityDim = sorted(order, key=lambda d: (dim_means[d], -dim_spread[d], order.index(d)))[0]
    priorityScore = {"Communication": avgComm, "Decision-Making": avgDm,
                     "Collaboration": avgCollab}[priorityDim]
    priorityBand = band(priorityScore)
    priorityBelow = priorityScore <= 59

    # Banded spread per dimension (lowest member band .. highest member band)
    _order = ["Foundation", "Emerging", "Developing", "Strong"]
    dimBandSpread = {}
    for label, key in DIMS:
        bs = sorted((band(m[key]) for m in out_members), key=_order.index)
        dimBandSpread[label] = (bs[0], bs[-1])

    checkIn = [m for m in out_members if m["flag"] == "Check-In"]
    stretch = [m for m in out_members if m["flag"] == "Stretch"]

    # Change Order 1: every flagged member gets a theme; page 5 tables
    # paginate. Theme length per group (35 words at <=8 members, 25 at 9+).
    themed_ci_names = [m["name"] for m in checkIn]
    themed_st_names = [m["name"] for m in stretch]
    theme_words_ci = 25 if len(checkIn) >= 9 else 35
    theme_words_st = 25 if len(stretch) >= 9 else 35

    present = {m["archetype"] for m in out_members}
    absent = [a for a in ARCHETYPES if a not in present]

    # Page 4 card rule (Data Contract Section 3)
    patternCardCount = n if n <= 4 else min(4, max(3, n - 2))

    return {
        "members": out_members,
        "avgComm": avgComm, "avgDm": avgDm, "avgCollab": avgCollab,
        "avgOverall": avgOverall,
        "priorityDim": priorityDim, "priorityScore": priorityScore,
        "priorityBand": priorityBand, "priorityBelow": priorityBelow,
        "bandComm": band(avgComm), "bandDm": band(avgDm),
        "bandCollab": band(avgCollab), "bandOverall": band(avgOverall),
        "dimBandSpread": dimBandSpread,
        "priorityMemberScores": {m["name"]: m[dict((l, k) for l, k in DIMS)[priorityDim]] for m in out_members},
        "checkInCount": len(checkIn), "stretchCount": len(stretch), "teamSize": n,
        "checkInNames": [m["name"] for m in checkIn],
        "stretchNames": [m["name"] for m in stretch],
        "themedCheckIn": themed_ci_names,
        "themedStretch": themed_st_names,
        "themeWordsCi": theme_words_ci,
        "themeWordsSt": theme_words_st,
        "absentArchetypes": absent,
        "patternCardCount": patternCardCount,
        "missingCardCount": min(2, len(absent)),
        "cards": [
            {"label": "Communication", "band": band(avgComm)},
            {"label": "Decision-Making", "band": band(avgDm)},
            {"label": "Collaboration", "band": band(avgCollab)},
        ],
    }

def build_payload(team, date_str, leader_name, derived, composed):
    """Merge derived + composed into the template payload."""
    members = []
    for m in derived["members"]:
        mm = {"name": m["name"], "archetype": m["archetype"],
              "comm": m["bandComm"], "dm": m["bandDm"],
              "collab": m["bandCollab"], "flag": m["flag"]}
        if m["name"] in derived["themedCheckIn"]:
            mm["focusTheme"] = composed["focusThemes"][m["name"]]
        elif m["name"] in derived["themedStretch"]:
            mm["stretchTheme"] = composed["stretchThemes"][m["name"]]
        members.append(mm)
    return {
        "team": team, "date": date_str, "leaderName": leader_name,
        "members": members,
        "cards": derived["cards"],
        "avgComm": derived["bandComm"], "avgDm": derived["bandDm"],
        "avgCollab": derived["bandCollab"],
        "priorityDim": derived["priorityDim"],
        "priorityBand": derived["priorityBand"],
        "priorityBelow": derived["priorityBelow"],
        "leaderVerdict": composed["leaderVerdict"],
        "workingWell": composed["workingWell"],
        "needsSupport": composed["needsSupport"],
        "teamRisk": composed["teamRisk"],
        "teamOpportunity": composed["teamOpportunity"],
        "themeShort": derived["themeWordsCi"] == 25 and (derived["stretchCount"] == 0 or derived["themeWordsSt"] == 25),
        "firstMove": composed["firstMove"],
        "patternLabel": composed["patternLabel"],
        "patternTitle": composed["patternTitle"],
        "definingPatternP1": composed["definingPatternP1"],
        "definingPatternP2": composed["definingPatternP2"],
        "patternCards": composed["patternCards"],
        "missingCards": composed["missingCards"],
        "risks": composed["risks"],
        "prescription": composed["prescription"],
        "closingVerdict": composed["closingVerdict"],
    }

_TEMPLATE_CACHE = None

def inject(payload, template_path=None):
    """Inject the payload into the wired template bundle."""
    global _TEMPLATE_CACHE
    path = template_path or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "lir_template_wired.html")
    if _TEMPLATE_CACHE is None or template_path:
        tpl = open(path).read()
        if not template_path:
            _TEMPLATE_CACHE = tpl
    else:
        tpl = _TEMPLATE_CACHE
    token = "__LIR_PAYLOAD_JSON__"
    assert token in tpl
    # payload JSON, escaped as JSON-string content (it sits inside the
    # JSON-encoded __bundler/template string)
    inner = json.dumps(json.dumps(payload, ensure_ascii=False))[1:-1]
    # File-level escaping: never let "</" appear inside the outer script element
    inner = inner.replace("</", "<\\u002F")
    return tpl.replace(token, inner)

def report_filename(team, date_str):
    d = datetime.strptime(date_str, "%d %B %Y")
    team_part = re.sub(r"\s+", "_", team.strip())
    return f"LIR_{team_part}_{d.strftime('%Y-%m-%d')}.pdf"
