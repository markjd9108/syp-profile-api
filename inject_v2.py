# -*- coding: utf-8 -*-
"""
inject_v2 — personalize the REDESIGNED self-contained profile templates
(donuts, band-only, Best Practices, inline Tailwind) for one participant and
return the full bundler-wrapped HTML, ready to host and open in a browser.

Used by the hosted-link delivery path (GET /p/<slug>). Unlike the legacy
generate_html_profile (old templates -> PDF), this works on templates_v2/.
"""
import os, re, json, datetime
import html as _html
import working_style as ws_mod
import dimension_content as dc
from working_style_html import render_working_style_section

_DIR = os.path.join(os.path.dirname(__file__), "templates_v2")

ARCH_FILES = {
    "anchor": "Anchor.html", "compass": "Compass.html", "navigator": "Navigator.html",
    "relay": "Relay.html", "signal": "Signal.html", "summit": "Summit.html",
}

# TLDR donut / scale colours (the bright band set used in the summary)
BAND_HEX = {"foundation": "#F87171", "emerging": "#FBBF24",
            "developing": "#60A5FA", "strong": "#34D399"}

_TPL_RE = re.compile(r'(<script type="__bundler/template">)(.*?)(</script>)', re.S)


def get_band(score):
    score = int(round(float(score)))
    if score >= 80: return "strong", "Strong"
    if score >= 60: return "developing", "Developing"
    if score >= 40: return "emerging", "Emerging"
    return "foundation", "Foundation"


def _load(archetype):
    fn = ARCH_FILES[archetype]
    raw = open(os.path.join(_DIR, fn), encoding="utf-8").read()
    inner = json.loads(_TPL_RE.search(raw).group(2))
    return raw, inner


def _save(raw, inner):
    enc = json.dumps(inner, ensure_ascii=False).replace("</script>", "<\\/script>")
    return _TPL_RE.sub(lambda m: m.group(1) + enc + m.group(3), raw, count=1)


def _initials(name):
    p = name.strip().split()
    return (p[0][0] + p[-1][0]).upper() if len(p) >= 2 else name[:2].upper()


def _esc(s):
    return _html.escape(s, quote=False)


def _bullets_ul(items):
    lis = "".join(
        '<li style="position:relative;padding-left:16px;margin-bottom:6px;">'
        '<span style="position:absolute;left:0;top:8px;width:5px;height:5px;'
        'border-radius:50%;background:var(--c-soft,#7BBDF4);"></span>'
        + _esc(x) + '</li>' for x in items)
    return ('<ul class="text-[13.5px] text-[var(--fg-2)] leading-[1.6] mt-6" '
            'style="list-style:none;padding:0;margin-top:18px;">' + lis + '</ul>')


def _strong_html(what, why, tip):
    return (
        '<div style="margin-top:18px;padding-top:16px;'
        'border-top:1px solid rgba(170,195,240,0.12);">'
        '<div style="font-size:9.5px;letter-spacing:1.6px;text-transform:uppercase;'
        'color:var(--c-soft,#7BBDF4);font-weight:700;margin-bottom:8px;">'
        'What strong looks like</div>'
        '<p style="font-size:12.5px;color:var(--fg-2);line-height:1.55;margin:0 0 10px;">'
        + _esc(what) + ' ' + _esc(why) + '</p>'
        '<div style="font-size:12.5px;color:var(--fg-1,#E7EEFB);line-height:1.5;'
        'background:rgba(123,189,244,0.08);border-left:2px solid var(--c-soft,#7BBDF4);'
        'padding:8px 12px;border-radius:6px;">'
        '<strong style="color:var(--c-soft,#7BBDF4);">Your next step:</strong> '
        + _esc(tip) + '</div></div>')


