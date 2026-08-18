# -*- coding: utf-8 -*-
"""
Working Style layer — HTML renderer (web profile + PDF-via-Chromium).

Dark/blue theme matched to the participant profile. Self-contained (scoped .ws-* CSS,
inline SVG icons) so it renders identically standalone or injected into the compiled
archetype template. Visual-first for ESL readers: a per-dimension icon, a visual
"style mix" bar, icon chips for the how-to-work-with-you points, and a complementary-
style card. Supporting language is kept alongside the visuals.
"""
import html as _html
import math
from working_style import build_blocks

WS_SUBHEAD = ("How you like to work: your preferences, your strengths, and what helps you "
              "do your best.")

# ── Inline SVG icons (solid filled flat style, currentColor) ────────────────────
_IC_COMM = ('<svg viewBox="0 0 24 24" fill="currentColor"><path d="M4 2.5h16a2 2 0 0 1 2 2v10a2 2 '
            '0 0 1-2 2h-7.2L8 20.5v-4H4a2 2 0 0 1-2-2v-10a2 2 0 0 1 2-2z"/>'
            '<circle cx="8" cy="9.5" r="1.2" fill="#fff" opacity=".9"/>'
            '<circle cx="12" cy="9.5" r="1.2" fill="#fff" opacity=".9"/>'
            '<circle cx="16" cy="9.5" r="1.2" fill="#fff" opacity=".9"/></svg>')
_IC_DEC  = ('<svg viewBox="0 0 24 24" fill="currentColor"><path d="M13.1 2.6 22 11.5a1.6 1.6 0 0 1 '
            '0 2.3l-8.9 8.9a1.6 1.6 0 0 1-2.3 0L2 13.8a1.6 1.6 0 0 1 0-2.3l8.9-8.9a1.6 1.6 0 0 1 '
            '2.2 0z"/><path d="m15.8 9.4-4.6 4.7-2.4-2.4" fill="none" stroke="#fff" '
            'stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>')
_IC_COLL = ('<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="8.8" cy="12" r="6.3" '
            'opacity=".62"/><circle cx="15.2" cy="12" r="6.3" opacity=".62"/>'
            '<path d="M12 6.6a6.3 6.3 0 0 1 0 10.8 6.3 6.3 0 0 1 0-10.8z"/></svg>')
_IC_CHECK= ('<svg viewBox="0 0 24 24" fill="currentColor"><path d="M20.3 5.7a1.5 1.5 0 0 1 0 2.1'
            'l-9.2 9.2a1.5 1.5 0 0 1-2.1 0L3.7 11.7a1.5 1.5 0 1 1 2.1-2.1l4.2 4.2 8.2-8.2a1.5 1.5 '
            '0 0 1 2.1 0z"/></svg>')
_IC_PAIR = ('<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="8.6" cy="7.6" r="3.4"/>'
            '<path d="M2.2 19.6a6.4 6.4 0 0 1 12.8 0v.4H2.2z"/>'
            '<circle cx="16.7" cy="8.4" r="2.7" opacity=".6"/>'
            '<path d="M16.6 20c0-2.1-.6-4-1.7-5.5a5.6 5.6 0 0 1 6.9 5.1v.4z" opacity=".6"/></svg>')
_DIM_ICON = {"Communication": _IC_COMM, "Decision-Making": _IC_DEC, "Collaboration": _IC_COLL,
             # Leadership Workshop (TLW) dimensions — reuse the same filled icon set.
             "Leadership": _IC_DEC, "Change Management": _IC_COLL, "Conflict Management": _IC_COMM}

