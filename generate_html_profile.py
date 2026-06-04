"""
generate_html_profile.py
TEW Profile — HTML Template Injection Engine v1.0

Loads the archetype HTML template, injects participant-specific data
(name, scores, cohort info, dates), and returns ready-to-render HTML.
The outer bundler wrapper is preserved so Playwright gets full asset loading.
"""

import json
import math
import re
import os
import datetime

# ── Directory containing the 6 HTML templates ──────────────────────────────────
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

# Working Style (V3) — shared content/resolver + HTML renderer
try:
    from working_style import build_blocks as _ws_build_blocks
    from working_style_html import render_working_style_section as _ws_render
except Exception:
    _ws_build_blocks = None
    _ws_render = None


# ── Sample data baked into every template (what we're replacing) ───────────────
SAMPLE = {
    "name":       "Alex Nguyen",
    "initials":   "AN",
    "company":    "AED Global",
    "month_year": "May 2026",
    "cohort":     "TEW Q2",         # appears as "AED Global · TEW Q2"
    "date":       "May 18, 2026",
    "profile_id": "TPL-2604-S-074",
    "cohort_size": 23,
    "comm_avg":   60,
    "dec_avg":    54,
    "collab_avg": 52,
    "comm_hp":    85,
    "dec_hp":     80,
    "collab_hp":  79,
}

# ── Archetype key → template filename ──────────────────────────────────────────
ARCHETYPE_FILES = {
    "anchor":    "TEW_Self Assessment Profile_The Anchor.html",
    "compass":   "TEW_Self Assessment Profile_The Compass.html",
    "navigator": "TEW_Self Assessment Profile_The Navigator.html",
    "relay":     "TEW_Self Assessment Profile_The Relay.html",
    "signal":    "TEW_Self Assessment Profile_The Signal.html",
    "summit":    "TEW_Self Assessment Profile_The Summit.html",
}

# ── Band helpers ────────────────────────────────────────────────────────────────
def get_band(score: int):
    """Return (css_key, label, axis_start) for a given score 0–100."""
    if score >= 80: return "strong",     "Strong",     80
    if score >= 60: return "developing", "Developing", 60
    if score >= 40: return "emerging",   "Emerging",   40
    return            "foundation",  "Foundation", 0

def score_to_dot(score: int):
    """Return (cx, cy) for the gauge dot SVG position."""
    angle = (1 - score / 100) * math.pi
    cx = round(150 + 130 * math.cos(angle))
    cy = round(160 - 130 * math.sin(angle))
    return cx, cy

def make_gauge_axis(band_start_val: int) -> str:
    axis_vals = [0, 40, 60, 80, 100]
    spans = []
    for v in axis_vals:
        if v == band_start_val:
            spans.append(f'<span class="band-start">{v}</span>')
        else:
            spans.append(f'<span>{v}</span>')
    return "".join(spans)

def get_initials(name: str) -> str:
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper()

