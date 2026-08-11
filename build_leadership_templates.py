# -*- coding: utf-8 -*-
"""
build_leadership_templates.py

Generates the six Leadership Workshop (TLW) archetype profile templates from the
existing TEW base template (templates_v2/Navigator.html). Each output is a clone
of the base with, baked in:

  * the three score-band dimension labels renamed to the Leadership names
    (Leadership, Change Management, Conflict Management),
  * the workshop label set to "The Leadership Workshop",
  * the Working Style block removed (TLW does not capture working-style answers),
  * the "Best practices" section (Section 03) rewritten for the leadership skills,
  * the archetype name + tagline set per archetype.

All score-driven body copy (score-card bullets, "What stood out", "Your next
three moves", the TL;DR snapshot) is still injected at render time by
inject_v2 / dimension_content / narrative_v2, which are made leadership-aware
separately. This builder only bakes the static, per-family and per-archetype
content into the template files.

Run:  python3 build_leadership_templates.py
Writes: templates_v2/Keystone.html, Lighthouse.html, Pathfinder.html,
        Diplomat.html, Vanguard.html, Cornerstone.html
"""
import os, re, json

_DIR = os.path.join(os.path.dirname(__file__), "templates_v2")
BASE = os.path.join(_DIR, "Navigator.html")
_TPL_RE = re.compile(r'(<script type="__bundler/template">)(.*?)(</script>)', re.S)

# ── per-archetype identity ──────────────────────────────────────────────────
# tagline pattern mirrors the base ("strength. now the growth nudge.") — no em dashes.
ARCHETYPES = {
    "Keystone":    "You hold the team together. Now stretch what it can reach.",
    "Lighthouse":  "You set the direction. Now bring everyone into it.",
    "Pathfinder":  "You find the way through change. Now take people with you.",
    "Diplomat":    "You make it safe to disagree. Now turn that into better work.",
    "Vanguard":    "You drive the team forward. Now make room for the hard conversations.",
    "Cornerstone": "You are the steady base. Now build on it.",
}

# ── family-wide label swaps (all six templates) ─────────────────────────────
# TL;DR donut labels
TLDR_LABELS = [
    ('<div class="tldr-g-label">Communication</div>',   '<div class="tldr-g-label">Leadership</div>'),
    ('<div class="tldr-g-label">Decision-Making</div>', '<div class="tldr-g-label">Change Management</div>'),
    ('<div class="tldr-g-label">Collaboration</div>',   '<div class="tldr-g-label">Conflict Management</div>'),
]
# score-card titles (Section 01)
SCORED_TITLES = [
    ('<span class="text-[13px] font-medium tracking-tight">Communication</span>',
     '<span class="text-[13px] font-medium tracking-tight">Leadership</span>'),
    ('<span class="text-[13px] font-medium tracking-tight">Decision-Making</span>',
     '<span class="text-[13px] font-medium tracking-tight">Change Management</span>'),
    ('<span class="text-[13px] font-medium tracking-tight">Collaboration</span>',
     '<span class="text-[13px] font-medium tracking-tight">Conflict Management</span>'),
]
# Best-practices card titles (Section 03)
BEST_TITLES = [
    ('<span class="text-[14px] font-semibold tracking-tight">Communication</span>',
     '<span class="text-[14px] font-semibold tracking-tight">Leadership</span>'),
    ('<span class="text-[14px] font-semibold tracking-tight">Decision-Making</span>',
     '<span class="text-[14px] font-semibold tracking-tight">Change Management</span>'),
    ('<span class="text-[14px] font-semibold tracking-tight">Collaboration</span>',
     '<span class="text-[14px] font-semibold tracking-tight">Conflict Management</span>'),
]
# Section 03 subhead
BEST_SUBHEAD = (
    'Simple habits that work in any meeting. Three for each skill.',
    'Simple habits that hold up under pressure. Three for each skill.',
)
# Section 03 bullet text swaps (old exact -> new). Straight quotes; original used curly.
BEST_BULLETS = [
    # Leadership (was Communication)
    ('Say the goal first, then the detail. When people know where you are heading, they follow the detail more easily and ask better questions.',
     'Say the why before the what. When people know where you are heading and why, they follow the detail more easily and make better calls on their own.'),
    ('Check that the message landed. Ask the other person to say back what they heard. This catches a misunderstanding while it is still cheap to fix.',
     'Read the field before you set the plan. Notice what the team is already doing, then aim your direction at reality instead of the whiteboard.'),
    ('Invite questions out loud. A short “What is not clear yet?” gives quieter team members a way in and surfaces gaps before they grow into problems.',
     'Confirm the team is with you. Before you move on, check each person knows their part, so alignment is real and not assumed.'),
    # Change Management (was Decision-Making)
    ('Name the objective before the options. When the team agrees what a good outcome looks like, choosing between options gets faster and calmer.',
     'Understand the whole before you change a part. Map how the work flows now, so a change fixes the real problem instead of moving it.'),
    ('State your limits early. Time, budget, and people are real limits. Saying them out loud stops the team from planning work it cannot do.',
     'Name the change honestly. Say whether this is a small tweak or a new way of working, so people know how much to expect.'),
    ('Make the call, then say what you assumed. A clear decision with its assumptions written down is easy to revisit if something changes.',
     'Build the path with the people in it. Expect the pushback, involve those affected early, and move them through rather than around.'),
    # Conflict Management (was Collaboration)
    ('When the work stalls, fix the setup before you push harder. More effort on a broken setup wastes energy. A small change to roles or order often unblocks everyone.',
     'Say it while it is still one piece. Raise a problem early, about the work, before it grows into something nobody wants to touch.'),
    ('Make roles clear. When each person knows what they own, work stops falling through the gaps and nobody doubles up.',
     'Set the ground first. Make it normal to question the work, so people speak up before a small issue becomes an expensive one.'),
    ('Agree the next single action. When a group loses momentum, naming one concrete next step gets the work moving again.',
     'Get to the interests under the position. Ask what each person is actually trying to do, then solve for that, and trust goes up.'),
]

