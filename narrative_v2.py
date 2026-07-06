# -*- coding: utf-8 -*-
"""
narrative_v2 — score-driven content for the hosted profile's performance
sections: "What stood out" (Strength + Growth Edge), "Your next three moves"
(+ Support), and a trimmed "Keep the momentum going".

Everything here that describes the participant is DYNAMIC — the Strength is
their actual strongest dimension, the Growth Edge their actual weakest, and the
moves/support are tailored to those two. Generic explanations ("what strong
looks like") live in dimension_content.py instead.

Voice: specific, plain, concise — say more with less, no repetition, no jargon,
and the word "session" is deliberately avoided (we say "meeting").

Renders full <section> HTML matched to templates_v2 classes; inject_v2 swaps the
baked sections for these.
"""
import html as _html

DIM_NAME = {"comm": "Communication", "dec": "Decision-Making", "collab": "Collaboration"}
# present-tense practice phrase used in moves/support
DIM_ACTION = {
    "comm": "say the goal first, then check the other person understood it",
    "dec": "make one clear call and say what you based it on",
    "collab": "spot when someone is stuck and help before pushing on your own task",
}
DIM_SKILL = {"comm": "communicating clearly", "dec": "making decisions under pressure",
             "collab": "working with a team"}
DIM_TOPIC = {"comm": "clear communication", "dec": "decision-making",
             "collab": "collaboration and teamwork"}

BAND_HEX = {"foundation": "#F87171", "emerging": "#FBBF24",
            "developing": "#60A5FA", "strong": "#34D399"}
BAND_LABEL = {"foundation": "Foundation", "emerging": "Emerging",
              "developing": "Developing", "strong": "Strong"}
NEXT_BAND = {"foundation": "emerging", "emerging": "developing",
             "developing": "strong", "strong": "strong"}
DIM_ORDER = ("comm", "dec", "collab")


def band_of(score):
    s = int(round(float(score)))
    if s >= 80: return "strong"
    if s >= 60: return "developing"
    if s >= 40: return "emerging"
    return "foundation"


def select(scores):
    """scores = [comm, dec, collab]. Return (strong_dim, weak_dim) keys, always distinct."""
    order = sorted(range(3), key=lambda i: (-scores[i], i))
    return DIM_ORDER[order[0]], DIM_ORDER[order[-1]]


# ── Strength copy: what their strongest area is + why it matters ────────────────
# tier "established" = developing/strong (a real strength); "emerging" = foundation/emerging
STRENGTH = {
    "comm": {
        "established": ("You keep people clear and aligned.",
            "You state things clearly and make sure they land, so the people around "
            "you know what is going on and what to do. That clarity is what keeps a "
            "team moving in the same direction."),
        "emerging": ("Communication is your strongest starting point.",
            "Of your three areas, communicating clearly is where you are furthest "
            "along. It is the best place to build from, because clear communication "
            "prevents the misunderstandings that slow a team down."),
    },
    "dec": {
        "established": ("You make the call and keep things moving.",
            "You are willing to decide with the information you have and stand behind "
            "it, instead of waiting for certainty. That keeps the team moving when "
            "others would stall."),
        "emerging": ("Decision-making is where you are furthest along.",
            "Of your three areas, making clear calls is your strongest starting "
            "point. It is worth building on, because a team keeps moving when someone "
            "is willing to decide."),
    },
    "collab": {
        "established": ("You keep the team steady and connected.",
            "You stay calm when things get difficult and keep the people around you "
            "working together. That steadiness is what stops a team from coming apart "
            "under pressure."),
        "emerging": ("Supporting the team is your strongest starting point.",
            "Of your three areas, working with others is where you are furthest "
            "along. It is a solid base to build from, because a steady, connected "
            "team holds together when things get hard."),
    },
}

# ── Growth Edge copy: the ONE thing to work on next (band-aware, single focus) ──
GROWTH_HEAD = {
    "comm": "Make your message land every time.",
    "dec": "Back yourself to make the call.",
    "collab": "Stay with the team when it is hard.",
}
GROWTH_BODY = {
    "comm": {
        "low": "This is your biggest opportunity. Focus on one habit: after you "
               "explain something, ask a quick question to check the other person "
               "understood before you move on.",
        "developing": "You are close to strong here. The next step is to adapt when "
               "your message is not landing — change how you say it instead of "
               "repeating it.",
        "strong": "Even your growth area is a strength. Keep it sharp by raising "
               "issues early and clearly, before you are asked.",
    },
    "dec": {
        "low": "This is your biggest opportunity. Focus on one habit: when a "
               "decision is unclear, pick a direction you can adjust and commit to "
               "it out loud.",
        "developing": "You are close to strong here. The next step is to make more "
               "of the calls yourself under uncertainty, rather than waiting for the "
               "moment to be obvious.",
        "strong": "Even your growth area is a strength. Keep it sharp by explaining "
               "the reasoning behind your calls so others can follow them.",
    },
    "collab": {
        "low": "This is your biggest opportunity. Focus on one habit: when pressure "
               "rises, take one action to help someone else before returning to your "
               "own work.",
        "developing": "You are close to strong here. The next step is to actively "
               "hold the group together when pressure rises, not only when things "
               "are calm.",
        "strong": "Even your growth area is a strength. Keep it sharp by setting a "
               "steady tone early so the team settles around it.",
    },
}


