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
    from working_style_html import STYLE_ICONS as _STYLE_ICONS
except Exception:
    _ws_build_blocks = None
    _ws_render = None
    _STYLE_ICONS = {}

# Personalized lead paragraph (hybrid: Claude API with composer fallback)
try:
    from lead_engine import generate_lead as _generate_lead
except Exception:
    _generate_lead = None


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

def _show_band_only(t: str, comm_score, dec_score, collab_score) -> str:
    """Participant-facing de-scoring (#2): show the BAND, not the number.
    Swaps each gauge number for its band word, hides the numeric axis, the
    '/ 100' denominator, and all cohort comparison/ranking. Raw scores are
    unaffected upstream (still written to the Sheet/dataset)."""
    css = ('<style id="tpl-band-only">'
           '.gauge-axis,.gauge-number .denom,.cohort-position,.cohort-legend,'
           '.cohort-avg-line,.cohort-top-line,.cohort-bar-scale{display:none !important}'
           '.gauge-number .num{font-size:33px !important;font-weight:800 !important;'
           'letter-spacing:0 !important;line-height:1 !important;white-space:nowrap;'
           # Solid band colour instead of clipped-gradient text. The gradient
           # `background-clip:text` leaves a thin gradient strip above the word
           # in the Chromium PDF pipeline (a faint line over "Strong" etc.).
           'background:none !important;-webkit-background-clip:border-box !important;'
           'background-clip:border-box !important;-webkit-text-fill-color:var(--c) !important;'
           'color:var(--c) !important}'
           '</style>')
    for sc in (comm_score, dec_score, collab_score):
        sc = int(sc)
        _key, label, _start = get_band(sc)
        t = t.replace(f'<div class="num band-text">{sc}</div>',
                      f'<div class="num band-text">{label}</div>')
    # strip numeric ranges from the band legend (#2)
    t = t.replace(
        '<span class="text-[var(--fg-2)]">Foundation 0–39</span> · Emerging 40–59 · Developing 60–79 · Strong 80–100',
        '<span style="color:#F87171">Foundation</span> · <span style="color:#FBBF24">Emerging</span> · '
        '<span style="color:#60A5FA">Developing</span> · <span style="color:#34D399">Strong</span>')
    # remove the old numeric scale tick-marks from the gauge arc (no numbers shown now).
    # Broadened to catch any opacity / stroke-width / whitespace variant of the tick group.
    t = re.sub(r'<g\s+stroke="rgba\(\s*170\s*,\s*195\s*,\s*240[^"]*"[^>]*>.*?</g>',
               '', t, flags=re.DOTALL)
    return css + t


def _balanced_div_end(t, start):
    """Given index of a '<div' opening at `start`, return index just past its matching </div>."""
    import re as _re
    depth = 0; i = start
    for m in _re.finditer(r'<div\b|</div>', t[start:]):
        tok = m.group(0)
        depth += 1 if tok == '<div' else -1
        if depth == 0:
            return start + m.end()
    return -1


