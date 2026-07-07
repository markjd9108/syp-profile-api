# COMPOSITION SPEC — Leadership Insight Report
**The Performance Lens · Team Effectiveness Workshop**
**For: Cowork wiring build. This document governs every COMPOSED field in the Data Contract. The composition API generates these fields fresh for each report from the team's actual data. Nothing here is optional; a composed output that violates any rule in Section 1 or 2 is rejected and regenerated.**

---

## 1. Global rules (apply to every composed field)

**Traceability.** Every name, count, score, and archetype in composed copy must exist in the payload. No invented people, no rounded-differently numbers, no interpolated scores. If a sentence cites "92", a 92 exists in the member data.

**The six archetypes only.** Summit, Navigator, Signal, Anchor, Compass, Relay. No other archetype-style label may ever be introduced (no "the Driver", "the Challenger", or similar coinages).

**Banned outright:** "actually" · "rather than" · "instead of" · the "X, not Y" contrast construction · em dashes (use commas, full stops, or colons) · "manager" (always "leader") · "diagnostic" · "challenges" as a noun (use "problems") · "transform / unlock / empower / synergy / game-changing" · idioms and figures of speech (ESL-accessible plain English only) · scripted dialogue in quotation marks in any action or theme.

**Register.** Plain, spoken, warm, precise. Short sentences. British English spelling to match the locked template copy (behaviour, normalised, recognise). Describe what the data shows; never speculate about motives, personality, or life outside the exercises. No outcome promises anywhere: observables describe visible behaviour change, never score movement.

**No gendered pronouns.** Composed copy never uses he, she, him, her, his, or hers. Refer to members by name, or by they, them, their. Never infer gender from a name. Note that the approved sample copy in the template predates this rule and uses gendered pronouns; do not imitate it on this one dimension. Everything else about its register remains the reference.

**Score framing.** Scores are behaviour under structured pressure, one data point. Composed copy may reference the 60 threshold and the bands' logic but never labels a person with a band name (bands are participant-facing).

**Snapshot caveat.** Appears once in the template (page 5, locked). Composed copy never restates it.

## 2. Per-block specification

Word limits are hard maximums. Design containers are tested at 60 to 100 percent of each limit; under-filling is fine, overfilling is rejected.

### leaderVerdict · 60 words
Reads: leaderName, team averages, priority dimension, member spread. Must cover: overall position in one sentence, the leading strength, the priority gap, the shape of the work ahead. Addressed to the leader by first name, once. Register example (approved): "Your team decides well and pulls together when the work gets hard, Mark. The strain is communication: at 50 it sits below the working threshold and splits widely across the three of you."

### headline · 25 words
Reads: avgOverall, leading dimension, priority dimension. One sentence: team average, leader dimension with score, priority dimension with score, and the gap between them when it is the story.

### priorityRead · 50 words
Reads: priority dimension member scores. Must cover: the average, the spread (low and high), and what the spread means in working terms. If the spread is narrow, say the level is shared instead of inventing a split.

### firstMove · 45 words
Reads: priority dimension, team structure. One concrete structural action the leader can run this week without a facilitator. Specific enough to start, never a script.

### patternLabel · 6 words · patternTitle · 5 words
The label is a small-caps kicker ("The pattern that shapes this team" is the default; vary only with reason). The title names the pattern in plain words. Approved register: "Strong hands, thin shared voice."

### definingPatternP1, definingPatternP2 · 55 words each
P1: the single most important structural fact of this team's composition, grounded in the numbers. P2: the risk that follows and one sentence of direction. Together they are the report's thesis; everything downstream must be consistent with them.

### patternCards · body 90 words each
Count set by the Data Contract card rule (every member at teamSize ≤ 4; the 3 or 4 most consequential at teamSize ≥ 5). Card name format: "{{Name}} · {{Archetype}}". Each body: what this person contributes (with their actual scores), one specific watch-out, one option the leader can act on, introduced as "One option:". Never two watch-outs, never a verdict on the person.

### missingCards · body 55 words each
Only archetypes absent from the team. Each body: the sentence pattern "No member fills the {{Archetype}} seat.", what the absence means in practice for THIS team's composition, then "One structural option:" with a rotation-or-structure move. When no archetypes are absent, this array is empty and the block is suppressed (Data Contract, Template guards).

### focusTheme · 45 words per Check-In member
Fixed shape: "The data:" plus the member's actual score pattern in one or two sentences, then "Worth exploring in a 1:1," plus the theme as a subject. The theme is a topic, never a question in quotation marks and never advice to relay verbatim. Approved register: "Worth exploring in a 1:1, the distance between how much he steadies the group and how little he voices what he is seeing."

### stretchTheme · 40 words per Stretch member
Fixed shape: "The data:" plus the strength pattern, then "One stretch:" plus a concrete way to extend them. Strength framing throughout; no deficit language for Stretch members.

### risks · 2 or 3, ordered by severity in the data
- title · 6 words. Names the risk plainly.
- statement · 40 words. What the data shows and why it matters. Numbers must trace.
- moves · 2 or 3 · 35 words each. Structural options a leader runs without a facilitator. Best practices, never step-by-step programs, never scripted lines.
- observable · 25 words. Completes the locked lead-in "You will know this is moving when". Visible behaviour only, never a score target.
Risk 01 must align with the priority dimension unless the data shows a sharper structural risk, in which case priority appears as risk 02.

### prescription · 45 words
Must name the priority dimension with its score and the matching Focused Session from the fixed mapping: Communication → Communicating with Clarity; Decision-Making → Deciding with Conviction; Collaboration → Collaborating Under Pressure. No other session may ever be prescribed. Ends before selling; the locked template copy after it handles format and boundaries.

### closingVerdict · 50 words
The bookend to leaderVerdict: what strong looks like for this team and the two or three moves that get there. Confident, specific, zero promises. Approved register: "Strong for this team looks like its shared voice catching up to its judgement and its trust."

## 3. Internal consistency requirements

- The pattern named on page 4 must be the same pattern the headline, the risks, and both verdicts describe. One thesis per report.
- The first risk's moves and the firstMove block must not contradict each other; overlap is fine, conflict is not.
- Person cards, focus themes, and stretch themes for the same member must agree on that member's story.
- If every member is Check-In, the narrative is team-level (per the locked fallback); composed copy must not single out one member as "the problem".

## 4. Generation mechanics

- One composition call per report. Input: the derived payload minus composed fields, plus this spec's rules. Output: strict JSON containing only the composed fields.
- Validate before use: JSON parses; every field present; every word limit respected; banned-language scan passes; traceability scan passes (every number and name in composed copy exists in the payload); archetype names ∈ the six.
- On any validation failure: regenerate up to twice with the failure named in the retry prompt; after three failures, halt and flag for Mark's review rather than shipping a degraded report.
- Temperature low (0.3 or under). Consistency beats flair; the register examples carry the voice.

## 5. Register sources and one known deviation

The approved register reference is the composed sample copy in the final Claude Design template (Pizzahut and Mekong Digital datasets), with one known deviation that must NOT be imitated: the Mekong Digital risk move "Work the rows, not the average" uses the banned contrast construction. The compliant form is "Work the rows before the average." Treat the corrected form as canonical.