def _esc(s):
    return _html.escape(s, quote=False)


def _band_span(key):
    return '<span style="color:%s">%s</span>' % (BAND_HEX[key], BAND_LABEL[key])


def _card_open(band):
    return (
        '<article class="card-soft p-8 relative band-' + band + ' overflow-hidden">'
        '<div class="absolute -top-24 -right-24 w-[320px] h-[320px] rounded-full '
        'pointer-events-none" style="background: radial-gradient(circle, '
        'color-mix(in oklab, var(--c) 40%, transparent), transparent 65%);"></div>'
        '<div class="absolute top-0 left-0 right-0 h-[2px] band-rule"></div>'
        '<div class="relative">')


def render_stood_out(scores):
    s_dim, g_dim = select(scores)
    s_score = scores[DIM_ORDER.index(s_dim)]
    g_score = scores[DIM_ORDER.index(g_dim)]
    s_band = band_of(s_score)
    g_band = band_of(g_score)
    tier = "established" if s_band in ("developing", "strong") else "emerging"
    s_head, s_body = STRENGTH[s_dim][tier]
    g_key = {"foundation": "low", "emerging": "low"}.get(g_band, g_band)
    g_head = GROWTH_HEAD[g_dim]
    g_body = GROWTH_BODY[g_dim][g_key]
    g_target = NEXT_BAND[g_band]

    strength = (
        _card_open(s_band) +
        '<div class="flex items-center gap-2.5 mb-6"><span class="band-dot"></span>'
        '<span class="eyebrow" style="color: var(--c-soft)">Your Strength</span></div>'
        '<h3 class="display text-[26px] mb-5 leading-[1.08]">' + _esc(s_head) + '</h3>'
        '<p class="text-[15px] text-[var(--fg-2)] leading-[1.7]">' + _esc(s_body) + '</p>'
        '<div class="mt-7 pt-5 border-t hairline grid grid-cols-2 gap-6">'
        '<div><div class="eyebrow mb-1.5">Dimension</div>'
        '<div class="text-[13.5px] font-medium">' + DIM_NAME[s_dim] + '</div></div>'
        '<div><div class="eyebrow mb-1.5">Band</div>'
        '<div class="text-[13.5px] font-medium tabular" style="color: var(--c-soft)">'
        + _band_span(s_band) + '</div></div></div></div></article>')

    growth = (
        _card_open(g_band) +
        '<div class="flex items-center gap-2.5 mb-6"><span class="band-dot"></span>'
        '<span class="eyebrow" style="color: var(--c-soft)">Your Growth Edge</span></div>'
        '<h3 class="display text-[26px] mb-5 leading-[1.08]">' + _esc(g_head) + '</h3>'
        '<p class="text-[15px] text-[var(--fg-2)] leading-[1.7]">' + _esc(g_body) + '</p>'
        '<div class="mt-7 pt-5 border-t hairline grid grid-cols-2 md:grid-cols-3 gap-6">'
        '<div><div class="eyebrow mb-1.5">Focus area</div>'
        '<div class="text-[13.5px] font-medium">' + DIM_NAME[g_dim] + '</div></div>'
        '<div><div class="eyebrow mb-1.5">Current</div>'
        '<div class="text-[13.5px] font-medium tabular" style="color: var(--c-soft)">'
        + _band_span(g_band) + '</div></div>'
        '<div><div class="eyebrow mb-1.5">30-day target</div>'
        '<div class="text-[13.5px] font-medium tabular">' + _band_span(g_target) +
        '</div></div></div></div></article>')

    return (
        '<section id="sec-stood-out" class="mt-20 rise rise-3">'
        '<div class="flex items-end justify-between mb-6"><div>'
        '<div class="eyebrow mb-2">Section 02</div>'
        '<h2 class="display text-[28px] tracking-tight">What stood out</h2></div></div>'
        '<div class="grid grid-cols-1 md:grid-cols-2 gap-5">' + strength + growth +
        '</div></section>')


def _move(num, step, head, body, meta):
    return (
        '<article class="card p-7 flex flex-col">'
        '<div class="flex items-start justify-between mb-8"><span class="num-badge">'
        + num + '</span><span class="has-tip"><span class="check" data-step="' + step +
        '" role="button" aria-label="Track practice"></span>'
        '<span class="tip">Tap to track when you have practised this</span></span></div>'
        '<h3 class="display text-[20px] leading-[1.18] mb-3">' + _esc(head) + '</h3>'
        '<p class="text-[13.5px] text-[var(--fg-2)] leading-[1.65] mb-6">' + _esc(body) + '</p>'
        '<div class="mt-auto pt-5 border-t hairline flex items-center justify-end '
        'text-[11.5px] mono text-[var(--fg-3)]"><span class="tabular">' + _esc(meta) +
        '</span></div></article>')