def _polish_profile(t, comm_score=None, dec_score=None, collab_score=None):
    """Round-2 layout polish (#2 cohort, #11 numbers, #12 framework width, #8 bullets)."""
    import re as _re
    # (a) Replace the cover Cohort Snapshot panel with a teaser "What's inside" summary
    c = t.find('<!-- Cohort snapshot bars -->')
    if c != -1:
        d = t.find('<div', c)
        end = _balanced_div_end(t, d)
        if end != -1:
            _BANDCOL = {"strong": "#34D399", "developing": "#60A5FA",
                        "emerging": "#FBBF24", "foundation": "#F87171"}
            def _mini(dim_label, score):
                key, label, _a = get_band(int(score))
                col = _BANDCOL.get(key, "#7BBDF4")
                return (f'<div style="flex:1;text-align:center;min-width:0;">'
                        f'<div class="text-white/50" style="font-size:8px;letter-spacing:.09em;'
                        f'text-transform:uppercase;margin-bottom:2px;">{dim_label}</div>'
                        f'<svg viewBox="0 0 90 50" style="width:100%;max-width:80px;display:inline-block;">'
                        f'<path d="M7 46 A 38 38 0 0 1 83 46" fill="none" stroke="rgba(255,255,255,.14)" '
                        f'stroke-width="6" stroke-linecap="round"/>'
                        f'<path d="M7 46 A 38 38 0 0 1 83 46" fill="none" stroke="{col}" stroke-width="6" '
                        f'stroke-linecap="round" pathLength="100" stroke-dasharray="{int(score)} 100"/>'
                        f'</svg>'
                        f'<div style="font-size:10.5px;font-weight:800;color:{col};margin-top:-3px;">{label}</div>'
                        f'</div>')
            gauges = ('<div style="display:flex;gap:6px;margin:4px 0 14px;">'
                      + _mini("Communication", comm_score)
                      + _mini("Decision-Making", dec_score)
                      + _mini("Collaboration", collab_score) + '</div>')
            # NB: this whole right-hand panel is replaced by the meta block in
            # _restructure_hero; the gauges now live inside the TLDR card.
            teaser = ('<div class="relative z-10 px-6 pb-6">'
                      '<div class="eyebrow text-white/55 mb-2">At a glance</div>'
                      + gauges +
                      '</div>')
            t = t[:c] + teaser + t[end:]

    # (b) CSS: enlarge the 01/02/03 move numbers; ensure no stray cohort text shows
    css = ('<style id="tpl-polish">'
           '.num-badge{font-size:26px !important;font-weight:800 !important;'
           'font-family:"Barlow","Inter",sans-serif !important;color:#7BBDF4 !important;'
           'letter-spacing:0 !important;}'
           '.cohort-bars,.cohort-legend,.cohort-position{display:none !important}'
           '</style>')
    t = css + t

    # (c) Framework Priority paragraph: run full width (drop the 78ch cap)
    t = t.replace('text-[14px] text-[var(--fg-2)] leading-[1.7] mb-6 max-w-[78ch]',
                  'text-[14px] text-[var(--fg-2)] leading-[1.7] mb-6')

    # (d) Score-card paragraphs under each arch -> bullet list (easier to scan)
    def _to_bullets(m):
        body = m.group(1).strip()
        parts = [p.strip() for p in _re.split(r'(?<=[.!?])\s+', body) if p.strip()]
        # Drop sentences that are just a band word ("Emerging.") — the band is
        # already shown in the gauge and the card's corner chip (#redundancy)
        parts = [p for p in parts
                 if p.rstrip('.!? ') not in ("Foundation", "Emerging", "Developing", "Strong")]
        lis = ''.join(f'<li style="position:relative;padding-left:16px;margin-bottom:6px;">'
                      f'<span style="position:absolute;left:0;top:8px;width:5px;height:5px;'
                      f'border-radius:50%;background:var(--c-soft,#7BBDF4);"></span>{p}</li>'
                      for p in parts)
        return ('<ul class="text-[13.5px] text-[var(--fg-2)] leading-[1.6] mt-6" '
                'style="list-style:none;padding:0;margin-top:18px;">' + lis + '</ul>')
    t = _re.sub(r'<p class="text-\[13\.5px\] text-\[var\(--fg-2\)\] leading-\[1\.65\] mt-6">(.*?)</p>',
                _to_bullets, t, flags=_re.DOTALL)

    # (e) "What stood out" footer stats: drop cohort columns + numbers, keep band only
    def _remove_col(tt, label):
        es = tt.find('<div class="eyebrow mb-1.5">' + label + '</div>')
        if es == -1:
            return tt
        wrap = tt.rfind('<div', 0, es)
        end = _balanced_div_end(tt, wrap)
        return tt[:wrap] + tt[end:] if end != -1 else tt
    t = _remove_col(t, "Cohort rank")
    t = _remove_col(t, "Cohort avg")
    # rebalance the footer grids now that a column is gone
    t = t.replace('mt-7 pt-5 border-t hairline grid grid-cols-3 gap-6',
                  'mt-7 pt-5 border-t hairline grid grid-cols-2 gap-6')
    t = t.replace('mt-7 pt-5 border-t hairline grid grid-cols-2 md:grid-cols-4 gap-6',
                  'mt-7 pt-5 border-t hairline grid grid-cols-2 md:grid-cols-3 gap-6')
    # "Score" label reads odd with a band -> "Band"
    t = t.replace('<div class="eyebrow mb-1.5">Score</div>', '<div class="eyebrow mb-1.5">Band</div>')
    # Show the INDIVIDUAL's band per dimension (numbers stay in the data for managers).
    if comm_score is not None:
        _DS = {"Communication": int(comm_score), "Decision-Making": int(dec_score),
               "Decision Making": int(dec_score), "Collaboration": int(collab_score)}
        _BC = {"strong": "#34D399", "developing": "#60A5FA", "emerging": "#FBBF24", "foundation": "#F87171"}
        _ORD = ["foundation", "emerging", "developing", "strong"]
        _LBL = {"foundation": "Foundation", "emerging": "Emerging", "developing": "Developing", "strong": "Strong"}
        def _cell(score, up=False):
            k, _l, _a = get_band(int(score))
            if up:
                k = _ORD[min(_ORD.index(k) + 1, 3)]
            return '<span style="color:' + _BC[k] + '">' + _LBL[k] + '</span>'
        ms = _re.search(r'>Dimension</div>\s*<div class="text-\[13\.5px\] font-medium">([^<]+)</div>', t)
        mg = _re.search(r'>Linked to</div>\s*<div class="text-\[13\.5px\] font-medium">([^<]+)</div>', t)
        sdim = ms.group(1).strip() if ms else None
        gdim = mg.group(1).strip() if mg else None
        if sdim in _DS:
            t = _re.sub(r'(>Band</div>\s*<div class="text-\[13\.5px\] font-medium tabular"[^>]*>)[^<]*(</div>)',
                        lambda mm: mm.group(1) + _cell(_DS[sdim]) + mm.group(2), t, count=1)
        if gdim in _DS:
            t = _re.sub(r'(>Current</div>\s*<div class="text-\[13\.5px\] font-medium tabular"[^>]*>)[^<]*(</div>)',
                        lambda mm: mm.group(1) + _cell(_DS[gdim]) + mm.group(2), t, count=1)
            t = _re.sub(r'(>30-day target</div>\s*<div class="text-\[13\.5px\] font-medium tabular"[^>]*>)[^<]*(</div>)',
                        lambda mm: mm.group(1) + _cell(_DS[gdim], up=True) + mm.group(2), t, count=1)
    # remove the score-based growth progress bar (not band-only) + its "48 -> 60" label
    _gp = t.find('<div class="growth-progress')
    if _gp != -1:
        _ge = _balanced_div_end(t, _gp)
        if _ge != -1:
            t = t[:_gp] + t[_ge:]
    t = _re.sub(r'<div class="mono text-\[9\.5px\][^"]*"[^>]*>\s*\d+\s*→\s*\d+\s*</div>', '', t)
    return t


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
def _strip_tags(s: str) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s)).strip()


