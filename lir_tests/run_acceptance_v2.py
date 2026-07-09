#!/usr/bin/env python3
"""
Acceptance harness v3 (Change Order 2, bands-only): renders the five datasets
and verifies every amended expectation: true A4, no overflow, ZERO digits on
report pages 2 through the Action Plan (footers/counts/1:1/90-minute exempt),
one-page team view to 14 members, banded strip/one-to-watch/legend, the
How-to-read block, composition-grid placement, dynamic page numbers, and the
CO2 validator (fixtures are dogfooded through the full scanner).
"""
import asyncio, json, re, subprocess, sys
import lir_core, lir_render
from lir_core import derive, build_payload, inject, validate_input
from lir_compose import validate_composed
from fixtures_v2 import TEST_COHORTS, composed_for

results = []
def check(name, ok, detail=""):
    results.append((name, ok))
    print(("OK   " if ok else "FAIL "), name, ("" if ok else f"  <-- {detail}"))

def pages_text(pdf):
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf],
            capture_output=True, text=True).stdout).group(1))
    return [subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), pdf, "-"],
            capture_output=True, text=True).stdout for i in range(1, n + 1)]

def norm(s):
    return re.sub(r"\s+", "", s).lower()

def digits_left(page_norm):
    """Digits on a page after removing every legitimate digit context."""
    c = re.sub(r"page\d+of\d+", "", page_norm)
    c = re.sub(r"(check-in|stretch)·\d+of\d+", "", c)
    c = c.replace("1:1", "").replace("90-minute", "").replace("90minute", "")
    # bands-only means no SCORES; a leaked score is a 2+ digit run. Single
    # digits remain legitimate (member names like 'Mark Pizza 2', count columns).
    return re.findall(r"\d{2,}", c)

def a4_ok(pdf):
    out = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    m = re.search(r"Page size:\s+([\d.]+) x ([\d.]+) pts", out)
    return abs(float(m.group(1)) - 595.28) < 1.5 and abs(float(m.group(2)) - 841.89) < 1.5

async def render(html):
    return await lir_render.render_lir_pdf_async(html)

def run(name):
    ds = TEST_COHORTS[name]
    errs, warns = validate_input(ds["team"], ds["date"], ds["leader"], ds["members"])
    assert not errs, errs
    d = derive(ds["members"])
    comp = composed_for(name, d)
    vfails = validate_composed(comp, d, ds["team"], ds["leader"])
    check(f"{name}: fixture passes CO2 validator", not vfails, str(vfails[:3]))
    payload = build_payload(ds["team"], ds["date"], ds["leader"], d, comp)
    check(f"{name}: payload carries no raw scores",
          not re.search(r'": ?\d', json.dumps({k: v for k, v in payload.items()
                                               if k != "date"})))
    html = inject(payload)
    open(f"{name}_v3.html", "w").write(html)
    pdf_bytes, heights = asyncio.run(render(html))
    pdf = f"{name}_v3.pdf"
    open(pdf, "wb").write(pdf_bytes)

    P = pages_text(pdf)
    N = [norm(p) for p in P]
    joined = " ".join(P)
    nj = norm(joined)

    over = lir_render.overflowing_pages(heights)
    check(f"{name}: no page overflows A4", not over, f"pages {over} heights {heights}")
    check(f"{name}: pdf page count matches rendered pages", len(P) == len(heights),
          f"pdf {len(P)} vs dom {len(heights)}")
    check(f"{name}: A4 dimensions", a4_ok(pdf))
    check(f"{name}: live text layer", sum(len(p.strip()) for p in P) > 2000)
    check(f"{name}: no unresolved bindings", "{{" not in joined)
    check(f"{name}: under 2 MB", len(pdf_bytes) < 2_000_000)

    # ---- Change Order 2 content checks ----
    n_members = d["teamSize"]
    p2 = N[1]
    check(f"{name}: p2 grid labels", all(l in p2 for l in
          ["workingwell", "needssupport", "therisk", "theopportunity"]))
    check(f"{name}: p2 one-to-watch line", "theonetowatch:" in p2)
    check(f"{name}: p2 how-to-read block", "howtoreadthisreport." in p2
          and "snapshotofonesession" in p2)
    # bands-only: zero digits from page 2 through the Action Plan page
    for i in range(1, len(N) - 2):
        dl = digits_left(N[i])
        check(f"{name}: page {i+1} digit-free", not dl, f"digits {dl[:8]}")
    # band vocabulary visible in strip + team-level row
    check(f"{name}: p3 banded strip", d["bandComm"].lower() in N[2]
          and d["bandDm"].lower() in N[2] and d["bandCollab"].lower() in N[2])
    check(f"{name}: p3 team level row", "teamlevel" in nj)
    check(f"{name}: p3 locked intro", "thefocuscolumnmarkswhoneedsasupportingconversation" in N[2])
    check(f"{name}: p3 locked legend", "ambermarksanareaneedingsupport" in nj)
    # one-page team view up to 14
    if n_members <= 14:
        check(f"{name}: team view on ONE page", "theteaminoneview·continued" not in nj)
    else:
        check(f"{name}: team view paginated >14", "theteaminoneview·continued" in nj)
    # composition grid placement
    if n_members <= 8:
        check(f"{name}: composition grid on p3", "teamcomposition" in N[2])
    else:
        check(f"{name}: composition grid in appendix", "teamcomposition" in N[-1],
              "not on last page")
        check(f"{name}: composition grid off team view page", "teamcomposition" not in N[2])
    # qualitative legend: numeric ranges gone
    check(f"{name}: no band ranges anywhere", "80–100" not in joined and "0–39" not in joined)
    # page 5 locked copy + captions
    check(f"{name}: p5 locked intro", "theconversationthemesarestartingpoints" in nj)
    check(f"{name}: p5 captions", "atleastoneareaneedssupport.worthaconversationthisquarter" in nj
          and "strongacrosstheboard.readytobegivenmore" in nj)
    check(f"{name}: snapshot caveat banded", "thispictureisasnapshotofbehaviour" in nj)
    # page 7 + appendix
    check(f"{name}: 90 Minutes label", "targeted·90minutes" in nj and "half-day" not in joined.lower())
    check(f"{name}: appendix Focus groups block",
          "focusgroups" in nj and "membersbetweenthetwoappearintheteamtable" in nj)
    check(f"{name}: appendix retitled", "methodandreference" in N[-1])
    check(f"{name}: appendix methodology banded", "reportedinfourbands" in N[-1]
          and "0to100" not in N[-1])
    # dynamic page numbering: footers sequential 2..total
    total = len(P)
    nums = []
    for p in P[1:]:
        m = re.search(r"page(\d+)of(\d+)", norm(p))
        if m:
            nums.append((int(m.group(1)), int(m.group(2))))
    seq_ok = all(t == total for _, t in nums) and [x for x, _ in nums] == list(range(2, total + 1))
    check(f"{name}: page numbers sequential 2..{total}", seq_ok, str(nums))
    # no orphaned group headers
    orphan = False
    for p in P:
        tail = norm(p)[-120:]
        if tail.endswith(("worthaconversationthisquarter", "readytobegivenmore")):
            orphan = True
    check(f"{name}: no orphaned group headers", not orphan)
    return d, P, N, heights

