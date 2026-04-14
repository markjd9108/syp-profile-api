#!/usr/bin/env python3
"""
SYP Team Effectiveness Lab — Participant Profile PDF Generator v2 Improved
2-page personalised PDF with expanded content and improved spacing
  Page 1 — Assessment overview: header, hook, scores, strength, gap
  Page 2 — Action plan: next steps, recommendations, leadership CTA, framework table
"""

import math, os, sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph, KeepInFrame
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from PIL import Image, ImageOps

# ─── Brand palette ─────────────────────────────────────────────────────────────
SYP_DARK_BLUE   = colors.HexColor("#0D2A66")
SYP_SKY_BLUE    = colors.HexColor("#1E88E5")
SYP_NEAR_BLACK  = colors.HexColor("#1A1A2E")
SYP_WHITE       = colors.white
SYP_MID_GREY    = colors.HexColor("#64748B")
SYP_LIGHT_GREY  = colors.HexColor("#F8FAFC")
SYP_DIVIDER     = colors.HexColor("#E2E8F0")
SYP_WARM_BG     = colors.HexColor("#FAFAF9")

BAND_STRONG     = colors.HexColor("#15803D")
BAND_DEVELOPING = colors.HexColor("#1D4ED8")
BAND_EMERGING   = colors.HexColor("#B45309")
BAND_FOUNDATION = colors.HexColor("#B91C1C")
BAND_HIGH_BG    = colors.HexColor("#F0FDF4")
BAND_LOW_BG     = colors.HexColor("#FFF5F5")

def hc(h): return colors.HexColor(h)

# ─── Logo generation ───────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def ensure_white_logo():
    """Generate white logo from black logo if it doesn't exist."""
    # Try relative paths first (for deployment), then absolute paths (for local dev)
    white_logo_candidates = [
        os.path.join(SCRIPT_DIR, "syp_logo_white_wm.png"),
        "/sessions/bold-dreamy-carson/syp_logo_white_wm.png",
    ]
    black_logo_candidates = [
        os.path.join(SCRIPT_DIR, "SYP Brand Assets", "Logos", "SYP Logo+Wordmark Black PNG.png"),
        "/sessions/bold-dreamy-carson/mnt/SYP Soft Skills - Self Assessment Profile/SYP Brand Assets/Logos/SYP Logo+Wordmark Black PNG.png",
    ]

    # Check if white logo already exists
    for wp in white_logo_candidates:
        if os.path.exists(wp):
            return wp

    # Find the black logo source
    black_logo_path = None
    for bp in black_logo_candidates:
        if os.path.exists(bp):
            black_logo_path = bp
            break

    white_logo_path = white_logo_candidates[0]  # save to script directory

    if black_logo_path:
        try:
            img = Image.open(black_logo_path).convert("RGBA")
            r, g, b, a = img.split()
            rgb_img = Image.merge("RGB", (r, g, b))
            inv_rgb = ImageOps.invert(rgb_img)
            ri, gi, bi = inv_rgb.split()
            white_img = Image.merge("RGBA", (ri, gi, bi, a))
            white_img.save(white_logo_path, "PNG")
            return white_logo_path
        except Exception as e:
            print(f"Warning: Could not generate white logo: {e}")
            return white_logo_path
    else:
        print(f"Warning: Black logo not found in any candidate path")
        return white_logo_path

# ─── Page geometry ─────────────────────────────────────────────────────────────
PW, PH = A4                 # 595.28 × 841.89 pt
ML = 18 * mm
MR = 18 * mm
CW = PW - ML - MR
HEADER_H   = 58 * mm        # p1 header
HDR2_H     = 16 * mm        # p2 thin header
FOOTER_H   = 10 * mm
BODY_TOP_1 = PH - HEADER_H - 5 * mm
BODY_TOP_2 = PH - HDR2_H   - 5 * mm
BODY_BOT   = FOOTER_H + 5 * mm

LOGO_PATH  = ensure_white_logo()

