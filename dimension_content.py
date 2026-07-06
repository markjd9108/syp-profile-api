# -*- coding: utf-8 -*-
"""
dimension_content — band-appropriate feedback for the three assessed
dimensions (Communication, Decision-Making, Collaboration) on the
"How you scored" cards, plus a "what strong looks like / why / next step"
block per dimension.

Voice (The Performance Lens): confident not boastful, specific not vague,
diagnostic not motivational. No "transform/unlock/empower/journey/synergy/
superpower/elevate" language.

Grounding: the "what strong looks like" statements describe the highest-
scoring (10-point) behaviours in the TEW scoring model; the "why" reuses the
team-value rationale from lead_engine._VALUE. Bands: Foundation <40,
Emerging 40-59, Developing 60-79, Strong 80+.
"""

# --- per-dimension, per-band bullets (exactly what shows on the score card) ---
# keys: dimension in {"comm","dec","collab"}; band in
# {"foundation","emerging","developing","strong"}

BULLETS = {
    "comm": {
        "foundation": [
            "Getting your message across took effort today — points sometimes "
            "landed differently than you intended.",
            "The place to start: say less, make each thing clear, and check it "
            "landed before moving on.",
        ],
        "emerging": [
            "You communicate clearly when things are straightforward, but under "
            "pressure your message doesn't always land the first time.",
            "Your next gain is checking for understanding — a short pause to "
            "confirm people got it before you move on.",
        ],
        "developing": [
            "You communicate clearly and keep information moving, so people "
            "generally stay pointed in the same direction.",
            "The step toward Strong is adapting when your message isn't landing "
            "— change how you say it rather than repeating it.",
        ],
        "strong": [
            "You communicate to be understood, not just heard — clear, precise, "
            "and adjusted to your audience.",
            "You keep information moving and people aligned, which makes you a "
            "reference point others rely on.",
        ],
    },
    "dec": {
        "foundation": [
            "When decisions were called for, you tended to wait for more "
            "certainty than the moment allowed.",
            "The place to start: make a call you can adjust later rather than "
            "holding out for the perfect one.",
        ],
        "emerging": [
            "You commit once things are clear, but when the picture is uncertain "
            "you lean toward waiting or handing the call to someone else.",
            "Your next gain is deciding with the information you have and owning "
            "the outcome, then adjusting as you learn.",
        ],
        "developing": [
            "You make calls when they're needed and you stand behind them, which "
            "keeps the team moving.",
            "The step toward Strong is making more of the calls yourself under "
            "uncertainty, rather than waiting for the moment to be obvious.",
        ],
        "strong": [
            "You commit to a direction while others are still weighing options, "
            "and you own the outcome.",
            "You create momentum by deciding — the scarcest and most valuable "
            "thing a team has under pressure.",
        ],
    },
    "collab": {
        "foundation": [
            "When the group came under pressure, you focused on your own part "
            "more than on holding the team together.",
            "The place to start: stay connected to the group — notice when others "
            "need support, and offer it.",
        ],
        "emerging": [
            "You support the people around you when things are calm, but under "
            "pressure you tend to narrow to your own task.",
            "Your next gain is staying oriented to the whole team when it matters "
            "most, not just your piece of it.",
        ],
        "developing": [
            "You support the people around you reliably, and the team can count "
            "on you to stay steady.",
            "The step toward Strong is actively holding the group together when "
            "pressure rises, not only when things are calm.",
        ],
        "strong": [
            "When pressure rises you keep the team together — steady yourself, "
            "and keeping others oriented.",
            "That composure is contagious: the group borrows its steadiness from "
            "you, which is what stops teams fragmenting.",
        ],
    },
}

# --- "what strong looks like" + "why" (same for all readers) + band-aware tip ---
STRONG = {
    "comm": {
        "what": "Strong communication means being understood, not just heard: "
                "describing the goal clearly, checking it landed, and adapting "
                "your words when it doesn't — instead of repeating them louder.",
        "why": "Most team breakdowns are communication failures, so the person "
               "who makes things clear becomes the reference point everyone else "
               "aligns to.",
        "tips": {
            "foundation": "Before moving on from a point, ask one question that "
                          "checks the other person actually got it.",
            "emerging": "Before moving on from a point, ask one question that "
                        "checks the other person actually got it.",
            "developing": "When something isn't landing, change your words or "
                          "your medium instead of restating it.",
            "strong": "Put your clarity to work earlier — name issues before "
                      "you're asked, so it reads as leadership.",
        },
    },
    "dec": {
        "what": "Strong decision-making means making the call the moment asks "
                "for — committing to a direction with the information you have, "
                "owning it, and adjusting as you learn, rather than waiting for "
                "certainty.",
        "why": "Teams stall without someone willing to decide, and decisions "
               "are what create momentum — a team's scarcest resource under "
               "pressure.",
        "tips": {
            "foundation": "Next time a call is unclear, pick a direction you can "
                          "adjust and commit to it out loud.",
            "emerging": "Next time a call is unclear, pick a direction you can "
                        "adjust and commit to it out loud.",
            "developing": "When you notice a decision going unmade, make it "
                          "yourself rather than waiting for consensus.",
            "strong": "Make your decisiveness visible — state the call and the "
                      "reasoning so others can follow it.",
        },
    },
    "collab": {
        "what": "Strong collaboration means holding the team together when "
                "pressure rises: staying steady, keeping others oriented, and "
                "protecting the group's shared structure instead of retreating "
                "into your own task.",
        "why": "Under pressure most teams fragment, and composure is contagious "
               "— a team borrows its steadiness from whoever has it.",
        "tips": {
            "foundation": "When pressure hits, take one action that helps someone "
                          "else before returning to your own task.",
            "emerging": "When pressure hits, take one action that helps someone "
                        "else before returning to your own task.",
            "developing": "Be the person who names what's happening to the group "
                          "when things wobble, not just after.",
            "strong": "Use your steadiness deliberately — set the tone early so "
                      "the team stabilises around it.",
        },
    },
}

DIM_ORDER = ("comm", "dec", "collab")  # matches score order Comm/Dec/Collab


def bullets(dim, band):
    """dim in DIM_ORDER, band in foundation/emerging/developing/strong."""
    return BULLETS[dim][band]


def strong_block(dim, band):
    """Return (what, why, tip) for the 'what strong looks like' block."""
    s = STRONG[dim]
    return s["what"], s["why"], s["tips"][band]