# ── Score section replacer ──────────────────────────────────────────────────────
def replace_score_section(html: str, dim: str, old_score: int, new_score: int,
                           old_avg: int, new_avg: int,
                           old_hp: int, new_hp: int) -> str:
    """
    Replace all score-related values for one dimension (comm/dec/collab).
    dim: human label e.g. "Communication", "Decision-Making", "Collaboration"
    """
    old_band_key, old_band_label, old_axis_start = get_band(old_score)
    new_band_key, new_band_label, new_axis_start = get_band(new_score)

    old_cx, old_cy = score_to_dot(old_score)
    new_cx, new_cy = score_to_dot(new_score)

    # 1. Card header comment
    html = html.replace(
        f"<!-- ====== {dim} {old_score} · {old_band_label} ====== -->",
        f"<!-- ====== {dim} {new_score} · {new_band_label} ====== -->"
    )

    # 2. Band CSS class on the article element (only within this dimension card)
    html = html.replace(
        f'"card relative overflow-hidden band-{old_band_key}"',
        f'"card relative overflow-hidden band-{new_band_key}"',
        1  # replace only first occurrence after we've handled prior dims
    )

    # 3. Band pill text
    html = html.replace(
        f'<span class="band-pill">{old_band_label}</span>',
        f'<span class="band-pill">{new_band_label}</span>',
        1
    )

    # 4. Workshop card score comment + score text
    html = html.replace(
        f"<!-- {dim} {old_score} -->",
        f"<!-- {dim} {new_score} -->"
    )
    # Score text in workshop bar (mono tabular) — replace first remaining occurrence
    html = html.replace(
        f'mono tabular font-medium">{old_score}</span>',
        f'mono tabular font-medium">{new_score}</span>',
        1
    )

    # 5. Bar fill width (may have "muted" class for non-leading scores)
    html = re.sub(
        rf'(cohort-bar-fill[^"]*)" style="width: {old_score}%"',
        rf'\1" style="width: {new_score}%"',
        html, count=1
    )

    # 6. Cohort avg line + label
    html = html.replace(
        f'cohort-avg-line" style="left: {old_avg}%"',
        f'cohort-avg-line" style="left: {new_avg}%"',
        1
    )
    html = html.replace(
        f'style="left: {old_avg}%">Cohort avg <span class="v">{old_avg}</span>',
        f'style="left: {new_avg}%">Cohort avg <span class="v">{new_avg}</span>',
        1
    )

    # 7. High performers line + label
    html = html.replace(
        f'cohort-top-line" style="left: {old_hp}%"',
        f'cohort-top-line" style="left: {new_hp}%"',
        1
    )
    html = html.replace(
        f'style="left: {old_hp}%">High performers <span class="v">{old_hp}</span>',
        f'style="left: {new_hp}%">High performers <span class="v">{new_hp}</span>',
        1
    )

    # 8. Gauge arc
    html = html.replace(
        f"<!-- score {old_score} -->",
        f"<!-- score {new_score} -->"
    )
    html = html.replace(
        f'stroke-dasharray="{old_score} 100"',
        f'stroke-dasharray="{new_score} 100"',
        1
    )

    # 9. Score dot
    html = html.replace(
        f"<!-- score dot at {old_score} -->",
        f"<!-- score dot at {new_score} -->"
    )
    html = html.replace(
        f'<circle cx="{old_cx}" cy="{old_cy}" r="5.5"',
        f'<circle cx="{new_cx}" cy="{new_cy}" r="5.5"',
        1
    )

    # 10. Gauge number
    html = html.replace(
        f'<div class="num band-text">{old_score}</div>',
        f'<div class="num band-text">{new_score}</div>',
        1
    )

    # 11. Gauge axis band-start marker
    old_axis = make_gauge_axis(old_axis_start)
    new_axis = make_gauge_axis(new_axis_start)
    html = html.replace(old_axis, new_axis, 1)

    return html