def _replace_text_flex(t: str, old: str, new: str, label: str) -> str:
    """Replace `old` (matched with flexible whitespace) with `new`.
    Soft-fails with a warning so a template wording drift never breaks renders."""
    pattern = r'\s+'.join(re.escape(tok) for tok in old.split())
    t2, n = re.subn(pattern, new, t, count=1)
    if n == 0:
        print(f"[tldr] WARNING: boilerplate trim '{label}' found no match — skipped")
    return t2


# ── Copy trims (#too-much-text): tighten shared boilerplate at injection time ──
# The momentum rewrite also absorbs the removed Framework Priority section: the
# frameworks become something to lean on, not a practice schedule.
_TRIMS = [
    ("momentum",
     "Your leader has already received your profile. The awareness is there. What "
     "happens next is up to you. Pick one of the three moves from Section 03 and commit "
     "to using it consistently this month. Growth does not happen in a workshop. It "
     "happens in the meetings and conversations that follow. Make it visible.",
     "Your leader has already received your profile. Pick one of the three moves from "
     "Section 03 and commit to it this month. And keep the three workshop frameworks "
     "within reach: the Clarity Loop, the Decision Engine, and the Collaboration Reset. "
     "They are not homework. They are there to lean on whenever a meeting calls for one, "
     "deliberate at first and automatic with repetition, until they stop being tools you "
     "reach for and simply become how you work. Growth happens in the meetings and "
     "conversations that follow. Make it visible."),
]

def _trim_boilerplate(t: str) -> str:
    for label, old, new in _TRIMS:
        t = _replace_text_flex(t, old, new, label)
    return t


