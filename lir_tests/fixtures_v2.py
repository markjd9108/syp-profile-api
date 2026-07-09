#!/usr/bin/env python3
"""
Spec v2 composed-copy fixtures for the four acceptance datasets.
Production copy comes from the composition API; these exist to verify wiring,
derivations, pagination and rendering, and they must pass the full v2
validator (dogfooding it).
"""

TEST_COHORTS = {
    "test1": {
        "team": "Pizzahut", "date": "6 July 2026", "leader": "Mark Dickens",
        "members": [
            {"name": "Mark Pizza", "archetype": "Relay", "comm": 58, "dm": 75, "collab": 71},
            {"name": "Mark Pizza 2", "archetype": "Anchor", "comm": 28, "dm": 53, "collab": 92},
            {"name": "Jane Pizza", "archetype": "Compass", "comm": 65, "dm": 75, "collab": 43}],
    },
    "test2": {
        "team": "Mekong Digital", "date": "6 July 2026", "leader": "Mark Dickens",
        "members": [
            {"name": "Linh Tran", "archetype": "Navigator", "comm": 72, "dm": 81, "collab": 68},
            {"name": "Duc Pham", "archetype": "Summit", "comm": 70, "dm": 76, "collab": 74},
            {"name": "An Le", "archetype": "Relay", "comm": 55, "dm": 62, "collab": 70},
            {"name": "Minh Vo", "archetype": "Anchor", "comm": 48, "dm": 58, "collab": 84},
            {"name": "Hoa Nguyen", "archetype": "Signal", "comm": 82, "dm": 54, "collab": 66}],
    },
    "test3": {
        "team": "Edge Cohort", "date": "6 July 2026", "leader": "Alex Chen",
        "members": [
            {"name": "A Nguyen", "archetype": "Summit", "comm": 82, "dm": 80, "collab": 78},
            {"name": "B Tran", "archetype": "Navigator", "comm": 70, "dm": 85, "collab": 66},
            {"name": "C Le", "archetype": "Signal", "comm": 84, "dm": 62, "collab": 70},
            {"name": "D Pham", "archetype": "Anchor", "comm": 58, "dm": 64, "collab": 86},
            {"name": "E Vo", "archetype": "Compass", "comm": 68, "dm": 72, "collab": 55},
            {"name": "F Hoang", "archetype": "Relay", "comm": 62, "dm": 64, "collab": 66},
            {"name": "G Dang", "archetype": "Relay", "comm": 66, "dm": 58, "collab": 72},
            {"name": "H Bui", "archetype": "Relay", "comm": 71, "dm": 69, "collab": 75}],
    },
    # Acceptance Test 4 (Change Order 1 §6.3, five archetypes per Mark 7 Jul):
    # 20 members, no Compass, 9 Check-In, 5 Stretch, 6 Steady.
    "test4": {
        "team": "Synthetic Twenty", "date": "6 July 2026", "leader": "Mark Dickens",
        "members": [
            {"name": "Thu Le", "archetype": "Anchor", "comm": 55, "dm": 70, "collab": 75},
            {"name": "Binh Ngo", "archetype": "Relay", "comm": 58, "dm": 66, "collab": 72},
            {"name": "Chi Vu", "archetype": "Signal", "comm": 72, "dm": 56, "collab": 68},
            {"name": "Dat Ho", "archetype": "Relay", "comm": 62, "dm": 59, "collab": 70},
            {"name": "Em Ly", "archetype": "Navigator", "comm": 70, "dm": 64, "collab": 54},
            {"name": "Phuc Vo", "archetype": "Summit", "comm": 57, "dm": 74, "collab": 66},
            {"name": "Giang Do", "archetype": "Anchor", "comm": 66, "dm": 58, "collab": 71},
            {"name": "Hanh Bui", "archetype": "Relay", "comm": 59, "dm": 63, "collab": 69},
            {"name": "Khoa Ngu", "archetype": "Signal", "comm": 68, "dm": 61, "collab": 52},
            {"name": "Lan Truong", "archetype": "Summit", "comm": 80, "dm": 76, "collab": 74},
            {"name": "Minh Chau", "archetype": "Navigator", "comm": 72, "dm": 82, "collab": 70},
            {"name": "Nga Han", "archetype": "Signal", "comm": 76, "dm": 70, "collab": 78},
            {"name": "Oanh Kim", "archetype": "Anchor", "comm": 66, "dm": 72, "collab": 84},
            {"name": "Phong Sa", "archetype": "Relay", "comm": 70, "dm": 71, "collab": 72},
            {"name": "Quan Vinh", "archetype": "Relay", "comm": 62, "dm": 64, "collab": 66},
            {"name": "Rin Ta", "archetype": "Anchor", "comm": 64, "dm": 66, "collab": 62},
            {"name": "Son Hai", "archetype": "Signal", "comm": 66, "dm": 62, "collab": 64},
            {"name": "Tam Uong", "archetype": "Summit", "comm": 63, "dm": 65, "collab": 61},
            {"name": "Uyen Xa", "archetype": "Navigator", "comm": 61, "dm": 67, "collab": 65},
            {"name": "Vy Yen", "archetype": "Relay", "comm": 60, "dm": 70, "collab": 68}],
    },
    "test5": {
        "team": "BritCham", "date": "9 July 2026", "leader": "Matt Ryland",
        "members": [
            {"name": "Thao Uyen Nguyen", "archetype": "Anchor", "comm": 56, "dm": 48, "collab": 86},
            {"name": "Anh Hong Nguyen", "archetype": "Relay", "comm": 43, "dm": 77, "collab": 75},
            {"name": "Khanh Dinh", "archetype": "Relay", "comm": 72, "dm": 83, "collab": 60},
            {"name": "Nhu Truong", "archetype": "Relay", "comm": 68, "dm": 63, "collab": 77},
            {"name": "Linh Cao", "archetype": "Anchor", "comm": 73, "dm": 65, "collab": 93},
            {"name": "Van Ha", "archetype": "Summit", "comm": 81, "dm": 79, "collab": 86},
            {"name": "Trinh Trần", "archetype": "Relay", "comm": 78, "dm": 70, "collab": 75},
            {"name": "Khue", "archetype": "Relay", "comm": 37, "dm": 72, "collab": 69},
            {"name": "Uyen Nguyen", "archetype": "Relay", "comm": 82, "dm": 55, "collab": 92},
            {"name": "Giang Ngo", "archetype": "Signal", "comm": 63, "dm": 42, "collab": 38}],
    },
}