# ─── Archetype data ─────────────────────────────────────────────────────────────
ARCHETYPES = {
    # ── The Operator ────────────────────────────────────────────────────────────
    "operator": {
        "number": "ARCHETYPE 3",
        "name":   "The Operator",
        "subtitle": "Steady under fire. Sharper in the brief.",
        "light":  "#FEF3C7", "accent": "#92400E", "dark": "#78350F",
        "pill_bg": "#B45309",
        "comm": 45, "decision": 74, "collab": 68,
        "hook": (
            "You make strong calls, keep the team running, and recover quickly when things "
            "break. But your communication doesn't yet match the quality of your thinking, "
            "and that gap is costing your team more than you realise."
        ),
        "strength_paras": [
            "You have operational instincts that most people spend years developing. In "
            "today's sessions you made decisions under constraint, committed to them without "
            "second-guessing, and when collaboration broke down, you paused and restructured "
            "rather than escalated. These are behaviours typically associated with experienced "
            "operators: the people teams depend on when execution has to happen under pressure.",

            "In professional environments this translates into reliability. Teams with an "
            "Operator at the table move faster and experience less momentum loss during "
            "disruption. You are the person a leader can delegate to when the brief is "
            "incomplete, not because you always have the perfect answer, but because you will "
            "commit to finding one. That combination of decisiveness and adaptive execution "
            "distinguishes strong individual contributors from future team leads.",

            "The opportunity in front of you is significant. Decision quality paired with "
            "recovery instincts under pressure is the foundation of senior operational "
            "leadership. The gap between where you are now and having full impact is not about "
            "becoming more capable, it is about ensuring the quality of your thinking becomes "
            "visible to the people around you. When your communication matches your execution, "
            "your ceiling rises dramatically.",
        ],
        "gap_paras": [
            "Your instructions were clear to you, but the picture your teammates built from "
            "them didn't match what you intended. You are working from a complete mental model "
            "and transmitting it in fragments. This isn't a communication failure, it's a "
            "translation gap. Your brain has already solved for the outcome before your words "
            "have finished describing the starting point.",

            "In the workplace this shows up as misaligned execution. Your team finishes a task "
            "that isn't quite what you envisioned. Revisions happen after delivery instead of "
            "being caught in the brief. The cost is invisible in any single instance but "
            "accumulates as rework, friction, and a quiet erosion of confidence, even when "
            "your operational instincts remain entirely sound.",

            "The cost of leaving this unaddressed scales directly with your seniority. A "
            "communication gap at individual contributor level creates minor friction. The same "
            "gap at team lead or manager level creates systemic misalignment. Addressing this "
            "now, before your scope of responsibility grows, is the highest-leverage investment "
            "you can make in your professional development.",
        ],
        "steps": [
            ("Say the destination first, always",
             "Before giving any instruction, state the outcome: 'We're trying to end up with "
             "X. Here's how I think we get there.' One sentence of context before the steps "
             "doubles the alignment rate of everything that follows. Practice this deliberately "
             "in your next three project handoffs or team briefings."),
            ("Close the loop deliberately",
             "After giving a brief or instruction, ask: 'What's your understanding of what we "
             "need?' This is not micromanagement, it is the Clarity Loop in action. You are "
             "verifying that your mental model has transferred correctly before execution begins, "
             "not after it diverges."),
            ("Share the 'because'",
             "When you give an instruction that emerged from a reasoning process, share the "
             "one-line version of that reasoning. Not the full logic, just the 'because.' "
             "'We're doing X because Y' reduces resistance, builds context, and helps your "
             "team make good decisions when you're not in the room."),
        ],
        "recommendations": (
            "The single highest-leverage development area is the transition from 'clear in my "
            "head' to 'clear in the room.' Before important handoffs or meetings, draft one "
            "sentence that describes the outcome you are driving toward and use it to open. "
            "The discipline of articulating destination before method feels unnatural at first, "
            "but it becomes a professional superpower when automatic. This shift will ensure "
            "that you and your team are on the same page and moving as a unit. Ask a trusted "
            "colleague to give you real-time signals when your instructions are unclear, so you "
            "can calibrate in the moment rather than discovering misalignment after delivery."
        ),
        "leadership_cta": (
            "Schedule time to discuss this profile with your leader within the next 7 days. "
            "Over the next 30 days, plan to: 1) Identify two live projects or handoffs where "
            "you will deliberately practise outcome-first communication, opening with the "
            "destination before the steps. 2) Ask your leader to observe one team briefing per "
            "week and give you specific feedback on whether you led with outcome or method. "
            "3) Track your progress by noting after each briefing whether you opened with the "
            "outcome or launched into the method. Your goal is a 100% success rate on opening "
            "with destination, which will take 3-4 weeks of conscious practice."
        ),
        "framework_rows": [
            ("Clarity Loop",        "Primary",  "Communication is your highest-leverage development area."),
            ("Decision Engine",     "Continue", "Decision instincts are strong. Keep the standard high."),
            ("Collaboration Reset", "Continue", "Recovery skills are present. Deepen the precision."),
        ],
    },

    # ── The Architect ───────────────────────────────────────────────────────────
    "architect": {
        "number": "ARCHETYPE 1",
        "name":   "The Architect",
        "subtitle": "You build clarity everywhere except inside yourself.",
        "light":  "#EDE9FE", "accent": "#4C1D95", "dark": "#3B0764",
        "pill_bg": "#6D28D9",
        "comm": 78, "decision": 72, "collab": 42,
        "hook": (
            "You think in systems, communicate with precision, and make structured decisions "
            "under pressure. But today revealed a blind spot: when the team around you breaks "
            "down, you solve for the output, not the people."
        ),
        "strength_paras": [
            "You are the person others instinctively turn to when things are unclear. In "
            "today's sessions your instructions were precise, your decisions were structured, "
            "and when constraints hit you adapted your framework rather than abandoning it. "
            "That combination of communication clarity and structured decision-making is "
            "genuinely rare, and it consistently de-risked your team's performance when the "
            "pressure intensified.",

            "What drives this strength is systems thinking applied in real time. You don't "
            "just respond to what is in front of you. You build mental models of how the "
            "pieces connect, and those models allow you to communicate and decide faster than "
            "most. In professional environments this shows up as reliability under ambiguity: "
            "colleagues trust your briefings, leaders delegate complex problems to you, and "
            "you are often asked to structure the thinking of those around you.",

            "The opportunity in front of you is a leadership track built on analytical "
            "credibility. Your precision is a rare asset. The question is not whether your "
            "thinking will serve you. It will. The question is whether you can extend that "
            "clarity to include the human dimension of your teams, which would make you not "
            "just effective, but genuinely influential at scale.",
        ],
        "gap_paras": [
            "Collaboration was where today revealed a gap. Under pressure, your instinct was "
            "to solve the output problem rather than re-align the people creating it. When the "
            "team around you broke down, you moved faster toward the answer rather than pausing "
            "to check whether everyone was still oriented toward the same question. Teammates "
            "sometimes experienced this as being treated like variables in your system rather "
            "than partners in it.",

            "This gap has a specific behavioral root: when you have a clear model of the right "
            "answer, the human process of aligning others can feel like friction. It isn't. "
            "It is a requirement. The clearer your thinking, the more intentional you need to "
            "be about externalising it in ways that bring people with you rather than leaving "
            "them to catch up. Efficiency in your thinking must be matched by investment in "
            "shared understanding.",

            "The downstream cost is real and compound. Decisions get made correctly but don't "
            "land with team ownership. Projects succeed technically but don't build the "
            "capability or trust that makes future work easier. Over time, people follow your "
            "lead without contributing to it. Your impact ceiling stays lower than your "
            "capability ceiling, simply because you are carrying more of the cognitive load "
            "than you need to.",
        ],
        "steps": [
            ("Before naming the solution, name the dynamic",
             "When collaboration breaks down, resist the urge to solve the output problem first. "
             "Pause and say out loud: 'Before we push forward, are we all still pointed at the "
             "same thing?' This is not inefficiency. It is the investment that makes your output "
             "durable and builds team ownership alongside delivery."),
            ("Make space for disagreement",
             "In your next project or meeting, deliberately invite challenge: 'I've got a view on "
             "this. I want to hear if you see it differently before we proceed.' This signals "
             "that the team's thinking matters to your process, not just their execution, and "
             "builds the collaborative ownership your outputs currently lack."),
            ("Separate confidence from certainty",
             "You can be confident in your process without being closed to revision. Practice "
             "saying 'Here's my thinking. What am I missing?' instead of 'Here's the plan.' "
             "The signal your team needs is not that you have the answer, but that you have a "
             "rigorous approach to finding it. They are part of that approach."),
        ],
        "recommendations": (
            "Your highest-leverage development is learning to distinguish between problems that "
            "require your individual thinking and problems that require collective thinking. Not "
            "every challenge is best solved by your clarity alone. Some are best solved by the "
            "team developing shared understanding together, even if it takes longer. This "
            "distinction will dramatically increase your team's capability and ownership. Invest "
            "in facilitation skills: guiding a group toward clarity is the natural extension of "
            "your existing individual strength and multiplies your impact significantly. Your "
            "teams will move faster and with more autonomy when they feel like partners rather "
            "than executors of your thinking."
        ),
        "leadership_cta": (
            "Schedule a conversation with your leader within the next 7 days to discuss your "
            "collaboration gap. Over the next 30 days, plan to: 1) In your next two projects, "
            "deliberately facilitate team thinking rather than presenting solutions. Open by "
            "naming the problem and inviting the team's approach before you propose yours. "
            "2) Ask your leader to observe how you bring your team into your thinking process "
            "and notice whether they feel like partners or executors. 3) After each facilitated "
            "session, reflect on whether the team felt ownership of the direction and track how "
            "this increases their autonomy and reduces your cognitive load in implementation."
        ),
        "framework_rows": [
            ("Collaboration Reset", "Primary",  "The gap between your output quality and team alignment."),
            ("Clarity Loop",        "Continue", "Already strong. Keep the standard high."),
            ("Decision Engine",     "Continue", "Structured thinking is a foundation. Build on it."),
        ],
    },

    # ── The Navigator ───────────────────────────────────────────────────────────
    "navigator": {
        "number": "ARCHETYPE 2",
        "name":   "The Navigator",
        "subtitle": "You can read the room. Now learn to steer.",
        "light":  "#D1FAE5", "accent": "#065F46", "dark": "#064E3B",
        "pill_bg": "#047857",
        "comm": 71, "decision": 44, "collab": 76,
        "hook": (
            "You communicate well, hold the team together under pressure, and notice "
            "breakdowns before most people do. Your gap is decision-making. When the path "
            "forward is unclear, you hesitate where others need you to call it."
        ),
        "strength_paras": [
            "Your ability to read what is happening in a room and pull people back into "
            "alignment before things fully break is one of the most valuable and difficult "
            "skills in team dynamics. Today, your communication kept people oriented even when "
            "the simulation was failing around them. When your team became disoriented, you "
            "noticed, re-engaged them, and created enough shared clarity for the group to "
            "continue functioning.",

            "This strength emerges from high social attunement combined with genuine "
            "communication skill. You process interpersonal dynamics in real time: who is "
            "disengaging, where the miscommunication is occurring, what the team needs to hear "
            "to re-anchor. In professional environments, this translates into team leadership "
            "potential that operates through trust rather than authority. Peers come to you "
            "during breakdown moments not because you have the answers, but because your "
            "presence stabilises the system.",

            "The opportunity is to pair this with decisiveness, which would make you genuinely "
            "formidable. Right now you are someone teams hold together around. Add the ability "
            "to call the direction confidently, and you become someone teams follow, combining "
            "the relational intelligence of a great collaborator with the directional clarity "
            "of a trusted leader. That combination is rare and consistently rewarded.",
        ],
        "gap_paras": [
            "When the path forward was unclear today, you hesitated. You are highly skilled at "
            "facilitating other people's decisions: helping a team surface options, find shared "
            "consensus, build collective buy-in. But when the moment required you to own a "
            "call under ambiguity and time pressure, you stalled. This is not a capacity gap. "
            "It is a confidence pattern.",

            "The behavioral root is that your collaborative instinct, which is genuinely "
            "strong, can become a dependency. When alignment feels incomplete, you wait for "
            "it rather than creating it through a committed call. You are most comfortable "
            "being the person who helps others decide; you are less comfortable being the "
            "person who decides when others cannot. In fast-moving environments, the ability "
            "to call a direction, even an imperfect one, is often worth more than the "
            "ability to facilitate a perfect decision that arrives too late.",

            "The cost of leaving this unaddressed is a ceiling on your career development at "
            "the point where leadership requires individual decisiveness rather than group "
            "facilitation. You can go very far on your collaboration and communication "
            "strengths. But you will encounter roles that require visible, singular "
            "accountability for calls under pressure and building that muscle now, while the "
            "stakes are lower, is the smartest investment you can make.",
        ],
        "steps": [
            ("Resist facilitating, make the call instead",
             "The next time your team is stuck, try something different: instead of opening "
             "the floor, decide. Say: 'Here is what I think we should do, and here is why. "
             "Push back if you see something I'm missing.' The permission you are giving "
             "yourself is not to be right. It is to be the one who moves things forward."),
            ("Separate facilitation from leadership",
             "Facilitation is a skill you have. Leadership requires also being accountable for "
             "a direction. Begin identifying moments where you are facilitating when you should "
             "be leading and make a deliberate choice. The difference is one question: 'Am I "
             "helping them decide, or am I avoiding deciding myself?'"),
            ("Build decisiveness in low-stakes contexts",
             "Start with decisions where the cost of being wrong is low: meeting agendas, "
             "task allocation, direction of a discussion. Make the call without checking with "
             "everyone first. Review the outcome. The goal is to build the reflex of decisive "
             "action so it is available when the stakes are higher."),
        ],
        "recommendations": (
            "Study how confident decision-makers in your environment frame and communicate "
            "their calls. What language do they use? How do they signal accountability without "
            "claiming certainty? You don't need to change your style. You need to extend it. "
            "Your collaborative instincts will actually make you a better decision-maker than "
            "most, because you will make calls with genuine awareness of the human context. "
            "That combination of relational intelligence and decisiveness is rare and opens "
            "doors to leadership roles that require both trust and direction. Start making "
            "three small decisions per week without seeking consensus first, and you will build "
            "the muscle memory that makes bigger calls accessible."
        ),
        "leadership_cta": (
            "Schedule time with your leader within the next 7 days to discuss this development "
            "area. Over the next 30 days, plan to: 1) Identify three moments in your work where "
            "you need to step into a decision rather than facilitate one, and commit to making "
            "the call even if alignment feels incomplete. 2) Ask your leader to observe these "
            "moments and give you honest feedback afterwards: How did you frame the call? How "
            "did it land? What was the outcome? 3) Track your progress by noting each decision "
            "you made, how it landed, and what you learned about your decisiveness. Your goal "
            "is to build confidence through success, not perfection."
        ),
        "framework_rows": [
            ("Decision Engine",     "Primary",  "Owning calls under pressure is your next development frontier."),
            ("Clarity Loop",        "Continue", "Communication strength is present. Keep sharpening."),
            ("Collaboration Reset", "Continue", "Recovery instincts are strong. Add decisiveness to them."),
        ],
    },

    # ── The Signal ──────────────────────────────────────────────────────────────
    "signal": {
        "number": "ARCHETYPE 4",
        "name":   "The Signal",
        "subtitle": "Clear voice. Waiting for someone to tune in.",
        "light":  "#FEE2E2", "accent": "#7F1D1D", "dark": "#450A0A",
        "pill_bg": "#B91C1C",
        "comm": 75, "decision": 48, "collab": 41,
        "hook": (
            "You communicate with clarity and precision, and today that was your most visible "
            "asset. But when the team needed direction or recovery, you transmitted clearly "
            "without leading."
        ),
        "strength_paras": [
            "Your communication was among the strongest in today's workshop. Instructions were "
            "precise, questions were targeted, and when feedback was restricted you adapted "
            "your language rather than repeating yourself. That adaptability under constraint, "
            "adjusting how you communicate when the normal channels close, is a skill most "
            "professionals don't develop without significant experience under real pressure.",

            "The behavioral root of this strength is disciplined language precision. Where "
            "others reach for approximations when the pressure hits, you look for the most "
            "accurate representation of what you mean. This is a cognitive habit built from a "
            "genuine concern for being understood, not just heard. The distinction matters "
            "enormously. People who communicate to be understood consistently produce better "
            "outcomes, stronger trust, and more reliable execution from those around them.",

            "In professional environments, your communication precision translates into "
            "consistent credibility wherever information quality matters: strategy, stakeholder "
            "management, professional services, complex project delivery. You are the person "
            "whose briefings are trusted, whose updates land with clarity, and who gets asked "
            "to represent complex decisions because others know you'll capture them accurately. "
            "The opportunity is to deploy this asset more assertively, not just to inform, "
            "but to lead.",
        ],
        "gap_paras": [
            "When the team drifted today, you observed more than you intervened. When decisions "
            "were underdefined, you waited for clarity to arrive rather than proposing it. You "
            "are most visible, most effective, and most comfortable when the system is working. "
            "When it isn't, you are less certain of your role. Your communication strength is "
            "currently deployed reactively and it needs to become proactive.",

            "This gap has a specific behavioral root: high communication precision combined "
            "with an under-active sense of permission to lead. You have the language and "
            "clarity to intervene, propose, and redirect. But something in your default "
            "orientation says that role belongs to someone else. It doesn't. Precision in "
            "communication without the willingness to use it for direction-setting is a "
            "significant capability left on the table.",

            "In the workplace, this creates a perception gap between your actual capability "
            "and your visible contribution. Colleagues and managers may underestimate your "
            "thinking because you share it less often than you could. The cost is not just "
            "missed impact in the moment. It is how you are seen, developed, and considered "
            "for opportunities. Closing the gap between what you observe and what you say is "
            "the most direct path to having your actual potential recognised.",
        ],
        "steps": [
            ("Convert observations into proposals",
             "The next time you notice a problem, a drift, or an underdefined decision, turn "
             "your observation into a proposal. Instead of 'I notice we haven't agreed on X,' "
             "say: 'I think we need to decide X before we continue. Here is my recommendation.' "
             "One sentence shifts your role in the room from observer to participant."),
            ("Claim the floor without being invited",
             "In your next meeting or collaboration, offer your view without being asked. Not "
             "loudly, not with false certainty, but with the precise language you already have. "
             "'I want to share a perspective on this' is enough. Visibility requires action, "
             "not just capability, and you have more than enough to act on."),
            ("Use your communication skill for team recovery",
             "When your team is off-track, deploy your strength deliberately: 'I want to pause. "
             "I think we have lost alignment on X. Can we take 60 seconds to re-anchor?' "
             "This is exactly what your communication precision is designed for. Practice making "
             "it a reflex rather than something you observe others needing to do."),
        ],
        "recommendations": (
            "The development edge for you is not about acquiring new skills. It is about "
            "deploying the ones you already have in new contexts. Every time you observe a "
            "problem and stay silent, or wait to be asked before contributing, you are choosing "
            "not to use your most significant professional asset. Communication precision "
            "without initiative is like having the best instrument in the ensemble and waiting "
            "to be asked to play. Start playing and play with the authority your precision "
            "has earned. Your clarity is a form of leadership; you've been using it informally. "
            "Now it's time to claim it overtly. This shift will open doors to influence and "
            "opportunity that are currently invisible to you."
        ),
        "leadership_cta": (
            "Take this profile to your leader within the next 7 days and ask for their support "
            "on a specific development plan. Over the next 30 days, plan to: 1) Identify two "
            "team situations where you notice a problem or drift, and deliberately propose a "
            "direction or solution rather than waiting for others to see it. Use your precise "
            "language as your authority. 2) Ask your leader for honest feedback on whether your "
            "contribution in team environments matches your capability when you're working "
            "one-on-one, and ask them to call it out in real time when they see you holding back. "
            "3) Track your progress by noting each moment you claimed the floor and what "
            "happened as a result. Most likely you'll find that your precision is exactly what "
            "teams need, and that visibility is your gateway to greater impact."
        ),
        "framework_rows": [
            ("Decision Engine",     "Primary",  "Build the habit of proposing rather than just observing."),
            ("Collaboration Reset", "Primary",  "Your communication precision makes you effective here. Use it."),
            ("Clarity Loop",        "Continue", "Communication strength is strong. Maintain and extend it."),
        ],
    },

    # ── The Anchor ──────────────────────────────────────────────────────────────
    "anchor": {
        "number": "ARCHETYPE 5",
        "name":   "The Anchor",
        "subtitle": "The team holds together because of you.",
        "light":  "#DBEAFE", "accent": "#1E3A8A", "dark": "#172554",
        "pill_bg": "#1D4ED8",
        "comm": 44, "decision": 47, "collab": 73,
        "hook": (
            "You are the gravitational centre of your team when things break down. Today "
            "exposed that your collaboration instinct is strong, but it is running without "
            "the communication precision and decision structure that would make it truly powerful."
        ),
        "strength_paras": [
            "When the simulation splintered, you moved toward the people and the problem "
            "rather than away from them. That instinct, consistently present under pressure, "
            "is the foundation of genuine team leadership. Most people, when faced with "
            "interpersonal breakdown under time pressure, either escalate or withdraw. You "
            "did neither. You re-engaged. That is a rare and significant behavioural default.",

            "This strength is rooted in a fundamentally relational orientation. Where others "
            "see team dynamics as overhead, you see them as the work itself. You understand, "
            "perhaps intuitively rather than analytically, that a team which is not aligned "
            "is not a team; it is a collection of individuals with a shared deadline. That "
            "understanding makes you the person who holds the human architecture of a team "
            "together when the conditions are hardest.",

            "In the workforce, this is an irreplaceable function on high-performance teams. "
            "Project managers and senior leaders look for this deliberately when assembling "
            "teams for high-stakes work. People who can hold teams together under pressure "
            "are significantly rarer and harder to develop than people who can simply "
            "execute under pressure. The opportunity: if you can pair this with communication "
            "precision and structured decision-making, the compound effect on your leadership "
            "potential would be extraordinary.",
        ],
        "gap_paras": [
            "Your resets were felt but sometimes imprecise. People knew you were trying to "
            "re-align the team, but they weren't always sure what they were being aligned to. "
            "And when decisions needed to be made under pressure, your strength in reading the "
            "team didn't translate into a clear call. You diagnosed the problem accurately but "
            "sometimes left the prescription incomplete.",

            "The behavioral root of this gap is that your relational attunement operates "
            "ahead of your structural clarity. You feel the misalignment before you can name "
            "it precisely, and you act on that feeling, which is the right instinct. But "
            "action without precision creates motion without direction. A reset that doesn't "
            "name the specific thing being re-aligned leaves the team re-energised but still "
            "navigating without a clear destination.",

            "The cost of leaving this unaddressed is that your influence stays at the level "
            "of team cohesion rather than team performance. You will prevent breakdowns "
            "reliably but you may not yet be enabling breakthroughs. The leaders who are "
            "truly effective at the Collaboration Reset are the ones who can both sense the "
            "breakdown and structure the recovery with enough precision that the team doesn't "
            "just reconnect emotionally, but re-orients operationally.",
        ],
        "steps": [
            ("Name what is misaligned before attempting the reset",
             "When you sense a team is off-track, pause before acting on the feeling. Ask "
             "yourself: 'What exactly is misaligned right now?' Then open with that: 'I want "
             "to pause. I think we have lost agreement on X. Can we take a moment to re-anchor "
             "on that before we continue?' The precision of the pause determines the quality of "
             "the reset."),
            ("Build your decisiveness through structured micro-calls",
             "You don't need to become a directive decision-maker. Your collaborative style "
             "is genuinely valuable. But develop the ability to make a clear call when the "
             "team needs one. Start with small decisions: task allocation, direction of a "
             "discussion, order of operations. Make the call cleanly: 'I think we should do X. "
             "Any strong objections before we proceed?'"),
            ("Match your emotional intelligence with structural intelligence",
             "Your relational awareness is strong. Now build the parallel ability to structure "
             "problems out loud: 'What do we know? What are we deciding? What is the first "
             "step?' These questions, combined with your ability to hold the team together, "
             "would make your recovery attempts far more effective and your leadership "
             "presence far more complete."),
        ],
        "recommendations": (
            "The Clarity Loop is your single highest-leverage development target. Not because "
            "your communication is ineffective. It moves people. But right now it moves them "
            "emotionally without always moving them structurally. The upgrade is adding "
            "precision to warmth: when you say 'I think we need to regroup,' add 'specifically, "
            "I think we need to agree on X.' That single addition doubles the impact of what "
            "you already do well, and it is a learnable, practiseable habit. This investment in "
            "structural clarity, combined with your natural relational strength, will make you "
            "exceptional at holding teams together while also moving them forward."
        ),
        "leadership_cta": (
            "Share this profile with your leader and schedule a conversation within 7 days. "
            "Over the next 30 days, plan to: 1) Identify two team resets or moments of "
            "breakdown where you will deliberately pause to name the exact misalignment before "
            "attempting the reset. Practice the Clarity Loop in your moments of influence. "
            "2) Ask your leader to observe these moments and give you feedback on whether "
            "people understood what they were aligning to and whether the direction became clear. "
            "3) Track after each reset whether people knew what they were re-aligning to and "
            "whether the direction was clear. Your goal is to blend your natural warmth with "
            "structural precision, making your resets count for both cohesion and performance."
        ),
        "framework_rows": [
            ("Clarity Loop",        "Primary",  "Precision in communication makes your resets land with direction."),
            ("Decision Engine",     "Primary",  "Structured calls will compound your natural recovery instincts."),
            ("Collaboration Reset", "Continue", "Your natural strength. Add language and structure to amplify it."),
        ],
    },

    # ── The Ember ───────────────────────────────────────────────────────────────
    "ember": {
        "number": "ARCHETYPE 6",
        "name":   "The Ember",
        "subtitle": "Not out. Not yet lit. Today was the ignition.",
        "light":  "#F3F4F6", "accent": "#374151", "dark": "#111827",
        "pill_bg": "#4B5563",
        "comm": 38, "decision": 42, "collab": 35,
        "hook": (
            "Today was hard. Every simulation surfaced something uncomfortable. That discomfort "
            "is the most honest and useful signal in this entire report because it means the "
            "workshop worked exactly as designed."
        ),
        "strength_paras": [
            "You showed up. You stayed in it. Somewhere in today's sessions, in a moment of "
            "frustration, confusion, or a game that didn't go the way you expected, you "
            "noticed something true about yourself. That noticing is the beginning of everything "
            "this workshop is designed to build. The willingness to sit with honest feedback "
            "rather than deflect it is not a small thing. Most people never actually do it.",

            "This matters more than it sounds. The most significant development barrier any "
            "professional faces is rarely skill. It is self-awareness. You can teach someone "
            "communication frameworks, decision tools, and collaboration techniques. You cannot "
            "teach the willingness to see clearly when the feedback is uncomfortable. That "
            "willingness has to come from within, and you demonstrated it today.",

            "In the workforce, this capacity for honest self-assessment represents a raw growth "
            "potential that polished-but-fixed professionals often lack. Someone who can look "
            "at precise feedback and sit with it, rather than reframe it, explain it away, or "
            "get defensive, is someone who can actually change. Every other archetype in this "
            "framework is built on skills that can be developed through deliberate practice. "
            "None of them require more than what you showed up with today.",
        ],
        "gap_paras": [
            "All three dimensions are development areas right now. Communication, Decision "
            "Making, and Collaboration are each below the threshold that indicates reliable, "
            "consistent performance under pressure. This is not a verdict. It is a starting "
            "point, and honest starting points are genuinely rare. Most professionals go years "
            "without receiving feedback this specific about where they actually are.",

            "The behavioral root of today's results is likely not a lack of capability. It is "
            "a lack of practised frameworks. Under pressure, people default to their most "
            "practised behaviours. If those behaviours haven't yet been built in communication, "
            "decision-making, or team collaboration, the simulation surfaces the gaps quickly. "
            "The good news: all three dimensions are learnable. The behaviours that produce "
            "high scores in this framework are specific, practiceable, and teachable.",

            "In the workplace, these three gaps compound. Low communication precision creates "
            "misalignment. Misalignment under low decision confidence creates stalled execution. "
            "Stalled execution under weak collaboration tools creates team breakdown. The "
            "pattern is a cascade and the upstream intervention, communication, addresses "
            "all three. This is why the Clarity Loop is your starting point, not because it "
            "is the most important framework in isolation, but because it is the one that "
            "unlocks progress in the others.",
        ],
        "steps": [
            ("Build one communication habit this week",
             "Before you finish any conversation at work where something important was agreed, "
             "say: 'I just want to make sure I am understanding correctly.' Then go on to "
             "reiterate your understanding of the instructions and requirements. This gives you "
             "an opportunity to confirm alignment and close the clarity loop. This single "
             "question builds the Clarity Loop in both directions and practices the precision "
             "of checking rather than assuming. Do it every day. The compound effect over 30 days "
             "is significant."),
            ("Make one decision per day without seeking consensus first",
             "It doesn't need to be significant. Meeting location, approach to a task, how "
             "to structure an email. Make the call and execute it. The goal is repetition, "
             "building the pathway of decision, commitment, and action. Decisiveness is a "
             "muscle. Small daily practice builds it faster than infrequent high-stakes "
             "attempts. Exercise your brain and resist becoming reliant on AI to make your "
             "decisions. Although AI tools are quick and convenient, building your own "
             "decision-making muscle requires real mental effort. The pathway from thought to "
             "commitment to action needs to be yours."),
            ("In your next team breakdown, name what you see",
             "You don't need to have the solution. You just need to name the problem: 'I "
             "think we have lost alignment. Can we pause?' That single sentence is a "
             "Collaboration Reset, and it is available to you right now, with the skills "
             "you already have. You do not need to wait to be more developed to start."),
        ],
        "recommendations": (
            "The most important thing you can do with this report is not read it once and "
            "file it. Come back to it in 30 days and ask honestly: which of these three "
            "dimensions have I actually practised? The gap between awareness and action is "
            "where development is won or lost. You have the awareness now. The work is in "
            "finding low-stakes opportunities every day to practise the specific behaviours "
            "in this report, not waiting for the perfect moment, but building the reflex "
            "through consistent, small repetition. Every time you practise the Clarity Loop, "
            "you are rewiring your default response. Progress will be incremental but real."
        ),
        "leadership_cta": (
            "Schedule a conversation with your leader or manager within 7 days. This profile "
            "benefits significantly from supported follow-up. Over the next 30 days, plan to: "
            "1) Identify three specific moments each week in your real work where you can "
            "practise one of these three behaviours with support. Ask your leader to help you "
            "identify these opportunities in advance so you're not starting from zero. "
            "2) Request honest, specific observations after each attempt, not general "
            "encouragement, but real feedback on what you did well and where the next step is. "
            "3) Track your progress by documenting one win each week where you practised a skill "
            "deliberately. Your goal is to build evidence that change is possible, which fuels "
            "continued effort. Supported practice in real work contexts will accelerate your "
            "development faster than anything else available to you."
        ),
        "framework_rows": [
            ("Clarity Loop",        "Primary",  "Start here. This is the foundation that unlocks the others."),
            ("Decision Engine",     "Continue", "Build structure gradually. Small daily calls compound fast."),
            ("Collaboration Reset", "Continue", "Recovery instincts will emerge as communication strengthens."),
        ],
    },
}

