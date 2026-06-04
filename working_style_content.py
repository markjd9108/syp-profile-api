# -*- coding: utf-8 -*-
"""
The Performance Lens — Working Style layer (single source of truth).
Content is verbatim from "Working Style Mapping Logic v1" Word doc, Section 7.
Resolver logic matches "Working Style Mapping — Logic Table v1.xlsx" (validated 192/192).
DO NOT paraphrase participant-facing copy here. Update the Word doc first, then regenerate.
"""

# dimension -> answer letter -> style name (internal keying; never shown to participants)
KEYED = {
    'Communication': {
        'A': 'Considered & Thorough',
        'B': 'Direct & To-the-Point',
        'C': 'Warm & Attuned',
        'D': 'Curious & Questioning',
    },
    'Decision-Making': {
        'A': 'Measured & Analytical',
        'B': 'Decisive & Committed',
        'C': 'Consultative & Inclusive',
        'D': 'Adaptive & Iterative',
    },
    'Collaboration': {
        'A': 'Self-Directed & Focused',
        'B': 'Close & Collaborative',
        'C': 'Flexible & Versatile',
        'D': 'Candid & Open',
    },
}

# Tiebreak weighting: when all three answers differ, these question positions decide
# order. Tuple = (primary_idx, secondary_idx, third_idx) into [ans_q_a, ans_q_b, ans_q_c].
# Communication Q2>Q3>Q1; Decision-Making Q5>Q6>Q4; Collaboration Q9>Q8>Q7.
TIEBREAK = {
    'Communication':   (1, 2, 0),
    'Decision-Making': (1, 2, 0),
    'Collaboration':   (2, 1, 0),
}

# Which 3 questions feed each dimension (Typeform variables ws_q1..ws_q9)
DIMENSION_QUESTIONS = {
    'Communication':   ('ws_q1', 'ws_q2', 'ws_q3'),
    'Decision-Making': ('ws_q4', 'ws_q5', 'ws_q6'),
    'Collaboration':   ('ws_q7', 'ws_q8', 'ws_q9'),
}

# Output variable prefix per dimension
DIMENSION_PREFIX = {
    'Communication': 'comm', 'Decision-Making': 'decision', 'Collaboration': 'collab',
}

WORKING_STYLE_CONTENT = {
    'Considered & Thorough': {
        "dimension": 'Communication',
        "summary": 'You like to understand something fully before you engage with it. You take in detail, think before you speak, and plan how you’ll say something so it comes out the way you mean it.',
        "bullets": [
            'Give you the full picture up front, including the detail',
            'Allow a beat to process before expecting a response',
            'Put complex points in writing where you can work through them at your own pace',
        ],
        "third_preference_phrase": 'a considered, think-it-through approach to communication',
    },
    'Direct & To-the-Point': {
        "dimension": 'Communication',
        "summary": 'You get to the point and you appreciate the same in return. You stay clear even when a message is uncomfortable, and you keep conversations moving toward a resolution.',
        "bullets": [
            'Lead with the headline and the ask',
            'Keep updates short and skip the long preamble',
            'Read your directness as a way of saving everyone time',
        ],
        "third_preference_phrase": 'a clear, get-to-the-point communication style',
    },
    'Warm & Attuned': {
        "dimension": 'Communication',
        "summary": 'You pay attention to how a message lands as much as to what it says. You look for common ground, ease into harder messages, and read the room as a conversation unfolds.',
        "bullets": [
            'Make space for the human side of a conversation alongside the task',
            'Give hard topics a little context before getting into them',
            'Check in on how things land, as well as whether they’re done',
        ],
        "third_preference_phrase": 'a warm, people-aware way of communicating',
    },
    'Curious & Questioning': {
        "dimension": 'Communication',
        "summary": 'You understand by asking. You want the reasoning behind things, and you draw out what’s really being disagreed about before you settle on a view.',
        "bullets": [
            'Welcome your questions as a sign of engagement',
            'Explain the why alongside the what',
            'Give you room to probe an idea before you’re asked to back it',
        ],
        "third_preference_phrase": 'a curious, question-led approach to communication',
    },
    'Measured & Analytical': {
        "dimension": 'Decision-Making',
        "summary": 'You like to understand the full picture before you commit. You gather information, weigh the options, and look for a sound basis for the call you make.',
        "bullets": [
            'Bring the data and the reasoning alongside the conclusion',
            'Give you time to weigh options where the stakes justify it',
            'Flag what’s known and unknown so you can factor it in',
        ],
        "third_preference_phrase": 'a measured, weigh-the-options approach to decisions',
    },
    'Decisive & Committed': {
        "dimension": 'Decision-Making',
        "summary": 'You’re comfortable making the call and moving. You trust your read of a situation, commit to a direction, and get on with executing it.',
        "bullets": [
            'Be ready to move once a direction is set',
            'Bring a recommendation alongside the open question',
            'Raise concerns early, while the call is still open',
        ],
        "third_preference_phrase": 'a decisive, commit-and-move approach to decisions',
    },
    'Consultative & Inclusive': {
        "dimension": 'Decision-Making',
        "summary": 'You decide by thinking things through with others. You draw on input and trusted judgment as you work toward a direction.',
        "bullets": [
            'Be available to talk a decision through',
            'Share your honest read when you’re asked for it',
            'Expect to be brought into the thinking early',
        ],
        "third_preference_phrase": 'a consultative, talk-it-through approach to decisions',
    },
    'Adaptive & Iterative': {
        "dimension": 'Decision-Making',
        "summary": 'You’re comfortable deciding with incomplete information and adjusting as things unfold. You treat a decision as something you can refine as you learn more.',
        "bullets": [
            'Keep you posted as things change so you can course-correct',
            'Treat an early call as a starting point you’ll build on',
            'Bring new information as it arrives',
        ],
        "third_preference_phrase": 'an adaptive, adjust-as-you-go approach to decisions',
    },
    'Self-Directed & Focused': {
        "dimension": 'Collaboration',
        "summary": 'You do your best work in a clear lane. You like to own your part, think it through yourself, and be trusted to deliver it.',
        "bullets": [
            'Define the role and the outcome, then give you room to run',
            'Give you space to work once expectations are set',
            'Come to you with a clear ask',
        ],
        "third_preference_phrase": 'a self-directed, own-your-part way of working with a team',
    },
    'Close & Collaborative': {
        "dimension": 'Collaboration',
        "summary": 'You do your best work in close, continuous collaboration. You like to build alongside others and stay in constant exchange as the work develops.',
        "bullets": [
            'Stay engaged and build alongside you',
            'Share work in progress as it develops',
            'Keep the back-and-forth open throughout',
        ],
        "third_preference_phrase": 'a close, build-it-together way of working with a team',
    },
    'Flexible & Versatile': {
        "dimension": 'Collaboration',
        "summary": 'You read the team and find your place in it. You flex how you contribute to what the group needs, and you stay open to changing your approach.',
        "bullets": [
            'Be clear about what the team needs from you right now',
            'Tell you when the priority shifts so you can move with it',
            'Make use of your range across different modes',
        ],
        "third_preference_phrase": 'a flexible, fit-the-team way of working',
    },
    'Candid & Open': {
        "dimension": 'Collaboration',
        "summary": 'You surface things openly. When a dynamic is off or something has broken, your instinct is to name it and get it on the table.',
        "bullets": [
            'Treat your directness as help',
            'Make it safe to raise the hard thing early',
            'Respond to what you name head-on',
        ],
        "third_preference_phrase": 'a candid, name-it-openly way of working with a team',
    },
}


