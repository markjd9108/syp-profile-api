#!/usr/bin/env python3
"""
Layout check for the first live 10-member cohort (BritCham Jul 2026).
Uses the real member data + synthetic max-length composed copy (render-only;
copy content doesn't affect the page-3 table that overflowed live).
"""
import asyncio, re, subprocess
from lir_core import derive, build_payload, inject, validate_input
import lir_render

MEMBERS = [
    {"name": "Thao Uyen Nguyen", "archetype": "Anchor", "comm": 56, "dm": 48, "collab": 86},
    {"name": "Anh Hong Nguyen", "archetype": "Relay", "comm": 43, "dm": 77, "collab": 75},
    {"name": "Khanh Dinh", "archetype": "Relay", "comm": 72, "dm": 83, "collab": 60},
    {"name": "Nhu Truong", "archetype": "Relay", "comm": 68, "dm": 63, "collab": 77},
    {"name": "Linh Cao", "archetype": "Anchor", "comm": 73, "dm": 65, "collab": 93},
    {"name": "Van Ha", "archetype": "Summit", "comm": 81, "dm": 79, "collab": 86},
    {"name": "Trinh Trần", "archetype": "Relay", "comm": 78, "dm": 70, "collab": 75},
    {"name": "Khue", "archetype": "Relay", "comm": 37, "dm": 72, "collab": 69},
    {"name": "Uyen Nguyen", "archetype": "Relay", "comm": 82, "dm": 55, "collab": 92},
    {"name": "Giang Ngo", "archetype": "Signal", "comm": 63, "dm": 42, "collab": 38},
]

def words(n, seed="the team works through a shared decision frame and names owners early"):
    w = (seed.split() * 10)[:n]
    return " ".join(w).capitalize() + "."

def theme(n=35):
    return words(n)

def main():
    errs, warns = validate_input("BritCham", "9 July 2026", "Matt Ryland", MEMBERS)
    assert not errs, errs
    d = derive(MEMBERS)
    print("teamSize", d["teamSize"], "checkIn", d["checkInCount"], "stretch", d["stretchCount"],
          "priority", d["priorityDim"], d["priorityScore"])
    comp = {
        "leaderVerdict": words(52), "workingWell": theme(), "needsSupport": theme(),
        "teamRisk": theme(), "teamOpportunity": theme(), "firstMove": words(55),
        "patternLabel": "The pattern that shapes this team",
        "patternTitle": "Strength split across the room",
        "definingPatternP1": words(60), "definingPatternP2": words(45),
        "patternCards": [{"label": "The ceiling", "name": f"{m['name']} · {m['archetype']}",
                          "body": words(64)} for m in MEMBERS[:d["patternCardCount"]]],
        "missingCards": [{"name": a, "body": words(40)} for a in d["absentArchetypes"][:d["missingCardCount"]]],
        "risks": [{"title": words(4)[:-1], "statement": words(38),
                   "moves": [words(28), words(28)], "observable": words(18)[:-1]} for _ in range(2)],
        "focusThemes": {nm: theme(d["themeWordsCi"]) for nm in d["themedCheckIn"]},
        "stretchThemes": {nm: theme(d["themeWordsSt"]) for nm in d["themedStretch"]},
        "prescription": words(40), "closingVerdict": words(50),
    }
    payload = build_payload("BritCham", "9 July 2026", "Matt Ryland", d, comp)
    html = inject(payload)
    open("britcham_check.html", "w").write(html)
    pdf, heights = asyncio.run(lir_render.render_lir_pdf_async(html))
    open("britcham_check.pdf", "wb").write(pdf)
    over = lir_render.overflowing_pages(heights)
    print("pages", len(heights), "heights", heights)
    print("overflowing:", over)
    # wiw table must now span two pages with the legend on the second
    txt = subprocess.run(["pdftotext", "britcham_check.pdf", "-"],
                         capture_output=True, text=True).stdout
    norm = re.sub(r"\s+", "", txt).lower()
    assert "theteaminoneview·continued" in norm, "expected wiw continuation page"
    assert "ambermarksanareaneedingsupport" in norm, "legend missing"
    assert not over, f"OVERFLOW on pages {over}"
    print("BRITCHAM LAYOUT OK")

if __name__ == "__main__":
    main()