def _set_scored_cards(t, scores):
    """Update the 3 'How you scored' dimension cards (order Comm/Dec/Collab):
    band pill, ring %, band text, band-appropriate bullets, and the
    'what strong looks like / why / next step' block."""
    s = t.find('id="sec-scored"'); e = t.find('id="sec-stood-out"')
    if s == -1 or e == -1: return t
    head, seg, tail = t[:s], t[s:e], t[e:]
    arts = list(re.finditer(r'<article class="card relative overflow-hidden band-\w+">.*?</article>', seg, re.S))
    if len(arts) != 3: return t
    out = seg
    for m, sc, dim in zip(reversed(arts), reversed(scores), reversed(dc.DIM_ORDER)):
        key, label = get_band(sc)
        a = m.group(0)
        a = re.sub(r'(<article class="card relative overflow-hidden )band-\w+(">)', r'\1band-%s\2' % key, a, count=1)
        a = re.sub(r'<span class="band-pill">[^<]*</span>', '<span class="band-pill">%s</span>' % label, a, count=1)
        a = re.sub(r'stroke-dasharray="\d+ 100"', 'stroke-dasharray="%d 100"' % int(round(sc)), a, count=1)
        a = re.sub(r'<div class="num band-text">[^<]*</div>', '<div class="num band-text">%s</div>' % label, a, count=1)
        # band-appropriate bullets + "what strong looks like" block (replaces the baked <ul>)
        what, why, tip = dc.strong_block(dim, key)
        replacement = _bullets_ul(dc.bullets(dim, key)) + _strong_html(what, why, tip)
        a = re.sub(r'<ul class="text-\[13\.5px\].*?</ul>', lambda _m: replacement, a, count=1, flags=re.S)
        out = out[:m.start()] + a + out[m.end():]
    return head + out + tail


def _set_tldr_donuts(t, scores):
    """Update the 3 TLDR summary donuts (order Comm/Dec/Collab)."""
    blocks = list(re.finditer(r'<div class="tldr-g">.*?</div></div>', t, re.S))
    # the first 3 tldr-g blocks are the dimension donuts
    if len(blocks) < 3: return t
    out = t
    for m, sc in zip(reversed(blocks[:3]), reversed(scores)):
        key, label = get_band(sc); hexc = BAND_HEX[key]
        b = m.group(0)
        b = re.sub(r'stroke="#[0-9A-Fa-f]{6}"', 'stroke="%s"' % hexc, b)          # arc colour (track is rgba)
        b = re.sub(r'stroke-dasharray="\d+ 100"', 'stroke-dasharray="%d 100"' % int(round(sc)), b, count=1)
        b = re.sub(r'<div class="tldr-g-band" style="color:[^"]*">[^<]*</div>',
                   '<div class="tldr-g-band" style="color:%s">%s</div>' % (hexc, label), b, count=1)
        out = out[:m.start()] + b + out[m.end():]
    return out


def _set_working_style(t, answers):
    """Replace the baked Working Style style+section with freshly rendered output."""
    if not answers:
        return t
    try:
        blocks = ws_mod.build_blocks(answers)
        rendered = render_working_style_section(blocks)
        # keep the anchor id so TLDR "How you naturally work" links still resolve
        rendered = rendered.replace('<section class="ws-zone rise"',
                                    '<section id="sec-style" class="ws-zone rise"', 1)
    except Exception as ex:
        print("[inject_v2] working_style render failed:", ex)
        return t
    sec = t.find('<section id="sec-style"')
    if sec == -1: return t
    style_start = t.rfind('<style>', 0, sec)
    sec_end = t.find('</section>', sec)
    if style_start == -1 or sec_end == -1: return t
    sec_end += len('</section>')
    return t[:style_start] + rendered + t[sec_end:]


def inject(archetype, data):
    """data: dict with name, company, cohort, assessed_date, profile_id,
    comm_score, dec_score, collab_score, working_style(dict ws_q1..9)."""
    raw, t = _load(archetype)
    name = data.get("name") or "Participant"
    company = data.get("company") or "Company"
    cohort = data.get("cohort") or "TEW"
    now = datetime.datetime.now()
    assessed = data.get("assessed_date") or now.strftime("%B %d, %Y").replace(" 0", " ")
    pid = data.get("profile_id") or ""
    month_year = now.strftime("%B %Y")

    # identity tokens (sample values baked into the template)
    t = t.replace("Alex Nguyen", name)
    t = t.replace("AED Global", company)
    t = t.replace("May 18, 2026", assessed)
    t = t.replace("May 2026", month_year)
    t = re.sub(r"TPL-2604-[A-Z]-074", pid or "TPL-XXXX", t)
    t = t.replace("Q2 2026", cohort)
    t = t.replace("TEW Q2", cohort)
    t = re.sub(r'(<span class="avatar">)[A-Z]{1,3}(</span>)',
               lambda m: m.group(1) + _initials(name) + m.group(2), t)

    # scores -> bands (How you scored cards + TLDR donuts)
    scores = [int(round(float(data["comm_score"]))),
              int(round(float(data["dec_score"]))),
              int(round(float(data["collab_score"]))) ]
    t = _set_scored_cards(t, scores)
    t = _set_tldr_donuts(t, scores)

    # working style
    t = _set_working_style(t, data.get("working_style"))

    return _save(raw, t)