# ── Style-specific icons (one per working style) ────────────────────────────────
# Solid filled style (flat, two-tone): main silhouette in currentColor, interior
# details in white, secondary elements at reduced opacity — matching the flat
# marketing-icon reference style rather than thin outlines.
_S = '<svg viewBox="0 0 24 24" fill="currentColor">{}</svg>'
STYLE_ICONS = {
    # Communication
    "Direct & To-the-Point":    _S.format(
        '<path d="M3 9.3h9.5V5.6c0-.88 1.06-1.32 1.7-.7l6.5 6.4c.4.39.4 1.01 0 1.4l-6.5 6.4'
        'c-.64.62-1.7.18-1.7-.7v-3.7H3a1 1 0 0 1-1-1v-3.4a1 1 0 0 1 1-1z"/>'),
    "Considered & Thorough":    _S.format(
        '<path d="M6.5 2A1.5 1.5 0 0 0 5 3.5V21a1.5 1.5 0 0 0 1.5 1.5h11A1.5 1.5 0 0 0 19 21'
        'V7.5L13.5 2z"/>'
        '<path d="M13.5 2v4a1.5 1.5 0 0 0 1.5 1.5h4z" fill="#fff" opacity=".4"/>'
        '<rect x="8" y="11" width="8" height="1.7" rx=".85" fill="#fff" opacity=".9"/>'
        '<rect x="8" y="14.4" width="8" height="1.7" rx=".85" fill="#fff" opacity=".9"/>'
        '<rect x="8" y="17.8" width="5.4" height="1.7" rx=".85" fill="#fff" opacity=".9"/>'),
    "Warm & Attuned":           _S.format(
        '<path d="M12 21.3 10.55 20C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 '
        '4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54z"/>'),
    "Curious & Questioning":    _S.format(
        '<path d="M4 2.5h16A2 2 0 0 1 22 4.5v11a2 2 0 0 1-2 2h-7.2L8 21.5v-4H4a2 2 0 0 1-2-2v-11'
        'a2 2 0 0 1 2-2z"/>'
        '<path d="M9.7 7.6a2.6 2.6 0 0 1 5.1.75c0 1.7-2.4 2.1-2.4 3.55" fill="none" '
        'stroke="#fff" stroke-width="1.9" stroke-linecap="round"/>'
        '<circle cx="12.4" cy="14.6" r="1.15" fill="#fff"/>'),
    # Decision-Making
    "Measured & Analytical":    _S.format(
        '<rect x="3.5" y="13" width="4.4" height="8" rx="1"/>'
        '<rect x="9.8" y="8" width="4.4" height="13" rx="1" opacity=".75"/>'
        '<rect x="16.1" y="3" width="4.4" height="18" rx="1"/>'),
    "Decisive & Committed":     _S.format(
        '<path d="M13.2 2 4.3 13.1c-.45.56-.05 1.4.67 1.4h4.53l-1 7.5 8.9-11.1c.45-.56.05-1.4'
        '-.67-1.4h-4.53z"/>'),
    "Consultative & Inclusive": _S.format(
        '<circle cx="5.3" cy="8.2" r="2.3" opacity=".55"/>'
        '<path d="M.8 15.4a4.5 4.5 0 0 1 6.5-4 7.3 7.3 0 0 0-2.4 4z" opacity=".55"/>'
        '<circle cx="18.7" cy="8.2" r="2.3" opacity=".55"/>'
        '<path d="M23.2 15.4a4.5 4.5 0 0 0-6.5-4 7.3 7.3 0 0 1 2.4 4z" opacity=".55"/>'
        '<circle cx="12" cy="7" r="3.1"/>'
        '<path d="M6.3 15.9a5.7 5.7 0 0 1 11.4 0v.6H6.3z"/>'),
    "Adaptive & Iterative":     _S.format(
        '<path d="M12 3.5a8.5 8.5 0 0 1 7.9 5.4h2.6l-4.2 4.9-4.2-4.9h3a5.7 5.7 0 0 0-9.8-1.1'
        'L5 6.1A8.46 8.46 0 0 1 12 3.5z"/>'
        '<path d="M12 20.5a8.5 8.5 0 0 1-7.9-5.4H1.5l4.2-4.9 4.2 4.9h-3a5.7 5.7 0 0 0 9.8 1.1'
        'l2.3 1.7a8.46 8.46 0 0 1-7 2.6z" opacity=".75"/>'),
    # Collaboration
    "Self-Directed & Focused":  _S.format(
        '<path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm0 3.2a6.8 6.8 0 1 1 0 13.6 6.8 6.8 0 '
        '0 1 0-13.6z" fill-rule="evenodd"/>'
        '<path d="M12 8.2a3.8 3.8 0 1 0 0 7.6 3.8 3.8 0 0 0 0-7.6zm0 2.4a1.4 1.4 0 1 1 0 2.8 '
        '1.4 1.4 0 0 1 0-2.8z" fill-rule="evenodd" opacity=".75"/>'
        '<circle cx="12" cy="12" r="1.4"/>'),
    "Close & Collaborative":    _S.format(
        '<circle cx="8.6" cy="7.6" r="3.4"/>'
        '<path d="M2.2 19.6a6.4 6.4 0 0 1 12.8 0v.4H2.2z"/>'
        '<circle cx="16.7" cy="8.4" r="2.7" opacity=".6"/>'
        '<path d="M16.6 20c0-2.1-.6-4-1.7-5.5a5.6 5.6 0 0 1 6.9 5.1v.4z" opacity=".6"/>'),
    "Flexible & Versatile":     _S.format(
        '<path d="M12 1.8 15.2 5.5h-2.1v3.6h-2.2V5.5H8.8z"/>'
        '<path d="M12 22.2 8.8 18.5h2.1v-3.6h2.2v3.6h2.1z"/>'
        '<path d="M1.8 12 5.5 8.8v2.1h3.6v2.2H5.5v2.1z" opacity=".75"/>'
        '<path d="M22.2 12 18.5 15.2v-2.1h-3.6v-2.2h3.6V8.8z" opacity=".75"/>'
        '<circle cx="12" cy="12" r="2.1"/>'),
    "Candid & Open":            _S.format(
        '<path d="M12 4.8C5.8 4.8 2 12 2 12s3.8 7.2 10 7.2S22 12 22 12s-3.8-7.2-10-7.2z"/>'
        '<circle cx="12" cy="12" r="3.4" fill="#fff" opacity=".92"/>'
        '<circle cx="12" cy="12" r="1.6"/>'),
}

