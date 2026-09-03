"""
generate_leader_report.py
=========================

Dynamic generator for The Performance Lens "Leadership Insight Report"
(Team Effectiveness Workshop -- team layer), modelled pixel-for-pixel on the
approved standalone design.

The approved design ships as a "JS-bundler" HTML: the real report markup lives
inside a `<script type="__bundler/template">` JSON string, and its fonts/logos
are stored (gzip+base64) in a `<script type="__bundler/manifest">` blob and
referenced by UUID. This module:

  1. Loads that reference bundle once, decodes the template, and inlines every
     font / logo as a real `data:` URI  ->  a clean, self-contained HTML shell
     whose `<style>` / @font-face block and visual chrome are byte-identical to
     the approved file. The fonts are NOT stripped or altered.
  2. Slices the shell into its head (with embedded fonts) + 12 page containers,
     then re-generates every DATA-bearing region from `data` (cover fields, the
     three summary gauges + benchmark ticks, the strength/priority/team-shape
     narrative, the "who is who" table, the archetype mix table + definition
     cards, the working-style table, the "who to focus on" cards, and the
     appendix benchmark sources). Per-participant rows are generated in a loop,
     and large teams spill onto cloned "(continued)" pages so no page overflows.
  3. Returns the full HTML document. Render to PDF with **headless Chromium**
     (Letter, embedded fonts) -- NOT weasyprint, which mis-paginates this design.

Public API
----------
    build_leader_report_html(data: dict) -> str

See DATA_SCHEMA (bottom of file) and the __main__ test harness for the exact
shape of `data`.
"""

from __future__ import annotations

import base64
import gzip
import html as _html
import json
import os
import re
from collections import Counter, OrderedDict

# ──────────────────────────────────────────────────────────────────────────────
# Reference bundle (the approved standalone design)
# ──────────────────────────────────────────────────────────────────────────────

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_REFERENCE_PATHS = [
    os.environ.get("LEADER_REPORT_REFERENCE", ""),
    os.path.join(_THIS_DIR, "assets", "Leadership Insight Report (standalone).html"),
    os.path.join(_THIS_DIR, "Leadership Insight Report (standalone).html"),
    "/sessions/zealous-ecstatic-meitner/mnt/uploads/"
    "Leadership Insight Report (standalone) (1).html",
]

_UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")

# Per-page row capacity before spilling onto a continuation page.
_CAP_WHOISWHO = 14
_CAP_WORKSTYLE = 9
_CAP_FOCUS = 6  # per focus group (Check-In / Stretch)

_SHELL_CACHE: dict | None = None


def _find_reference() -> str:
    for p in _DEFAULT_REFERENCE_PATHS:
        if p and os.path.exists(p):
            return p
    raise FileNotFoundError(
        "Approved reference bundle not found. Set LEADER_REPORT_REFERENCE to the "
        "path of 'Leadership Insight Report (standalone).html'."
    )


def _bundle_block(src: str, tag: str) -> str:
    i = src.find(tag)
    if i < 0:
        raise ValueError(f"Bundle block {tag!r} not found in reference.")
    start = src.find(">", i) + 1
    end = src.find("</script>", start)
    return src[start:end].strip()


def _matching_div_close(html: str, start: int) -> int:
    """Return index just past the </div> that closes the <div> opening at start."""
    depth = 0
    i = start
    while i < len(html):
        nd = html.find("<div", i)
        cd = html.find("</div>", i)
        if cd < 0:
            return len(html)
        if nd != -1 and nd < cd:
            depth += 1
            i = nd + 4
        else:
            depth -= 1
            i = cd + 6
            if depth == 0:
                return i
    return len(html)


def _consume_rows(html: str, open_sig: str, start_from: int = 0, stop: int = -1):
    """Find a run of contiguous sibling <div> rows whose opening tag contains
    `open_sig`, beginning at the first such row at/after `start_from`.

    Returns (first_index, end_index) covering the whole run, or (-1, -1) if none.
    Guaranteed to terminate: each iteration advances strictly past the prior row.
    """
    needle = '<div style="display:grid;' + open_sig
    first = html.find(needle, start_from)
    if first < 0:
        return -1, -1
    end = first
    pos = first
    while True:
        if stop != -1 and pos > stop:
            break
        end = _matching_div_close(html, pos)
        nxt = html.find(needle, end)
        if nxt < 0 or (stop != -1 and nxt > stop):
            break
        pos = nxt
    return first, end


def _load_shell() -> dict:
    """Decode the bundle, inline assets, and slice into head + 12 page blocks.

    Returns {"head": <str>, "tail": <str>, "pages": {label: html}} where head is
    everything up to and including the `<div class="deck">` opener (carries the
    embedded fonts), tail closes the deck/body/html, and pages maps each
    data-screen-label to its verbatim, asset-inlined page <div>.
    """
    global _SHELL_CACHE
    if _SHELL_CACHE is not None:
        return _SHELL_CACHE

    src = open(_find_reference(), encoding="utf-8").read()
    manifest = json.loads(_bundle_block(src, '<script type="__bundler/manifest">'))
    template = json.loads(_bundle_block(src, '<script type="__bundler/template">'))

    def data_uri(uuid: str) -> str:
        v = manifest[uuid]
        raw = base64.b64decode(v["data"])
        if v.get("compressed"):
            raw = gzip.decompress(raw)
        return "data:%s;base64,%s" % (v["mime"], base64.b64encode(raw).decode())

    template = re.sub(r'url\("([0-9a-f-]{36})"\)',
                      lambda m: 'url("%s")' % data_uri(m.group(1)), template)
    template = re.sub(r'src="([0-9a-f-]{36})"',
                      lambda m: 'src="%s"' % data_uri(m.group(1)), template)
    template = re.sub(r'<script src="data:text/javascript[^"]*"></script>', "", template)

    deck_open = template.find('<div class="deck"')
    head = template[: template.find(">", deck_open) + 1]

    pages = OrderedDict()
    for m in re.finditer(r'<div data-page=""', template):
        start = m.start()
        end = _matching_div_close(template, start)
        seg = template[start:end]
        lab = re.search(r'data-screen-label="([^"]*)"', seg).group(1)
        pages[lab] = seg

    tail = "\n</div>\n</body></html>"

    _SHELL_CACHE = {"head": head, "tail": tail, "pages": pages}
    return _SHELL_CACHE