_CI_THEMES = [
    "{n} steadies the group and raises little of what they see. Worth exploring in a 1:1, what would make raising problems early feel routine.",
    "{n} delivers reliably and goes quiet when direction is unclear. A 1:1 could open with what a clearer brief would change for them.",
    "{n} reads the room well and holds back their own view. One for your next 1:1: what would make speaking first feel safe.",
    "{n} commits fast and checks alignment late. Worth exploring in a 1:1, the moment where a shared check would help them most.",
    "{n} carries load without signalling it. A 1:1 could open with how the team would know when they need support.",
]
_ST_THEMES = [
    "{n} sets a standard the room can see and follow. One stretch: chair the next contested decision without voting in it, so the room shows its own judgement.",
    "{n} decides when others defer, and the decisions hold. A stretch to offer: narrate the reasoning behind one live decision so the method spreads.",
    "{n} connects people and reads the room before acting. A stretch to offer: convene the team's next shared conversation and turn that awareness into a channel.",
    "{n} absorbs pressure and keeps the work moving. One stretch: mentor one developing member through a full piece of work, start to close.",
    "{n} executes cleanly against any clear brief. One stretch: own the framing of the next brief, so the standard they deliver to becomes the standard they set.",
]

def _themes(names, pool, short=False):
    out = {}
    for i, n in enumerate(names):
        t = pool[i % len(pool)].format(n=n)
        if short:
            # 25-word form: compress the insight sentence
            t = pool[i % len(pool)].format(n=n)
            words = t.split()
            if len(words) > 25:
                # deterministic short variants
                shorts = [
                    "{n} steadies others and raises little. Worth exploring in a 1:1, what would make raising problems early feel routine.",
                    "{n} delivers well and goes quiet without direction. A 1:1 could open with what a clearer brief would change.",
                    "{n} reads the room and holds back. One for your next 1:1: what would make speaking first feel safe.",
                    "{n} commits fast and checks alignment late. Worth exploring in a 1:1, where a shared check would help most.",
                    "{n} carries load without signalling it. A 1:1 could open with how the team would know they need support.",
                ]
                t = shorts[i % len(shorts)].format(n=n)
        out[n] = t
    return out

