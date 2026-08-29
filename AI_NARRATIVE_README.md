# Grounded AI narrative for hosted profiles

Makes the profile's narrative read as an individual summary instead of templated
copy, without touching the scoring.

## What it does

Four narrative slots on the hosted profile are now written per person by Claude,
grounded in that participant's real facts only:

- the "Snapshot of the day" paragraph
- the Strength and Growth-Edge cards ("What stood out")
- the three "next moves"

Everything else stays exactly as it was: the scores, bands, donuts, archetype
routing, the score-card bullets, and the working-style section are all still
deterministic. The AI is told to use only the scores, bands, strongest and
growth-edge dimension, archetype, and preferred working styles, and to invent
nothing about what happened in the games.

## Files

- `ai_narrative.py` (new): builds the fact sheet, calls the Anthropic REST API
  (same pattern as `lead_engine` / `lir_compose`, no new dependency), parses and
  cleans the JSON, and returns the four slots. Returns `None` on any problem.
- `narrative_v2.py` (changed): the four render functions take an optional `ai`
  argument and use it when present, otherwise the existing copy. Additive.
- `inject_v2.py` (changed): calls `ai_narrative.generate(...)` once per profile
  and threads the result through. If it returns `None`, the profile renders with
  the deterministic copy exactly as before.

No change to `requirements.txt` (the REST call uses the standard library).

## It is on as soon as you deploy

`ANTHROPIC_API_KEY` is already set on Railway for the leader-report features, and
this reuses it. So after you push, new profiles get the AI narrative
automatically. Nothing else to configure.

## Safety and controls

- Fallback: if the key is missing, the call errors, or the JSON is malformed,
  `generate()` returns `None` and the profile falls back to the deterministic
  copy. A profile can never fail to render because of this.
- Turn it off without a code change: set `AI_NARRATIVE=0` in Railway. Every
  profile then uses the deterministic copy.
- Model: defaults to `claude-sonnet-4-5` (matching `lir_compose`). Override with
  `AI_NARRATIVE_MODEL` in Railway if you want a cheaper or newer model.
- Cost and latency: one short call per profile (roughly a couple of seconds and a
  few cents). Delivery is already per-person, so this adds one call per profile.

## Deploy

1. Review the change: `git diff narrative_v2.py inject_v2.py` and read
   `ai_narrative.py`.
2. Double-click `deploy_ai_narrative.command` (commits the three files and pushes
   to `main`; Railway rebuilds).
3. Regenerate a sample profile and read the Snapshot, What-stood-out and Moves.
   They should now read as a bespoke summary of that person's pattern.