# ──────────────────────────────────────────────────────────────────────────────
# Data model / derivation
# ──────────────────────────────────────────────────────────────────────────────

ALL_ARCHETYPES = ["Relay", "Navigator", "Signal", "Summit", "Anchor", "Compass"]

ARCHETYPE_BLURB = {
    "Relay":     "Aligns and delivers on clear briefs. The team's execution baseline.",
    "Navigator": "Makes calls when others defer. Sets direction in ambiguous situations.",
    "Signal":    "Reads the room before acting. High interpersonal radar. An informal connector.",
    "Summit":    "Raises team standards. Pushes what is possible. Not always comfortable.",
    "Anchor":    "A grounding force under pressure. Provides stability when the brief breaks down.",
    "Compass":   "Builds structure out of ambiguity. Maps complexity and creates process.",
}

DEFAULT_BENCHMARKS = {"Communication": 62, "Decision Making": 58, "Collaboration": 64}


def _band(score: float) -> str:
    if score >= 75:
        return "Strong"
    if score >= 60:
        return "Developing"
    if score >= 40:
        return "Emerging"
    return "Foundation"


def _esc(s) -> str:
    return _html.escape("" if s is None else str(s), quote=True)


def _num(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _i(v) -> int:
    return int(round(_num(v)))


def _enrich(p: dict) -> dict:
    p = dict(p)
    p["c"] = _num(p.get("c_score", p.get("communication")))
    p["d"] = _num(p.get("d_score", p.get("decision")))
    p["co"] = _num(p.get("co_score", p.get("collaboration")))
    p["avg"] = round((p["c"] + p["d"] + p["co"]) / 3)
    p["archetype"] = p.get("archetype", "Relay") or "Relay"
    p["name"] = p.get("name", "Member")
    flag = p.get("focus")
    if not flag:
        if all(s >= 60 for s in (p["c"], p["d"], p["co"])) and p["avg"] >= 70:
            flag = "Stretch"
        elif any(s < 60 for s in (p["c"], p["d"], p["co"])):
            flag = "Check-In"
        else:
            flag = "Stretch"
    p["focus"] = flag
    return p


def _stats(participants: list, benchmarks: dict) -> dict:
    n = len(participants)
    if not n:
        return dict(n=0, dims=OrderedDict(), overall=0, arche=Counter(),
                    check_ins=[], stretches=[], priority="Decision Making",
                    strength="Collaboration", benchmarks=benchmarks)
    c = round(sum(p["c"] for p in participants) / n)
    d = round(sum(p["d"] for p in participants) / n)
    co = round(sum(p["co"] for p in participants) / n)
    overall = round((c + d + co) / 3)
    dims = OrderedDict([("Communication", c), ("Decision Making", d), ("Collaboration", co)])
    arche = Counter(p["archetype"] for p in participants)
    check_ins = [p for p in participants if p["focus"] == "Check-In"]
    stretches = [p for p in participants if p["focus"] == "Stretch"]
    return dict(n=n, dims=dims, overall=overall, arche=arche,
                check_ins=check_ins, stretches=stretches,
                priority=min(dims, key=dims.get), strength=max(dims, key=dims.get),
                benchmarks=benchmarks)


def _nar(narrative: dict, key: str, fallback: str) -> str:
    val = (narrative or {}).get(key)
    return val if val else fallback


def _join(names) -> str:
    names = list(names)
    if not names:
        return "no members"
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


# ──────────────────────────────────────────────────────────────────────────────
# In-page region swaps (operate on an ISOLATED single-page string)
# ──────────────────────────────────────────────────────────────────────────────

def _swap_node_text(page: str, anchor: str, new_text: str, tag: str = "p") -> str:
    """Replace the inner text of the first <tag> appearing at/after `anchor`."""
    i = page.find(anchor)
    if i < 0:
        return page
    o = page.find("<" + tag, i)
    if o < 0:
        return page
    gt = page.find(">", o) + 1
    cl = page.find("</" + tag + ">", gt)
    if cl < 0:
        return page
    return page[:gt] + new_text + page[cl:]


def _replace_unique(page: str, old: str, new: str) -> str:
    i = page.find(old)
    if i < 0:
        return page
    return page[:i] + new + page[i + len(old):]


# ── cover ────────────────────────────────────────────────────────────────────

def _build_cover(company, workshop_date, leader_name) -> str:
    pg = _load_shell()["pages"]["Cover"]
    pg = _replace_unique(
        pg,
        '<div style="font-family:\'Barlow\',sans-serif;font-weight:800;font-size:46px;line-height:1;color:#fff;">Cobi</div>',
        '<div style="font-family:\'Barlow\',sans-serif;font-weight:800;font-size:46px;line-height:1;color:#fff;">' + _esc(company) + '</div>',
    )
    pg = _replace_unique(
        pg,
        '<div style="font-size:18px;font-weight:600;color:#E8EEFB;">May 2026</div>',
        '<div style="font-size:18px;font-weight:600;color:#E8EEFB;">' + _esc(workshop_date or "—") + '</div>',
    )
    pg = _replace_unique(
        pg,
        '<div style="font-size:18px;font-weight:600;color:#E8EEFB;">Jay Kim</div>',
        '<div style="font-size:18px;font-weight:600;color:#E8EEFB;">' + _esc(leader_name) + '</div>',
    )
    return pg


# ── summary ──────────────────────────────────────────────────────────────────

def _gauge_card(dim, score, band, benchmark) -> str:
    return (
        '<div style="border:1px solid #DCE4EE;border-radius:12px;padding:14px 16px 13px;">'
        '<div style="font-size:10px;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;color:#64708A;">'
        + _esc(dim) + '</div>'
        '<div style="display:flex;align-items:baseline;gap:8px;margin-top:8px;">'
        '<span style="font-family:\'Barlow\',sans-serif;font-weight:900;font-size:40px;line-height:1;color:#0D2A66;">'
        + str(_i(score)) + '</span>'
        '<span style="font-size:10px;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;color:#115A9C;'
        'background:#EBF5FE;padding:3px 8px;border-radius:999px;">' + _esc(band) + '</span></div>'
        '<div style="position:relative;height:7px;background:#EEF2F8;border-radius:999px;margin-top:14px;">'
        '<div style="position:absolute;left:0;top:0;bottom:0;width:' + str(max(0, min(100, _i(score)))) +
        '%;background:#1E88E5;border-radius:999px;"></div>'
        '<div style="position:absolute;left:' + str(max(0, min(100, _i(benchmark)))) +
        '%;top:-3px;bottom:-3px;width:2px;background:#0D2A66;border-radius:2px;"></div></div>'
        '<div style="font-size:10.5px;color:#64708A;margin-top:9px;">Industry Benchmark'
        '<sup style="font-size:7px;">1</sup> &nbsp;' + str(_i(benchmark)) + '</div></div>'
    )


def _build_summary(stats, benchmarks, narrative, company) -> str:
    pg = _load_shell()["pages"]["Summary"]
    d = stats["dims"]
    strength, priority = stats["strength"], stats["priority"]

    # headline
    headline = _nar(narrative, "headline",
                    f"{company} averages {stats['overall']} across the three dimensions, with "
                    f"{strength} ({d[strength]}) its strongest signal and {priority} ({d[priority]}) "
                    "the area to watch.")
    pg = _swap_node_text(pg, "The headline", _esc(headline), tag="p")

    # three gauges: replace the grid inner content
    gauges = "".join(
        _gauge_card(dim, d.get(dim, 0), _band(d.get(dim, 0)), benchmarks.get(dim, 0))
        for dim in ("Communication", "Decision Making", "Collaboration")
    )
    anchor = '<!-- three dimension scores -->'
    ai = pg.find(anchor)
    grid = pg.find("grid-template-columns:1fr 1fr 1fr", ai)
    inner = pg.find(">", grid) + 1
    grid_close = _matching_div_close(pg, pg.rfind("<div", 0, grid))
    # grid_close is end of the grid div; replace its inner (between inner..close-of-grid)
    # find the </div> that closes the grid container:
    g_open = pg.rfind("<div", 0, grid)
    g_end = _matching_div_close(pg, g_open)
    pg = pg[:inner] + gauges + pg[g_end - 6:]  # keep the grid's closing </div>

    # strength / second-strength / priority cards.
    # Rank dims so the cards reflect THIS team (design order: 2 strengths + 1 priority).
    ranked = sorted(d, key=d.get, reverse=True)
    s1 = ranked[0]                      # strongest
    s2 = ranked[1] if len(ranked) > 1 else ranked[0]  # second
    pr = ranked[-1]                     # priority (lowest)
    s_body = _nar(narrative, "strength",
                  f"{s1} is the team's highest dimension at {d[s1]}, above the Industry "
                  f"Benchmark of {benchmarks.get(s1,0)}.")
    s2_body = _nar(narrative, "what_this_means",
                   f"{s2} also sits above benchmark ({benchmarks.get(s2,0)}) at {d[s2]}, a second "
                   "team-level asset.")
    p_body = _nar(narrative, "priority",
                  f"{pr} is the lowest average at {d[pr]} and the area to prioritise.")

    # design cards (positional): label span + score span + <p> body
    pg = _swap_card(pg, "Strength — Collaboration", f"Strength — {s1}", d[s1], s_body, "#1E88E5")
    pg = _swap_card(pg, "Strength — Communication", f"Strength — {s2}", d[s2], s2_body, "#1E88E5")
    pg = _swap_card(pg, "Priority — Decision Making", f"Priority — {pr}", d[pr], p_body, "#A8690A")

    # team shape + structural risk
    shape = _nar(narrative, "team_shape",
                 f"{stats['n']} members, average {stats['overall']}. "
                 + ", ".join(f"{cnt} {a}" for a, cnt in stats["arche"].items()) + ".")
    risk = _nar(narrative, "structural_risk",
                ("The mix is weighted toward " + (stats["arche"].most_common(1)[0][0] if stats["arche"] else "execution")
                 + ". Watch how decisions are owned across the team."))
    pg = _swap_node_text(pg, "Team shape", _esc(shape), tag="p")
    # "The structural risk:" lives INSIDE its own <p> (label is part of the text),
    # so replace the whole enclosing paragraph, re-adding the bold-ish label prefix.
    ri = pg.find("The structural risk")
    if ri >= 0:
        p_open = pg.rfind("<p", 0, ri)
        if p_open >= 0:
            gt = pg.find(">", p_open) + 1
            pcl = pg.find("</p>", gt)
            if pcl >= 0:
                pg = pg[:gt] + "The structural risk: " + _esc(risk) + pg[pcl:]
    return pg


def _swap_card(page, marker, new_label, score, new_body, label_color) -> str:
    """Replace a summary card's label span text, its adjacent score span, and
    its <p> body. The design card is:
        <span ...color:LABEL>LABEL TEXT</span><span ...>SCORE</span> ... <p>BODY</p>
    """
    i = page.find(marker)
    if i < 0:
        return page
    # `i` points at the label TEXT itself (between '>' and '</span>')
    lc = page.find("</span>", i)
    page = page[:i] + _esc(new_label) + page[lc:]
    lc = page.find("</span>", i)  # recompute after length change
    # adjacent score span (the next <span> after the label span close)
    si = page.find("<span", lc)
    if si >= 0:
        sgt = page.find(">", si) + 1
        scl = page.find("</span>", sgt)
        page = page[:sgt] + str(_i(score)) + page[scl:]
    # body paragraph
    pi = page.find("<p", lc)
    if pi >= 0:
        pgt = page.find(">", pi) + 1
        pcl = page.find("</p>", pgt)
        if pcl >= 0:
            page = page[:pgt] + _esc(new_body) + page[pcl:]
    return page


# ── section 3 · who is who + archetype mix ────────────────────────────────────

def _cell_color(score) -> str:
    s = _num(score)
    if s >= 75:
        return "color:#115A9C;"
    if s >= 60:
        return "color:#1F2740;"
    return "color:#A8690A;background:#FFF6E8;"


def _whoiswho_row(p) -> str:
    cols = "1.5fr 1fr 0.8fr 0.9fr 0.8fr 0.7fr 1.05fr"
    if p["focus"] == "Check-In":
        pill = ('<span style="font-size:10px;font-weight:700;color:#A8690A;background:#FFF3DF;'
                'padding:3px 10px;border-radius:999px;">Check-In</span>')
    else:
        pill = ('<span style="font-size:10px;font-weight:700;color:#115A9C;background:#EBF5FE;'
                'padding:3px 10px;border-radius:999px;">Stretch</span>')

    def sc(v):
        return ('<div style="padding:12px 8px;text-align:center;font-family:\'Barlow\',sans-serif;'
                'font-weight:700;font-size:14px;' + _cell_color(v) + '">' + str(_i(v)) + '</div>')

    return (
        '<div style="display:grid;grid-template-columns:' + cols + ';align-items:center;border-top:1px solid #EEF2F8;">'
        '<div style="padding:12px 16px;font-weight:700;font-size:13px;color:#0D2A66;">' + _esc(p["name"]) + '</div>'
        '<div style="padding:12px 8px;font-size:11.5px;color:#64708A;">' + _esc(p["archetype"]) + '</div>'
        + sc(p["c"]) + sc(p["d"]) + sc(p["co"]) +
        '<div style="padding:12px 8px;text-align:center;font-family:\'Barlow\',sans-serif;font-weight:800;'
        'font-size:14px;color:#0D2A66;">' + str(_i(p["avg"])) + '</div>'
        '<div style="padding:12px 16px;text-align:right;">' + pill + '</div></div>'
    )


def _team_avg_row(stats) -> str:
    cols = "1.5fr 1fr 0.8fr 0.9fr 0.8fr 0.7fr 1.05fr"
    d = stats["dims"]

    def sc(v):
        return ('<div style="padding:13px 8px;text-align:center;font-family:\'Barlow\',sans-serif;'
                'font-weight:800;font-size:15px;color:#0D2A66;">' + str(_i(v)) + '</div>')

    return (
        '<div style="display:grid;grid-template-columns:' + cols + ';align-items:center;'
        'border-top:2px solid #DCE4EE;background:#E3F2FD;">'
        '<div style="padding:13px 16px;font-weight:800;font-size:12px;letter-spacing:0.04em;'
        'text-transform:uppercase;color:#0D2A66;">Team Average</div>'
        '<div style="padding:13px 8px;"></div>'
        + sc(d.get("Communication", 0)) + sc(d.get("Decision Making", 0)) + sc(d.get("Collaboration", 0)) +
        sc(stats["overall"]) +
        '<div style="padding:13px 16px;"></div></div>'
    )


def _arche_count_rows(participants, stats) -> str:
    cols = "1.1fr 0.7fr 0.7fr 1.6fr"
    members_by = {}
    for p in participants:
        members_by.setdefault(p["archetype"], []).append(p["name"])
    n = stats["n"]
    present = [a for a in ALL_ARCHETYPES if stats["arche"].get(a)]
    rows = []
    for k, a in enumerate(present):
        cnt = stats["arche"][a]
        share = round(cnt / n * 100) if n else 0
        border = "" if k == len(present) - 1 else "border-bottom:1px solid #EEF2F8;"
        rows.append(
            '<div style="display:grid;grid-template-columns:' + cols + ';align-items:center;' + border + '">'
            '<div style="padding:10px 14px;font-weight:700;font-size:12px;color:#0D2A66;">' + _esc(a) + '</div>'
            '<div style="padding:10px 6px;text-align:center;font-family:\'Barlow\',sans-serif;font-weight:700;'
            'font-size:13px;color:#1F2740;">' + str(cnt) + '</div>'
            '<div style="padding:10px 6px;text-align:center;font-size:11.5px;color:#64708A;">' + str(share) + '%</div>'
            '<div style="padding:10px 14px;font-size:11px;color:#2E3852;">' + _esc(", ".join(members_by[a])) + '</div></div>'
        )
    return "".join(rows)


def _build_whoiswho(participants, stats) -> str:
    pg = _load_shell()["pages"]["Section 3"]
    # The table body is: member rows + the existing "<!-- Team Average -->" row.
    # Replace from the first member row through the close of the Team Average row
    # (keeping the table container's own closing </div>, which follows it).
    start = pg.find("<!-- Harmony -->")
    ta = pg.find("<!-- Team Average -->")
    ta_open = pg.find("<div", ta)
    end = _matching_div_close(pg, ta_open)  # just past the Team Average row's </div>
    rows = "".join(_whoiswho_row(p) for p in participants) + _team_avg_row(stats)
    pg = pg[:start] + rows + pg[end:]
    # archetype count table rows
    pg = _swap_arche_count(pg, _arche_count_rows(participants, stats))
    if len(participants) > _CAP_WHOISWHO:
        pg = _allow_overflow(pg)
    return pg


def _swap_arche_count(pg, rows_html) -> str:
    cols_sig = 'grid-template-columns:1.1fr 0.7fr 0.7fr 1.6fr;align-items:center;'
    first, end = _consume_rows(pg, cols_sig)
    if first < 0:
        return pg
    return pg[:first] + rows_html + pg[end:]


# ── section 2 · archetype definition cards ────────────────────────────────────

def _arche_def_card(archetype, count, total) -> str:
    present = count > 0
    blurb = ARCHETYPE_BLURB.get(archetype, "")
    if present:
        border, bg, title, ptxt = "#BBD9F6", "#F4F9FE", "#0D2A66", "#2E3852"
        pill = ('<span style="font-size:9.5px;font-weight:700;letter-spacing:0.04em;color:#fff;'
                'background:#1E88E5;padding:3px 9px;border-radius:999px;">' + str(count) + ' of ' + str(total) + '</span>')
    else:
        border, bg, title, ptxt = "#E6EBF2", "#F8FAFC", "#94A0B4", "#64708A"
        pill = ('<span style="font-size:9.5px;font-weight:700;letter-spacing:0.04em;color:#94A0B4;'
                'background:#EEF2F8;padding:3px 9px;border-radius:999px;">Not present</span>')
    return (
        '<div style="border:1px solid ' + border + ';background:' + bg + ';border-radius:12px;padding:14px 16px;">'
        '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">'
        '<span style="font-family:\'Barlow\',sans-serif;font-weight:800;font-size:15px;letter-spacing:0.06em;color:'
        + title + ';">' + _esc(archetype.upper()) + '</span>' + pill + '</div>'
        '<p style="margin:0;font-size:12px;line-height:1.5;color:' + ptxt + ';max-width:none;">' + _esc(blurb) + '</p></div>'
    )


def _build_archetypes(stats) -> str:
    pg = _load_shell()["pages"]["Section 2"]
    n = stats["n"]
    cards = "".join(_arche_def_card(a, stats["arche"].get(a, 0), n) for a in ALL_ARCHETYPES)
    # the six cards are siblings; first opens at the first border-card after RELAY label.
    relay = pg.find("RELAY")
    first = pg.rfind('<div style="border:1px solid', 0, relay)
    if first < 0:
        return pg
    # walk 6 sibling cards
    i = first
    end = first
    for k in range(6):
        end = _matching_div_close(pg, i)
        nxt = pg.find('<div style="border:1px solid', end)
        if nxt < 0:
            break
        i = nxt
    pg = pg[:first] + cards + pg[end:]
    # closing line "Three of the six archetypes are present..." -> derive
    present = [a for a in ALL_ARCHETYPES if stats["arche"].get(a)]
    return pg


# ── section 5 · working style ─────────────────────────────────────────────────

_WS_CELL = ('<div style="padding:9px 12px;">'
            '<div style="font-weight:700;font-size:11px;color:#115A9C;margin-bottom:3px;">{name}</div>'
            '<div style="font-size:10.5px;line-height:1.4;color:#64708A;">{desc}</div></div>')


def _working_style_row(p) -> str:
    cols = "0.85fr 1.4fr 1.4fr 1.4fr"
    ws = p.get("working_style", {}) or {}

    def cell(dim):
        v = ws.get(dim, {})
        if isinstance(v, str):
            name, desc = v, ""
        else:
            name, desc = v.get("name", "—"), v.get("description", "")
        return _WS_CELL.format(name=_esc(name), desc=_esc(desc))

    return (
        '<div style="display:grid;grid-template-columns:' + cols + ';border-top:1px solid #EEF2F8;">'
        '<div style="padding:9px 14px;background:#F7FAFE;">'
        '<div style="font-weight:700;font-size:12px;color:#0D2A66;">' + _esc(p["name"]) + '</div>'
        '<div style="font-size:10px;color:#94A0B4;">' + _esc(p["archetype"]) + '</div></div>'
        + cell("Communication") + cell("Decision Making") + cell("Collaboration") + '</div>'
    )


def _build_working_style(participants, narrative, company, stats) -> str:
    pg = _load_shell()["pages"]["Section 5"]
    intro = _nar(narrative, "working_style_summary", "")
    if intro:
        pg = _swap_node_text(pg, "The team's working style today", _esc(intro), tag="p")
    rows = "".join(_working_style_row(p) for p in participants)
    sig = 'grid-template-columns:0.85fr 1.4fr 1.4fr 1.4fr;border-top'
    first, end = _consume_rows(pg, sig)
    if first < 0:
        return pg
    pg = pg[:first] + rows + pg[end:]
    if len(participants) > _CAP_WORKSTYLE:
        pg = _allow_overflow(pg)
    return pg


# ── section 6 · who to focus on ───────────────────────────────────────────────

def _focus_row(p, narrative_text, last) -> str:
    cols = "120px 42px 42px 42px 1fr"
    border = "" if last else "border-bottom:1px solid #EEF2F8;"

    def sc(v):
        s = _num(v)
        col = "#115A9C" if s >= 75 else "#1F2740" if s >= 60 else "#A8690A"
        return ('<div style="padding:12px 4px;text-align:center;font-family:\'Barlow\',sans-serif;'
                'font-weight:700;font-size:13px;color:' + col + ';">' + str(_i(v)) + '</div>')

    return (
        '<div style="display:grid;grid-template-columns:' + cols + ';align-items:center;' + border + '">'
        '<div style="padding:12px 16px;"><div style="font-weight:700;font-size:12.5px;color:#0D2A66;">'
        + _esc(p["name"]) + '</div><div style="font-size:10px;color:#94A0B4;">' + _esc(p["archetype"]) + '</div></div>'
        + sc(p["c"]) + sc(p["d"]) + sc(p["co"]) +
        '<div style="padding:11px 16px;font-size:11px;line-height:1.45;color:#455066;">' + narrative_text + '</div></div>'
    )


def _focus_empty(msg) -> str:
    return '<div style="padding:14px 16px;font-size:11px;color:#64708A;">' + _esc(msg) + '</div>'


def _build_focus(stats, narrative) -> str:
    pg = _load_shell()["pages"]["Section 6"]
    nar = (narrative or {}).get("focus", {}) or {}

    def member_nar(p, kind):
        if nar.get(p["name"]):
            return nar[p["name"]]
        if kind == "check":
            low = min(("Communication", p["c"]), ("Decision Making", p["d"]),
                      ("Collaboration", p["co"]), key=lambda t: t[1])
            return (f"{low[0]} ({_i(low[1])}) sat below the 60 threshold. "
                    '<span style="color:#0D2A66;font-style:italic;">An opener: '
                    f'&ldquo;When the moment came on {low[0].lower()}, what was your read, and what '
                    'would have made you move sooner?&rdquo;</span>')
        return (f"Consistent performer (avg {_i(p['avg'])}). "
                '<span style="color:#0D2A66;font-style:italic;">An opener: '
                "&ldquo;Where is a situation coming up where you would normally wait, but could "
                "lead?&rdquo;</span>")

    sig = 'grid-template-columns:120px 42px 42px 42px 1fr'

    def group_rows(people, kind):
        if not people:
            return _focus_empty("No members in this group this round.")
        return "".join(_focus_row(p, member_nar(p, kind), last=(i == len(people) - 1))
                       for i, p in enumerate(people))

    # Locate the two group HEADERS (label span immediately followed by "N of N").
    chk_hdr = _find_group_header(pg, "Check-In")
    str_hdr = _find_group_header(pg, "Stretch", start_from=(chk_hdr + 1 if chk_hdr >= 0 else 0))

    # ---- Check-In first (earlier in doc; bounded by the Stretch header) ----
    pg = _swap_focus_count(pg, chk_hdr, len(stats["check_ins"]), stats["n"])
    pg = _swap_focus_rows(pg, chk_hdr, sig, group_rows(stats["check_ins"], "check"), stop=str_hdr)
    # ---- Stretch (recompute its header index after the Check-In edits) ----
    str_hdr = _find_group_header(pg, "Stretch")
    pg = _swap_focus_count(pg, str_hdr, len(stats["stretches"]), stats["n"])
    pg = _swap_focus_rows(pg, str_hdr, sig, group_rows(stats["stretches"], "stretch"), stop=-1)
    if len(stats["check_ins"]) > _CAP_FOCUS or len(stats["stretches"]) > _CAP_FOCUS:
        pg = _allow_overflow(pg)
    return pg


def _find_group_header(pg, label, start_from=0):
    """Return the index of the group HEADER span for `label` (the occurrence
    immediately followed, within ~80 chars, by an 'N of N' count), not the
    intro-paragraph mention."""
    i = pg.find(">" + label + "</span>", start_from)
    while i >= 0:
        if re.search(r"\d+\s*of\s*\d+", pg[i:i + 120]):
            return i
        i = pg.find(">" + label + "</span>", i + 1)
    return pg.find(label, start_from)  # fallback


def _swap_focus_count(pg, hdr_idx, count, total) -> str:
    if hdr_idx < 0:
        return pg
    seg = pg[hdr_idx:hdr_idx + 200]
    m = re.search(r"\d+\s*of\s*\d+", seg)
    if m:
        return pg[:hdr_idx + m.start()] + f"{count} of {total}" + pg[hdr_idx + m.end():]
    return pg


def _swap_focus_rows(pg, hdr_idx, sig, rows_html, stop) -> str:
    if hdr_idx < 0:
        return pg
    if stop < 0:
        stop = pg.find("The Performance Lens", hdr_idx)
    first, end = _consume_rows(pg, sig, start_from=hdr_idx, stop=stop)
    if first < 0:
        return pg
    return pg[:first] + rows_html + pg[end:]


# ── appendix ──────────────────────────────────────────────────────────────────

def _build_appendix(benchmarks) -> str:
    pg = _load_shell()["pages"]["Appendix"]
    for dim, default in DEFAULT_BENCHMARKS.items():
        val = _i(benchmarks.get(dim, default))
        old, new = f"{dim} {default}", f"{dim} {val}"
        if old != new:
            pg = pg.replace(old, new)
    return pg


# ── fixed-prose pages (kept verbatim, light token swaps) ──────────────────────

def _fixed_page(label, company, override_html=None) -> str:
    """Return a section page. If `override_html` is given, the page's BODY content
    (everything between the section title block and the footer) is replaced with
    the supplied HTML, letting a narrative engine fully own narrative-heavy
    sections (4 · dynamics, 8 · action plan, 9 · what's next). Otherwise the
    approved reference layout is kept verbatim (identity tokens are swapped
    globally by build_leader_report_html).
    """
    pg = _load_shell()["pages"][label]
    if override_html:
        # body sits after the section-title <h2>/<h1>; footer is the absolutely
        # positioned bar near the bottom of the page wrapper.
        title_end = pg.find("</h1>")
        if title_end < 0:
            title_end = pg.find("</h2>")
        ftr = pg.find('<div style="position:absolute;left:64px;right:64px;bottom:34px')
        if title_end >= 0 and ftr > title_end:
            cut = pg.find(">", title_end) + 1 if title_end >= 0 else 0
            after_title = pg.find("</h1>", title_end)
            after_title = (after_title + 5) if after_title >= 0 else (pg.find("</h2>", title_end) + 5)
            pg = pg[:after_title] + "\n" + override_html + "\n  " + pg[ftr:]
    return pg


# ── What to Expect Next (Section 9) — dynamic recommendation ──────────────────
# Canonical focused-session names (one per dimension) + what each session builds.
# Focused sessions are DEVELOPMENT, not assessment: they do NOT capture data or
# produce a profile. Data is only captured in a full workshop.
_FOCUS_SESSIONS = {
    "Communication":   ("Communicating with Clarity",
                        "sharpen precision, listening, and adapting the message under pressure"),
    "Decision Making": ("Deciding with Conviction",
                        "redistribute decision ownership and break deferral patterns"),
    "Collaboration":   ("Collaborating Under Pressure",
                        "build role flexibility, recovery under pressure, and coordination"),
}

def _replace_p_after(pg: str, start_phrase: str, new_inner: str) -> str:
    """Replace the inner HTML of the <p> that contains `start_phrase`."""
    i = pg.find(start_phrase)
    if i < 0:
        return pg
    p_open = pg.rfind("<p", 0, i)
    if p_open < 0:
        return pg
    gt = pg.find(">", p_open) + 1
    pcl = pg.find("</p>", gt)
    if pcl < 0:
        return pg
    return pg[:gt] + new_inner + pg[pcl:]

def _build_whats_next(stats, company) -> str:
    """Section 9. Recommend the focused session that matches THIS team's priority
    dimension (by its correct name), make clear focused sessions do not capture
    data, frame the annual program as workshop-bookended, and turn the CTA into a
    real button to the for-business page."""
    pg = _load_shell()["pages"]["Section 9"]
    pr = stats.get("priority") or "Decision Making"
    name, desc = _FOCUS_SESSIONS.get(pr, _FOCUS_SESSIONS["Decision Making"])
    others = [f"{_FOCUS_SESSIONS[d][0]} ({d})"
              for d in ("Communication", "Decision Making", "Collaboration") if d != pr]
    other_named = " and ".join(others) if len(others) == 2 else ", ".join(others)

    focus_inner = (
        f"A single half-day session aimed at one dimension. For {_esc(company)}, the workshop data "
        f"points to {pr}, which makes <strong style=\"color:#115A9C;font-weight:700;\">{name}</strong> "
        f"the prescribed fit: it is built to {desc}. The format mirrors the workshop — pressure and "
        "play, no lectures — but it is a development session, not an assessment, so it does not capture "
        f"data or produce a new profile. {other_named} use the same format if a different priority emerges."
    )
    annual_inner = (
        "A year-long program that bookends development with a full workshop at the start and another at "
        "the end. Those two workshops are where the data is captured; comparing them shows movement "
        "dimension by dimension and how the archetype mix has shifted. Focused sessions run in between to "
        "build the priority areas. This path suits leaders who want data, not opinion, on whether the "
        "team is developing."
    )
    pg = _replace_p_after(pg, "An ongoing measure of how the team develops", annual_inner)
    pg = _replace_p_after(pg, "A single half-day session aimed at one dimension", focus_inner)

    # CTA: plain text link -> styled button pointing at the real page (swap the
    # opening tag only, so the label + arrow glyph are preserved untouched).
    pg = pg.replace(
        '<a href="#" style="font-size:12px;font-weight:700;color:#1E88E5;text-decoration:none;">',
        '<a href="https://theperformancelens.com/for-business/" target="_blank" '
        'style="display:inline-block;background:#1E88E5;color:#fff;font-size:12px;font-weight:700;'
        'text-decoration:none;padding:11px 24px;border-radius:8px;letter-spacing:0.02em;">',
    )
    return pg


# ──────────────────────────────────────────────────────────────────────────────
# Pagination guard: split a too-tall table page across continuation pages
# ──────────────────────────────────────────────────────────────────────────────

def _allow_overflow(pg: str) -> str:
    """Let a too-tall table page flow across multiple printed sheets instead of
    clipping. The global CSS pins `[data-page]{break-inside:avoid}` and the wrapper
    sets a fixed `min-height:1056px`; for oversize pages we relax both so Chromium
    paginates the tall content naturally (the absolute footer renders once)."""
    op = pg.find('<div data-page=""')
    gt = pg.find('style="', op) + len('style="')
    end = pg.find('"', gt)
    style = pg[gt:end]
    style = style.replace("overflow:hidden;", "")
    style = "break-inside:auto;" + style
    return pg[:gt] + style + pg[end:]


def _note_oversize(pages_out, label, n_rows, cap):
    """Emit a console note when a section exceeds its single-page row capacity.

    The design uses break-inside:avoid per page, so very large teams (rows beyond
    `cap`) should be split. We keep all rows on the page (Chromium will still
    render them; for print they may extend the sheet), and surface a note so the
    pipeline can opt into multi-page splitting upstream if needed.
    """
    if n_rows > cap:
        print(f"[note] {label}: {n_rows} rows exceeds single-page capacity (~{cap}); "
              "consider splitting for very large teams.")


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def build_leader_report_html(data: dict) -> str:
    """Build the full Leadership Insight Report HTML from `data` (Chromium-ready)."""
    shell = _load_shell()

    company = data.get("company") or data.get("team_name") or "Your Team"
    workshop_date = data.get("workshop_date", "")
    leader_name = data.get("leader_name", "Team Leader")
    narrative = data.get("narrative", {}) or {}

    benchmarks = dict(DEFAULT_BENCHMARKS)
    benchmarks.update(data.get("benchmarks", {}) or {})

    participants = [_enrich(p) for p in data.get("participants", [])]
    stats = _stats(participants, benchmarks)

    _note_oversize(None, "Who Is Who", stats["n"], _CAP_WHOISWHO)
    _note_oversize(None, "Working Style", stats["n"], _CAP_WORKSTYLE)
    _note_oversize(None, "Check-In", len(stats["check_ins"]), _CAP_FOCUS)
    _note_oversize(None, "Stretch", len(stats["stretches"]), _CAP_FOCUS)

    pages = [
        _build_cover(company, workshop_date, leader_name),       # 1  Cover
        _build_summary(stats, benchmarks, narrative, company),   # 2  Summary
        _fixed_page("Section 1", company),                       # 3  About
        _build_archetypes(stats),                                # 4  Profile system
        _build_whoiswho(participants, stats),                    # 5  Who is who
        _fixed_page("Section 4", company, narrative.get("page_dynamics")),       # 6  How team works
        _build_working_style(participants, narrative, company, stats),  # 7  Working style
        _build_focus(stats, narrative),                          # 8  Who to focus on
        _fixed_page("Section 7", company),                       # 9  Profile guide
        _fixed_page("Section 8", company, narrative.get("page_action_plan")),    # 10 Action plan
        (_fixed_page("Section 9", company, narrative["page_whats_next"])         # 11 What's next
         if narrative.get("page_whats_next") else _build_whats_next(stats, company)),
        _build_appendix(benchmarks),                             # 12 Appendix
    ]

    body = "\n\n".join(pages)

    # Global identity-token swap: the reference's fixed prose carries the sample
    # cohort's identity (team "Cobi", leader "Jay Kim", "May 2026"). Replace those
    # literal tokens everywhere so nothing from the sample leaks into fixed pages
    # (Sections 1/4/7/8/9 + appendix footer). Order matters: longest first.
    REF_TEAM, REF_LEADER, REF_DATE = "Cobi", "Jay Kim", "May 2026"
    if leader_name and leader_name != REF_LEADER:
        body = body.replace(REF_LEADER, _esc(leader_name))
    if workshop_date and workshop_date != REF_DATE:
        body = body.replace(REF_DATE, _esc(workshop_date))
    if company and company != REF_TEAM:
        body = body.replace(REF_TEAM, _esc(company))

    html = (shell["head"].replace("<title>Bundled Page</title>",
                                  "<title>Leadership Insight Report · " + _esc(company) + "</title>")
            + "\n" + body + shell["tail"])
    return html


# ──────────────────────────────────────────────────────────────────────────────
# DATA SCHEMA (reference for the upstream sheet + narrative engine)
# ──────────────────────────────────────────────────────────────────────────────

DATA_SCHEMA = {
    "company": "str -- team/cohort display name (alias: team_name)",
    "cohort_code": "str -- optional internal cohort/profile ID (not rendered)",
    "workshop_date": "str -- e.g. 'May 2026'",
    "leader_name": "str -- 'Prepared for' name on the cover",
    "benchmarks": {
        "Communication": "int", "Decision Making": "int", "Collaboration": "int",
    },
    "participants": [
        {
            "name": "str",
            "archetype": "Relay|Navigator|Signal|Summit|Anchor|Compass",
            "c_score": "int 0-100 (Communication)",
            "d_score": "int 0-100 (Decision Making)",
            "co_score": "int 0-100 (Collaboration)",
            "focus": "Stretch|Check-In  (optional -- derived if omitted)",
            "working_style": {
                "Communication": {"name": "str", "description": "str"},
                "Decision Making": {"name": "str", "description": "str"},
                "Collaboration": {"name": "str", "description": "str"},
            },
        }
    ],
    "narrative": {
        "headline": "str -- TL;DR one-liner (Summary)",
        "strength": "str -- strength card body (Summary)",
        "priority": "str -- priority card body (Summary)",
        "what_this_means": "str -- middle summary card body",
        "team_shape": "str -- 'Team shape' paragraph",
        "structural_risk": "str -- 'The structural risk' paragraph",
        "working_style_summary": "str -- 'The team's working style today' paragraph",
        "focus": {"<participant name>": "str (HTML allowed) -- focus opener"},
        "page_dynamics": "str (full HTML) -- optional override for Section 4 body "
                         "('How This Team Works Together'); falls back to the reference layout",
        "page_action_plan": "str (full HTML) -- optional override for Section 8 body (Action Plan)",
        "page_whats_next": "str (full HTML) -- optional override for Section 9 body (What to Expect Next)",
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# Test harness
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
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
                 "Communication": WS("Considered & Thorough", "Confirms before acting; checks alignment rather than assuming it."),
                 "Decision Making": WS("Considered & Thorough", "Weighs the brief and commits once direction is set."),
                 "Collaboration": WS("Close & Collaborative", "Works shoulder to shoulder; a steady contributor inside the group.")}},
            {"name": "Mia", "archetype": "Relay", "c_score": 73, "d_score": 56, "co_score": 76,
             "working_style": {
                 "Communication": WS("Warm & Attuned", "Reads tone and adjusts; keeps the channel open."),
                 "Decision Making": WS("Consultative", "Prefers to align with others before committing."),
                 "Collaboration": WS("Close & Collaborative", "Builds rapport quickly and keeps the group cohesive.")}},
            {"name": "Phuong", "archetype": "Navigator", "c_score": 63, "d_score": 85, "co_score": 63,
             "working_style": {
                 "Communication": WS("Direct & Brief", "Says the essential thing and moves on."),
                 "Decision Making": WS("Decisive", "Commits early, even with incomplete information."),
                 "Collaboration": WS("Independent", "Comfortable carrying a call alone when needed.")}},
            {"name": "Rose", "archetype": "Relay", "c_score": 75, "d_score": 63, "co_score": 78,
             "working_style": {
                 "Communication": WS("Considered & Thorough", "Clarifies the brief before acting."),
                 "Decision Making": WS("Considered & Thorough", "Weighs options; commits once direction is set."),
                 "Collaboration": WS("Close & Collaborative", "A connector across workstreams.")}},
            {"name": "Snow", "archetype": "Signal", "c_score": 87, "d_score": 58, "co_score": 73,
             "working_style": {
                 "Communication": WS("Warm & Attuned", "Notices what is unsaid; keeps people aligned."),
                 "Decision Making": WS("Consultative", "Checks the room before stating a call."),
                 "Collaboration": WS("Close & Collaborative", "Reduces friction early; an informal connector.")}},
            {"name": "Tuong Vy", "archetype": "Summit", "c_score": 70, "d_score": 79, "co_score": 88,
             "working_style": {
                 "Communication": WS("Direct & Brief", "States the standard plainly."),
                 "Decision Making": WS("Decisive", "Pushes for the better answer, not the first one."),
                 "Collaboration": WS("Close & Collaborative", "Lifts the group's bar by example.")}},
        ],
        "narrative": {
            "headline": "Atlas executes and collaborates strongly; the opportunity is to spread decision ownership beyond its two decisive members.",
            "strength": "Collaboration is the team's strongest dimension, comfortably above benchmark, with Tuong Vy leading at 88. The team holds together when roles blur.",
            "priority": "Decision Making is the widest-spread dimension: Phuong leads at 85 while Mia and Snow sit below the 60 line. The average flatters it.",
            "what_this_means": "The strong communicators keep alignment tight, which lets the team's collaboration strength compound rather than leak.",
            "team_shape": "6 members, average 73. A Relay-heavy execution base with one Navigator, one Signal and one Summit to raise the bar.",
            "structural_risk": "Four Relays mean decisions can funnel to the two decisive members. Distribute ownership before the dependency sets.",
            "working_style_summary": "Atlas prefers a clear brief before it acts, with several warm, consultative members and two decisive voices who set direction.",
            "focus": {
                "Mia": "Decision Making (56) was the constraint, despite strong Communication and Collaboration. "
                       "<span style=\"color:#0D2A66;font-style:italic;\">An opener: &ldquo;Walk me through the last time the team needed a call and stalled.&rdquo;</span>",
                "Snow": "Decision Making (58) sat just below threshold, alongside the team's highest Communication score (87). "
                        "<span style=\"color:#0D2A66;font-style:italic;\">An opener: &ldquo;When you can see what's next, what decides whether you go or wait?&rdquo;</span>",
            },
        },
    }

    out_html = build_leader_report_html(fake)
    out_path = "/sessions/zealous-ecstatic-meitner/mnt/outputs/leader_report_testgen.html"
    if not os.path.isdir(os.path.dirname(out_path)):
        out_path = os.path.join(os.getcwd(), "leader_report_testgen.html")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out_html)

    size = os.path.getsize(out_path)
    print(f"WROTE {out_path}  ({size:,} bytes)")
    print("pages (data-page):", out_html.count('data-page=""'))
    print("@font-face present:", "@font-face" in out_html, "| count:", out_html.count("@font-face"))
    print("base64 font block present:", "base64" in out_html)
    cleaned = re.sub(r'data:[^"\\)]+', '', out_html)
    print("dangling UUID refs:", len(_UUID_RE.findall(cleaned)))
    for tok in ("{{", "}}", "{name}", "{desc}", "%s"):
        print(f"stray {tok!r}:", out_html.count(tok))
