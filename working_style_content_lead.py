# -*- coding: utf-8 -*-
"""
The Performance Lens: Working Style layer, LEADERSHIP WORKSHOP (TLW) variant.
Drop-in parallel of working_style_content.py, re-authored around the three
Leadership Workshop dimensions rather than the Team Effectiveness Workshop ones.

Dimensions (mirror the TLW frameworks, see tlw_frameworks.py):
    Leadership          -> Leading with Intention  -> The Flywheel
    Change Management   -> Navigating Change        -> The Crossing
    Conflict Management -> Managing Conflict         -> The Forge

Same structure and symbol names as working_style_content.py, so this module
can be swapped in for that one wherever the resolver (working_style.py) needs
leadership-flavoured content instead of TEW content. Styles here are
preferences, not abilities: none is better than another. Voice: warm, plain,
second person. No em dashes anywhere in this file.
"""

# dimension -> answer letter -> style name (internal keying; never shown to participants)
KEYED = {
    'Leadership': {
        'A': 'Vision-Led & Big-Picture',
        'B': 'Structured & Step-by-Step',
        'C': 'People-First & Relational',
        'D': 'Adaptive & Field-Reading',
    },
    'Change Management': {
        'A': 'Systems-Minded & Deliberate',
        'B': 'Collaborative & Co-Created',
        'C': 'Steady & Reassuring',
        'D': 'Fast-Moving & Momentum-Driven',
    },
    'Conflict Management': {
        'A': 'Early & Direct',
        'B': 'Calm & De-escalating',
        'C': 'Interest-Seeking & Diagnostic',
        'D': 'Steady & Task-Focused',
    },
}

# Tiebreak weighting: when all three answers differ, these question positions decide
# order. Tuple = (primary_idx, secondary_idx, third_idx) into [ans_q_a, ans_q_b, ans_q_c].
# Mirrors the TEW logic: the later, more situational question is weighted first, the
# opening preference question is weighted last.
# Leadership Q2>Q3>Q1; Change Management Q5>Q6>Q4; Conflict Management Q9>Q8>Q7.
TIEBREAK = {
    'Leadership':          (1, 2, 0),
    'Change Management':   (1, 2, 0),
    'Conflict Management': (2, 1, 0),
}

# Which 3 questions feed each dimension (Typeform variables ws_q1..ws_q9)
DIMENSION_QUESTIONS = {
    'Leadership':          ('ws_q1', 'ws_q2', 'ws_q3'),
    'Change Management':   ('ws_q4', 'ws_q5', 'ws_q6'),
    'Conflict Management': ('ws_q7', 'ws_q8', 'ws_q9'),
}

# Output variable prefix per dimension
DIMENSION_PREFIX = {
    'Leadership': 'lead', 'Change Management': 'change', 'Conflict Management': 'conflict',
}

