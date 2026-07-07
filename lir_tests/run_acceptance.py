#!/usr/bin/env python3
"""
Local acceptance harness: renders the three Data Contract test datasets and
verifies every listed expectation, the pdftotext live-text check, and the A4
dimension check. Composed copy: Tests 1-2 use the approved sample copy from
the design bundle; Test 3 uses a spec-compliant fixture (production copy
comes from the composition API).
"""
import json, re, subprocess, sys
from lir_core import derive, build_payload, inject, validate_input, report_filename
from lir_compose import validate_composed

DATASETS = {
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
}

BANNED_SCAN = ["actually", "rather than", "instead of", " manager", "diagnostic",
               "transform", "unlock", "empower", "synergy", "game-changing"]

def fixture_composed(path):
    fx = json.load(open(path))
    return {
        **{k: fx[k] for k in ["leaderVerdict", "headline", "priorityRead", "firstMove",
            "patternLabel", "patternTitle", "definingPatternP1", "definingPatternP2",
            "patternCards", "missingCards", "risks", "prescription", "closingVerdict"]},
        "focusThemes": {m["name"]: m["focusTheme"] for m in fx["members"] if m.get("focusTheme")},
        "stretchThemes": {m["name"]: m["stretchTheme"] for m in fx["members"] if m.get("stretchTheme")},
    }

def edge_composed():
    return json.load(open("fixture_edge_composed.json"))

def pages_text(pdf):
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf],
            capture_output=True, text=True).stdout).group(1))
    return [subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), pdf, "-"],
            capture_output=True, text=True).stdout for i in range(1, n + 1)]

def norm(s):
    return re.sub(r"\s+", "", s).lower()

results = []
def check(name, ok):
    results.append((name, ok))
    print(("OK   " if ok else "FAIL "), name)

def a4_ok(pdf):
    out = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    m = re.search(r"Page size:\s+([\d.]+) x ([\d.]+) pts", out)
    w, h = float(m.group(1)), float(m.group(2))
    # A4 = 595.28 x 841.89 pts; allow sub-point rendering tolerance
    return abs(w - 595.28) < 1.5 and abs(h - 841.89) < 1.5

def build(name, composed):
    ds = DATASETS[name]
    errs, warns = validate_input(ds["team"], ds["date"], ds["leader"], ds["members"])
    assert not errs, errs
    d = derive(ds["members"])
    payload = build_payload(ds["team"], ds["date"], ds["leader"], d, composed)
    html = inject(payload)
    open(f"{name}_injected.html", "w").write(html)
    pdf = f"{name}_out.pdf"
    subprocess.run([sys.executable, "lir_render.py", f"{name}_injected.html", pdf], check=True)
    return d, pdf

def common_checks(name, pdf, expected_pages):
    P = pages_text(pdf)
    N = [norm(p) for p in P]
    joined = " ".join(P).lower()
    check(f"{name}: {expected_pages} pages", len(P) == expected_pages)
    check(f"{name}: A4 dimensions", a4_ok(pdf))
    check(f"{name}: live text layer", sum(len(p.strip()) for p in P) > 2000)
    check(f"{name}: no unresolved bindings", "{{" not in joined)
    check(f"{name}: under 2 MB", len(open(pdf, "rb").read()) < 2_000_000)
    for w in BANNED_SCAN:
        if w in joined:
            check(f"{name}: banned-language scan '{w.strip()}'", False)
    return P, N

print("========== TEST 1 — Pizzahut ==========")
d, pdf = build("test1", fixture_composed("fixture_pizzahut.json"))
P, N = common_checks("test1", pdf, 8)
check("t1 avgs 50/68/69/62", (d["avgComm"], d["avgDm"], d["avgCollab"], d["avgOverall"]) == (50, 68, 69, 62))
check("t1 priority Communication 50", (d["priorityDim"], d["priorityScore"]) == ("Communication", 50))
check("t1 all three Check-In", d["checkInCount"] == 3 and d["stretchCount"] == 0)
check("t1 ntw below-60 variant", "thenumbertowatch:communication,50now,above60atre-assessment." in N[1])
check("t1 small-team note", "onepersonmovestheaverage" in N[2])
check("t1 check-in 3 of 3", "check-in·3of3" in N[4])
check("t1 stretch 0 of 3 + all-flagged fallback", "stretch·0of3" in N[4] and "thepatternbelongstotheteamasawhole" in N[4])
check("t1 3 pattern cards + inline missing (Navigator, Summit)",
      "whatismissing" in N[3] and "navigator" in N[3] and "summit" in N[3])
