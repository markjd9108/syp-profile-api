#!/usr/bin/env python3
"""
Build-time transformer: approved Claude Design bundle -> wired LIR template.

Implements the five template guards from the Data Contract Section 4:
  1. Steady flag renders no pill
  2. What Is Missing suppressed when missingCards is empty (inline + continuation)
  3. Four-variant fallback copy (locked strings, from Data Contract Section 3)
  4. Two-variant number-to-watch line (locked strings, from Data Contract Section 3)
  5. pizzahut/mixed sample switch removed; payload is the only data source

Output: lir_template_wired.html containing the token __LIR_PAYLOAD_JSON__.
At generation time the token is replaced with the JSON-string-escaped payload.
No copy is changed anywhere; the locked strings below are verbatim from the
Data Contract.
"""
import json, re, sys, html as H

SRC = "bundle.html"
OUT = "lir_template_wired.html"

# Locked copy — Data Contract Section 3, verbatim.
FALLBACK_STRETCH_ALL = ("No members sit in the Stretch group this round. When every member "
    "flags on at least one dimension, the pattern belongs to the team as a whole. "
    "The Action Plan on the next page is built around it.")
FALLBACK_STRETCH_SHORT = "No members sit in the Stretch group this round."
FALLBACK_CHECKIN_ALL = ("No members sit in the Check-In group this round. When every member "
    "clears the threshold on every dimension, the work ahead is stretch, and the "
    "Action Plan on the next page is built around it.")
FALLBACK_CHECKIN_SHORT = "No members sit in the Check-In group this round."

# The dc runtime's own table aliases (RAW_WRAP). Using them in the saved
# template prevents HTML table parsing from foster-parenting <sc-for> loops
# out of tables (which is exactly the corruption the saved bundle carries).
RAW_WRAP = {"table": "sc-raw-table", "tbody": "sc-raw-tbody", "thead": "sc-raw-thead",
            "tfoot": "sc-raw-tfoot", "tr": "sc-raw-tr", "td": "sc-raw-td",
            "th": "sc-raw-th", "caption": "sc-raw-caption"}

def repair_tables(tpl):
    """The bundle was serialised from a DOM where every <sc-for> inside a
    <table> had been foster-parented out (left empty before the table, its
    row template stranded inside). Restore each loop around its rows and
    alias the table tags so it can never happen again at load time."""
    pattern = re.compile(r'<sc-for\s+([^>]*)>\s*</sc-for>\s*(?=<table[\s>])')
    repaired = 0
    while True:
        m = pattern.search(tpl)
        if not m:
            break
        attrs = m.group(1)
        var = re.search(r'as="([^"]+)"', attrs).group(1)
        tstart = tpl.find("<table", m.end())
        tend = tpl.find("</table>", tstart) + len("</table>")
        assert tstart >= 0 and tend > tstart
        table = tpl[tstart:tend]
        rows = [r for r in re.finditer(r"<tr[\s>].*?</tr>", table, re.S)
                if "{{ " + var + "." in r.group(0)]
        assert rows, f"no template rows found for loop var '{var}'"
        first, last = rows[0].start(), rows[-1].end()
        table = (table[:first] + f"<sc-for {attrs}>" + table[first:last]
                 + "</sc-for>" + table[last:])
        for real, alias in RAW_WRAP.items():
            table = re.sub(r"(</?)" + real + r"(?=[\s>])", r"\1" + alias, table)
        tpl = tpl[:m.start()] + table + tpl[tend:]
        repaired += 1
    print(f"repaired {repaired} foster-parented table loops")
    assert repaired == 5, f"expected 5 table repairs, got {repaired}"
    return tpl

