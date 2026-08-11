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

# ===========================================================================
# LEADERSHIP WORKSHOP (TLW) variant
# ---------------------------------------------------------------------------
# The three score slots are reused by position for the leadership dimensions:
#   comm  -> Leadership          (Leading with Intention / The Flywheel)
#   dec   -> Change Management   (Navigating Change / The Crossing)
#   collab-> Conflict Management (Managing Conflict / The Forge)
# Copy is grounded in the TLW framework "one move" behaviours and the SJT
# scoring model. Same voice, same band structure, no em dashes.
# ===========================================================================

BULLETS_LEAD = {
    "comm": {  # Leadership
        "foundation": [
            "Setting a clear direction was hard to hold onto today. People were "
            "not always sure what you were steering toward.",
            "The place to start: say why before what. Give the goal first, then "
            "let people work out the steps.",
        ],
        "emerging": [
            "You set a direction when the goal is clear, but under pressure the "
            "why gets lost and people fall back on guessing.",
            "Your next gain is leading from intent: name the outcome you want, "
            "then check the team is pointed at it before you move.",
        ],
        "developing": [
            "You lead with a clear intent and keep the team aimed at it, so "
            "people generally know what they are working toward.",
            "The step toward Strong is reading the field as you go, adjusting "
            "your direction to what the team is actually doing rather than "
            "holding the plan.",
        ],
        "strong": [
            "You lead from a clear why and keep the team moving toward it, so "
            "people can act without waiting for you.",
            "You read the field and adjust, which keeps the direction real "
            "instead of a plan people quietly abandon.",
        ],
    },
    "dec": {  # Change Management
        "foundation": [
            "When the situation shifted, you tended to change one part before "
            "you understood how the whole thing worked.",
            "The place to start: see the whole first. Learn how the pieces fit "
            "before you move any of them.",
        ],
        "emerging": [
            "You handle change well when the path is obvious, but when it is "
            "not you either rush the fix or wait for it to settle on its own.",
            "Your next gain is naming the change honestly: is this a small "
            "tweak or a new way of working, then building the path with the "
            "people affected.",
        ],
        "developing": [
            "You work through change in a steady way and bring people along, so "
            "the team adapts without coming apart.",
            "The step toward Strong is expecting the pushback and moving people "
            "through it, rather than assuming a good plan sells itself.",
        ],
        "strong": [
            "You understand the whole before you change a part, and you build "
            "the path with the people who have to walk it.",
            "You move people through the hard middle of change and re-anchor "
            "once it lands, so the new way actually sticks.",
        ],
    },
    "collab": {  # Conflict Management
        "foundation": [
            "When tension showed up, it was easier to smooth it over or let it "
            "pass than to name what was going on.",
            "The place to start: make it normal to raise things. Say the "
            "problem while it is still small, and about the work.",
        ],
        "emerging": [
            "You address problems once they are clear, but you tend to wait "
            "until they are big rather than naming them early.",
            "Your next gain is speaking up while an issue is still one piece: "
            "name it early, and keep it about the work, not the person.",
        ],
        "developing": [
            "You raise problems and keep them about the work, so disagreements "
            "get handled instead of buried.",
            "The step toward Strong is getting past positions to what each "
            "person is actually trying to do, then resolving it so trust goes up.",
        ],
        "strong": [
            "You make it safe to challenge the work, and you name problems "
            "early while they are still cheap to fix.",
            "You get to the interests under a disagreement and resolve it in a "
            "way that leaves the team stronger, not bruised.",
        ],
    },
}

STRONG_LEAD = {
    "comm": {  # Leadership
        "what": "Leading from a clear why, reading what the team is actually "
                "doing, and adjusting your direction instead of holding a plan "
                "that has stopped fitting.",
        "why": "When people understand the intent, they can move without "
               "waiting for you.",
        "tips": {
            "foundation": "Before your next task, say the goal and the why out "
                          "loud, then let the team work out the how.",
            "emerging": "Before your next task, say the goal and the why out "
                        "loud, then let the team work out the how.",
            "developing": "When the plan meets reality, adjust your direction "
                          "to what the team is doing rather than repeating the "
                          "original instruction.",
            "strong": "Set the intent early and out loud, so the team can act "
                      "on it when you are not in the room.",
        },
    },
    "dec": {  # Change Management
        "what": "Understanding the whole before you change a part, building the "
                "path with the people affected, and moving them through the "
                "pushback instead of around it.",
        "why": "Change sticks when people help build it and are carried "
               "through the hard middle.",
        "tips": {
            "foundation": "Next time something shifts, map how the whole works "
                          "before you change any single part.",
            "emerging": "Next time something shifts, map how the whole works "
                        "before you change any single part.",
            "developing": "Plan for the resistance in advance, and name who "
                          "will struggle with the change before you roll it out.",
            "strong": "Once a change lands, re-anchor it: make the new way the "
                      "default so the team does not drift back.",
        },
    },
    "collab": {  # Conflict Management
        "what": "Making it safe to challenge the work, naming problems early "
                "while they are small, and resolving them in a way that leaves "
                "trust higher than before.",
        "why": "A team that can disagree well catches problems while they are "
               "still cheap to fix.",
        "tips": {
            "foundation": "Next time you notice a problem in someone's work, "
                          "say it early and about the work, not the person.",
            "emerging": "Next time you notice a problem in someone's work, say "
                        "it early and about the work, not the person.",
            "developing": "When a disagreement stalls, ask what each person is "
                          "actually trying to achieve, and solve for that.",
            "strong": "Set the ground so people know challenging the work is "
                      "welcome, before any conflict arises.",
        },
    },
}

_FAMILIES = {"tew": (BULLETS, STRONG), "lead": (BULLETS_LEAD, STRONG_LEAD)}


def bullets(dim, band, family="tew"):
    """dim in DIM_ORDER, band in foundation/emerging/developing/strong."""
    return _FAMILIES.get(family, _FAMILIES["tew"])[0][dim][band]


def strong_block(dim, band, family="tew"):
    """Return (what, why, tip) for the 'what strong looks like' block."""
    s = _FAMILIES.get(family, _FAMILIES["tew"])[1][dim]
    return s["what"], s["why"], s["tips"][band]