def _restructure_hero(t: str) -> str:
    """One comprehensive summary up top (#combine-boxes): the hero keeps only the
    archetype name + tagline on the left, with Workshop / Assessed / Cohort /
    Profile ID as a meta block in the top-right corner. The gradient panel
    (gauges etc.) is removed — that content now lives inside the TLDR card."""
    h0 = t.find("<!-- ============== HERO ============== -->")
    h1 = t.find("<!-- ============== WHAT TODAY REVEALED ============== -->")
    if h0 == -1 or h1 == -1:
        print("[tldr] WARNING: hero bounds not found — hero left unchanged")
        return t
    hero = t[h0:h1]

    # Pull the workshop title + mono line out of the old panel before deleting it
    m = re.search(r'<div class="display text-white text-\[20px\][^"]*">(.*?)</div>', hero, re.DOTALL)
    ws_title = _strip_tags(m.group(1)) if m else "Team Effectiveness Workshop"
    m = re.search(r'<div class="text-white/65 text-\[12px\] mono[^"]*">(.*?)</div>', hero, re.DOTALL)
    ws_mono = _strip_tags(m.group(1)) if m else ""

    # Pull the Assessed / Cohort / Profile ID pairs out of the old meta row
    mi = hero.find('meta-row"')
    meta_pairs = []
    if mi != -1:
        d0 = hero.rfind('<div', 0, mi)
        d1 = _balanced_div_end(hero, d0)
        meta_html = hero[d0:d1]
        meta_pairs = re.findall(
            r'<div class="eyebrow mb-1.5">(.*?)</div>\s*<div[^>]*>(.*?)</div>',
            meta_html, re.DOTALL)
        hero = hero[:d0] + hero[d1:]          # remove the bottom meta row
    else:
        print("[tldr] WARNING: hero meta row not found")

    # Drop the long archetype description paragraph (its content leads the TLDR)
    hero2 = re.sub(
        r'<p class="text-\[15px\] text-\[var\(--fg-2\)\] max-w-\[58ch\] leading-\[1\.7\]">.*?</p>\s*',
        '', hero, count=1, flags=re.DOTALL)
    if hero2 == hero:
        print("[tldr] WARNING: hero description paragraph not found — skipped")
    hero2 = hero2.replace('leading-[1.35] mb-8', 'leading-[1.35] mb-2', 1)

    # Replace the gradient panel column with a right-aligned meta block
    meta_items = "".join(
        f'<div><div class="eyebrow mb-1.5">{k.strip()}</div>'
        f'<div class="text-[var(--fg)] text-[13.5px] font-medium'
        f'{" mono" if "Profile" in k else ""}">{_strip_tags(v)}</div></div>'
        for k, v in meta_pairs)
    meta_block = (
        '<div class="col-span-12 lg:col-span-5 relative">'
        '<div class="flex flex-col items-end text-right gap-5 pt-1">'
        '<div><div class="eyebrow mb-1.5">Workshop</div>'
        f'<div class="text-[var(--fg)] text-[15px] font-medium">{ws_title}</div>'
        + (f'<div class="text-[var(--fg-3)] mono text-[11.5px] mt-1">{ws_mono}</div>' if ws_mono else "")
        + f'</div>{meta_items}</div></div>')
    p0 = hero2.find('<div class="col-span-12 lg:col-span-5 relative">')
    if p0 != -1:
        p1 = _balanced_div_end(hero2, p0)
        hero2 = hero2[:p0] + meta_block + hero2[p1:]
    else:
        print("[tldr] WARNING: hero panel column not found — panel left in place")
    return t[:h0] + hero2 + t[h1:]


def _remove_framework_section(t: str) -> str:
    """Remove Section 04 (Framework priority) — its message is folded into the
    closing 'Keep the momentum going' section instead."""
    i0 = t.find("<!-- ============== FRAMEWORK PRIORITY ============== -->")
    i1 = t.find("<!-- ============== ALIGN WITH LEADER ============== -->")
    if i0 == -1 or i1 == -1:
        print("[tldr] WARNING: framework section bounds not found — left in place")
        return t
    return t[:i0] + t[i1:]