def _base(leader_first, prio_dim, prio_band, session):
    return {
        "leaderVerdict": (f"{leader_first}, this team's commitment is not in question. Work gets "
                          "picked up, held, and finished. What holds the team back is how "
                          f"{prio_dim.lower().replace('-', ' ')} works day to day: too much depends "
                          "on individuals, and the group works from different pictures of the same "
                          "job. The work ahead is building one shared operating picture."),
        "workingWell": ("Work gets owned and finished. Members hold together under load and "
                        "commitments made in the room are kept without chasing."),
        "needsSupport": ("Information moves person to person on request. Members act on different "
                         "pictures of the same work, and gaps surface late, when they are "
                         "expensive to fix."),
        "teamRisk": ("Decisions made without shared context. The work still ships, but each "
                     "member is building from a different picture, and that breaks first "
                     "under pressure."),
        "teamOpportunity": ("This is a structural fix, one habit away. Give the team a shared "
                            "operating picture and its existing judgement starts compounding."),
        "firstMove": ("This team needs its working picture made visible. A standard practice: "
                      "set aside twenty minutes this week for each member to name their top "
                      "priority and the one thing blocking it, before any other business."),
        "patternLabel": "The pattern that shapes this team",
        "patternTitle": "Strong hands, thin shared voice",
        "definingPatternP1": ("The individual capability is in place: members deliver, steady one "
                              "another, and hold standards. What the team lacks is a shared "
                              "picture. Information lives in individuals and moves only when "
                              "someone asks, so alignment depends on who happens to be in the room."),
        "definingPatternP2": ("The risk is quiet drift. Nothing looks broken day to day, which is "
                              "why this pattern hides. Direction: give the team one routine that "
                              "makes the shared picture explicit, and hold it until it is habit."),
        "risks": [
            {"title": "Working from different pictures",
             "statement": ("Members act on private versions of the same plan. The work gets done "
                           "twice or arrives misaligned, and the cost lands late in delivery, "
                           "where it is hardest to absorb."),
             "moves": [
                 ("This team needs a single visible source of priorities. A standard practice: "
                  "one shared list of current commitments, reviewed together at the start of "
                  "your next team discussion."),
                 ("This team needs decisions to travel. An established practice: every decision "
                  "of consequence is written where the whole team reads it, with an owner named."),
             ],
             "observable": ("members reference the shared list unprompted and misalignments are "
                            "caught in conversation before they reach delivery.")},
            {"title": "Strength hiding the seams",
             "statement": ("Because the team performs, nothing invites examination. The habits "
                           "that carry today's load are the same ones that will crack when the "
                           "load doubles."),
             "moves": [
                 ("This team needs a regular look at how it works. A widely used practice: a "
                  "short end-of-project debrief naming one thing to keep and one to change."),
                 ("This team needs its quieter reads surfaced. An established practice: collect "
                  "written positions before contested calls, then discuss them together."),
             ],
             "observable": ("the team runs its own debriefs without prompting and quieter "
                            "members' positions shape final calls.")},
        ],
        "prescription": (f"The priority is {prio_dim.lower().replace('-', ' ')}, the area with the "
                         f"most room to grow, at {prio_band} today. The matching next step is "
                         f"{session}, a 90-minute development session built to turn individual "
                         "capability into a shared team habit."),
        "closingVerdict": ("Strong for this team looks like the same hands working from one "
                           "picture. Hold a single visible list of commitments, write decisions "
                           "down where everyone reads them, and keep the debrief routine. The "
                           "capability is present; the structure makes it compound."),
    }