# ── Leadership Workshop (TLW) style icons ────────────────────────────────────
# The 12 lead styles are new names with no direct match in STYLE_ICONS above.
# Reasonable fallback: render_working_style_section() and _set_tldr_ws() both
# use STYLE_ICONS.get(name, "") so an unmatched name never crashes (it just
# renders without an icon). Beyond that safety net, reuse the existing solid
# filled two-tone icon set 1:1 by concept so every lead style still gets an
# icon rather than falling back to blank.
STYLE_ICONS.update({
    # Leadership (Leading with Intention)
    "Vision-Led & Big-Picture":  STYLE_ICONS["Candid & Open"],          # sees the whole picture
    "Structured & Step-by-Step": STYLE_ICONS["Measured & Analytical"],  # stepped/sequenced bars
    "People-First & Relational": STYLE_ICONS["Close & Collaborative"],  # relationship pair
    "Adaptive & Field-Reading":  STYLE_ICONS["Adaptive & Iterative"],   # adjust-as-you-go cycle
    # Change Management (Navigating Change)
    "Systems-Minded & Deliberate":   STYLE_ICONS["Considered & Thorough"],   # deliberate, plan-first
    "Collaborative & Co-Created":    STYLE_ICONS["Consultative & Inclusive"],# group/network
    "Steady & Reassuring":           STYLE_ICONS["Warm & Attuned"],          # warmth/reassurance
    "Fast-Moving & Momentum-Driven": STYLE_ICONS["Decisive & Committed"],    # momentum/bolt
    # Conflict Management (Managing Conflict)
    "Early & Direct":               STYLE_ICONS["Direct & To-the-Point"],     # direct arrow
    "Calm & De-escalating":         STYLE_ICONS["Flexible & Versatile"],      # steady, multi-directional
    "Interest-Seeking & Diagnostic": STYLE_ICONS["Curious & Questioning"],    # question-led
    "Steady & Task-Focused":        STYLE_ICONS["Self-Directed & Focused"],   # focused target
})