def _merge_resources_into_moves(t: str) -> str:
    """Fold 'What to use next' (Section 06) into 'Your next three moves' as a
    compact support strip, then remove the standalone section. The two sections
    competed: both prescribed actions."""
    r0 = t.find("<!-- ============== RECOMMENDATIONS ============== -->")
    r1 = t.find("<!-- ============== FOOTER ============== -->")
    n1 = t.find("<!-- ============== FRAMEWORK PRIORITY ============== -->")
    if r0 == -1 or r1 == -1 or n1 == -1:
        print("[tldr] WARNING: resources/moves bounds not found — merge skipped")
        return t
    rec = t[r0:r1]

    cards = []
    for am in re.finditer(r'<article[^>]*>(.*?)</article>', rec, re.DOTALL):
        a = am.group(1)
        chips = re.findall(r'<span[^>]*>([^<]{2,40})</span>', a)
        h3 = re.search(r'<h3[^>]*>(.*?)</h3>', a, re.DOTALL)
        body = re.search(r'<p[^>]*>(.*?)</p>', a, re.DOTALL)
        if not (h3 and body and len(chips) >= 2):
            continue
        first_sentence = re.split(r'(?<=\.)\s+', _strip_tags(body.group(1)))[0]
        cards.append({"cat": chips[0], "cad": chips[1],
                      "title": _strip_tags(h3.group(1)), "body": first_sentence})
    if len(cards) != 3:
        print(f"[tldr] WARNING: expected 3 resource cards, found {len(cards)} — merge skipped")
        return t

    strip_cards = "".join(
        '<div class="card p-5">'
        '<div class="flex items-center justify-between gap-3 mb-3">'
        f'<span class="eyebrow" style="font-size:10px;">{c["cat"]}</span>'
        '<span class="text-[11px] text-[var(--fg-3)] tabular whitespace-nowrap">'
        f'{c["cad"]}</span></div>'
        f'<div class="text-[14.5px] font-semibold leading-[1.25] mb-2">{c["title"]}</div>'
        f'<p class="text-[12.5px] text-[var(--fg-3)] leading-[1.55]">{c["body"]}</p>'
        '</div>'
        for c in cards)
    strip = (
        '\n      <div class="mt-10 mb-4">'
        '<div class="eyebrow mb-1.5">Support your moves</div>'
        '<div class="text-[13px] text-[var(--fg-3)] max-w-[64ch]">'
        'A challenge, a person, and a learning habit. Use them alongside '
        'whichever move you pick.</div></div>'
        f'<div class="grid grid-cols-1 md:grid-cols-3 gap-5">{strip_cards}</div>\n    ')

    # Insert before the closing </section> of the NEXT STEPS section
    sec_end = t.rfind('</section>', 0, n1)
    t = t[:sec_end] + strip + t[sec_end:]

    # Remove the standalone recommendations section (indices shifted by insert)
    off = len(strip)
    return t[:r0 + off] + t[r1 + off:]


def _renumber_sections(t: str) -> str:
    """After removing Sections 04/06, the closing section becomes 04."""
    return t.replace("Section 05 · What happens next", "Section 04 · What happens next")


def _boost_contrast(t: str) -> str:
    """Raise text contrast on the dark theme (#readability). The template's
    tertiary text (#5A6E92) measures ~3.8:1 against the page background —
    below the 4.5:1 small-text threshold — and it carries captions, eyebrows,
    resource bodies and the footer. Appended last so it wins document order;
    the print/light theme uses !important and is unaffected."""
    css = ('<style id="tpl-contrast">'
           ':root{--fg-2:#A6B6D6;--fg-3:#8FA2C4;--fg-4:#5C719A;}'
           '.ws-zone{--ws-soft:#BCCBE8;}'
           '</style>')
    return t + css


# Section ids so the TLDR can deep-link into the body (web profile; harmless in PDF)
_SECTION_IDS = [
    ("<!-- ============== DIMENSION CARDS ============== -->", "sec-scored"),
    ("<!-- ============== STRENGTH + GROWTH EDGE ============== -->", "sec-stood-out"),
    ("<!-- ============== NEXT STEPS ============== -->", "sec-moves"),
]

def _add_section_ids(t: str) -> str:
    for comment, sid in _SECTION_IDS:
        i = t.find(comment)
        if i == -1:
            continue
        j = t.find("<section", i)
        if j != -1 and f'id="{sid}"' not in t[i:j+200]:
            t = t[:j] + f'<section id="{sid}"' + t[j+len("<section"):]
    t = t.replace('<section class="ws-zone rise"',
                  '<section id="sec-style" class="ws-zone rise"', 1)
    return t

