#!/usr/bin/env python3
"""
Acceptance harness v2 (Change Order 1): renders the four datasets and verifies
the amended expectations: every page true A4, no overflow, no orphaned
headers, new page 2/3/5/7/appendix content, table pagination, dynamic page
numbers, Spec v2 copy rules (fixtures pre-validated against the full scanner).
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
    check(f"{name}: fixture passes Spec v2 validator", not vfails, str(vfails[:3]))
    payload = build_payload(ds["team"], ds["date"], ds["leader"], d, comp)
    html = inject(payload)
    open(f"{name}_v2.html", "w").write(html)
    pdf_bytes, heights = asyncio.run(render(html))
    pdf = f"{name}_v2.pdf"
    open(pdf, "wb").write(pdf_bytes)

    P = pages_text(pdf)
    N = [norm(p) for p in P]
    joined = " ".join(P)

    over = lir_render.overflowing_pages(heights)
    check(f"{name}: no page overflows A4", not over, f"pages {over} heights {heights}")
    check(f"{name}: pdf page count matches rendered pages", len(P) == len(heights),
          f"pdf {len(P)} vs dom {len(heights)}")
    check(f"{name}: A4 dimensions", a4_ok(pdf))
    check(f"{name}: live text layer", sum(len(p.strip()) for p in P) > 2000)
    check(f"{name}: no unresolved bindings", "{{" not in joined)
    check(f"{name}: under 2 MB", len(pdf_bytes) < 2_000_000)

    # ---- Change Order 1 content checks ----
    # page 2: at-a-glance grid, exactly one number (the ntw line)
    p2 = P[1]
    check(f"{name}: p2 grid labels", all(l in norm(p2) for l in
          ["workingwell", "needssupport", "therisk", "theopportunity"]))
    p2_body = re.sub(r"page\d+of\d+", "", norm(p2)).replace("1:1", "")
    for nm in TEST_COHORTS[name]["members"]:
        p2_body = p2_body.replace(norm(nm["name"]), "")
    digits_p2 = set(re.findall(r"\d+", p2_body))
    ntw_nums = {str(d["priorityScore"]), "60"}
    check(f"{name}: p2 numbers only from ntw line",
          digits_p2 <= ntw_nums, str(sorted(digits_p2)))
    check(f"{name}: p2 old blocks gone", "priority—" not in norm(p2) and
          d["priorityDim"].lower() + str(d["avgComm"]) not in norm(p2))
    # page 3: strip + locked copy
    p3 = norm(P[2])
    check(f"{name}: p3 dimension strip scores", all(str(x) in P[2] for x in
          [d["avgComm"], d["avgDm"], d["avgCollab"]]))
    check(f"{name}: p3 locked intro", "thefocuscolumnmarkswhoneedsasupportingconversation" in p3)
    # legend lives on the LAST wiw page
    check(f"{name}: p3 locked legend", "ambermarksanareaneedingsupport" in norm(joined))
    # page 5 locked copy + captions
    check(f"{name}: p5 locked intro", "theconversationthemesarestartingpoints" in norm(joined))
    check(f"{name}: p5 captions", "atleastoneareaneedssupport.worthaconversationthisquarter" in norm(joined)
          and "strongacrosstheboard.readytobegivenmore" in norm(joined))
    # page 7 + appendix
    check(f"{name}: 90 Minutes label", "targeted·90minutes" in norm(joined)
          and "half-day" not in joined.lower())
    check(f"{name}: appendix Focus groups block",
          "focusgroups" in norm(joined) and "membersbetweenthetwoappearintheteamtable" in norm(joined))
    # dynamic page numbering: footers sequential 2..total
    total = len(P)
    nums = []
    for p in P[1:]:
        m = re.search(r"page(\d+)of(\d+)", norm(p))
        if m:
            nums.append((int(m.group(1)), int(m.group(2))))
    seq_ok = all(t == total for _, t in nums) and [n for n, _ in nums] == list(range(2, total + 1))
    check(f"{name}: page numbers sequential 2..{total}", seq_ok, str(nums))
    # no orphaned group headers: a header must never be the last text block of a page
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
check("t1 ntw below-60 variant", "thenumbertowatch:communication,50now,above60atre-assessment." in N[1])
check("t1 small-team note", "onepersonmovestheaverage" in N[2])
check("t1 missing 2 cards inline", "whatismissing" in N[3])
check("t1 all-flagged fallback", "thepatternbelongstotheteamasawhole" in " ".join(N))

print("========== TEST 2 — Mekong Digital ==========")
d, P, N, H = run("test2")
check("t2 total pages 8", len(P) == 8, str(len(P)))
check("t2 ntw 60-plus variant", "thedimensionwiththemostroomatre-assessment." in N[1])
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
check("t4 wiw continuation page", "theteaminoneview·continued" in joinedN)
check("t4 wiw header repeated", joinedN.count("archetype") >= 2)
check("t4 page4 split renders (missing on continuation)",
      "whatismissing" in joinedN and any("continued" in n and "whatismissing" in n for n in N))
check("t4 focus tables paginated", "twogroupsthisquarter·continued" in joinedN)
check("t4 all 20 in who-is-who", all(norm(m["name"]) in (N[2] + N[3]) for m in TEST_COHORTS["test4"]["members"]))
check("t4 counts", "check-in·9of20" in joinedN and "stretch·5of20" in joinedN)

bad = [n for n, ok in results if not ok]
print(f"\n===== {len(results) - len(bad)}/{len(results)} checks passed =====")
if bad:
    print("FAILED:", *bad, sep="\n  ")
    sys.exit(1)
