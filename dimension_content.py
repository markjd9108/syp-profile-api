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
            "Getting your message across took effort today. Your points sometimes "
            "landed differently than you intended.",
            "The place to start: say less, make each thing clear, and check it "
            "landed before moving on.",
        ],
        "emerging": [
            "You communicate clearly when things are straightforward, but under "
            "pressure your message doesn't always land the first time.",
            "Your next gain is checking for understanding, with a short pause to "
            "confirm people got it before you move on.",
        ],
        "developing": [
            "You communicate clearly and keep information moving, so people "
            "generally stay pointed in the same direction.",
            "The step toward Strong is adapting when your message isn't landing, "
            "by changing how you say it rather than repeating it.",
        ],
        "strong": [
            "You communicate to be understood, not just heard. You are clear and "
            "precise, and you adjust to your audience.",
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
            "You create momentum by deciding, which keeps the team moving when it "
            "matters most.",
        ],
    },
    "collab": {
        "foundation": [
            "When the group came under pressure, you focused on your own part "
            "more than on holding the team together.",
            "The place to start: stay connected to the group. Notice when others "
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
            "When pressure rises you keep the team together. You stay steady "
            "and keep others oriented.",
            "That composure is contagious: the group borrows its steadiness from "
            "you, which is what stops teams fragmenting.",
        ],
    },
}

# --- "what strong looks like" + "why" (same for all readers) + band-aware tip ---
STRONG = {
    "comm": {
        "what": "Being clear, checking that people understood, and rephrasing "
                "when they didn't, instead of just repeating yourself.",
        "why": "It prevents the misunderstandings that cause most team problems.",
        "tips": {
            "foundation": "Before moving on, ask one question to confirm the "
                          "other person understood.",
            "emerging": "Before moving on, ask one question to confirm the "
                        "other person understood.",
            "developing": "If your message is not getting through, rephrase it "
                          "or change how you deliver it instead of repeating the "
                          "same words.",
            "strong": "Raise issues early and clearly, before you are asked. "
                      "This is what turns clear communication into visible "
                      "leadership.",
        },
    },
    "dec": {
        "what": "Making a clear call with the information you have and adjusting "
                "as you learn, instead of waiting until you're certain.",
        "why": "It keeps the team moving instead of waiting for direction.",
        "tips": {
            "foundation": "Next time a choice is unclear, pick a direction you "
                          "can adjust later and commit to it clearly.",
            "emerging": "Next time a choice is unclear, pick a direction you "
                        "can adjust later and commit to it clearly.",
            "developing": "When you notice a decision is not being made, make it "
                          "yourself instead of waiting for everyone to agree.",
            "strong": "Explain the reasoning behind your decisions, so others "
                      "understand them and can act on them.",
        },
    },
    "collab": {
        "what": "Staying calm under pressure and keeping the team working "
                "together, instead of narrowing to your own task.",
        "why": "A steady presence keeps the group coordinated when things get "
               "difficult.",
        "tips": {
            "foundation": "When pressure rises, take one action to help someone "
                          "else before returning to your own work.",
            "emerging": "When pressure rises, take one action to help someone "
                        "else before returning to your own work.",
            "developing": "When things start to go wrong, be the person who says "
                          "out loud what is happening, so the team can respond "
                          "together.",
            "strong": "Set a calm, steady tone early, so the team settles and "
                      "stays coordinated.",
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