# ─── Utility helpers ───────────────────────────────────────────────────────────
def band_label(score):
    if score >= 80: return "Strong",     BAND_STRONG
    if score >= 60: return "Developing", BAND_DEVELOPING
    if score >= 40: return "Emerging",   BAND_EMERGING
    return "Foundation", BAND_FOUNDATION

def rr(c, x, y, w, h, r, fill, stroke=None, sw=0.5):
    """Draw a rounded rectangle."""
    c.saveState()
    c.setFillColor(fill)
    if stroke:
        c.setStrokeColor(stroke)
        c.setLineWidth(sw)
        c.roundRect(x, y, w, h, r, fill=1, stroke=1)
    else:
        c.setStrokeColor(fill)
        c.roundRect(x, y, w, h, r, fill=1, stroke=0)
    c.restoreState()

def draw_divider(c, x, y, w, color=None, lw=0.4):
    c.saveState()
    c.setStrokeColor(color or SYP_DIVIDER)
    c.setLineWidth(lw)
    c.line(x, y, x + w, y)
    c.restoreState()

def draw_circular_progress(c, cx, cy, radius, score, accent_hex):
    track_col  = colors.HexColor("#E2E8F0")
    fill_col   = hc(accent_hex)
    track_w    = 5.5
    fill_w     = 6.5

    c.saveState()
    # Track circle
    c.setStrokeColor(track_col)
    c.setLineWidth(track_w)
    c.circle(cx, cy, radius, fill=0, stroke=1)

    # Progress arc
    pct   = max(0, min(score, 100)) / 100.0
    steps = max(int(pct * 360 * 1.5), 4)
    sweep = pct * 360
    c.setStrokeColor(fill_col)
    c.setLineWidth(fill_w)
    c.setLineCap(1)
    prev_x = cx + radius * math.cos(math.radians(90))
    prev_y = cy + radius * math.sin(math.radians(90))
    for i in range(1, steps + 1):
        a  = 90 - (sweep * i / steps)
        nx = cx + radius * math.cos(math.radians(a))
        ny = cy + radius * math.sin(math.radians(a))
        p  = c.beginPath()
        p.moveTo(prev_x, prev_y)
        p.lineTo(nx, ny)
        c.drawPath(p, stroke=1, fill=0)
        prev_x, prev_y = nx, ny

    # Score number
    txt = str(score)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(hc(accent_hex))
    tw = c.stringWidth(txt, "Helvetica-Bold", 12)
    c.drawString(cx - tw / 2, cy - 4.5, txt)
    c.restoreState()