_CSS = """
<style>
.ws-zone{--ws-navy:#0A1733;--ws-panel:#0E2148;--ws-line:rgba(120,170,235,.18);
  --ws-sky:#3E9BFF;--ws-sky2:#1E88E5;--ws-ink:#EAF1FF;--ws-soft:#A9BCDC;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  background:linear-gradient(165deg,#0E2148 0%,#0A1733 100%);
  border:1px solid var(--ws-line);border-radius:20px;padding:34px 34px 22px;margin:34px 0 38px;color:var(--ws-ink);}
.ws-zone .ws-head{border-bottom:1px solid var(--ws-line);padding-bottom:18px;margin-bottom:8px;}
.ws-zone .ws-eyebrow{text-transform:uppercase;letter-spacing:.18em;font-size:11px;font-weight:700;color:var(--ws-sky);}
.ws-zone h2.ws-title{font-size:27px;line-height:1.12;font-weight:800;color:#fff;margin:7px 0 7px;}
.ws-zone .ws-subhead{font-size:13.5px;color:var(--ws-soft);max-width:62ch;margin:0;}
.ws-zone .ws-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;}
.ws-zone .ws-block{background:rgba(255,255,255,.035);border:1px solid var(--ws-line);
  border-radius:14px;padding:18px 18px 16px;display:flex;flex-direction:column;}
.ws-zone .ws-dimrow{display:flex;align-items:center;gap:10px;margin-bottom:10px;}
.ws-zone .ws-dimicon{width:30px;height:30px;flex:0 0 30px;border-radius:9px;display:flex;align-items:center;
  justify-content:center;background:rgba(62,155,255,.14);color:var(--ws-sky);}
.ws-zone .ws-dimicon svg{width:18px;height:18px;}
.ws-zone .ws-dim{text-transform:uppercase;letter-spacing:.16em;font-size:10.5px;font-weight:700;color:var(--ws-sky);}
.ws-zone .ws-namerow{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin:0 0 8px;}
.ws-zone .ws-name{font-size:18px;font-weight:800;color:#fff;margin:0;line-height:1.15;}
.ws-zone .ws-styleicon{width:46px;height:46px;flex:0 0 46px;border-radius:13px;display:flex;
  align-items:center;justify-content:center;background:rgba(62,155,255,.14);
  border:1px solid rgba(62,155,255,.30);color:var(--ws-sky);}
.ws-zone .ws-styleicon svg{width:27px;height:27px;}
.ws-zone .ws-summary{font-size:12.5px;line-height:1.5;color:var(--ws-ink);margin:0 0 14px;}
/* style-mix visual */
.ws-zone .ws-mix{margin:2px 0 18px;}
.ws-zone .ws-donutwrap{display:flex;align-items:center;gap:13px;margin-bottom:6px;}
.ws-zone .ws-donut{width:74px;height:74px;flex:0 0 74px;}
.ws-zone .ws-legend{display:flex;flex-direction:column;gap:9px;}
.ws-zone .ws-leg{display:flex;align-items:flex-start;gap:7px;font-size:11.5px;font-weight:700;color:var(--ws-ink);line-height:1.2;}
.ws-zone .ws-leg small{display:block;font-weight:600;font-size:9.5px;letter-spacing:.1em;
  text-transform:uppercase;color:var(--ws-soft);margin-bottom:1px;}
.ws-zone .ws-dot{width:11px;height:11px;flex:0 0 11px;border-radius:3px;margin-top:2px;}
.ws-zone .ws-mixnote{font-size:10.5px;color:var(--ws-soft);font-style:italic;margin:7px 0 0;line-height:1.4;}
/* how-to-work chips */
.ws-zone .ws-best{font-size:12px;font-weight:700;color:#fff;margin:4px 0 8px;letter-spacing:.01em;}
.ws-zone .ws-chips{display:flex;flex-direction:column;gap:8px;margin:0 0 16px;}
.ws-zone .ws-chip{display:flex;align-items:center;gap:9px;background:rgba(255,255,255,.05);
  border:1px solid var(--ws-line);border-radius:9px;padding:8px 11px;}
.ws-zone .ws-chip .ic{width:20px;height:20px;flex:0 0 20px;border-radius:50%;display:flex;align-items:center;
  justify-content:center;background:var(--ws-sky2);color:#fff;}
.ws-zone .ws-chip .ic svg{width:14px;height:14px;}
.ws-zone .ws-chip span{font-size:12px;line-height:1.35;color:var(--ws-ink);}
/* complement card */
.ws-zone .ws-comp{display:flex;align-items:flex-start;gap:9px;margin-top:auto;background:rgba(62,155,255,.12);
  border:1px solid rgba(62,155,255,.34);border-left:3px solid var(--ws-sky);border-radius:11px;
  padding:13px 16px;margin:2px 0 4px;}
.ws-zone .ws-comp .ic{width:26px;height:26px;flex:0 0 26px;color:var(--ws-sky);margin-top:1px;}
.ws-zone .ws-comp p{font-size:11.5px;line-height:1.45;color:var(--ws-ink);margin:0;}
.ws-zone .ws-comp b{color:#fff;}
.ws-zone .ws-comp .lab{display:block;text-transform:uppercase;letter-spacing:.12em;font-size:9.5px;
  font-weight:700;color:var(--ws-sky);margin-bottom:3px;}
@media (max-width:760px){.ws-zone .ws-grid{grid-template-columns:1fr;}}
@media (max-width:640px){.ws-zone{padding:22px 18px 12px;border-radius:14px;}
  .ws-zone h2.ws-title{font-size:22px;}.ws-zone .ws-name{font-size:19px;}
  .ws-zone .ws-mixlabel{flex-basis:96px;font-size:11.5px;}.ws-zone .ws-mixnote{margin-left:0;}}
</style>
""".strip()


