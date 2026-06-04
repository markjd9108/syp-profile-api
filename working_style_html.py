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
  border:1px solid var(--ws-line);border-radius:20px;padding:34px 34px 22px;margin:0 0 38px;color:var(--ws-ink);}
.ws-zone .ws-head{border-bottom:1px solid var(--ws-line);padding-bottom:18px;margin-bottom:8px;}
.ws-zone .ws-eyebrow{text-transform:uppercase;letter-spacing:.18em;font-size:11px;font-weight:700;color:var(--ws-sky);}
.ws-zone h2.ws-title{font-size:27px;line-height:1.12;font-weight:800;color:#fff;margin:7px 0 7px;}
.ws-zone .ws-subhead{font-size:13.5px;color:var(--ws-soft);max-width:62ch;margin:0;}
.ws-zone .ws-block{padding:22px 0 4px;border-top:1px solid var(--ws-line);}
.ws-zone .ws-block:first-of-type{border-top:none;}
.ws-zone .ws-dimrow{display:flex;align-items:center;gap:10px;margin-bottom:10px;}
.ws-zone .ws-dimicon{width:30px;height:30px;flex:0 0 30px;border-radius:9px;display:flex;align-items:center;
  justify-content:center;background:rgba(62,155,255,.14);color:var(--ws-sky);}
.ws-zone .ws-dimicon svg{width:18px;height:18px;}
.ws-zone .ws-dim{text-transform:uppercase;letter-spacing:.16em;font-size:10.5px;font-weight:700;color:var(--ws-sky);}
.ws-zone .ws-name{font-size:21px;font-weight:800;color:#fff;margin:0 0 8px;}
.ws-zone .ws-summary{font-size:14px;line-height:1.55;color:var(--ws-ink);margin:0 0 16px;}
/* style-mix visual */
.ws-zone .ws-mix{margin:0 0 18px;}
.ws-zone .ws-mixrow{display:flex;align-items:center;gap:12px;margin-bottom:8px;}
.ws-zone .ws-mixlabel{flex:0 0 132px;font-size:12.5px;font-weight:700;color:var(--ws-ink);text-align:right;}
.ws-zone .ws-mixlabel small{display:block;font-weight:600;font-size:10px;letter-spacing:.08em;
  text-transform:uppercase;color:var(--ws-soft);}
.ws-zone .ws-bar{height:12px;border-radius:7px;background:linear-gradient(90deg,var(--ws-sky2),var(--ws-sky));}
.ws-zone .ws-bar.primary{width:100%;}
.ws-zone .ws-bar.shade{width:58%;opacity:.62;}
.ws-zone .ws-bar.thread{width:34%;opacity:.40;}
.ws-zone .ws-mixnote{font-size:12px;color:var(--ws-soft);font-style:italic;margin:6px 0 0 144px;line-height:1.45;}
/* how-to-work chips */
.ws-zone .ws-best{font-size:13px;font-weight:700;color:#fff;margin:2px 0 10px;letter-spacing:.01em;}
.ws-zone .ws-chips{display:flex;flex-direction:column;gap:8px;margin:0 0 16px;}
.ws-zone .ws-chip{display:flex;align-items:center;gap:12px;background:rgba(255,255,255,.045);
  border:1px solid var(--ws-line);border-radius:11px;padding:11px 14px;}
.ws-zone .ws-chip .ic{width:24px;height:24px;flex:0 0 24px;border-radius:50%;display:flex;align-items:center;
  justify-content:center;background:var(--ws-sky2);color:#fff;}
.ws-zone .ws-chip .ic svg{width:14px;height:14px;}
.ws-zone .ws-chip span{font-size:13.5px;line-height:1.4;color:var(--ws-ink);}
/* complement card */
.ws-zone .ws-comp{display:flex;align-items:flex-start;gap:12px;background:rgba(62,155,255,.12);
  border:1px solid rgba(62,155,255,.34);border-left:3px solid var(--ws-sky);border-radius:11px;
  padding:13px 16px;margin:2px 0 4px;}
.ws-zone .ws-comp .ic{width:26px;height:26px;flex:0 0 26px;color:var(--ws-sky);margin-top:1px;}
.ws-zone .ws-comp p{font-size:13px;line-height:1.5;color:var(--ws-ink);margin:0;}
.ws-zone .ws-comp b{color:#fff;}
.ws-zone .ws-comp .lab{display:block;text-transform:uppercase;letter-spacing:.12em;font-size:9.5px;
  font-weight:700;color:var(--ws-sky);margin-bottom:3px;}
@media (max-width:640px){.ws-zone{padding:22px 18px 12px;border-radius:14px;}
  .ws-zone h2.ws-title{font-size:22px;}.ws-zone .ws-name{font-size:19px;}
  .ws-zone .ws-mixlabel{flex-basis:96px;font-size:11.5px;}.ws-zone .ws-mixnote{margin-left:0;}}
</style>
""".strip()


def _esc(s):
    return _html.escape(s, quote=False)


def _mix(block):
    """Visual style-mix bars (primary / shade / thread) + supporting language."""
    r = block["resolved"]
    rows = [f'<div class="ws-mixrow"><div class="ws-mixlabel"><small>Mainly</small>{_esc(r["primary"])}</div>'
            f'<div class="ws-bar primary"></div></div>']
    if r.get("secondary"):
        rows.append(f'<div class="ws-mixrow"><div class="ws-mixlabel"><small>A shade of</small>{_esc(r["secondary"])}</div>'
                    f'<div class="ws-bar shade"></div></div>')
    if r.get("third"):
        rows.append(f'<div class="ws-mixrow"><div class="ws-mixlabel"><small>A thread of</small>{_esc(r["third"])}</div>'
                    f'<div class="ws-bar thread"></div></div>')
    notes = "".join(f'<div class="ws-mixnote">{_esc(line)}</div>' for line in block["closer_lines"])
    return '<div class="ws-mix">' + "".join(rows) + notes + '</div>'


def render_working_style_section(blocks):
    """Return the full Working Style HTML fragment (scoped <style> + <section>)."""
    p = [_CSS, '<section class="ws-zone rise" aria-label="Your Working Style">']
    p.append('<div class="ws-head">')
    p.append('<div class="ws-eyebrow">Your Working Style</div>')
    p.append('<h2 class="ws-title">How you naturally work</h2>')
    p.append(f'<p class="ws-subhead">{_esc(WS_SUBHEAD)}</p>')
    p.append('</div>')
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
                     f'someone who is <b>{_esc(comp["style"])}</b> — {_esc(comp["reason"])}.</p></div>')
        p.append('</div>')
    p.append('</section>')
    return "\n".join(p)


def render_from_answers(answers):
    return render_working_style_section(build_blocks(answers))