def wrap_and_draw(c, text, x, y, width, font, size, color, leading=None):
    """Wrap and draw text; return y below last line."""
    if leading is None:
        leading = size * 1.48
    c.setFont(font, size)
    words  = text.split()
    lines  = []
    cur    = ""
    for w in words:
        test = (cur + " " + w).strip()
        if c.stringWidth(test, font, size) <= width:
            cur = test
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    c.saveState()
    c.setFillColor(color)
    for line in lines:
        c.setFont(font, size)
        c.drawString(x, y, line)
        y -= leading
    c.restoreState()
    return y

def text_block_height(c, text, width, font, size, leading=None):
    """Estimate height of wrapped text block."""
    if leading is None:
        leading = size * 1.48
    c.setFont(font, size)
    words = text.split()
    lines = 0; cur = ""
    for w in words:
        test = (cur + " " + w).strip()
        if c.stringWidth(test, font, size) <= width:
            cur = test
        else:
            lines += 1; cur = w
    if cur: lines += 1
    return lines * leading

def section_header(c, label, x, y, accent_hex):
    """Draw a pill + uppercase label. Returns y below."""
    PILL_W = 4
    PILL_H = 10
    c.saveState()
    c.setFillColor(hc(accent_hex))
    c.rect(x, y - PILL_H + 2, PILL_W, PILL_H, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(SYP_NEAR_BLACK)
    c.drawString(x + PILL_W + 6, y, label)
    c.restoreState()
    return y - 14

def draw_paragraphs(c, paras, x, y, width, font, size, color,
                    leading=None, para_gap=5):
    """Draw a list of paragraph strings. Returns final y."""
    for i, para in enumerate(paras):
        y = wrap_and_draw(c, para, x, y, width, font, size, color, leading)
        if i < len(paras) - 1:
            y -= para_gap
    return y

# ─── Header / footer ───────────────────────────────────────────────────────────
def draw_header_p1(c, arch):
    """Full page-1 header."""
    acc   = arch["accent"]
    BOTTOM = PH - HEADER_H

    # Dark Blue band
    c.saveState()
    c.setFillColor(SYP_DARK_BLUE)
    c.rect(0, BOTTOM, PW, HEADER_H, fill=1, stroke=0)

    # Left accent bar
    c.setFillColor(hc(acc))
    c.rect(0, BOTTOM, 4 * mm, HEADER_H, fill=1, stroke=0)
    c.restoreState()

    # Logo — top right, with top padding
    logo_w = 36 * mm; logo_h = 13 * mm
    logo_x = PW - MR - logo_w
    logo_y = PH - 12 * mm - logo_h
    try:
        img = ImageReader(LOGO_PATH)
        c.drawImage(img, logo_x, logo_y, width=logo_w, height=logo_h,
                    mask="auto", preserveAspectRatio=True)
    except Exception:
        pass

    # Archetype pill
    PX = ML + 6 * mm
    pill_top = PH - 12 * mm
    pill_h = 5 * mm; pill_w = 34 * mm
    rr(c, PX, pill_top - pill_h, pill_w, pill_h, 1.5 * mm, hc(arch["pill_bg"]))
    c.saveState()
    c.setFont("Helvetica-Bold", 6.5)
    c.setFillColor(SYP_WHITE)
    lbl = arch["number"]
    lw  = c.stringWidth(lbl, "Helvetica-Bold", 6.5)
    c.drawString(PX + (pill_w - lw) / 2, pill_top - pill_h + (pill_h - 6.5) / 2 + 1, lbl)
    c.restoreState()

    # Archetype name
    name_y = pill_top - pill_h - 4 * mm
    c.saveState()
    c.setFont("Helvetica-Bold", 25)
    c.setFillColor(SYP_WHITE)
    c.drawString(PX, name_y - 18, arch["name"].upper())
    c.restoreState()

    # Subtitle — white for legibility on dark background
    sub_y = name_y - 18 - 7 * mm
    c.saveState()
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(colors.HexColor("#CBD5E1"))   # light slate — visible but softer
    c.drawString(PX, sub_y, arch["subtitle"])
    c.restoreState()

    # Hairline divider
    div_y = sub_y - 5 * mm
    c.saveState()
    c.setStrokeColor(colors.HexColor("#334155"))
    c.setLineWidth(0.4)
    c.line(PX, div_y, PW - MR, div_y)
    c.restoreState()

    # Meta row
    meta_y = div_y - 4.5 * mm
    c.saveState()
    c.setFont("Helvetica", 7.5)
    c.setFillColor(colors.HexColor("#94A3B8"))
    meta_label = arch.get("_meta_line", "Participant  ·  Company  ·  April 2026")
    c.drawString(PX, meta_y, meta_label)
    c.setFont("Helvetica-Bold", 7)
    c.drawRightString(PW - MR, meta_y, "TEAM EFFECTIVENESS LAB")
    c.restoreState()

def draw_header_p2(c, arch):
    """Slim page-2 header."""
    BOTTOM = PH - HDR2_H
    c.saveState()
    c.setFillColor(SYP_DARK_BLUE)
    c.rect(0, BOTTOM, PW, HDR2_H, fill=1, stroke=0)
    c.setFillColor(hc(arch["accent"]))
    c.rect(0, BOTTOM, 4 * mm, HDR2_H, fill=1, stroke=0)

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(SYP_WHITE)
    label = f"{arch['name'].upper()}  ·  ACTION PLAN"
    c.drawString(ML + 6 * mm, BOTTOM + HDR2_H / 2 - 4, label)

    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#94A3B8"))
    c.drawRightString(PW - MR, BOTTOM + HDR2_H / 2 - 4, "Page 2 of 2")
    c.restoreState()

def draw_footer(c):
    c.saveState()
    c.setFillColor(SYP_DARK_BLUE)
    c.rect(0, 0, PW, FOOTER_H, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(SYP_WHITE)
    c.drawString(ML, FOOTER_H / 2 - 3, "SAIGON YOUNG PROFESSIONALS")
    c.setFont("Helvetica", 7)
    c.drawRightString(PW - MR, FOOTER_H / 2 - 3, "www.saigonyoungprofessionals.com")
    c.restoreState()

# ─── Score section ─────────────────────────────────────────────────────────────
def draw_scores(c, arch, y):
    """Draw 3-column score cards. Returns y below."""
    acc       = arch["accent"]
    scores    = [arch["comm"], arch["decision"], arch["collab"]]
    labels    = ["Communication", "Decision Making", "Collaboration"]

    circle_r  = 10.5 * mm
    col_w     = CW / 3
    card_pad  = 3 * mm

    label_fs  = 7.5
    label_h   = 11
    gap1      = 10       # label → circle top (IMPROVED: was 3, now 10)
    gap2      = 8        # circle bottom → pill top (IMPROVED: was 4, now 8 to compensate for removed threshold hint)
    pill_h    = 10
    gap3      = 3        # pill → arrow
    arrow_h   = 8
    card_h    = (card_pad + label_h + gap1 + circle_r * 2
                 + gap2 + pill_h + gap3 + arrow_h + card_pad)

    for i, (lbl, score) in enumerate(zip(labels, scores)):
        cx      = ML + col_w * i + col_w / 2
        card_x  = ML + col_w * i + 2.5
        card_w  = col_w - 5
        is_high = score >= 60
        blbl, bcol = band_label(score)
        card_bg = BAND_HIGH_BG if is_high else BAND_LOW_BG
        border_col = colors.HexColor("#D1FAE5") if is_high else colors.HexColor("#FEE2E2")

        rr(c, card_x, y - card_h, card_w, card_h, 3 * mm, card_bg,
           stroke=border_col, sw=0.8)

        # Label at top of card
        lb_y = y - card_pad - label_h + 2
        c.saveState()
        c.setFont("Helvetica-Bold", label_fs)
        c.setFillColor(SYP_NEAR_BLACK)
        lw2 = c.stringWidth(lbl, "Helvetica-Bold", label_fs)
        c.drawString(cx - lw2 / 2, lb_y, lbl)
        c.restoreState()

        # Circle
        circle_y = lb_y - gap1 - circle_r
        draw_circular_progress(c, cx, circle_y, circle_r, score, acc)

        # Band pill
        pl_w = c.stringWidth(blbl, "Helvetica-Bold", 7) + 10
        pl_x = cx - pl_w / 2
        pl_y = circle_y - circle_r - gap2 - pill_h - 3
        rr(c, pl_x, pl_y, pl_w, pill_h, 1.5 * mm, bcol)
        c.saveState()
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(SYP_WHITE)
        bw = c.stringWidth(blbl, "Helvetica-Bold", 7)
        c.drawString(cx - bw / 2, pl_y + (pill_h - 7) / 2 + 1, blbl)
        c.restoreState()

        # Arrow
        arrow   = "▲  HIGH" if is_high else "▼  LOW"
        arr_col = BAND_STRONG if is_high else BAND_FOUNDATION
        c.saveState()
        c.setFont("Helvetica-Bold", 6.5)
        c.setFillColor(arr_col)
        aw = c.stringWidth(arrow, "Helvetica-Bold", 6.5)
        c.drawString(cx - aw / 2, pl_y - gap3 - arrow_h + 1, arrow)
        c.restoreState()

    return y - card_h - 5 * mm

# ─── Page 1 ────────────────────────────────────────────────────────────────────
def draw_page1(c, arch):
    draw_header_p1(c, arch)
    draw_footer(c)

    acc  = arch["accent"]
    x0   = ML
    y    = BODY_TOP_1

    # Profile note
    c.saveState()
    c.setFont("Helvetica-Oblique", 7.5)
    c.setFillColor(SYP_MID_GREY)
    c.drawString(x0, y,
        "This profile reflects how you showed up under pressure today, not a fixed trait or permanent label.")
    c.restoreState()
    y -= 5 * mm

    # ── Hook box ──────────────────────────────────────────────────────────────
    hook_pad  = 4 * mm
    hook_tw   = CW - hook_pad * 2 - 5 * mm
    hook_th   = text_block_height(c, arch["hook"], hook_tw, "Helvetica-Oblique", 9) + hook_pad * 2 + 2
    rr(c, x0, y - hook_th, CW, hook_th, 3 * mm,
       hc(arch["light"]), stroke=hc(arch["accent"]), sw=0.8)
    # Left accent rule inside box
    c.saveState()
    c.setFillColor(hc(acc))
    c.rect(x0 + 3, y - hook_th + 5, 3, hook_th - 10, fill=1, stroke=0)
    c.restoreState()
    wrap_and_draw(c, arch["hook"],
                  x0 + hook_pad + 4, y - hook_pad - 9,
                  hook_tw, "Helvetica-Oblique", 9, SYP_NEAR_BLACK, leading=13.5)
    y -= hook_th + 4 * mm

    # ── Mirror copy (motivational introduction) ────────────────────────────────
    mirror_text = (
        "The first step, and often the hardest, is taking a good long hard look in the mirror. "
        "Today you did exactly that. We tested and exposed your abilities to communicate, make "
        "decisions, and collaborate with your teammates. We hope this experience revealed something "
        "eye-opening to you."
    )
    mirror_pad = 2 * mm
    mirror_tw = CW - mirror_pad * 2
    mirror_th = text_block_height(c, mirror_text, mirror_tw, "Helvetica-Oblique", 8) + mirror_pad * 2
    c.saveState()
    wrap_and_draw(c, mirror_text,
                  x0 + mirror_pad, y - mirror_pad,
                  mirror_tw, "Helvetica-Oblique", 8, SYP_MID_GREY, leading=11.5)
    c.restoreState()
    y -= mirror_th + 2 * mm

    # ── Scores ────────────────────────────────────────────────────────────────
    y = draw_scores(c, arch, y)

    # ── Thin rule ─────────────────────────────────────────────────────────────
    draw_divider(c, x0, y, CW)
    y -= 4 * mm

    # ── Strength ──────────────────────────────────────────────────────────────
    y = section_header(c, "STRENGTH", x0, y, acc)
    y -= 1 * mm
    y = draw_paragraphs(c, arch["strength_paras"], x0 + 10, y, CW - 10,
                         "Helvetica", 8, SYP_NEAR_BLACK,
                         leading=12, para_gap=5)
    y -= 3 * mm

    # ── Gap ───────────────────────────────────────────────────────────────────
    y = section_header(c, "GAP", x0, y, acc)
    y -= 1 * mm
    draw_paragraphs(c, arch["gap_paras"], x0 + 10, y, CW - 10,
                     "Helvetica", 8, SYP_NEAR_BLACK,
                     leading=12, para_gap=5)

# ─── Page 2 ────────────────────────────────────────────────────────────────────
def draw_step(c, num_str, title, body, x, y, width, accent_hex):
    """Draw a numbered step block. Returns y below."""
    CIRCLE_R = 8
    CIRCLE_CX = x + CIRCLE_R
    CIRCLE_CY = y - CIRCLE_R - 1

    # Number circle
    rr(c, CIRCLE_CX - CIRCLE_R, CIRCLE_CY - CIRCLE_R,
       CIRCLE_R * 2, CIRCLE_R * 2, CIRCLE_R,
       hc(accent_hex))
    c.saveState()
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(SYP_WHITE)
    nw = c.stringWidth(num_str, "Helvetica-Bold", 8)
    c.drawString(CIRCLE_CX - nw / 2, CIRCLE_CY - 3, num_str)
    c.restoreState()

    # Step title
    text_x   = x + CIRCLE_R * 2 + 6
    text_w   = width - CIRCLE_R * 2 - 6
    title_y  = y - 3
    c.saveState()
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(hc(accent_hex))
    c.drawString(text_x, title_y, title)
    c.restoreState()

    # Body text
    body_y = title_y - 3.5 * mm
    end_y  = wrap_and_draw(c, body, text_x, body_y, text_w,
                            "Helvetica", 8.5, SYP_NEAR_BLACK, leading=13)
    return end_y - 5 * mm

def draw_callout_box(c, label, text, x, y, width, accent_hex, light_hex):
    """Tinted callout box with label pill at top. Returns y below."""
    pad      = 4 * mm
    lbl_h    = 13
    lbl_gap  = 4
    text_w   = width - pad * 2 - 3
    text_h   = text_block_height(c, text, text_w, "Helvetica", 8.5, leading=13)
    th       = pad + lbl_h + lbl_gap + text_h + pad

    # Box
    rr(c, x, y - th, width, th, 3 * mm,
       hc(light_hex), stroke=hc(accent_hex), sw=0.6)

    # Label pill — near TOP of box (y - pad is near top edge)
    lbl_w = c.stringWidth(label, "Helvetica-Bold", 7) + 10
    pill_y = y - pad - lbl_h        # bottom of pill
    rr(c, x + pad, pill_y, lbl_w, lbl_h, 2 * mm, hc(accent_hex))
    c.saveState()
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(SYP_WHITE)
    c.drawString(x + pad + 5, pill_y + (lbl_h - 7) / 2 + 1, label)
    c.restoreState()

    # Body text below pill — 8pt gap after pill
    text_start_y = pill_y - 8
    wrap_and_draw(c, text, x + pad + 3, text_start_y,
                  text_w, "Helvetica", 8.5, SYP_NEAR_BLACK, leading=13)
    return y - th - 4 * mm

def draw_framework_table(c, arch, x, y, width):
    """Draw framework priority table. Returns y below."""
    acc       = arch["accent"]
    col_ws    = [width * 0.32, width * 0.16, width * 0.52]
    rows      = arch["framework_rows"]
    row_h     = 9.5 * mm
    hdr_h     = 12

    # Table header
    c.saveState()
    c.setFillColor(SYP_DARK_BLUE)
    c.rect(x, y - hdr_h, width, hdr_h + 2, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(SYP_WHITE)
    cx2 = x + 6
    for i, lbl in enumerate(["Framework", "Priority", "Why"]):
        c.drawString(cx2, y - hdr_h + 3, lbl)
        cx2 += col_ws[i]
    c.restoreState()
    y -= hdr_h + 2

    for ri, row in enumerate(rows):
        is_primary = row[1] == "Primary"
        bg = hc(arch["light"]) if is_primary else SYP_LIGHT_GREY
        border = hc(arch["accent"]) if is_primary else SYP_DIVIDER
        c.saveState()
        c.setFillColor(bg)
        c.rect(x, y - row_h, width, row_h, fill=1, stroke=0)
        draw_divider(c, x, y - row_h, width, border, 0.4)

        row_mid = y - row_h / 2
        cx2 = x + 6
        # Framework name
        c.setFont("Helvetica-Bold" if is_primary else "Helvetica", 8)
        c.setFillColor(hc(arch["dark"]) if is_primary else SYP_NEAR_BLACK)
        c.drawString(cx2, row_mid - 4, row[0])
        cx2 += col_ws[0]

        # Priority — pill style
        if is_primary:
            pw2 = c.stringWidth(row[1], "Helvetica-Bold", 7) + 8
            rr(c, cx2, row_mid - 7, pw2, 11, 2 * mm, hc(acc))
            c.setFont("Helvetica-Bold", 7)
            c.setFillColor(SYP_WHITE)
            c.drawString(cx2 + 4, row_mid - 3.5, row[1])
        else:
            c.setFont("Helvetica", 7.5)
            c.setFillColor(SYP_MID_GREY)
            c.drawString(cx2, row_mid - 4, row[1])
        cx2 += col_ws[1]

        # Why
        c.setFont("Helvetica", 7.5)
        c.setFillColor(SYP_NEAR_BLACK)
        c.drawString(cx2, row_mid - 4, row[2])
        c.restoreState()
        y -= row_h

    return y - 4 * mm

def draw_page2(c, arch):
    draw_header_p2(c, arch)
    draw_footer(c)

    acc  = arch["accent"]
    lt   = arch["light"]
    x0   = ML
    y    = BODY_TOP_2

    # ── Next Steps ────────────────────────────────────────────────────────────
    y = section_header(c, "NEXT STEPS", x0, y, acc)
    y -= 2 * mm

    for i, (title, body) in enumerate(arch["steps"]):
        y = draw_step(c, str(i + 1), title, body, x0, y, CW, acc)

    draw_divider(c, x0, y, CW)
    y -= 4 * mm

    # ── Recommendations ───────────────────────────────────────────────────────
    y = draw_callout_box(c, "RECOMMENDATIONS", arch["recommendations"],
                          x0, y, CW, acc, lt)

    # ── Leadership alignment ──────────────────────────────────────────────────
    y = draw_callout_box(c, "ALIGN WITH YOUR LEADER", arch["leadership_cta"],
                          x0, y, CW, "#0D2A66", "#EFF6FF")

    draw_divider(c, x0, y, CW)
    y -= 4 * mm

    # ── Framework table ───────────────────────────────────────────────────────
    y = section_header(c, "FRAMEWORK PRIORITY", x0, y, acc)
    y -= 1 * mm
    draw_framework_table(c, arch, x0, y, CW)

# ─── Main entry point ──────────────────────────────────────────────────────────
def generate_profile(archetype_key, output_dir=".",
                     participant_name=None, company=None,
                     comm_score=None, decision_score=None, collab_score=None,
                     output_filename=None):
    """Generate a personalised PDF profile.

    Parameters
    ----------
    archetype_key : str
        One of: operator, architect, navigator, signal, anchor, ember
    output_dir : str
        Directory to write the PDF into.
    participant_name : str, optional
        Participant's full name (default: template placeholder).
    company : str, optional
        Participant's company name (default: template placeholder).
    comm_score, decision_score, collab_score : int, optional
        Actual scores 0-100. If omitted, archetype defaults are used.
    output_filename : str, optional
        Custom filename for the PDF. If omitted, uses default naming.

    Returns
    -------
    str – path to the generated PDF.
    """
    import copy, datetime
    arch = copy.deepcopy(ARCHETYPES[archetype_key])

    # Override scores if provided
    if comm_score is not None:
        arch["comm"] = int(comm_score)
    if decision_score is not None:
        arch["decision"] = int(decision_score)
    if collab_score is not None:
        arch["collab"] = int(collab_score)

    # Build meta line for header
    name_part = participant_name or "Participant"
    company_part = company or "Company"
    month_year = datetime.datetime.now().strftime("%B %Y")
    arch["_meta_line"] = f"{name_part}  ·  {company_part}  ·  {month_year}"

    # Determine output path
    if output_filename:
        out = os.path.join(output_dir, output_filename)
    else:
        out = os.path.join(output_dir,
                           f"SYP_{arch['name'].replace(' ','_')}_Profile.pdf")

    c = rl_canvas.Canvas(out, pagesize=A4)
    c.setTitle(f"SYP Team Effectiveness Lab — {arch['name']}")

    # Page 1
    draw_page1(c, arch)
    c.showPage()

    # Page 2
    draw_page2(c, arch)
    c.save()
    return out


def generate_profile_bytes(archetype_key,
                           participant_name=None, company=None,
                           comm_score=None, decision_score=None,
                           collab_score=None):
    """Generate a PDF and return it as bytes (for API use)."""
    import copy, datetime, io
    arch = copy.deepcopy(ARCHETYPES[archetype_key])

    if comm_score is not None:
        arch["comm"] = int(comm_score)
    if decision_score is not None:
        arch["decision"] = int(decision_score)
    if collab_score is not None:
        arch["collab"] = int(collab_score)

    name_part = participant_name or "Participant"
    company_part = company or "Company"
    month_year = datetime.datetime.now().strftime("%B %Y")
    arch["_meta_line"] = f"{name_part}  ·  {company_part}  ·  {month_year}"

    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)
    c.setTitle(f"SYP Team Effectiveness Lab — {arch['name']}")

    draw_page1(c, arch)
    c.showPage()
    draw_page2(c, arch)
    c.save()

    buf.seek(0)
    return buf.read()


if __name__ == "__main__":
    OUTPUT = os.environ.get("OUTPUT_DIR", SCRIPT_DIR)
    keys = list(ARCHETYPES.keys()) if len(sys.argv) < 2 else sys.argv[1:]
    for k in keys:
        if k not in ARCHETYPES:
            print(f"Unknown archetype: {k}"); continue
        path = generate_profile(k, output_dir=OUTPUT)
        print(f"✓  {path}")