def _support(label, meta, head, body):
    return (
        '<div class="card p-5"><div class="flex items-center justify-between gap-3 mb-3">'
        '<span class="eyebrow" style="font-size:10px;">' + _esc(label) + '</span>'
        '<span class="text-[11px] text-[var(--fg-3)] tabular whitespace-nowrap">' + _esc(meta) +
        '</span></div><div class="text-[14.5px] font-semibold leading-[1.25] mb-2">' + _esc(head) +
        '</div><p class="text-[12.5px] text-[var(--fg-3)] leading-[1.55]">' + _esc(body) +
        '</p></div>')


def render_moves(scores):
    s_dim, g_dim = select(scores)
    sN, gN = DIM_NAME[s_dim], DIM_NAME[g_dim]
    sAct, gAct = DIM_ACTION[s_dim], DIM_ACTION[g_dim]

    m1 = _move("01", "1", "Lead with your strength.",
        "In your next few meetings, lean on your %s: %s. It is your most reliable "
        "contribution — use it on purpose." % (sN.lower(), sAct), "Every meeting")
    m2 = _move("02", "2", "Practise one new habit.",
        "Pick one moment in your next meeting to %s. One clear moment is enough — it "
        "adds up faster than trying to fix everything at once." % gAct, "1× per meeting")
    m3 = _move("03", "3", "Ask for one piece of feedback.",
        "After a meeting, ask one person: “What is one thing I did that helped the "
        "team today?” What others notice first is often a better signal than what "
        "you feel most sure of.", "Weekly")

    sup1 = _support("30-day focus", "Start this week", "One clear moment per meeting.",
        "This month, aim for one moment in each meeting where you %s — even when it "
        "feels easier not to." % gAct)
    sup2 = _support("Mentor pairing", "2 chats", "Learn from someone strong at %s." % gN,
        "Pick someone on your team who is genuinely good at %s, watch how they do it, "
        "and ask them one specific question about their approach." % DIM_SKILL[g_dim])
    sup3 = _support("Self-directed learning", "20 min / week",
        "Spend 20 minutes a week on %s." % gN,
        "Find a book, podcast, or short online course on %s and give it 20 focused "
        "minutes a week. Small, regular input adds up." % DIM_TOPIC[g_dim])

    return (
        '<section id="sec-moves" class="mt-20 rise rise-4 section-next-steps">'
        '<div class="flex items-end justify-between mb-6"><div>'
        '<div class="eyebrow mb-2">Section 04</div>'
        '<h2 class="display text-[28px] tracking-tight">Your next three moves</h2>'
        '<p class="text-[12.5px] text-[var(--fg-3)] mt-3 max-w-[60ch] no-print">'
        'Three small practices tailored to your results. Pick the one that fits your '
        'next meeting and start there.</p></div>'
        '<div class="text-[12.5px] text-[var(--fg-3)]">One move. One meeting. '
        'Repeat for 30 days.</div></div>'
        '<div class="grid grid-cols-1 md:grid-cols-3 gap-5">' + m1 + m2 + m3 + '</div>'
        '<div class="mt-10 mb-4"><div class="eyebrow mb-1.5">Support your moves</div>'
        '<div class="text-[13px] text-[var(--fg-3)] max-w-[64ch]">A focus, a person, '
        'and a learning habit — all pointed at your growth area.</div></div>'
        '<div class="grid grid-cols-1 md:grid-cols-3 gap-5">' + sup1 + sup2 + sup3 +
        '</div></section>')


def render_momentum():
    """Trimmed 'what happens next' — no framework list, no duplicated 30-day plan."""
    steps = [
        ("This week", "Pick one move above and tell one person you are working on it. "
                       "Saying it out loud makes it stick."),
        ("Day 15", "Check in with yourself — have you used your move at least twice?"),
        ("Day 30", "Re-read this profile and notice what feels different."),
    ]
    rows = "".join(
        '<div class="flex gap-4 items-start">'
        '<span class="eyebrow tabular" style="min-width:64px;">' + _esc(k) + '</span>'
        '<span class="text-[13px] text-[var(--fg-2)] leading-[1.55]">' + _esc(v) + '</span>'
        '</div>' for k, v in steps)
    return (
        '<section class="mt-20 rise rise-5">'
        '<article class="card-soft p-10 relative overflow-hidden"><div class="relative">'
        '<div class="eyebrow mb-2">Section 05 · What happens next</div>'
        '<h2 class="display text-[26px] tracking-tight mb-4">Keep the momentum going.</h2>'
        '<p class="text-[14px] text-[var(--fg-2)] leading-[1.7] max-w-[68ch] mb-7">'
        'Your leader has already received your profile. The real progress happens in '
        'the meetings that follow this workshop — so pick one move from Section 04 and '
        'use it this week.</p>'
        '<div class="grid gap-3 max-w-[70ch]">' + rows + '</div>'
        '</div></article></section>')