def _esc(s):
    return _html.escape(s, quote=False)


DONUT_COLORS = ["#1E88E5", "#5BA8F2", "#A7CFF7"]


def _donut(segs):
    cx = cy = 21.0; rad = 15.2; sw = 7.0
    parts = []; cum = 0.0
    for i, (_kind, _name, frac) in enumerate(segs):
        color = DONUT_COLORS[min(i, 2)]
        if frac >= 0.999:
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="{rad}" fill="none" '
                         f'stroke="{color}" stroke-width="{sw}"/>')
        else:
            a0 = -90 + cum * 360; a1 = -90 + (cum + frac) * 360
            x0 = cx + rad * math.cos(math.radians(a0)); y0 = cy + rad * math.sin(math.radians(a0))
            x1 = cx + rad * math.cos(math.radians(a1)); y1 = cy + rad * math.sin(math.radians(a1))
            large = 1 if (a1 - a0) > 180 else 0
            parts.append(f'<path d="M{x0:.2f},{y0:.2f} A{rad},{rad} 0 {large} 1 {x1:.2f},{y1:.2f}" '
                         f'fill="none" stroke="{color}" stroke-width="{sw}"/>')
        cum += frac
    return f'<svg viewBox="0 0 42 42" class="ws-donut" aria-hidden="true">{"".join(parts)}</svg>'


def _mix(block):
    """Compact donut showing the MAIN working style only (single, settled preference)."""
    r = block["resolved"]
    segs = [("Mainly", r["primary"], 1.0)]
    donut = _donut(segs)
    legend = (
        f'<div class="ws-leg"><span class="ws-dot" style="background:{DONUT_COLORS[0]}"></span>'
        f'<span><small>Mainly</small>{_esc(r["primary"])}</span></div>')
    return ('<div class="ws-mix"><div class="ws-donutwrap">' + donut +
            '<div class="ws-legend">' + legend + '</div></div></div>')


def render_working_style_section(blocks):
    """Return the full Working Style HTML fragment (scoped <style> + <section>)."""
    p = [_CSS, '<section class="ws-zone rise" aria-label="Your Working Style">']
    p.append('<div class="ws-head">')
    p.append('<div class="ws-eyebrow">Your Working Style</div>')
    p.append('<h2 class="ws-title">How you naturally work</h2>')
    p.append(f'<p class="ws-subhead">{_esc(WS_SUBHEAD)}</p>')
    p.append('</div>')
    p.append('<div class="ws-grid">')
    for b in blocks:
        dim = b["dimension"]
        p.append('<div class="ws-block">')
        p.append('<div class="ws-dimrow">'
                 f'<span class="ws-dimicon">{_DIM_ICON.get(dim, "")}</span>'
                 f'<span class="ws-dim">{_esc(dim)}</span></div>')
        _sicon = STYLE_ICONS.get(b["style_name"], "")
        p.append('<div class="ws-namerow">'
                 f'<div class="ws-name">{_esc(b["style_name"])}</div>'
                 + (f'<span class="ws-styleicon">{_sicon}</span>' if _sicon else "")
                 + '</div>')
        p.append(f'<p class="ws-summary">{_esc(b["summary"])}</p>')
        p.append(_mix(b))
        p.append('<p class="ws-best">People work best with you when they:</p>')
        p.append('<div class="ws-chips">')
        for bullet in b["bullets"]:
            p.append(f'<div class="ws-chip"><span class="ic">{_IC_CHECK}</span><span>{_esc(bullet)}</span></div>')
        p.append('</div>')
        comp = b.get("complement")
        if comp:
            p.append('<div class="ws-comp">'
                     f'<span class="ic">{_IC_PAIR}</span>'
                     '<p><span class="lab">You work best alongside</span>'
                     f'someone who is <b>{_esc(comp["style"])}</b>. {_esc(comp["reason"])}</p></div>')
        p.append('</div>')
    p.append('</div>')
    p.append('</section>')
    return "\n".join(p)


def render_from_answers(answers):
    return render_working_style_section(build_blocks(answers))