WORKSHOP_LABEL = ('Team Effectiveness Workshop', 'The Leadership Workshop')
BASE_ARCH_NAME = 'Navigator'
BASE_TAGLINE = 'You can read the room. Now learn to steer.'


def _require(t, old, label):
    n = t.count(old)
    if n != 1:
        raise SystemExit(f"[build] expected exactly 1 of {label}, found {n}: {old[:60]!r}")
    return t.replace(old, "<<<MATCHED>>>", 1)  # only for counting; not used to mutate


def _swap(t, old, new, label):
    n = t.count(old)
    if n != 1:
        raise SystemExit(f"[build] {label}: expected 1 occurrence, found {n}: {old[:70]!r}")
    return t.replace(old, new, 1)


def _strip_working_style(t):
    """Remove the TL;DR 'How you naturally work' block and the full Working Style
    <section id="sec-style"> (plus its preceding <style> block)."""
    # 1) TL;DR ws block: <div class="tldr-ws"> ... </div></div> before <div class="tldr-two">
    start = t.find('<div class="tldr-ws">')
    if start == -1:
        raise SystemExit("[build] tldr-ws block not found")
    anchor = t.find('<div class="tldr-two">', start)
    if anchor == -1:
        raise SystemExit("[build] tldr-two anchor not found")
    end = t.rfind('</div></div>', start, anchor)
    if end == -1:
        raise SystemExit("[build] tldr-ws close not found")
    end += len('</div></div>')
    t = t[:start] + t[end:]

    # 2) Working Style section: the <style> immediately before <section id="sec-style">
    sec = t.find('<section id="sec-style"')
    if sec == -1:
        raise SystemExit("[build] sec-style not found")
    style_start = t.rfind('<style>', 0, sec)
    sec_end = t.find('</section>', sec)
    if style_start == -1 or sec_end == -1:
        raise SystemExit("[build] sec-style boundaries not found")
    sec_end += len('</section>')
    t = t[:style_start] + t[sec_end:]
    return t


def build_family(t):
    for old, new in TLDR_LABELS:
        t = _swap(t, old, new, "tldr-label")
    for old, new in SCORED_TITLES:
        t = _swap(t, old, new, "scored-title")
    for old, new in BEST_TITLES:
        t = _swap(t, old, new, "best-title")
    t = _swap(t, *BEST_SUBHEAD, "best-subhead")
    for old, new in BEST_BULLETS:
        t = _swap(t, old, new, "best-bullet")
    t = _swap(t, *WORKSHOP_LABEL, "workshop-label")
    # tidy the invisible HTML comments that label each score card by old dim name
    t = _swap(t, '<!-- ====== Communication ',   '<!-- ====== Leadership ',          "comment-lead")
    t = _swap(t, '<!-- ====== Decision-Making ', '<!-- ====== Change Management ',   "comment-change")
    t = _swap(t, '<!-- ====== Collaboration ',   '<!-- ====== Conflict Management ', "comment-conflict")
    t = _strip_working_style(t)
    return t


def build_archetype(t, name, tagline):
    t = _swap(t, '<span class="accent-text">%s</span>' % BASE_ARCH_NAME,
              '<span class="accent-text">%s</span>' % name, "arch-name")
    t = _swap(t, BASE_TAGLINE, tagline, "tagline")
    return t


def main():
    raw = open(BASE, encoding="utf-8").read()
    m = _TPL_RE.search(raw)
    base_inner = json.loads(m.group(2))

    fam = build_family(base_inner)

    # sanity: leadership labels present, TEW labels gone from the visible spots
    for lbl in ("Leadership", "Change Management", "Conflict Management"):
        assert ('>%s</span>' % lbl in fam) or ('>%s</div>' % lbl in fam), "missing %s" % lbl

    for name, tagline in ARCHETYPES.items():
        inner = build_archetype(fam, name, tagline)
        enc = json.dumps(inner, ensure_ascii=False).replace("</script>", "<\\/script>")
        out_raw = _TPL_RE.sub(lambda _m: _m.group(1) + enc + _m.group(3), raw, count=1)
        outp = os.path.join(_DIR, name + ".html")
        with open(outp, "w", encoding="utf-8") as f:
            f.write(out_raw)
        print("wrote", outp, "(%d bytes)" % len(out_raw))


if __name__ == "__main__":
    main()