# Exact participant-facing option texts per question, in A-D order (keyed internally).
# Used to map a chosen option's text back to its letter, so Make can forward the raw
# answer text and the resolver normalizes it (no Typeform logic variables needed).
OPTION_TEXTS = {
    "ws_q1": [
        "Walk you through it step by step, in detail, even if it takes longer",
        "Give you the headline first, then let you ask for detail where you need it",
        "Show you, demonstrate, or give you an example to work from",
        "Explain their reasoning and let you question it until it fully makes sense to you",
    ],
    "ws_q2": [
        "Plan exactly what you'll say beforehand so you get the wording right",
        "Be direct and clear, even if it feels uncomfortable in the moment",
        "Lead with what's going well, then introduce the harder message",
        "Ask questions first to understand their view before sharing yours",
    ],
    "ws_q3": [
        "Listen carefully and only speak once you've fully formed your view",
        "Jump in to share your perspective and help move the conversation forward",
        "Find the common ground between the different views and surface it",
        "Ask questions that help the group think through what's actually being disagreed about",
    ],
    "ws_q4": [
        "You have time to gather information and weigh the options before deciding",
        "You can size up the situation, make the call, and move",
        "You can talk it through with others and get their input",
        "You can move quickly and adjust as you learn more",
    ],
    "ws_q5": [
        "Lay out the options and work through the trade-offs",
        "Trust your instinct and commit, then learn from the outcome",
        "Find someone whose judgment you trust and talk it through",
        "Pick a direction you can adjust later, and refine it as you learn more",
    ],
    "ws_q6": [
        "Reflect on whether it was the right call before fully moving on",
        "Commit fully and execute without second-guessing",
        "Communicate it clearly to others and bring them along",
        "Stay open to revisiting it if new information emerges",
    ],
    "ws_q7": [
        "You have a clearly defined role and can own your part",
        "The team works closely together throughout, exchanging ideas constantly",
        "You can flex between contributing your own work and shaping the group's direction",
        "You can name where things are heading and say so openly as the work unfolds",
    ],
    "ws_q8": [
        "Take ownership of your part and ask others to do the same",
        "Work through it together before deciding what to do next",
        "Look at what the team can learn and do differently next time",
        "Pause and name what happened and why, before moving forward",
    ],
    "ws_q9": [
        "Focus on doing your work well and let your behaviour model what's possible",
        "Build strong one-on-one relationships first, then influence the group",
        "Adapt to how the team operates and find your place within it",
        "Name what you're seeing and try to surface the dynamic openly",
    ],
}