def _inject_tldr(t: str, comm_score: int, dec_score: int, collab_score: int,
                 ws_blocks=None, lead_text: str = "") -> str:
    """Build a one-screen summary of the whole profile and place it directly
    after the hero, REPLACING the 'What today revealed' mirror section (its
    text becomes the TLDR lead, so the recap exists exactly once). All content
    is extracted from the final rendered profile, so the summary always
    matches the body."""

    anchor = "<!-- ============== WHAT TODAY REVEALED ============== -->"
    a0 = t.find(anchor)
    if a0 == -1:
        raise RuntimeError("TLDR anchor (WHAT TODAY REVEALED) not found in template")
    a1 = t.find("</section>", a0)
    if a1 == -1:
        raise RuntimeError("TLDR: mirror section end not found")
    a1 += len("</section>")

    # ── Lead: personalized text when provided, else the template's mirror copy ──
    revealed = lead_text.strip() if lead_text else ""
    if not revealed:
        m = re.search(r'What today revealed</div>\s*<p[^>]*>\s*(.*?)\s*</p>', t[a0:a1], re.DOTALL)
        revealed = _strip_tags(m.group(1)) if m else ""

    m = re.search(r'Your Strength</span>.*?<h3[^>]*>(.*?)</h3>', t, re.DOTALL)
    strength = _strip_tags(m.group(1)) if m else ""
    m = re.search(r'Your Growth Edge</span>.*?<h3[^>]*>(.*?)</h3>', t, re.DOTALL)
    growth = _strip_tags(m.group(1)) if m else ""

    moves, cadences = [], []
    i0 = t.find("<!-- ============== NEXT STEPS ============== -->")
    i1 = t.find("<!-- ============== FRAMEWORK PRIORITY ============== -->")
    if i0 != -1 and i1 != -1:
        moves = [_strip_tags(h) for h in
                 re.findall(r'<h3[^>]*>(.*?)</h3>', t[i0:i1], re.DOTALL)][:3]
        cadences = [_strip_tags(c) for c in
                    re.findall(r'<span class="tabular">([^<]+)</span>', t[i0:i1])][:3]

    # Per-dimension band + (optional) working-style label
    ws_by_dim = {}
    if ws_blocks:
        for b in ws_blocks:
            ws_by_dim[b["dimension"]] = b.get("style_name", "")

    # Gauge arcs (the data) now open the card, with a simple band legend below —
    # bars and colours only; the arcs themselves say where each skill landed.
    _BANDS_HEX = {"strong": "#34D399", "developing": "#60A5FA",
                  "emerging": "#FBBF24", "foundation": "#F87171"}
    dims = ["Communication", "Decision-Making", "Collaboration"]
    gauge_cells = []
    for label, score in zip(dims, (comm_score, dec_score, collab_score)):
        key, band, _ = get_band(int(score))
        col = _BANDS_HEX[key]
        gauge_cells.append(
            f'<div class="tldr-g">'
            f'<div class="tldr-g-label">{label}</div>'
            f'<svg viewBox="0 0 90 50"><path d="M7 46 A 38 38 0 0 1 83 46" fill="none" '
            f'stroke="rgba(120,170,235,.16)" stroke-width="6" stroke-linecap="round"/>'
            f'<path d="M7 46 A 38 38 0 0 1 83 46" fill="none" stroke="{col}" stroke-width="6" '
            f'stroke-linecap="round" pathLength="100" stroke-dasharray="{int(score)} 100"/></svg>'
            f'<div class="tldr-g-band" style="color:{col}">{band}</div>'
            f'</div>')
    scale = (
        '<div class="tldr-scale">'
        '<span class="tldr-scale-label">The development scale</span>'
        '<div class="tldr-scale-bars">'
        + "".join(
            f'<div class="tldr-scale-step"><div style="height:5px;border-radius:3px;'
            f'background:{_BANDS_HEX[k]};"></div>'
            f'<div class="tldr-scale-name" style="color:{_BANDS_HEX[k]}">{lab}</div></div>'
            for k, lab in (("foundation", "Foundation"), ("emerging", "Emerging"),
                           ("developing", "Developing"), ("strong", "Strong")))
        + '</div></div>')
    gauges_block = (
        f'<div class="tldr-gauges">{"".join(gauge_cells)}</div>{scale}')

    # Working style: its own panel — large style icons anchor each cell,
    # explicitly framed as preference, not score
    ws_row = ""
    if ws_by_dim:
        cells = "".join(
            f'<a class="tldr-ws-cell" href="#sec-style">'
            f'<span class="tldr-ws-icon">{_STYLE_ICONS.get(ws_by_dim[d], "")}</span>'
            f'<span class="tldr-ws-text"><span class="tldr-ws-dimlab">{d}</span>'
            f'<span class="tldr-ws-style">{ws_by_dim[d]}</span></span>'
            f'</a>'
            for d in dims if ws_by_dim.get(d))
        ws_row = (
            f'<div class="tldr-ws">'
            f'<div class="tldr-ws-head">'
            f'<span class="tldr-ws-label">How you naturally work</span>'
            f'<span class="tldr-ws-note">A preference, not a score</span>'
            f'</div>'
            f'<div class="tldr-ws-grid">{cells}</div>'
            f'</div>')

    lead = (f'<p class="tldr-lead">{revealed}</p>' if revealed else "")

    move_items = "".join(
        f'<a class="tldr-move" href="#sec-moves"><span class="tldr-move-num">0{i+1}</span>'
        f'<span class="tldr-move-body"><span class="tldr-move-text">{m}</span>'
        + (f'<span class="tldr-move-cad">{cadences[i]}</span>' if i < len(cadences) else "")
        + '</span></a>'
        for i, m in enumerate(moves))

    css = """
<style id="tpl-tldr">
.tldr-card{border:1px solid rgba(120,170,235,.28);border-radius:16px;
  padding:28px 34px 22px;position:relative;overflow:hidden;
  background:linear-gradient(170deg,rgba(62,155,255,.07),rgba(62,155,255,.015) 55%);}
.tldr-card a{color:inherit;text-decoration:none;}
.tldr-head{display:flex;align-items:flex-end;justify-content:space-between;
  gap:24px;margin-bottom:14px;}
.tldr-lead{font-size:16.5px;line-height:1.6;color:var(--fg-2);max-width:80ch;
  font-weight:300;margin:0 0 18px;}
.tldr-gauges{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:12px;}
.tldr-g{text-align:center;border:1px solid rgba(120,170,235,.16);border-radius:12px;
  padding:12px 14px 10px;background:rgba(255,255,255,.025);}
.tldr-g svg{width:100%;max-width:104px;display:inline-block;}
.tldr-g-label{text-transform:uppercase;letter-spacing:.15em;font-size:10px;
  font-weight:700;color:var(--fg-3);margin-bottom:6px;}
.tldr-g-band{font-size:15px;font-weight:800;margin-top:-4px;}
.tldr-scale{display:flex;align-items:flex-start;gap:16px;margin-bottom:18px;
  padding:0 4px;}
.tldr-scale-label{text-transform:uppercase;letter-spacing:.13em;font-size:9.5px;
  font-weight:700;color:var(--fg-3);white-space:nowrap;padding-top:1px;}
.tldr-scale-bars{display:flex;gap:5px;flex:1;}
.tldr-scale-step{flex:1;}
.tldr-scale-name{text-align:center;font-size:8.5px;letter-spacing:.08em;
  text-transform:uppercase;font-weight:700;margin-top:4px;}
.tldr-ws{border:1px dashed rgba(120,170,235,.22);border-radius:12px;padding:13px 16px 14px;}
.tldr-ws-head{display:flex;align-items:baseline;justify-content:space-between;
  gap:16px;margin-bottom:11px;}
.tldr-ws-label{text-transform:uppercase;letter-spacing:.14em;font-size:10px;
  font-weight:700;color:var(--fg-3);}
.tldr-ws-note{font-size:11px;font-style:italic;color:var(--fg-3);}
.tldr-ws-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;}
.tldr-ws-cell{display:flex;align-items:center;gap:11px;}
.tldr-ws-icon{width:42px;height:42px;flex:0 0 42px;border-radius:12px;display:flex;
  align-items:center;justify-content:center;background:rgba(62,155,255,.14);
  border:1px solid rgba(62,155,255,.30);color:#3E9BFF;}
.tldr-ws-icon svg{width:25px;height:25px;}
.tldr-ws-text{min-width:0;}
.tldr-ws-dimlab{display:block;text-transform:uppercase;letter-spacing:.13em;
  font-size:9.5px;font-weight:700;color:var(--fg-3);margin-bottom:2px;}
.tldr-ws-style{display:block;font-size:13.5px;font-weight:700;color:var(--fg);line-height:1.2;}
.tldr-ws-note{margin-left:auto;font-size:11px;font-style:italic;color:var(--fg-3);}
.tldr-two{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:12px;}
.tldr-half{border:1px solid rgba(120,170,235,.16);border-radius:12px;
  padding:13px 16px;background:rgba(255,255,255,.025);display:block;}
.tldr-eyebrow{text-transform:uppercase;letter-spacing:.16em;font-size:10.5px;
  font-weight:700;margin-bottom:7px;}
.tldr-headline{font-size:15.5px;font-weight:700;color:var(--fg);line-height:1.3;}
.tldr-moves{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:12px;}
.tldr-move{border:1px solid rgba(120,170,235,.16);border-radius:12px;
  padding:12px 14px;background:rgba(255,255,255,.025);
  display:flex;gap:10px;align-items:flex-start;}
.tldr-move-num{font-size:11px;font-weight:800;color:#3E9BFF;
  border:1px solid rgba(62,155,255,.4);border-radius:7px;padding:3px 7px;flex:0 0 auto;}
.tldr-move-body{display:flex;flex-direction:column;gap:5px;}
.tldr-move-text{font-size:13px;font-weight:600;color:var(--fg);line-height:1.35;}
.tldr-move-cad{font-size:11px;color:var(--fg-3);font-variant-numeric:tabular-nums;}
.tldr-foot{margin-top:16px;padding-top:13px;border-top:1px solid rgba(120,170,235,.14);
  font-size:12.5px;color:var(--fg-3);}
.tldr-foot strong{color:var(--fg-2);font-weight:600;}
</style>"""

    section = f"""{css}
<!-- ============== TLDR SUMMARY ============== -->
    <section class="mt-14 rise rise-2" id="tldr">
      <div class="tldr-card">
        <div class="tldr-head">
          <div>
            <div class="eyebrow mb-2">Your profile on one page</div>
            <h2 class="display text-[26px] tracking-tight">If you read nothing else, read this.</h2>
          </div>
          <div class="text-[12.5px] text-[var(--fg-3)] whitespace-nowrap">A 60-second read</div>
        </div>

        {gauges_block}

        {lead}

        {ws_row}

        <div class="tldr-two">
          <a class="tldr-half" href="#sec-stood-out">
            <div class="tldr-eyebrow" style="color:var(--band-strong)">Your strength</div>
            <div class="tldr-headline">{strength}</div>
          </a>
          <a class="tldr-half" href="#sec-stood-out">
            <div class="tldr-eyebrow" style="color:var(--band-emerging)">Your growth edge</div>
            <div class="tldr-headline">{growth}</div>
          </a>
        </div>

        <div class="tldr-moves">
          {move_items}
        </div>

        <div class="tldr-foot">
          <strong>That is the whole profile.</strong> Everything below is the evidence and the how.
          Read what's useful. Skip what isn't.
        </div>
      </div>
    </section>"""

    return t[:a0] + section + t[a1:]


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

    # ── #2 De-score: show band only, drop numbers + cohort ranking ──
    t = _show_band_only(t, new_comm, new_dec, new_collab)
    t = _polish_profile(t, new_comm, new_dec, new_collab)

    # ── Working Style layer (V3): insert before the performance scoring section ──
    ws = participant.get("working_style")
    _ws_blocks = None
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

    # ── TLDR layer (v7): restructure hero (meta top-right, no panel), merge
    #    resources into moves, drop Framework Priority (folded into momentum),
    #    renumber, then replace 'What today revealed' with the summary card ──
    t = _restructure_hero(t)
    t = _trim_boilerplate(t)
    t = _merge_resources_into_moves(t)
    t = _remove_framework_section(t)
    t = _renumber_sections(t)
    t = _add_section_ids(t)
    # Personalized lead (hybrid): explicit override > LLM-with-fallback > mirror copy
    _lead = participant.get("lead_text", "")
    if not _lead and _generate_lead:
        _lead = _generate_lead(key, new_comm, new_dec, new_collab, _ws_blocks,
                               seed=f"{name}|{profile_id}")
    t = _inject_tldr(t, new_comm, new_dec, new_collab, _ws_blocks, lead_text=_lead)
    t = _boost_contrast(t)

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
