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

WS_SUBHEAD = ("How you naturally work — your preferences, strengths, and the conditions that "
              "bring out your best.")

# ── Inline SVG icons (stroke style, currentColor) ────────────────────────────────
_IC_COMM = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" '
            'stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-8.5 '
            '8.5 8.5 8.5 0 0 1-3.8-.9L3 20l1.4-4.2A8.5 8.5 0 1 1 21 11.5z"/></svg>')
_IC_DEC  = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" '
            'stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v6"/><path d="M12 9c0 3-4 '
            '3-4 6a4 4 0 0 0 8 0c0-3-4-3-4-6z" opacity="0"/><path d="M6 21a3 3 0 1 0 0-6 3 3 0 0 0 0 '
            '6z"/><path d="M18 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/><path d="M12 9c0 3-6 3-6 6"/><path '
            'd="M12 9c0 3 6 3 6 6"/></svg>')
_IC_COLL = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" '
            'stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 '
            '0 0-4 4v2"/><circle cx="9" cy="7" r="3"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path '
            'd="M16 3.13A4 4 0 0 1 16 11"/></svg>')
_IC_CHECK= ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" '
            'stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>')
_IC_PAIR = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" '
            'stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="3"/><circle '
            'cx="17" cy="9" r="2.4"/><path d="M3.5 20a5.5 5.5 0 0 1 11 0"/><path d="M15 20a4.5 4.5 0 '
            '0 1 6-4"/></svg>')
_DIM_ICON = {"Communication": _IC_COMM, "Decision-Making": _IC_DEC, "Collaboration": _IC_COLL}

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
.ws-zone .ws-name{font-size:18px;font-weight:800;color:#fff;margin:0 0 8px;line-height:1.15;}
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
    """Compact donut showing the primary / shade / thread proportions + labels + supporting text."""
    r = block["resolved"]
    if r["pattern"] == "Pure":
        segs = [("Mainly", r["primary"], 1.0)]
    elif r["pattern"] == "Blend":
        segs = [("Mainly", r["primary"], 0.66), ("A shade of", r["secondary"], 0.34)]
    else:
        segs = [("Mainly", r["primary"], 0.50), ("A shade of", r["secondary"], 0.30),
                ("A thread of", r["third"], 0.20)]
    donut = _donut(segs)
    legend = "".join(
        f'<div class="ws-leg"><span class="ws-dot" style="background:{DONUT_COLORS[min(i,2)]}"></span>'
        f'<span><small>{_esc(kind)}</small>{_esc(name)}</span></div>'
        for i, (kind, name, _f) in enumerate(segs))
    notes = "".join(f'<div class="ws-mixnote">{_esc(line)}</div>' for line in block["closer_lines"])
    return ('<div class="ws-mix"><div class="ws-donutwrap">' + donut +
            '<div class="ws-legend">' + legend + '</div></div>' + notes + '</div>')


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
        p.append(f'<div class="ws-name">{_esc(b["style_name"])}</div>')
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
