#!/bin/bash
# Deploy new dark-theme profile templates to Railway
# Double-click this file in Finder to run

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================"
echo "Deploying new profile templates"
echo "================================"
echo ""

# Remove any stale lock files
rm -f .git/index.lock .git/HEAD.lock .git/MERGE_HEAD 2>/dev/null

# Stage all new and modified files
git add generate_html_profile.py
git add generate_manager_report.py
git add templates/
git add api_server.py
git add Dockerfile
git add requirements.txt
# Working Style (V3) layer modules (referenced by api_server + Dockerfile)
git add working_style.py working_style_content.py working_style_html.py
git add lead_engine.py
# Dynamic Leadership Insight Report (team layer) — generator + narrative engine
git add generate_leader_report.py
git add team_lead_engine.py
# Reference design bundle the generator de-bundles at runtime (must ship in image)
git add "assets/Leadership Insight Report (standalone).html"
git add assets/resource_pack.pdf assets/field_guide.pdf

echo "Files staged:"
git status --short

echo ""
echo "Committing..."
git commit -m "Add dynamic Leadership Insight Report + canonical profile IDs (v2.3.1)

- Add generate_leader_report.py: dynamic team-layer report generator
  (de-bundles approved design, inlines fonts, regenerates all data regions)
- Add team_lead_engine.py: cohort narrative engine (deterministic + API)
- api_server.py: /generate-leader-report endpoint; canonical TPL-<cohort>-NN
  profile IDs across /generate + /generate-cohort; blank-workshop_code guard
- Dockerfile: ship generator, engine, and reference design bundle"

echo ""
echo "Pushing to GitHub → Railway..."
git push

echo ""
echo "================================"
echo "Done! Railway is rebuilding."
echo "Takes ~3-5 minutes to redeploy."
echo "Check: https://railway.app"
echo "================================"
echo ""
read -p "Press Enter to close..."