WORKING_STYLE_CONTENT = {
    # --- Leadership (Leading with Intention / The Flywheel) ---
    'Vision-Led & Big-Picture': {
        "dimension": 'Leadership',
        "summary": 'You lead by naming the outcome and the why before anything else. You want people pointed at the destination, then trusted to work out their own route there.',
        "bullets": [
            'Give you the big picture and the reasoning, not just the task',
            'Let you set the destination before asking for the plan',
            'Come back to the why when the work starts to drift',
        ],
        "third_preference_phrase": 'a vision-led way of setting direction',
    },
    'Structured & Step-by-Step': {
        "dimension": 'Leadership',
        "summary": 'You lead by turning direction into a clear sequence. You want the steps laid out so everyone knows what comes next and in what order.',
        "bullets": [
            'Give you the sequence, not just the goal',
            'Let you turn a direction into a concrete plan',
            'Expect clear checkpoints as the work moves',
        ],
        "third_preference_phrase": 'a structured, step-by-step way of setting direction',
    },
    'People-First & Relational': {
        "dimension": 'Leadership',
        "summary": "You lead through relationships. You check how people are taking on the work, not just what they're doing, and you bring the team along with you.",
        "bullets": [
            'Give you time to check in with people before pushing pace',
            'Let you set direction through conversation, not just instruction',
            'Trust your read of how the team is really doing',
        ],
        "third_preference_phrase": 'a people-first, relational way of setting direction',
    },
    'Adaptive & Field-Reading': {
        "dimension": 'Leadership',
        "summary": "You lead by watching what's actually happening and adjusting as you go. You'd rather start moving and sharpen direction in real time than fix it all up front.",
        "bullets": [
            'Let you start before every detail is settled',
            'Expect direction to shift as the picture changes',
            'Trust your read of the field over the original plan',
        ],
        "third_preference_phrase": 'an adaptive, field-reading way of setting direction',
    },
    # --- Change Management (Navigating Change / The Crossing) ---
    'Systems-Minded & Deliberate': {
        "dimension": 'Change Management',
        "summary": "You want to understand how the whole system fits together before you change any part of it. You move carefully so a fix in one place doesn't break another.",
        "bullets": [
            'Give you time to see how a change connects to everything else',
            'Explain how one part affects the rest before asking you to move it',
            'Expect you to ask how the pieces fit before you commit',
        ],
        "third_preference_phrase": 'a systems-minded, deliberate approach to change',
    },
    'Collaborative & Co-Created': {
        "dimension": 'Change Management',
        "summary": "You want the people affected by a change involved in shaping it. Change lands better, in your view, when it's built with people rather than delivered to them.",
        "bullets": [
            'Bring you in early to help design the change, not just announce it',
            'Ask the people affected what would make it work',
            'Expect your buy-in to be earned, not assumed',
        ],
        "third_preference_phrase": 'a collaborative, co-created approach to change',
    },
    'Steady & Reassuring': {
        "dimension": 'Change Management',
        "summary": 'You carry people through change by staying calm and close. You want to be a steady presence while others find their footing in something new.',
        "bullets": [
            'Rely on you to keep things calm while a change beds in',
            "Give you time to stay close to people who are struggling with it",
            'Expect you to reassure before you rush the pace',
        ],
        "third_preference_phrase": 'a steady, reassuring approach to change',
    },
    'Fast-Moving & Momentum-Driven': {
        "dimension": 'Change Management',
        "summary": "You want to move quickly once a change is decided, building momentum before doubt has time to set in. You'd rather adjust on the move than slow down to relitigate.",
        "bullets": [
            'Let you move at pace once the direction is set',
            'Expect you to keep momentum rather than pause to re-debate',
            'Bring new information to you as it comes, so you can adjust on the move',
        ],
        "third_preference_phrase": 'a fast-moving, momentum-driven approach to change',
    },
    # --- Conflict Management (Managing Conflict / The Forge) ---
    'Early & Direct': {
        "dimension": 'Conflict Management',
        "summary": "You'd rather name friction the moment you notice it than let it sit. You say the real issue plainly, while it's still small and easy to resolve.",
        "bullets": [
            'Expect you to name a problem early, not weeks later',
            'Take your directness as help, not confrontation',
            "Give you room to say the plain version of what's going on",
        ],
        "third_preference_phrase": 'an early, direct way of handling conflict',
    },
    'Calm & De-escalating': {
        "dimension": 'Conflict Management',
        "summary": 'You lower the temperature before you get into the substance. You want people to feel safe enough to speak honestly before you dig into a disagreement.',
        "bullets": [
            'Give the conversation a calm start before getting into it',
            'Trust you to make it safe for others to speak up',
            'Expect you to slow the pace when things feel tense',
        ],
        "third_preference_phrase": 'a calm, de-escalating way of handling conflict',
    },
    'Interest-Seeking & Diagnostic': {
        "dimension": 'Conflict Management',
        "summary": "You want to understand what's really driving a disagreement before you try to resolve it. You ask questions until you can see what each side actually needs.",
        "bullets": [
            'Expect you to ask questions before proposing a fix',
            'Give you room to dig past positions to what people actually want',
            "Trust your read once you've gotten to the real issue",
        ],
        "third_preference_phrase": 'an interest-seeking, diagnostic way of handling conflict',
    },
    'Steady & Task-Focused': {
        "dimension": 'Conflict Management',
        "summary": "You keep a disagreement anchored to the work. You'd rather agree the practical next step than spend long on the feelings behind the friction.",
        "bullets": [
            'Keep the conversation on the work, not the personalities',
            'Expect you to land on a practical next step',
            'Trust you to move things forward once the point is made',
        ],
        "third_preference_phrase": 'a steady, task-focused way of handling conflict',
    },
}


