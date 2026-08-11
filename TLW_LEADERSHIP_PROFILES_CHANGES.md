# TLW Leadership Archetype Profiles: what changed and how to deploy

This adds the six Leadership Workshop (TLW) archetype profile pages to the
`syp-profile-api` app, alongside the existing TEW archetypes. Nothing about the
TEW path changes: every edit is additive and TEW keeps its exact behaviour.

## The six archetypes

Keystone, Lighthouse, Pathfinder, Diplomat, Vanguard, Cornerstone. They map to
the aggregation router you already validated (min-all-80 to Keystone, dimension
dominance to Lighthouse / Pathfinder / Diplomat, and so on).

## The three score-band labels

As requested, the three dimension labels read **Leadership**, **Change
Management**, and **Conflict Management** everywhere they appear (the one-page
snapshot donuts, the "How you scored" cards, "What stood out", and "Best
practices").

Under the hood the three score slots are reused by position, so the API contract
and the Make mapping stay identical to TEW:

| Sheet / API field | TLW dimension       |
|-------------------|---------------------|
| `comm_score`      | Leadership          |
| `decision_score`  | Change Management   |
| `collab_score`    | Conflict Management |

So the delivery scenario sends `I_score` as `comm_score`, `Ch_score` as
`decision_score`, and `Cf_score` as `collab_score`, exactly as the TEW delivery
scenario does.

## Files in this package

Extract at the repo root; paths line up with the existing layout.

Changed (four Python modules, additive only):
- `api_server.py` : six aliases added to `ARCHETYPE_ALIASES`.
- `inject_v2.py`  : six entries in `ARCH_FILES`, a `LEAD_ARCH` set + `_family()`,
  and the family threaded through the render helpers.
- `dimension_content.py` : leadership `BULLETS_LEAD` / `STRONG_LEAD`; `bullets()`
  and `strong_block()` take an optional `family` argument (defaults to `tew`).
- `narrative_v2.py` : leadership copy dicts + a `_pack(family)` selector; the
  render functions take an optional `family` argument (defaults to `tew`).

New template files:
- `templates_v2/Keystone.html`
- `templates_v2/Lighthouse.html`
- `templates_v2/Pathfinder.html`
- `templates_v2/Diplomat.html`
- `templates_v2/Vanguard.html`
- `templates_v2/Cornerstone.html`

New dev tool (not required at runtime, kept for regeneration):
- `build_leadership_templates.py` : rebuilds the six templates from
  `templates_v2/Navigator.html`. Re-run it whenever the base template changes.

## What the templates bake in vs render at request time

Baked into each template file (static, per family or per archetype):
- the three dimension labels renamed to the leadership names,
- the workshop label set to "The Leadership Workshop",
- the archetype name + tagline,
- the "Best practices" section rewritten for the leadership skills,
- the Working Style block removed, since TLW does not capture working-style
  answers. (The one-page snapshot, the score cards, and every other section are
  untouched, so there is no gap where it used to be.)

Rendered at request time by the shared code (score-driven, leadership-aware):
- the score-card bullets and "what strong looks like / why / next step" blocks,
- the "What stood out" strength and growth cards,
- "Your next three moves" and its support column,
- the one-page snapshot summary paragraph and headlines.

## Deploy

1. Extract this package at the repo root (overwriting the four `.py` files and
   adding the six templates + the builder).
2. Commit and push to `main`. Railway builds from the Dockerfile, which already
   ships `templates_v2/` and the `.py` modules, so no Dockerfile change is
   needed.
3. Smoke test after deploy:
   `POST /generate-hosted` with `{"archetype":"diplomat", "participant_name":
   "Test", "comm_score":55, "decision_score":58, "collab_score":84, ...}` and
   open the returned URL. You should see "The Diplomat", the three leadership
   labels, and Conflict Management as the strength.

## A note on em dashes

None of the leadership copy uses em dashes. The em dashes that remain in the
templates are all pre-existing base-template artifacts (developer CSS comments
and the brand alt text "The Performance Lens by Saigon Young Professionals"),
carried over unchanged from your TEW Navigator template so TLW stays visually
identical to TEW. Say the word if you want the brand alt text adjusted; I left
it matching TEW on purpose.