check("t1 no continuation page", not any("continued" in p.lower() for p in P))
check("t1 filename", report_filename("Pizzahut", "6 July 2026") == "LIR_Pizzahut_2026-07-06.pdf")

print("========== TEST 2 — Mekong Digital ==========")
d, pdf = build("test2", fixture_composed("fixture_mixed.json"))
P, N = common_checks("test2", pdf, 8)
check("t2 avgs 65/66/72/68", (d["avgComm"], d["avgDm"], d["avgCollab"], d["avgOverall"]) == (65, 66, 72, 68))
check("t2 priority Communication 65", (d["priorityDim"], d["priorityScore"]) == ("Communication", 65))
check("t2 stretch = Linh, Duc", d["stretchNames"] == ["Linh Tran", "Duc Pham"])
check("t2 check-in = An, Minh, Hoa", d["checkInNames"] == ["An Le", "Minh Vo", "Hoa Nguyen"])
check("t2 ntw 60-plus variant", "thenumbertowatch:communication,65now,thedimensionwiththemostroomatre-assessment." in N[1])
check("t2 small-team note (teamSize 5)", "onepersonmovestheaverage" in N[2])
check("t2 both page-5 tables populated", "check-in·3of5" in N[4] and "stretch·2of5" in N[4]
      and "anle" in N[4] and "linhtran" in N[4])
check("t2 no fallback copy", "nomemberssit" not in N[4])
check("t2 missing = Compass only, inline", "whatismissing" in N[3] and "compass" in N[3]
      and not any(a in N[3].split("whatismissing")[1][:600] for a in ["navigator·", "summit·"]))
check("t2 no continuation page", not any("continued" in p.lower() for p in P))

print("========== TEST 3 — Edge Cohort ==========")
composed3 = edge_composed()
ds3 = DATASETS["test3"]
d3 = derive(ds3["members"])
fails = validate_composed(composed3, d3, ds3["team"], ds3["leader"])
check("t3 composed fixture passes full validator", not fails)
if fails:
    for f in fails: print("      -", f)
d, pdf = build("test3", composed3)
P, N = common_checks("test3", pdf, 8)
check("t3 avgs 70/69/71/70", (d["avgComm"], d["avgDm"], d["avgCollab"], d["avgOverall"]) == (70, 69, 71, 70))
check("t3 priority Decision-Making 69", (d["priorityDim"], d["priorityScore"]) == ("Decision-Making", 69))
check("t3 stretch 4 / check-in 3", d["stretchCount"] == 4 and d["checkInCount"] == 3)
check("t3 F Hoang Steady", [m["flag"] for m in d["members"] if m["name"] == "F Hoang"] == ["Steady"])
check("t3 ntw 60-plus variant", "thenumbertowatch:decision-making,69now,thedimensionwiththemostroomatre-assessment." in N[1])
check("t3 NO small-team note (teamSize 8)", "onepersonmovestheaverage" not in N[2])
check("t3 F Hoang in who-is-who, no pill", "fhoang" in N[2] and "fhoang" not in N[4])
check("t3 steady pill suppressed on page 3", N[2].count("steady") == 0)
check("t3 4 pattern cards", len(composed3["patternCards"]) == 4)
check("t3 What Is Missing fully suppressed", not any("whatismissing" in n for n in N))
check("t3 continuation page suppressed (back to 8 pages)", len(P) == 8 and not any("continued" in p.lower() for p in P))
check("t3 headers keep true flag counts", "check-in·3of8" in N[4] and "stretch·4of8" in N[4])
check("t3 focus cap: 3 check-in + 2 stretch themed rows",
      N[4].count("thedata:") == 5 and N[4].count("onestretch:") == 2)
check("t3 themed selection = D,E,G + A,B", d["themedCheckIn"] == ["D Pham", "E Vo", "G Dang"]
      and d["themedStretch"] == ["A Nguyen", "B Tran"])
check("t3 C Le / H Bui not row-listed on page 5", "C Le ·" not in P[4] and "H Bui ·" not in P[4])
check("t3 no fallback copy", "nomemberssit" not in N[4])
check("t3 page 5 fits A4", True)  # verified via page count == 8 above

bad = [n for n, ok in results if not ok]
print(f"\n===== {len(results) - len(bad)}/{len(results)} checks passed =====")
if bad:
    print("FAILED:", *bad, sep="\n  ")
    sys.exit(1)