# Exact participant-facing option texts per question, in A-D order (keyed internally).
# Used to map a chosen option's text back to its letter, so Make can forward the raw
# answer text and the resolver normalizes it (no Typeform logic variables needed).
# All questions are non-evaluative PREFERENCE questions: how you prefer to lead,
# approach change, or handle conflict, not how skilled you are at any of it.
OPTION_TEXTS = {
    # Leadership (Leading with Intention)
    "ws_q1": [
        "Start with the big picture: where this is headed and why it matters",
        "Start with a clear plan: the steps, in order, that will get there",
        "Start with the people: how everyone's feeling about taking it on",
        "Start moving and let the direction sharpen as you go",
    ],
    "ws_q2": [
        "Return to the outcome and remind everyone why it matters",
        "Walk back through the plan to see where things sit against it",
        "Check in with individuals on how they're finding it",
        "Watch what's actually happening and take your cue from that",
    ],
    "ws_q3": [
        "Hold the outcome steady and trust the team to find their way to it",
        "Update the plan so the next steps stay clear",
        "Talk it through with the people closest to the work",
        "Change direction on the spot if that's what the moment calls for",
    ],
    # Change Management (Navigating Change)
    "ws_q4": [
        "Understand how all the pieces fit together before touching anything",
        "Bring the people affected in early to help shape how it will work",
        "Keep things calm and steady while everyone adjusts",
        "Move quickly and let the details settle as you go",
    ],
    "ws_q5": [
        "Map out how it affects everything else connected to it",
        "Design the new way together with the people who'll use it",
        "Reassure people and stay close while they get used to it",
        "Push ahead and build speed before doubts can set in",
    ],
    "ws_q6": [
        "Step back and check you still understand the whole picture",
        "Ask the people affected what's not working and adjust together",
        "Stay calm and steady so others can find their footing",
        "Keep the momentum going rather than slow down to relitigate it",
    ],
    # Conflict Management (Managing Conflict)
    "ws_q7": [
        "Name it straight away, before it grows",
        "Ease the tension first so people can talk without it feeling loaded",
        "Ask questions to understand what's really driving the disagreement",
        "Keep everyone focused on the work itself rather than the friction",
    ],
    "ws_q8": [
        "Say plainly what you think the real issue is",
        "Slow things down and de-escalate before going further",
        "Dig into what each side actually needs or wants",
        "Steer the conversation back to the task and what needs deciding",
    ],
    "ws_q9": [
        "Address it head-on and directly, sooner rather than later",
        "Create a calm space where people feel safe to speak",
        "Work through the underlying interests until you find common ground",
        "Agree the practical next step and move the work forward",
    ],
}

# Complementary working styles. For each style, the style that best complements it
# (a different style whose strengths balance yours) + a short, non-evaluative reason.
# PROPOSAL, mirrors the TEW pairing approach: intended to be reviewed/tuned before go-live.
COMPLEMENTS = {
    # Leadership
    "Vision-Led & Big-Picture":  {"style": "Structured & Step-by-Step",
        "reason": "You paint the big picture and the why. They turn that into clear steps. Together, your vision gets a path people can actually follow."},
    "Structured & Step-by-Step": {"style": "Vision-Led & Big-Picture",
        "reason": "You build the plan and the sequence. They hold the bigger why behind it. Together, your steps stay connected to a purpose worth following."},
    "People-First & Relational": {"style": "Adaptive & Field-Reading",
        "reason": "You bring the team along and read how people are doing. They read what's happening in the work and adjust fast. Together, you keep people and direction both on track."},
    "Adaptive & Field-Reading":  {"style": "Vision-Led & Big-Picture",
        "reason": "You adjust quickly to what you're seeing. They hold a steady outcome underneath the shifts. Together, your flexibility stays anchored to something worth reaching."},
    # Change Management
    "Systems-Minded & Deliberate":   {"style": "Fast-Moving & Momentum-Driven",
        "reason": "You map how the whole system fits together first. They build speed once the direction is set. Together, your care becomes change that actually moves."},
    "Collaborative & Co-Created":    {"style": "Steady & Reassuring",
        "reason": "You bring people into shaping the change. They stay calm and close while people adjust to it. Together, the change is both owned and carried well."},
    "Steady & Reassuring":           {"style": "Collaborative & Co-Created",
        "reason": "You keep people calm while things shift. They bring people into designing what's shifting. Together, change feels both steady and shared."},
    "Fast-Moving & Momentum-Driven": {"style": "Systems-Minded & Deliberate",
        "reason": "You build pace once a change is decided. They check how it connects to everything else first. Together, your speed doesn't outrun the details."},
    # Conflict Management
    "Early & Direct":               {"style": "Calm & De-escalating",
        "reason": "You name friction the moment you see it. They lower the temperature so it can be heard. Together, problems surface early and land well."},
    "Calm & De-escalating":          {"style": "Early & Direct",
        "reason": "You make it safe to speak. They make sure the real issue actually gets said. Together, tension gets named instead of just softened."},
    "Interest-Seeking & Diagnostic": {"style": "Steady & Task-Focused",
        "reason": "You dig into what's really driving the disagreement. They keep it anchored to the work and moving forward. Together, understanding turns into resolution."},
    "Steady & Task-Focused":         {"style": "Interest-Seeking & Diagnostic",
        "reason": "You keep a disagreement practical and moving. They make sure the real interests underneath get addressed. Together, the fix actually holds."},
}