def main():
    s = open(SRC).read()
    m = re.search(r'(<script type="__bundler/template">\s*)(".*")(\s*</script>)', s, re.S)
    assert m, "template script not found"
    tpl = json.loads(m.group(2))

    # ---- Repair the saved bundle's table loops ------------------------------
    tpl = repair_tables(tpl)

    # ---- Guard 5: remove sample switch -------------------------------------
    i = tpl.find("const D = {")
    j = tpl.find("const cfg = D[key];")
    assert i > 0 and j > i, "sample dataset block not found"
    j_end = j + len("const cfg = D[key];")
    replacement = (
        "const cfg = window.__LIR_PAYLOAD__;\n"
        "    if (!cfg || !Array.isArray(cfg.members)) { throw new Error('LIR payload missing or invalid'); }"
    )
    tpl = tpl[:i] + replacement + tpl[j_end:]

    # drop the design-time sample prop from data-props
    tpl = re.sub(r'(data-props=")[^"]*(")', r'\1{}\2', tpl, count=1)

    # ---- Guard 1: Steady flag renders no pill ------------------------------
    old = "avgStyle: avgStyleStr, flagStyle: this.flagStyle(m.flag),"
    assert old in tpl
    tpl = tpl.replace(old,
        "avgStyle: avgStyleStr, flagStyle: m.flag === 'Steady' ? 'display:none' : this.flagStyle(m.flag),")

    # ---- Guard 2: What Is Missing suppression ------------------------------
    old = "const splitPage4 = cfg.patternCards.length >= 4;"
    assert old in tpl
    tpl = tpl.replace(old,
        "const hasMissing = Array.isArray(cfg.missingCards) && cfg.missingCards.length > 0;\n"
        "    const splitPage4 = cfg.patternCards.length >= 4 && hasMissing;\n"
        "    const inlineMissingFlag = cfg.patternCards.length < 4 && hasMissing;")
    old = "splitPage4, inlineMissing: !splitPage4, patternGridCols,"
    assert old in tpl
    tpl = tpl.replace(old, "splitPage4, inlineMissing: inlineMissingFlag, patternGridCols,")

    # ---- Guard 3 markup: replace hardcoded all-flagged variants ------------
    n1 = tpl.count(FALLBACK_STRETCH_ALL)
    n2 = tpl.count(FALLBACK_CHECKIN_ALL)
    assert n1 == 1 and n2 == 1, (n1, n2)
    tpl = tpl.replace(FALLBACK_STRETCH_ALL, "{{ stretchFallback }}")
    tpl = tpl.replace(FALLBACK_CHECKIN_ALL, "{{ checkInFallback }}")

    # ---- Guard 4 markup: replace hardcoded below-60 line -------------------
    old = "The number to watch: {{ priorityDim }}, {{ priorityScore }} now, above 60 at re-assessment."
    assert tpl.count(old) == 1
    tpl = tpl.replace(old, "{{ numberToWatch }}")

    # ---- Focus selection (Mark, 7 Jul 2026): page 5 lists only THEMED
    #      members (code caps at 5); group headers keep true flag counts -----
    old = ("const checkInMembers = members.filter(m => m.flag === 'Check-In').map(m => ({ ...m, theme: m.focusTheme }));\n"
           "    const stretchMembers = members.filter(m => m.flag === 'Stretch').map(m => ({ ...m, theme: m.stretchTheme }));")
    assert old in tpl, "page-5 member filters not found"
    tpl = tpl.replace(old,
        "const checkInFlagCount = members.filter(m => m.flag === 'Check-In').length;\n"
        "    const stretchFlagCount = members.filter(m => m.flag === 'Stretch').length;\n"
        "    const checkInMembers = members.filter(m => m.flag === 'Check-In' && m.focusTheme).map(m => ({ ...m, theme: m.focusTheme }));\n"
        "    const stretchMembers = members.filter(m => m.flag === 'Stretch' && m.stretchTheme).map(m => ({ ...m, theme: m.stretchTheme }));")

    old = ("checkInCount: checkInMembers.length, stretchCount: stretchMembers.length, teamSize: members.length,\n"
           "      hasCheckIn: checkInMembers.length > 0, noCheckIn: checkInMembers.length === 0,\n"
           "      hasStretch: stretchMembers.length > 0, noStretch: stretchMembers.length === 0,")
    assert old in tpl, "count block not found"
    anchor = ("checkInCount: checkInFlagCount, stretchCount: stretchFlagCount, teamSize: members.length,\n"
              "      hasCheckIn: checkInMembers.length > 0, noCheckIn: checkInFlagCount === 0,\n"
              "      hasStretch: stretchMembers.length > 0, noStretch: stretchFlagCount === 0,")
    tpl = tpl.replace(old, anchor)

    # ---- Guards 3 + 4: computed locked-copy variants in renderVals ---------
    tpl = tpl.replace(anchor, anchor + "\n" +
        "      stretchFallback: checkInFlagCount === members.length ? "
        + json.dumps(FALLBACK_STRETCH_ALL) + " : " + json.dumps(FALLBACK_STRETCH_SHORT) + ",\n"
        "      checkInFallback: stretchFlagCount === members.length ? "
        + json.dumps(FALLBACK_CHECKIN_ALL) + " : " + json.dumps(FALLBACK_CHECKIN_SHORT) + ",\n"
        "      numberToWatch: cfg.priorityScore <= 59\n"
        "        ? 'The number to watch: ' + cfg.priorityDim + ', ' + cfg.priorityScore + ' now, above 60 at re-assessment.'\n"
        "        : 'The number to watch: ' + cfg.priorityDim + ', ' + cfg.priorityScore + ' now, the dimension with the most room at re-assessment.',")

    # ---- Payload hook + vendored React, in <head> BEFORE the dc runtime ----
    # The bundle loader re-executes scripts in document order, and the runtime
    # boots immediately, so the payload must be defined before the runtime
    # script tag. Vendored React means the runtime skips its CDN fetch
    # (loadReactUmd checks window.React) and renders have no network dependency.
    react = open("vendor_react.js").read()
    react_dom = open("vendor_react_dom.js").read()
    pre = ("<script>window.__LIR_PAYLOAD__ = __LIR_PAYLOAD_JSON__;</script>\n"
           "<script>/* vendored react@18.3.1 */\n" + react + "\n</script>\n"
           "<script>/* vendored react-dom@18.3.1 */\n" + react_dom + "\n</script>\n")
    k = tpl.find('<script src="ad3137fb-6bfc-4585-8010-0ccf27d9d8af">')
    assert k > 0, "dc runtime script tag not found"
    tpl = tpl[:k] + pre + tpl[k:]

    # Escape "</" so inner </script> tags cannot terminate the outer
    # __bundler/template script element (matches the original bundle encoding).
    encoded = json.dumps(tpl).replace("</", "<\\u002F")
    out = s[:m.start(2)] + encoded + s[m.end(2):]
    open(OUT, "w").write(out)
    print("wrote", OUT, len(out), "chars; token present:", "__LIR_PAYLOAD_JSON__" in out)

if __name__ == "__main__":
    main()
