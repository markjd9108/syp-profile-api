# -*- coding: utf-8 -*-
"""
Working Style layer — HTML renderer (web profile).

Renders the SAME shared content (working_style.build_blocks) the ReportLab PDF uses,
so the two formats can never drift. The section is self-contained (its own scoped
.ws-* CSS, explicit brand colours) so it renders identically whether previewed
standalone or injected into the compiled archetype template.
"""
import html as _html
from working_style import build_blocks

WS_FRAMING = ("This page describes how you prefer to work. The sections that follow describe how "
              "you showed up under pressure today. Two views of the same person — both useful, "
              "and together they show the full picture.")
WS_SUBHEAD = ("How you naturally work — your preferences, strengths, and the conditions that "
              "bring out your best.")

_CSS = """
<style>
.ws-zone{--ws-navy:#0D2A66;--ws-sky:#1E88E5;--ws-ink:#1A1A2E;--ws-grey:#64748B;
  --ws-tint:#F4F8FE;--ws-closer:#EAF3FD;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  background:var(--ws-tint);border:1px solid #DCE9FB;border-radius:18px;
  padding:34px 34px 14px;margin:0 0 40px;}
.ws-zone .ws-head{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;
  border-bottom:1px solid #DCE9FB;padding-bottom:18px;margin-bottom:20px;}
.ws-zone .ws-eyebrow{text-transform:uppercase;letter-spacing:.16em;font-size:11px;font-weight:700;
  color:var(--ws-sky);}
.ws-zone h2.ws-title{font-size:26px;line-height:1.15;font-weight:800;color:var(--ws-navy);margin:6px 0 6px;}
.ws-zone .ws-subhead{font-size:13.5px;color:var(--ws-grey);max-width:60ch;margin:0;}
.ws-zone .ws-framing{font-style:italic;font-size:13px;color:var(--ws-ink);background:#fff;
  border:1px solid var(--ws-sky);border-radius:10px;padding:12px 16px;margin:0 0 24px;line-height:1.5;}
.ws-zone .ws-block{padding:0 0 22px;margin-bottom:22px;border-bottom:1px solid #E3ECF8;}
.ws-zone .ws-block:last-child{border-bottom:none;margin-bottom:6px;}
.ws-zone .ws-dim{text-transform:uppercase;letter-spacing:.14em;font-size:10.5px;font-weight:700;color:var(--ws-sky);}
.ws-zone .ws-name{font-size:20px;font-weight:800;color:var(--ws-ink);margin:4px 0 8px;}
.ws-zone .ws-summary{font-size:14px;line-height:1.55;color:var(--ws-ink);margin:0 0 12px;}
.ws-zone .ws-best{font-size:13.5px;font-weight:700;color:var(--ws-ink);margin:0 0 8px;}
.ws-zone ul.ws-bullets{list-style:none;margin:0 0 14px;padding:0;}
.ws-zone ul.ws-bullets li{position:relative;padding-left:20px;font-size:13.5px;line-height:1.5;
  color:var(--ws-ink);margin-bottom:5px;}
.ws-zone ul.ws-bullets li::before{content:"";position:absolute;left:2px;top:7px;width:7px;height:7px;
  border-radius:50%;background:var(--ws-sky);}
.ws-zone .ws-closer{background:var(--ws-closer);border-left:3px solid var(--ws-sky);border-radius:8px;
  padding:11px 15px;}
.ws-zone .ws-closer p{font-style:italic;font-size:13px;line-height:1.5;color:#1D4ED8;margin:0 0 4px;}
.ws-zone .ws-closer p:last-child{margin-bottom:0;}
@media (max-width:640px){.ws-zone{padding:22px 20px 8px;border-radius:14px;}
  .ws-zone h2.ws-title{font-size:22px;}.ws-zone .ws-name{font-size:18px;}
  .ws-zone .ws-head{flex-direction:column;}}
</style>
""".strip()


def _esc(s):
    return _html.escape(s, quote=False)


def render_working_style_section(blocks):
    """Return the full Working Style HTML fragment (scoped <style> + <section>)."""
    parts = [_CSS, '<section class="ws-zone rise" aria-label="Your Working Style">']
    parts.append('<div class="ws-head"><div>')
    parts.append('<div class="ws-eyebrow">Your Working Style</div>')
    parts.append('<h2 class="ws-title">How you naturally work</h2>')
    parts.append(f'<p class="ws-subhead">{_esc(WS_SUBHEAD)}</p>')
    parts.append('</div></div>')
    parts.append(f'<p class="ws-framing">{_esc(WS_FRAMING)}</p>')
    for b in blocks:
        parts.append('<div class="ws-block">')
        parts.append(f'<div class="ws-dim">{_esc(b["dimension"])}</div>')
        parts.append(f'<div class="ws-name">{_esc(b["style_name"])}</div>')
        parts.append(f'<p class="ws-summary">{_esc(b["summary"])}</p>')
        parts.append('<p class="ws-best">People work best with you when they:</p>')
        parts.append('<ul class="ws-bullets">')
        for bullet in b["bullets"]:
            parts.append(f'<li>{_esc(bullet)}</li>')
        parts.append('</ul>')
        parts.append('<div class="ws-closer">')
        for line in b["closer_lines"]:
            parts.append(f'<p>{_esc(line)}</p>')
        parts.append('</div>')
        parts.append('</div>')
    parts.append('</section>')
    return "\n".join(parts)


def render_from_answers(answers):
    """answers: dict ws_q1..ws_q9 -> full HTML fragment."""
    return render_working_style_section(build_blocks(answers))