def _pattern_card(name, arch):
    beats = {
        "Relay": (f"{name} is the execution baseline of this team: give them a clear brief and "
                  "the work arrives done, on time, without noise. What they need is exactly that "
                  "clarity, because ambiguity stalls them quietly and without warning. One option: "
                  "make them the first reader of every new brief, and fix what they cannot restate."),
        "Navigator": (f"{name} makes the call when others defer and sets direction when the path "
                      "is unclear. What they need is visible context, because their calls are only "
                      "as good as the picture they see. One option: route the shared priority list "
                      "through them before contested decisions."),
        "Signal": (f"{name} reads the room before acting and connects people who would not "
                   "connect themselves. What they need is licence to say what they see, because "
                   "the team loses its best early warning when they stay quiet. One option: give "
                   "them a standing slot to report the mood of the work."),
        "Summit": (f"{name} raises the standard and does not accept the first adequate answer. "
                   "What they need is a channel that turns critique into direction, so the "
                   "pressure lands on the work and never on the person. One option: have them "
                   "define what good looks like at the start of each piece of work."),
        "Anchor": (f"{name} is the steadying force: when plans break, they hold function and "
                   "absorb pressure quietly. What they need is a defined way to signal load, "
                   "because they carry more than they show. One option: a regular check-in where "
                   "they report capacity before anyone asks."),
        "Compass": (f"{name} builds structure out of ambiguity and maps complexity into process "
                    "others can follow. What they need is early involvement, because structure "
                    "added late costs twice. One option: bring them in at framing, before the "
                    "work is shaped."),
    }
    return {"label": "Pattern to watch", "name": f"{name} · {arch}", "body": beats[arch]}

MISSING = {
    "Compass": ("No member fills the Compass seat. Nobody naturally builds structure out of "
                "ambiguity here, so process arrives late or never, and complex work leans on "
                "individual memory. One structural option: rotate a mapping duty, one member "
                "turns each new piece of work into steps the team can see."),
    "Navigator": ("No member fills the Navigator seat. When direction is unclear the team "
                  "waits, and calls default to the leader or to silence. One structural option: "
                  "name a decision owner for each piece of work before it starts."),
    "Summit": ("No member fills the Summit seat. The first adequate answer tends to stand, and "
               "standards drift without anyone noticing. One structural option: give one member "
               "per piece of work the explicit job of testing the plan before the team commits."),
    "Signal": ("No member fills the Signal seat. The team reads the work but never the room, "
               "so friction between people surfaces late. One structural option: close each "
               "team discussion with every member naming how the work felt, in one line."),
}

def composed_for(name, derived):
    ds = TEST_COHORTS[name]
    leader_first = ds["leader"].split()[0]
    from lir_compose import SESSION_MAP
    base = _base(leader_first, derived["priorityDim"], derived["priorityBand"],
                 SESSION_MAP[derived["priorityDim"]])
    by_name = {m["name"]: m["archetype"] for m in ds["members"]}
    # pattern cards: choose the first patternCardCount members deterministically
    picks = [m["name"] for m in ds["members"]][:derived["patternCardCount"]]
    base["patternCards"] = [_pattern_card(n, by_name[n]) for n in picks]
    base["missingCards"] = [{"name": a, "body": MISSING[a]}
                            for a in derived["absentArchetypes"][:derived["missingCardCount"]]]
    base["focusThemes"] = _themes(derived["themedCheckIn"], _CI_THEMES,
                                  short=derived["themeWordsCi"] == 25)
    base["stretchThemes"] = _themes(derived["themedStretch"], _ST_THEMES,
                                    short=derived["themeWordsSt"] == 25)
    return base