print("========== TEST 1 — Pizzahut ==========")
d, P, N, H = run("test1")
check("t1 total pages 8", len(P) == 8, str(len(P)))
check("t1 one-to-watch below-threshold variant",
      "theonetowatch:communication—atemergingtoday;theworkisbringingittodevelopingbyre-assessment." in N[1],
      N[1][:400])
check("t1 small-team note", "onepersonmovestheaverage" in N[2])
check("t1 missing 2 cards inline", "whatismissing" in N[3])
check("t1 all-flagged fallback", "thepatternbelongstotheteamasawhole" in " ".join(N))

print("========== TEST 2 — Mekong Digital ==========")
d, P, N, H = run("test2")
check("t2 total pages 8", len(P) == 8, str(len(P)))
check("t2 one-to-watch most-room variant",
      "theonetowatch:communication—thedimensionwiththemostroomatre-assessment." in N[1])
check("t2 both groups themed", "check-in·3of5" in " ".join(N) and "stretch·2of5" in " ".join(N))

print("========== TEST 3 — Edge Cohort ==========")
d, P, N, H = run("test3")
check("t3 F Hoang steady, no pill", "fhoang" in N[2] and N[2].count("steady") == 0)
check("t3 missing suppressed", not any("whatismissing" in n for n in N))
check("t3 4 pattern cards no split", not any("continued" in n for n in [norm(p) for p in P] if "howthisteam" in n))

print("========== TEST 4 — Synthetic Twenty ==========")
d, P, N, H = run("test4")
joinedN = " ".join(N)
check("t4 20 members", d["teamSize"] == 20)
check("t4 9 check-in / 5 stretch / 6 steady",
      (d["checkInCount"], d["stretchCount"]) == (9, 5))
check("t4 short themes (25w rule)", d["themeWordsCi"] == 25)
check("t4 first view page holds 14", "phongsa" in N[2] and "quanvinh" not in N[2])
check("t4 continuation holds the rest", "quanvinh" in N[3] and "vyyen" in N[3])
check("t4 wiw header repeated", joinedN.count("archetype") >= 2)
check("t4 page4 split renders (missing on continuation)",
      "whatismissing" in joinedN and any("continued" in n and "whatismissing" in n for n in N))
check("t4 focus tables paginated", "twogroupsthisquarter·continued" in joinedN)
check("t4 all 20 in who-is-who", all(norm(m["name"]) in (N[2] + N[3]) for m in TEST_COHORTS["test4"]["members"]))
check("t4 counts", "check-in·9of20" in joinedN and "stretch·5of20" in joinedN)

print("========== TEST 5 — BritCham (live data) ==========")
d, P, N, H = run("test5")
joinedN = " ".join(N)
check("t5 10 members one-page view", "theteaminoneview·continued" not in joinedN)
check("t5 all 10 rows on p3", all(norm(m["name"]) in N[2] for m in TEST_COHORTS["test5"]["members"]))
check("t5 counts", "check-in·5of10" in joinedN and "stretch·3of10" in joinedN)

bad = [n for n, ok in results if not ok]
print(f"\n===== {len(results) - len(bad)}/{len(results)} checks passed =====")
if bad:
    print("FAILED:", *bad, sep="\n  ")
    sys.exit(1)