# ── Main injection function ─────────────────────────────────────────────────────
def inject_participant_data(archetype_key: str, participant: dict) -> str:
    """
    archetype_key: 'signal' | 'anchor' | 'navigator' | 'relay' | 'summit' | 'compass'
    participant: {
        name, company, cohort, assessed_date, profile_id,
        comm_score, dec_score, collab_score,
        comm_avg, dec_avg, collab_avg,        (optional, defaults to sample values)
        comm_hp,  dec_hp,  collab_hp,         (optional)
        cohort_size, cohort_pct               (optional)
    }
    Returns: full HTML string ready for Playwright
    """
    key = archetype_key.lower()
    if key not in ARCHETYPE_FILES:
        raise ValueError(f"Unknown archetype: {archetype_key!r}. "
                         f"Must be one of: {list(ARCHETYPE_FILES)}")

    template_path = os.path.join(TEMPLATES_DIR, ARCHETYPE_FILES[key])
    with open(template_path, "r", encoding="utf-8") as f:
        outer_html = f.read()

    # Extract inner template JSON
    match = re.search(
        r'(<script type="__bundler/template">)(.*?)(</script>)',
        outer_html, re.DOTALL
    )
    if not match:
        raise RuntimeError("Could not find __bundler/template script tag")

    inner_html = json.loads(match.group(2).strip())

    # ── Extract per-template original score values ──────────────────────────────
    orig_scores = re.findall(r'stroke-dasharray="(\d+) 100"', inner_html)
    if len(orig_scores) < 3:
        raise RuntimeError(f"Expected 3 gauge arcs, found {len(orig_scores)}")
    old_comm, old_dec, old_collab = int(orig_scores[0]), int(orig_scores[1]), int(orig_scores[2])

    # ── Participant values ───────────────────────────────────────────────────────
    name         = participant["name"]
    initials     = get_initials(name)
    company      = participant["company"]
    cohort       = participant.get("cohort", "TEW Q2")
    assessed_date = participant.get("assessed_date",
                                    datetime.datetime.now().strftime("%B %d, %Y").replace(" 0", " "))
    profile_id   = participant.get("profile_id", SAMPLE["profile_id"])
    month_year   = participant.get("month_year",
                                   datetime.datetime.now().strftime("%B %Y"))

    new_comm   = int(participant["comm_score"])
    new_dec    = int(participant["dec_score"])
    new_collab = int(participant["collab_score"])

    new_comm_avg   = int(participant.get("comm_avg",   SAMPLE["comm_avg"]))
    new_dec_avg    = int(participant.get("dec_avg",    SAMPLE["dec_avg"]))
    new_collab_avg = int(participant.get("collab_avg", SAMPLE["collab_avg"]))

    new_comm_hp    = int(participant.get("comm_hp",    SAMPLE["comm_hp"]))
    new_dec_hp     = int(participant.get("dec_hp",     SAMPLE["dec_hp"]))
    new_collab_hp  = int(participant.get("collab_hp",  SAMPLE["collab_hp"]))

    cohort_size = int(participant.get("cohort_size", SAMPLE["cohort_size"]))
    cohort_pct  = int(participant.get("cohort_pct",  0))

    t = inner_html  # working copy

    # ── 1. Identity fields ───────────────────────────────────────────────────────
    # Title tag
    t = re.sub(
        r'<title>.*?</title>',
        f'<title>The Performance Lens · Participant Profile · {name}</title>',
        t
    )
    # Name displays (3 occurrences with distinct surrounding context)
    t = t.replace(
        f'<div class="text-[14px] font-semibold">{SAMPLE["name"]}</div>',
        f'<div class="text-[14px] font-semibold">{name}</div>'
    )
    # Footer mono line
    t = t.replace(
        f'{SAMPLE["name"]} · {SAMPLE["company"]} · {SAMPLE["profile_id"]}',
        f'{name} · {company} · {profile_id}'
    )

    # Initials avatar
    t = t.replace(
        f'<span class="avatar">{SAMPLE["initials"]}</span>',
        f'<span class="avatar">{initials}</span>'
    )

    # ── 2. Company + date ────────────────────────────────────────────────────────
    t = t.replace(
        f'{SAMPLE["company"]} · {SAMPLE["month_year"]}',
        f'{company} · {month_year}'
    )
    t = t.replace(
        f'{SAMPLE["company"]} · {SAMPLE["cohort"]}',
        f'{company} · {cohort}'
    )
    # Workshop card also shows cohort in "Q2 2026 · Company" format
    t = re.sub(
        r'[A-Z]\d \d{4} · ' + re.escape(SAMPLE["company"]),
        cohort.split()[-1] + ' ' + month_year.split()[-1] + ' · ' + company,
        t
    )
    # Catch-all: replace any remaining occurrences of sample company name
    t = t.replace(SAMPLE["company"], company)

    # ── 3. Profile ID ────────────────────────────────────────────────────────────
    t = t.replace(SAMPLE["profile_id"], profile_id)

    # ── 4. Assessed date ─────────────────────────────────────────────────────────
    t = t.replace(SAMPLE["date"], assessed_date)

    # ── 5. Cohort position ───────────────────────────────────────────────────────
    t = re.sub(
        r'Top \d+% of \d+ participants',
        f'Top {cohort_pct}% of {cohort_size} participants' if cohort_pct else '',
        t
    )
    t = t.replace(
        f'Your position vs. {SAMPLE["cohort_size"]} participants',
        f'Your position vs. {cohort_size} participants'
    )

    # ── 6. Score sections (comm → dec → collab, in document order) ───────────────
    t = replace_score_section(
        t, "Communication", old_comm, new_comm,
        SAMPLE["comm_avg"], new_comm_avg,
        SAMPLE["comm_hp"],  new_comm_hp
    )
    t = replace_score_section(
        t, "Decision-Making", old_dec, new_dec,
        SAMPLE["dec_avg"], new_dec_avg,
        SAMPLE["dec_hp"],  new_dec_hp
    )
    t = replace_score_section(
        t, "Collaboration", old_collab, new_collab,
        SAMPLE["collab_avg"], new_collab_avg,
        SAMPLE["collab_hp"],  new_collab_hp
    )

    # ── 7. Cohort snapshot text (page 1 right panel) ──────────────────────────────
    # These plain-text lines are NOT touched by replace_score_section (which only
    # handles the bar/gauge section on page 2).  Replace them explicitly.
    t = t.replace(
        f'Communication&nbsp;&nbsp;&nbsp;&nbsp;{old_comm} · cohort {SAMPLE["comm_avg"]} · high performers {SAMPLE["comm_hp"]}',
        f'Communication&nbsp;&nbsp;&nbsp;&nbsp;{new_comm} · cohort {new_comm_avg} · high performers {new_comm_hp}'
    )
    t = t.replace(
        f'Decision-Making&nbsp;&nbsp;{old_dec} · cohort {SAMPLE["dec_avg"]} · high performers {SAMPLE["dec_hp"]}',
        f'Decision-Making&nbsp;&nbsp;{new_dec} · cohort {new_dec_avg} · high performers {new_dec_hp}'
    )
    t = t.replace(
        f'Collaboration&nbsp;&nbsp;&nbsp;&nbsp;{old_collab} · cohort {SAMPLE["collab_avg"]} · high performers {SAMPLE["collab_hp"]}',
        f'Collaboration&nbsp;&nbsp;&nbsp;&nbsp;{new_collab} · cohort {new_collab_avg} · high performers {new_collab_hp}'
    )

    # ── Working Style layer (V3): insert before the performance scoring section ──
    ws = participant.get("working_style")
    if ws and _ws_render and _ws_build_blocks:
        _ws_blocks = ws if isinstance(ws, list) else (
            _ws_build_blocks(ws) if isinstance(ws, dict)
            and all(f"ws_q{i}" in ws for i in range(1, 10)) else None)
        if _ws_blocks:
            _anchor = "<!-- ============== DIMENSION CARDS ============== -->"
            if _anchor in t:
                t = t.replace(_anchor, _ws_render(_ws_blocks) + "\n\n    " + _anchor, 1)
            else:
                raise RuntimeError("Working Style anchor (DIMENSION CARDS) not found in template")

    # ── Re-encode template JSON and splice back into outer HTML ──────────────────
    # Escape </script> as / to prevent premature script tag closure in HTML
    new_json = json.dumps(t).replace('</script>', '<\\u002Fscript>')

    # Patch the outer wrapper HTML (title tag) before the template script block
    outer_before = re.sub(
        r'<title>.*?</title>',
        f'<title>The Performance Lens · Participant Profile · {name}</title>',
        outer_html[:match.start()]
    )

    new_outer = (
        outer_before
        + match.group(1)
        + new_json
        + match.group(3)
        + outer_html[match.end():]
    )
    return new_outer


# ── Quick CLI test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    arch = sys.argv[1] if len(sys.argv) > 1 else "signal"
    result = inject_participant_data(arch, {
        "name":         "Test Participant",
        "company":      "Demo Corp",
        "cohort":       "TEW Q3",
        "assessed_date":"June 1, 2026",
        "profile_id":   "TPL-TEST-001",
        "month_year":   "June 2026",
        "comm_score":   72,
        "dec_score":    55,
        "collab_score": 38,
        "cohort_size":  18,
        "cohort_pct":   15,
    })
    out = f"/tmp/test_profile_{arch}.html"
    with open(out, "w") as f:
        f.write(result)
    print(f"Written to {out}  ({len(result)//1024}KB)")
