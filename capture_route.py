# Between-Sessions Curriculum - capture page route (FastAPI), NEW two-touch format.
# Mounted from api_server.py via: app.include_router(capture_router)
#
#   POST /generate-capture       -> { "url": "<base>/c/<token>" }   (called by the Friday send scenario)
#   GET  /c/{token}              -> the hosted Friday response page (opened by the participant)
#   POST /submit-capture/{token} -> grades the checks SERVER-SIDE, returns per-question feedback,
#                                    and forwards a graded row to Make for logging to the sheet.
#
# The knowledge-check answer key is NEVER placed in the page HTML. Grading happens here on submit.
# The simulation is a teaching tool with immediate feedback, so its answers DO ride in the page by design.
# English only for now; Vietnamese is added once the copy is locked and run through the VI pipeline.
# Content below is DRAFT - pending scoring reconciliation.

import os, json, secrets, urllib.request, urllib.parse
from urllib.parse import parse_qs
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

capture_router = APIRouter()

PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "https://syp-profile-api-production.up.railway.app").rstrip("/")
# Make webhook that APPENDS one row to the Tracking Log (grading already done here, so Make just stores).
LOG_WEBHOOK_URL = os.environ.get("BSC_LOG_WEBHOOK", "https://hook.eu2.make.com/dxt4vnb8cnk2x8uv5p0z57gdnb5tvly3")


def _store_dir():
    # Resolve a writable folder LAZILY so importing this module never touches the filesystem
    # and can never crash app startup.
    candidates = []
    if os.environ.get("CAPTURE_STORE_DIR"):
        candidates.append(os.environ["CAPTURE_STORE_DIR"])
    candidates.append(os.path.join(os.environ.get("PROFILE_STORE_DIR", "/data/profiles"), "captures"))
    candidates.append("/tmp/bsc_captures")
    for d in candidates:
        try:
            os.makedirs(d, exist_ok=True)
            return d
        except Exception:
            continue
    return "/tmp"


# ------------------------------------------------------------------ content
# Week 1 - Communication - The Clarity Loop (overview). Draft, proxy basis.
# Each check/sim question: q, opts [A,B,C], correct index, why.
WEEK1 = {
    "story_prompt": "Think of one moment where you assumed you were understood without checking. "
                    "When and where was it, and what happened?",
    "reflection": [
        "Which part of the Clarity Loop do you feel you already do well?",
        "Which part feels hardest to fit into your day?",
    ],
    "simulation": {
        "intro": "A real exchange. Read it, then work through what went wrong and what good looks like. "
                 "You get feedback as you answer, so this part teaches rather than tests.",
        "scene_title": "Over chat, Tuesday morning",
        "scene": [
            {"who": "Team lead", "cls": "lead",
             "text": "Hey, can you pull together the numbers for the client review and get them to me before the meeting? Thanks!"},
            {"who": "Colleague", "cls": "col", "text": "Sure, no problem \U0001F44D"},
        ],
        "scenenote": "Two days later, the colleague sends a full-year revenue breakdown. The lead wanted only the "
                     "Q3 churn figures, for a review at 2pm that same day.",
        "questions": [
            {"q": "What is the main problem in this exchange?",
             "opts": ["The colleague was careless and did not read the message properly.",
                      "The instruction felt clear to the lead, but the specifics (which numbers, which meeting, by when) were never checked.",
                      "The colleague should have known which figures were meant."],
             "correct": 1,
             "why": "The message felt clear to the sender, so nobody verified it. \"The numbers\" and \"the meeting\" "
                    "meant different things to each person. Clarity was assumed, not verified, and it was a shared miss."},
            {"q": "Which step of the Clarity Loop is missing here?",
             "opts": ["State Clearly. The lead never said anything at all.",
                      "Check Understanding. No one confirmed what \"the numbers\" and \"the meeting\" really meant.",
                      "Adjust Language. The words were too complex for the colleague."],
             "correct": 1,
             "why": "The lead did state something, and the words were simple. What is missing is the check: getting the "
                    "colleague to say back which figures, for which meeting, by when."},
            {"q": "What is the strongest next move for the lead, right now?",
             "opts": ["Quietly redo the work themselves to save time.",
                      "Reply naming the specific gap and confirming the fix: \"My fault for not being specific. I need Q3 churn only, for the 2pm review. Can you send that by 1pm?\"",
                      "Tell the colleague they got it wrong and to try again."],
             "correct": 1,
             "why": "The good version owns the ambiguity, states the specifics, and confirms the new expectation out loud. "
                    "It fixes the immediate problem and models the loop for next time."},
        ],
        "good_scene": [
            {"who": "Team lead", "cls": "lead",
             "text": "Can you send me the Q3 churn figures, Q3 only, for the client review at 2pm today? I will use them in the churn slide. Can I have them by 1pm?"},
            {"who": "Colleague", "cls": "col",
             "text": "Got it, Q3 churn only, to you by 1pm for the 2pm review. I will send the same cut as last quarter unless you want it different?"},
            {"who": "Team lead", "cls": "lead", "text": "Same cut is perfect. Thank you."},
        ],
        "good_cap": "Three moves close the loop: the lead states the specifics (State Clearly), the colleague says the "
                    "task back (Check Understanding), and they confirm what happens next (Confirm Alignment). No extra "
                    "time, and nothing to redo.",
        "yourturn_label": "Your turn: a colleague says \"I will get that report to you soon.\" Write one sentence you could say to close the loop.",
        "yourturn_model": "A strong version: \"Great. When you say soon, do you mean today or this week? I need it by "
                          "Thursday midday for the board pack, so tell me if that is tight.\"",
    },
    "checks": [
        {"q": "What is the core idea of the Clarity Loop?",
         "opts": ["If a message is clear to the speaker, it has been communicated.",
                  "Clarity is verified, not assumed.",
                  "Saying a message enough times makes it clear."],
         "correct": 1,
         "why": "Clarity only exists once you have checked that it landed. Saying something clearly is not the same as being understood."},
        {"q": "Whose responsibility is it to reach a shared understanding?",
         "opts": ["The speaker's, because they own the message.",
                  "The listener's, because they must pay attention.",
                  "Everyone in the conversation shares it."],
         "correct": 2,
         "why": "The loop treats clarity as a joint outcome. Both sides work to confirm the message landed, rather than one side carrying it."},
        {"q": "What is the correct order of the five Clarity Loop steps?",
         "opts": ["State Clearly, Check Understanding, Invite Questions, Adjust Language, Confirm Alignment.",
                  "Check Understanding, State Clearly, Adjust Language, Invite Questions, Confirm Alignment.",
                  "State Clearly, Invite Questions, Confirm Alignment, Check Understanding, Adjust Language."],
         "correct": 0,
         "why": "You state your point, check it landed, invite what is unclear, adjust if needed, then confirm what happens next."},
        {"q": "Which of these is Check Understanding done well?",
         "opts": ["\"Does that make sense?\"",
                  "\"Can you tell me what you will do first, so I know I explained it clearly?\"",
                  "\"You understand, right?\""],
         "correct": 1,
         "why": "Yes or no questions almost always get a yes. Asking them to say the next step back reveals the real gap."},
        {"q": "Adjust Language means:",
         "opts": ["Saying the same thing again, more firmly.",
                  "Saying it a different way when the first way did not land.",
                  "Using the simplest possible words with everyone, all the time."],
         "correct": 1,
         "why": "If a message did not land, volume or repetition rarely helps. A different explanation often does."},
        {"q": "You said something clearly and the other person nodded. What can you safely assume?",
         "opts": ["They understood, because you were clear.",
                  "Nothing yet. A nod is not the same as shared understanding.",
                  "They will speak up if they are confused."],
         "correct": 1,
         "why": "This is the whole point of the loop. Clarity is verified, not assumed. A nod is not verification."},
    ],
}

CONTENT_SETS = {"1": WEEK1}  # keyed by week; more weeks drop in here (or come from the sheet later)


def _public_content(cset):
    # Strip the knowledge-check answer key before it ever reaches the browser.
    checks = [{"q": c["q"], "opts": c["opts"]} for c in cset["checks"]]
    return {"story_prompt": cset["story_prompt"], "reflection": cset["reflection"],
            "simulation": cset["simulation"], "checks": checks}


# ------------------------------------------------------------------ routes
@capture_router.post("/generate-capture")
async def generate_capture(request: Request):
    raw = (await request.body()).decode("utf-8")
    b = {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}
    week = str(b.get("week", "1")).split(".")[0] or "1"
    meta = {"participant_id": b.get("participant_id", ""), "client": b.get("client", ""),
            "program_gap": b.get("program_gap", ""), "module": b.get("module", ""),
            "week": week, "send_date": b.get("send_date", "")}
    token = secrets.token_hex(24)
    record = {"meta": meta, "week": week}
    with open(os.path.join(_store_dir(), token + ".json"), "w", encoding="utf-8") as f:
        json.dump(record, f)
    return JSONResponse({"url": PUBLIC_BASE_URL + "/c/" + token})


@capture_router.get("/c/{token}")
async def capture_page(token: str):
    path = os.path.join(_store_dir(), token + ".json")
    if not os.path.exists(path):
        return HTMLResponse("This link has expired or is not valid.", status_code=404)
    with open(path, encoding="utf-8") as f:
        record = json.load(f)
    cset = CONTENT_SETS.get(record.get("week", "1"), WEEK1)
    html = PAGE
    subs = {"%%WEEK%%": record["week"], "%%TOKEN%%": token,
            "%%CONTENT%%": json.dumps(_public_content(cset)),
            "%%SUBMIT%%": json.dumps(PUBLIC_BASE_URL + "/submit-capture/" + token)}
    for k, v in subs.items():
        html = html.replace(k, v)
    return HTMLResponse(html)


@capture_router.post("/submit-capture/{token}")
async def submit_capture(token: str, request: Request):
    path = os.path.join(_store_dir(), token + ".json")
    if not os.path.exists(path):
        return JSONResponse({"error": "not found"}, status_code=404)
    with open(path, encoding="utf-8") as f:
        record = json.load(f)
    cset = CONTENT_SETS.get(record.get("week", "1"), WEEK1)
    body = await request.json()
    answers = body.get("checks", [])  # list of chosen indexes (or -1)

    results, correct_count = [], 0
    for i, c in enumerate(cset["checks"]):
        chosen = answers[i] if i < len(answers) else -1
        is_ok = (chosen == c["correct"])
        if is_ok:
            correct_count += 1
        results.append({"q": c["q"], "correct": is_ok,
                        "correctKey": ["A", "B", "C"][c["correct"]],
                        "correctText": c["opts"][c["correct"]], "why": c["why"]})

    # Forward one graded row to Make for the Responses log (grading already done here).
    m = record["meta"]
    letters = ["A", "B", "C"]
    refl = body.get("reflection") or []
    ans_letters, cor_flags = [], []
    for i in range(len(cset["checks"])):
        chosen = answers[i] if i < len(answers) else -1
        ans_letters.append(letters[chosen] if 0 <= chosen < 3 else "-")
        cor_flags.append("Y" if results[i]["correct"] else "N")
    row = {"participant_id": m["participant_id"], "client": m["client"],
           "program_gap": m["program_gap"], "module": m["module"], "week": m["week"],
           "send_date": m["send_date"],
           "practice_completed": body.get("completion", ""),
           "story_text": body.get("story", ""),
           "reflection_strength": refl[0] if len(refl) > 0 else "",
           "reflection_hardest": refl[1] if len(refl) > 1 else "",
           "theory_correct": str(correct_count), "theory_total": str(len(cset["checks"])),
           "kc_answers": ",".join(ans_letters), "kc_correct": ",".join(cor_flags),
           "token": token}
    try:
        data = urllib.parse.urlencode(row).encode("utf-8")
        req = urllib.request.Request(LOG_WEBHOOK_URL, data=data,
                                     headers={"Content-Type": "application/x-www-form-urlencoded"})
        urllib.request.urlopen(req, timeout=8).read()
    except Exception as e:
        print("[capture] log webhook failed:", e)

    return JSONResponse({"results": results, "correct": correct_count, "total": len(cset["checks"])})


# ------------------------------------------------------------------ page
PAGE = r"""<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Performance Lens Studio &middot; Week %%WEEK%%</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow:wght@600;700;800;900&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&display=swap" rel="stylesheet">
<style>
:root{--navy:#040A1C;--blue:#1E88E5;--blue-2:#4AA1ED;--blue-3:#7BBDF4;
--ink:#EDF2FB;--body:#C2CCDA;--grey:#8b98b4;--grey-2:#5f6d88;--line:rgba(123,189,244,.14);--paper:#0c1930;
--good:#34D399;--bad:#F87171;--amber:#FBBF24;--radius:16px;
--shadow:0 1px 2px rgba(0,0,0,.45),0 18px 42px rgba(0,0,0,.5);--shadow-sm:0 1px 2px rgba(0,0,0,.45)}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(120% 90% at 50% -8%,#0b1a3c 0%,#040A1C 55%);background-attachment:fixed;
color:var(--body);line-height:1.62;-webkit-font-smoothing:antialiased;font-family:'Inter',-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif}
h1,h2{font-family:'Barlow','Inter',sans-serif}
button,textarea{font-family:inherit}
.btn,.opt,.tap,.send{transition:all .16s ease}
.topbar{background:var(--navy);border-bottom:1px solid rgba(123,189,244,.14)}
.topbar-in{max-width:760px;margin:0 auto;padding:14px 20px;display:flex;align-items:center;gap:12px}
.logo{width:34px;height:34px;flex:none}
.wordmark{display:flex;flex-direction:column;line-height:1}
.wordmark .t{font-family:'JetBrains Mono',monospace;font-size:9px;letter-spacing:.32em;color:var(--blue-3)}
.wordmark .n{font-family:'Barlow',sans-serif;font-weight:800;font-size:15px;letter-spacing:.12em;color:#fff;margin-top:3px}
.studio-tag{margin-left:auto;font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:600;letter-spacing:.18em;color:var(--blue-2);border:1px solid rgba(74,161,237,.4);border-radius:999px;padding:5px 11px;text-transform:uppercase}
.hero{background:radial-gradient(120% 150% at 82% 0%,#13294f 0%,#040A1C 62%);border-bottom:1px solid rgba(123,189,244,.12);position:relative;overflow:hidden}
.hero::after{content:"";position:absolute;right:-70px;top:-70px;width:280px;height:280px;border-radius:50%;border:1.5px solid rgba(74,161,237,.16);box-shadow:0 0 0 40px rgba(74,161,237,.05)}
.hero-in{max-width:760px;margin:0 auto;padding:30px 20px 34px;position:relative;z-index:1}
.eyebrow{font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;letter-spacing:.22em;color:var(--blue-3);text-transform:uppercase;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.eyebrow .dot{width:6px;height:6px;border-radius:50%;background:var(--blue)}
.hero h1{font-weight:800;font-size:33px;letter-spacing:-.01em;line-height:1.08;margin:12px 0 8px;color:#fff}
.hero h1 .pd{color:var(--blue)}
.hero p{color:#b9c6de;font-size:15px;max-width:52ch;margin:0}
.wrap{max-width:760px;margin:0 auto;padding:22px 20px 96px}
.card{background:var(--paper);border:1px solid var(--line);border-radius:var(--radius);padding:24px 26px;margin:16px 0;box-shadow:var(--shadow)}
.seclabel{font-family:'JetBrains Mono',monospace;font-size:10.5px;font-weight:600;letter-spacing:.18em;text-transform:uppercase;color:var(--blue-2);margin-bottom:6px}
.card h2{font-weight:700;font-size:20px;letter-spacing:-.01em;color:var(--ink);margin:0 0 4px}
.hint{font-size:13px;color:var(--grey);margin:4px 0 14px}
label.fld{display:block;font-weight:600;color:#dbe4f4;margin:16px 0 8px;font-size:15px}
label.fld:first-of-type{margin-top:0}
textarea{width:100%;min-height:74px;border:1.5px solid var(--line);border-radius:12px;padding:13px;font-size:15px;resize:vertical;color:var(--ink);background:#0a1730}
textarea:focus{outline:none;border-color:var(--blue);box-shadow:0 0 0 3px rgba(30,136,229,.22);background:#0b1a3a}
textarea::placeholder{color:#5f6d88}
.taprow{display:flex;gap:10px;flex-wrap:wrap;margin-top:8px}
.tap{flex:1;min-width:120px;border:1.5px solid var(--line);background:#0d1c3f;border-radius:12px;padding:13px;font-weight:600;cursor:pointer;text-align:center;font-size:15px;color:#dbe4f4}
.tap:hover{border-color:var(--blue-2);transform:translateY(-1px);box-shadow:var(--shadow-sm)}
.tap.sel{background:var(--blue);color:#fff;border-color:var(--blue);box-shadow:0 6px 16px rgba(30,136,229,.28)}
.scene{background:#0a1836;border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin:14px 0}
.stitle{display:flex;align-items:center;font-family:'JetBrains Mono',monospace;font-size:11px;text-transform:uppercase;letter-spacing:.12em;color:var(--grey);margin:0 -18px 12px;padding:0 18px 11px;border-bottom:1px solid var(--line);font-weight:600}
.stitle::before{content:"";width:9px;height:9px;border-radius:50%;background:#e0655a;box-shadow:15px 0 0 var(--amber),30px 0 0 #46c07f;margin-right:40px}
.scene.good{background:rgba(52,211,153,.09);border-color:rgba(52,211,153,.38)}
.scene.good .stitle{border-bottom-color:rgba(52,211,153,.38)}
.bubble{background:#0f2246;border:1px solid rgba(123,189,244,.16);border-radius:14px;padding:10px 14px;margin:8px 0;font-size:15px;color:var(--body)}
.bubble b{color:#eaf0fb}.bubble.lead{border-left:3px solid var(--blue)}.bubble.col{border-left:3px solid var(--grey)}
.scenenote{font-size:14px;color:var(--grey);font-style:italic;margin-top:12px;padding-top:12px;border-top:1px dashed var(--line)}
.simblock{margin:0 0 18px}
.q{margin:0 0 10px;font-weight:600;color:#e4ebf7;font-size:15.5px}.q .qnum{font-family:'JetBrains Mono',monospace;font-weight:600;color:var(--blue);margin-right:2px}
.opt{display:block;border:1.5px solid var(--line);border-radius:12px;padding:12px 15px;margin:8px 0;cursor:pointer;font-size:15px;background:#0b1a3c;color:var(--body)}
.opt:hover{border-color:var(--blue-2);background:#0e2247}
.opt.sel{border-color:var(--blue);background:rgba(30,136,229,.18);box-shadow:inset 0 0 0 1px var(--blue)}
.opt.good{border-color:var(--good);background:rgba(52,211,153,.15)}.opt.bad{border-color:var(--bad);background:rgba(248,113,113,.15)}
.opt .lbl{font-family:'JetBrains Mono',monospace;font-weight:600;color:var(--blue);margin-right:9px}
.simwhy{display:none;font-size:13.5px;color:var(--body);background:rgba(30,136,229,.13);border-left:3px solid var(--blue);border-radius:8px;padding:11px 14px;margin-top:8px}
.simwhy.show{display:block}.verdict{font-weight:700}.verdict.v-good{color:var(--good)}.verdict.v-bad{color:var(--bad)}
.btn{border:1.5px solid rgba(123,189,244,.32);background:transparent;color:var(--blue-2);font-weight:600;padding:9px 16px;border-radius:999px;cursor:pointer;font-size:13.5px}
.btn:hover{border-color:var(--blue);color:var(--blue-3)}.btn.small{font-size:12.5px;padding:8px 14px}
.revealwrap{margin:16px 0 4px}.reveal{display:none;margin-top:12px}.reveal.show{display:block}
.goodcap{font-size:14px;color:var(--grey);margin:12px 2px 0}
.yourturn{border-top:1px solid var(--line);margin-top:18px;padding-top:16px}
.yourturn label{display:block;font-weight:600;color:#dbe4f4;margin-bottom:8px}
.send{background:linear-gradient(180deg,var(--blue-2),var(--blue));color:#fff;border:none;border-radius:999px;padding:15px 40px;font-weight:700;font-size:16px;letter-spacing:.01em;cursor:pointer;display:block;margin:26px auto 0;box-shadow:0 10px 24px rgba(30,136,229,.32);font-family:'Barlow',sans-serif}
.send:hover{transform:translateY(-1px);box-shadow:0 14px 30px rgba(30,136,229,.4)}.send:disabled{opacity:.55}
.err{color:#fca5a0;font-size:13.5px;text-align:center;margin-top:12px;display:none}
.foot{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--grey-2);text-align:center;margin-top:18px;letter-spacing:.04em}
.scorewrap{display:flex;align-items:center;gap:20px;margin:6px 0 14px}
.ring{width:96px;height:96px;flex:none;position:relative}
.ring .val{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.ring .val b{font-family:'Barlow',sans-serif;font-weight:800;font-size:26px;color:var(--ink);line-height:1}
.ring .val span{font-family:'JetBrains Mono',monospace;font-size:9px;letter-spacing:.14em;color:var(--grey);text-transform:uppercase;margin-top:3px}
.scoremsg{font-size:15px;color:var(--body)}.scoremsg b{color:var(--ink)}
.resitem{border:1px solid var(--line);border-left-width:4px;border-radius:12px;padding:14px 16px;margin:10px 0}
.resitem.ok{border-left-color:var(--good);background:rgba(52,211,153,.08)}
.resitem.no{border-left-color:var(--bad);background:rgba(248,113,113,.08)}
.resline{font-family:'JetBrains Mono',monospace;font-weight:600;font-size:12px;letter-spacing:.06em;margin:6px 0 2px;text-transform:uppercase}
.resitem.ok .resline{color:var(--good)}.resitem.no .resline{color:var(--bad)}
.rescorrect{font-size:14px;color:#eaf0fb;font-weight:600;margin:2px 0 6px}
.reswhy{font-size:13.5px;color:var(--body);background:rgba(30,136,229,.13);border-left:3px solid var(--blue);border-radius:8px;padding:11px 14px;margin-top:4px}
.thanks{text-align:center;padding:30px 22px 12px}
.thanks .tick{width:56px;height:56px;margin:0 auto 14px;border-radius:50%;background:rgba(52,211,153,.16);color:var(--good);display:flex;align-items:center;justify-content:center;font-size:26px;font-weight:800}
.thanks h2{font-size:21px}.thanks p{color:var(--body)}
</style></head><body>
<div class="topbar"><div class="topbar-in">
  <svg class="logo" viewBox="0 0 40 40" aria-hidden="true"><circle cx="20" cy="20" r="16.5" fill="none" stroke="#1E88E5" stroke-width="2.4"></circle><circle cx="20" cy="20" r="9.7" fill="none" stroke="#4AA1ED" stroke-width="2" opacity="0.75"></circle><circle cx="20" cy="20" r="4" fill="#1E88E5"></circle></svg>
  <div class="wordmark"><span class="t">THE</span><span class="n">PERFORMANCE&nbsp;LENS</span></div>
  <span class="studio-tag">Studio</span>
</div></div>
<div class="hero"><div class="hero-in">
  <div class="eyebrow"><span class="dot"></span>Week %%WEEK%% &nbsp;&middot;&nbsp; Communication &nbsp;&middot;&nbsp; The Clarity Loop</div>
  <h1>Your check-in<span class="pd">.</span></h1>
  <p>About six minutes: a short simulation, a few quick checks, and one reflection on how the week went.</p>
</div></div>
<div class="wrap">

<form id="form">
  <div class="card"><div class="seclabel">Your week</div><h2>How did the practice go?</h2>
    <label class="fld">Were you able to try it this week?</label>
    <div class="taprow">
      <div class="tap" data-v="Y" onclick="tap(this)">Yes, a few times</div>
      <div class="tap" data-v="P" onclick="tap(this)">A little</div>
      <div class="tap" data-v="N" onclick="tap(this)">Not this week</div>
    </div>
    <label class="fld" id="story_label" style="margin-top:18px"></label>
    <textarea id="story" placeholder="Share as much or as little as you like (optional)"></textarea>
  </div>

  <div class="card"><div class="seclabel">Simulation</div><h2>Spot the gap</h2>
    <p class="hint" id="sim_intro"></p>
    <div class="scene" id="sim_scene"></div>
    <div id="sim"></div>
    <div class="revealwrap"><button class="btn" type="button" id="goodbtn">See what good looks like</button>
      <div class="reveal" id="goodex"></div></div>
    <div class="yourturn"><label id="yt_label"></label>
      <textarea id="yourturn" placeholder="Type your reply (optional)"></textarea>
      <button class="btn small" type="button" id="modelbtn">Reveal a strong example</button>
      <div class="reveal" id="model"></div></div>
  </div>

  <div class="card"><div class="seclabel">Knowledge checks</div><h2>Six quick checks</h2>
    <p class="hint">One answer each. You will see how you did the moment you send.</p><div id="checks"></div></div>

  <div class="card"><div class="seclabel">Reflection</div><h2>Looking back</h2><div id="reflection"></div></div>

  <button type="submit" class="send" id="send">Send my response</button>
  <p class="err" id="err">Please answer the six checks before sending.</p>
  <p class="foot">THE PERFORMANCE LENS STUDIO &middot; PRIVATE TO YOU, PLEASE DO NOT SHARE</p>
</form>

<div id="postsubmit" style="display:none">
  <div class="card"><div class="seclabel">Results</div><h2>How you did</h2>
    <div class="scorewrap"><div class="ring" id="ring"></div><div class="scoremsg" id="scoremsg"></div></div>
    <div id="resultlist"></div></div>
  <div class="card thanks"><div class="tick">&#10003;</div><h2>Thank you</h2><p>Your response for this week has been recorded. See you Monday.</p></div>
</div>
</div>

<script>
var C=%%CONTENT%%, SUBMIT=%%SUBMIT%%;
var state={completion:"",sim:{},checks:{}};
var L=['A','B','C'];
function el(id){return document.getElementById(id)}
function tap(t){state.completion=t.getAttribute('data-v');t.parentNode.querySelectorAll('.tap').forEach(function(x){x.classList.remove('sel')});t.classList.add('sel')}

el('story_label').textContent=C.story_prompt;
var refWrap=el('reflection');
C.reflection.forEach(function(r,i){var lab=document.createElement('label');lab.className='fld';lab.textContent=r;
  var ta=document.createElement('textarea');ta.id='ref'+i;ta.placeholder='Write a line or two (optional)';
  refWrap.appendChild(lab);refWrap.appendChild(ta)});

var S=C.simulation;el('sim_intro').textContent=S.intro;
var sc=el('sim_scene');sc.innerHTML='<div class="stitle">'+S.scene_title+'</div>';
S.scene.forEach(function(b){sc.innerHTML+='<div class="bubble '+b.cls+'"><b>'+b.who+':</b> '+b.text+'</div>'});
sc.innerHTML+='<div class="scenenote">'+S.scenenote+'</div>';
var simWrap=el('sim');
S.questions.forEach(function(item,qi){var blk=document.createElement('div');blk.className='simblock';
  var h='<div class="q"><span class="qnum">'+(qi+1)+'.</span> '+item.q+'</div>';
  item.opts.forEach(function(o,oi){h+='<label class="opt" data-c="'+(oi===item.correct)+'"><span class="lbl">'+L[oi]+'</span>'+o+'</label>'});
  h+='<div class="simwhy"><span class="verdict"></span> '+item.why+'</div>';blk.innerHTML=h;simWrap.appendChild(blk);
  blk.querySelectorAll('.opt').forEach(function(op){op.onclick=function(){var ok=op.getAttribute('data-c')==='true';
    blk.querySelectorAll('.opt').forEach(function(x){x.classList.remove('good','bad')});
    op.classList.add(ok?'good':'bad');var fb=blk.querySelector('.simwhy');var v=fb.querySelector('.verdict');
    v.textContent=ok?'Correct.':'Not quite.';v.className='verdict '+(ok?'v-good':'v-bad');fb.classList.add('show')}})});
var gx=el('goodex');gx.innerHTML='<div class="scene good"><div class="stitle">A better version</div>'+
  S.good_scene.map(function(b){return '<div class="bubble '+b.cls+'"><b>'+b.who+':</b> '+b.text+'</div>'}).join('')+
  '</div><p class="goodcap">'+S.good_cap+'</p>';
el('yt_label').textContent=S.yourturn_label;el('model').innerHTML='<b>'+S.yourturn_model.split(':')[0]+':</b>'+S.yourturn_model.split(':').slice(1).join(':');
el('goodbtn').onclick=function(){var s=gx.classList.toggle('show');this.textContent=s?'Hide what good looks like':'See what good looks like'};
el('modelbtn').onclick=function(){var s=el('model').classList.toggle('show');this.textContent=s?'Hide example':'Reveal a strong example'};

var cw=el('checks');
C.checks.forEach(function(item,qi){var blk=document.createElement('div');blk.style.margin='0 0 18px';
  var h='<div class="q"><span class="qnum">'+(qi+1)+'.</span> '+item.q+'</div>';
  item.opts.forEach(function(o,oi){h+='<label class="opt" data-i="'+oi+'"><span class="lbl">'+L[oi]+'</span>'+o+'</label>'});
  blk.innerHTML=h;cw.appendChild(blk);
  blk.querySelectorAll('.opt').forEach(function(op){op.onclick=function(){state.checks[qi]=parseInt(op.getAttribute('data-i'));
    blk.querySelectorAll('.opt').forEach(function(x){x.classList.remove('sel')});op.classList.add('sel')}})});

el('form').addEventListener('submit',function(e){e.preventDefault();
  if(Object.keys(state.checks).length<C.checks.length){el('err').style.display='block';return}
  el('err').style.display='none';var btn=el('send');btn.disabled=true;
  var answers=C.checks.map(function(_,i){return state.checks[i]==null?-1:state.checks[i]});
  var payload={completion:state.completion,story:el('story').value.trim(),
    reflection:C.reflection.map(function(_,i){return el('ref'+i).value.trim()}),
    checks:answers,yourturn:el('yourturn').value.trim()};
  fetch(SUBMIT,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})
    .then(function(r){return r.json()}).then(function(res){showResults(res)})
    .catch(function(){btn.disabled=false;el('err').textContent='Something went wrong sending your response. Please try again.';el('err').style.display='block'})});

function showResults(res){var out='';
  res.results.forEach(function(r,i){out+='<div class="resitem '+(r.correct?'ok':'no')+'">'+
    '<div class="q"><span class="qnum">'+(i+1)+'.</span> '+r.q+'</div>'+
    '<div class="resline">'+(r.correct?'✓ Correct':'✗ Not quite')+'</div>'+
    (r.correct?'':'<div class="rescorrect">Correct answer ('+r.correctKey+'): '+r.correctText+'</div>')+
    '<div class="reswhy"><b>Why:</b> '+r.why+'</div></div>'});
  el('resultlist').innerHTML=out;
  var pct=Math.round(res.correct/res.total*100);
  el('ring').innerHTML='<svg viewBox="0 0 42 42" style="transform:rotate(-90deg)"><circle cx="21" cy="21" r="15.5" fill="none" stroke="rgba(123,189,244,0.16)" stroke-width="5"></circle><circle cx="21" cy="21" r="15.5" fill="none" stroke="#1E88E5" stroke-width="5" stroke-linecap="round" pathLength="100" stroke-dasharray="'+pct+' 100"></circle></svg><div class="val"><b>'+res.correct+'/'+res.total+'</b><span>Theory</span></div>';
  el('scoremsg').innerHTML='You got <b>'+res.correct+' of '+res.total+'</b> right. Your answers are saved. Here is how each one landed, and the why behind it.';
  el('form').style.display='none';el('postsubmit').style.display='block';window.scrollTo({top:0,behavior:'smooth'})}
</script></body></html>"""


# ------------------------------------------------------------------ brand assets
# Official white-on-transparent horizontal lockup, served so emails can reference a stable URL.
from fastapi.responses import Response as _RawResponse
import base64 as _b64

_LOGO_NAVY_B64 = """iVBORw0KGgoAAAANSUhEUgAAAggAAAB5CAYAAABcHdkuAABFgUlEQVR42u19d5glRdX+e7rvxM27rCxsIiNJQJAgCCygCAgKsqNi/lBBFOUnKEE/ZtePLMGEioJ+SFBnFQl+KoISJAqSQeIubCBuDpPu7X5/f9SpvTW93ff2nbA7O1Pv8/TTM327q6uqq845deoEwMPDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw2ODg6SQFN8THh4eHh4eHmuFg7S/PTw8PDw8PLyQMInkWN8THh4eHh4eXigI9Lw3yaUk55Gcpte8JsHDw8PDw6OfEGwEQoHoEQCoIxkC+BCAcQC2ALCXXqsjGXhBwcPDw8PDYwgKCMrkQ5IFkoGIUI9YRLpEJAKwGgABxABWikgkIt16D7UcW0Y4LIWGmW0h2lg+ZraFiY4WtLF8rY0hkv3UyqBHGa0M/JTx8PDwGB4YFIxTtQMBgMgy+MRvE/WYAGAkgM8CmKm3XALgHwBWAlgK4C0RWVLhHbGIxP7Te3h4eHh4DEIBQVf1oYiUEtcnA9gDwF4A3gVgWwDvADA2h8ajCGAZgDcBvADgUQAPA3hMRBYnhAVRYYFD53NSACFImXrha1cH9fVTomLn0rCueQKLHXPnnznlRLQywGyJp1+wcHeEhbOjNd0nRgg7C83BNQHl0lfPnPTgHley7t8nSnHKhQs/X2gaf3TcvmwkGprr0L3m8flnTjkVpGBI9ZuHh4eHRxKFDaQtEN0qKOm13QAcDuCDAHYFMKaXxdepMPEOALsA+Khef5vkwwBuA/BXEXnBqU8hTXOxUWMWRJr4bEyMKjSP/xiLHdeTfA6gYCcjFAqiadK8yXGNXPVfz52xSceWP+w4Ll697CYAD67oNIKYEIfExfYPUjA7AEZA8LqfMh4eHh5eQBgIjUGgggFITgJwHIDjAeydoR2IACwGsADAIgBvqHZgPwCH6D03AHgZwOYANtPzVJjtCIuJAI7Qo4Pk3QCuBXCLiKzW+oQbv0ZB6/7sHJk/p+WSzb87d/tAgmOCzhWnvfrtrd90bQjIui52rip1RF0HTj9vUQe66ksQ6UwU2ImoOC8U/jFuf33l/O/saAQErz3w8PDw8AJCPwsGEcltAZwM4JPKuF3EAJ4F8ACA+wA8AeAVEVmeKPObAA7Wf38lInckft8EwDYAdgfwPgD7ANhSf25STcUHAcwleRWAq0TkbSsoWCFmo0YbQ77y2iYAwmJ980S0cTGeAcuSVwlh0FRg0H0dSIZ1jQVGK3oy/gAdQX3zDnGp60kWRj+8Y+vTBz87a6eiFxA8PDw8vIDQV+EgUIPASOMVfBPA5wGMSNz6bwA3A/g/AE8kGbQVMmC2EEow9gjWfmKcbhOEAIrqybBYNQ8PAvgpyWYAe8K4Rx4NYHt9disA5wM4heSPAVwhIitsvIWN2pixRaLgewtKBEuhxCW0SORqEEIUwKhYKsR1e4VB0N7d3T4PDKWnPiJojjpWPLHg7Gm7rb04208aDw8Pj+GAAXNbI1kQkZhkHcnTATwG4KuOcLAKwK8BHCAie4rI/4jIoyISuW6OJEXdHCMVAEoA/g6gC8DrAP6l17otQ9e4CWvdHEWkXUTuEZFvAdhNhYQ/wWxhAGZr4jwAj5A8XoWMWAWPjRZxFNSFzRMKEYN128FSY9g8rlBX37h0cseExUHzuAIYNAJAcakRvgjWh01jdp164cLrp1229MZpFyw8Xz+ujzXh4eHh4QWEmgUDUc1BieQ+AO4F8D0A4x3B4HIAu4nIZ0Xkn1agcASCSERKblwDXdFHev4HgJ0BvFtEXrVChHMfnTIiV2AQkU4RuVVEjoLZerjeERS2AXA9yZtJbqVt2PjiKOz4jO2L+XH7kkvqgbcAALPA8jZD9FzcvuSSJVFX16LxYLRm6SURi08BwBZqPArhHAR1lwuxWhAsRWKrx8PDw8PDI69wEDp/n02ymz1xjdogrL3ffaYWISTt7xoEmNBuI+i1fUjelqjrYpKfdIUe/4U9PDw8PDxqZ9oFPU8geYsy2UjPT5B8v3tvXxluf4RVtlEbnf8/Q/J1rXOs5x85bQs2so8iB7ayYOIjZP1mcGArC2mRFA9sZQGtLBzYykKPyIseHh4eHh41CAc7kfxPQji4XI0EkVy590ZzoEw9eUhfhAVbjv49meQcrXtRz38jOTGpJfHw8PDw8PCoLhzsR3JJQkV/jHNfWGO5Ums+BX2m4Noz9KYt+vepKuRYQedpktO9kODh4eHhMRzQVxV9QQ35ZgC4BUAzjOHjkwA+LiL/qSVSoePOiLRYBCRHABgN4wnRCJOwqQNAO4Dlsm6gH8v0c+dfcCM96rbIdTCRGQFgLoAPiMjLG0O8BO3P3n5j1vDN+t2I0/FI6cu2zqBoQ57xlvJ+av3jwfKtc3wP1hJorNq3rcXNOO84qbHMin1aw/ftc336cZwMxDYpxcdG8UgMtFDPB5JcTbKkK+27SY5PrsjzaAsS1xpI7kXy6yR/TfJhkgsS76L+vZLkXJL3kfw5yS+RfFfCEFFq8UggWafnHbRsi7kktxgumgSrwRkCbQgGUX1qHYuF9eFJ00+2QdKf963vsgbTex2NqGyM49xjmGoQ7OqZ5B4wMQlGwgQqug3AsSLSnneF7d6ng/tgmEyNhwDYui/zC8AzAP4K4Hci8kjaO3NqSKZrOe/Un54DcKCIvOUEgxpUmgMRIckmGNfNWqX7bgCLRWRpYuVBJ522fUezfqf+WkEEADptvgySU2DCZke9aMNbbhTOZDhtpw2N2k/9Oa+6ReT5SuNd/5+u/bc9jAYOMDE+XgIwN5E3JEwLIqZt2BTApF70UwnA224G1OS3TlzfHibAGhNzrQBgoYgsSbodVxifW8NoA+OUMbBMRBbUMOa3hYmSGlf4JiUAz1ebr079NgEwOaVPAwCrRGRejrZOBTAuo42rRWRuNbqo/2+l42Q7GO1pTePE+c0+H/fjWH9Zab54TYLXHLjGfAsda/+/K6HNpcZybQRINpM8ieSjCVfDWA0F045uPdJ+K6WU83eSxzn1D3LW02pKppJ82SnzXpL1gzFOglPnyxwtSy0oknxbv8dlJPdO+f72HZf38h1ZsN98hmqR3kx4ldTShjdJ/ovkBSR3SK78nDb8zwC14QOJ99jzSJJfJvlPkmsqlNNF8hF1Gd48Zd7Yc53ayPSmn0pqL/QYyUtJvjvlW1s7o08k7HKYeOcrJDerNLecPphJsjOj76j2TJtVoidOWYcrLajUdlvv0yppN63Bs67GH0kYXLt1bCd5VJom0em3zRy7rLS6dZDcKdlGp13j1BbqAb03C936/WY52k1JGecHOobX/QE7X34yXDSqHvlUo/U6aC3+RXJUDcKB61r4XySfTyGuJYfh94Y4l5wyXDxE8kNpdcnBcLdTN0g7MX5VidgMAgEh6Y3RF/xWU3H3iF9B8nf9+A6X6LSQHOP8H/ex3A6SF5NscMey/n31ALXhUw4Dt+/6KMkXU5hXUshNMqW3SJ6SZGSOgP1mP/VTRPIXJMc4AokVEE6r0E+2zTdkzSvHC2kcydcqMF+LbXIKCNfl+H6uy3WmAbPTp00kF2XUseRsNzYny3MEhK2c9sQZ7dwn0Rb77CdV4Kp1nCwneXaSZjtCWX8KwracW72AMDRR636VVV1dBhOFMAbwGoAPi8gqVW3FVQSMQLcn9iT5TwBXq9os0vKoaqtQ1ZaW+b4Ok1vhDwCuBPB9AD8AcBWMgeQjMPkXRJ8J9YCWG+mxF4BblbFNt6GdK+rQzD0FVeMdo+UUAXyO5Ik24uIg/L7dvdyasUesalkC+BiA+0m+S8eAHTvF/pRtnHPJOaPGLYy0NjTC5AL5swqzkmgDB6gNOoQkInkugN/rdkZJxxG1HoXEESTqPxHAD0leqwzbNVij8x3Yy+9t3yMAvgDgLpKTdD6n9VNyiyHQ5z9B8gMZ88pux50HE9685LQz2X+lSmpwG3FVDZdnOPSMGW0UPe8E4J26hRBU6ZdiRltDrd+WAM5M9FGyjFJGGfZstwLE0k+Sl8AYR093+iHvOBkD4DySf9K+cbeSSxnfb0PQGY8hpj2wUuhHHGm9m+R780iPCRXaNx31YslR/7mS7VKSN6kqdneroajyjnEk99WVzu0JtVxJpXZXRfoWyZak6rZC+XYldYLTB+0kd8yrPVnP3+qGflwZ26iYC1V1at9x/QCtvj9KcrSq2ftjZRw7Zd1kV/Z6vnKA2vAJ55uc47wj6mX97Te4NvGd3dVu3A/1t/30gG7z2HH/9Sr9FOn7nyfZmNgOsXXdJ2Wup62sS7rvnjqvnPLen7HKz9p2YqVtBqe+jSRfrVC2pSXtJLdxo6065y2dd2ZpEPZKjMXz+3Gc/EnrZcs+doA0CDd6DcIw1iDopLFGOz9VabWg0vP9urqOKjEslYxHkmwDcDGABpWeA0c6DmFSPH8VwM4i8hER+amIPKYaCrvFETrxDuz/IiLLROQBEblURN4PYFcArQBe0bLFeVekq7LfkbzA5n2oxORVU1AQkasB/K/2QROAq3Ry9Clg04aSJxJHFup0RTUZwOXO95ZevCPvgV6Wnfr5ANRrGz6sSbmKfeinPIcN4nUoTB7Mko7DrNVm5GgV0upfp6u1T6nmKqphvNXSv7af9gHwdU2GlpeexKoRPEtX1mGCqV+B/skBY9t9tKMlHIhnKpVFnf+XqXGeZGiTqhcmUlS36rO07/tjnBwJ4LT1MM69YeIw32KwqsGLYCylAwC3i8hlNs5BFeEgUiOrv8N4KJQctZ/dTngWwKcBvEdErhCR17KyOjqJmErO/0wEVwpE5AUR+S5MBsfTALyh74odwSQCcCbJNpL1KshU6hf7+9dg4iIQwL4ATk6o3jcWSOKIK3zPOv2tRT1Y8o4hqeEIHSLHXpYdVyD+9rufZVdWveynPG0IlHFcligjich5zj6b9Q0K2rbzSE7IYEx5688K77Hz5Bskx9Xwra2QcAbJHVSorte58TUA79Z39nW1GZGsB/DBGusGAHuRnJZjrldDqG05iuSRGdsqeeNL1OnCydazv8bJt9XDBX0YJ1mH3epq8Kx0mAoIDoPfF8DnddCtBnCSrl7iLNcWx95gMoA7YPb/i87gDfT/WSoYXKeSdKFSVscKUribxTG2BlYiskJELlNB4SpnAtr9xKIKLjepERuzVmYqKImIrAJwssOQZqvVdcyNxxc5ggky1Q5gDYBOR5PDCisMAfCJnEQn0rLbcxz2vhUA5ulKttp373Kec9uQtR9tCfjOAPIKOXHO+ts6rAGwEsAzOm920TLCjLJDvf9uAHc6giwrMOAJKlAjJ7PtTvRTh8NsWIE2bArgoBqFQSrT+JGlESSn6TyP+ypEK02iChvbOFrBPHWz9iiHuYHZ+kGTcJm6FecV2JLjcYbSp2rjZLGOkTv17zBDGLbjZKzStrzjpKOG+bpS73/Ws9JhCifXwT+dvacz9LdCpef0PMFxwSomzs8rAV078fOrTCmpSYjS6yKJMMozHfejUmKP/WabxKlSXZx92RucfrnCUaVuyG9WzQbB/n+j2hNMcc6HkLy1wt6r7a+H9B2/yXiHve8WLXuynqsdm9sVD8lpjhtgnGGV/rFEG6aSPFI9a7LaYOv6FX3P1VXacIdTt83yHlr2lY5nTZZl/U3KQO33G0/yB1W+QUzyHr1/hOMVEGe09cuJfppM8iAni2lWP8UkL9X3nFaDrYbtu8/oszfl3P+uaoPgzL1ze2E7snZcZpSd1wYhrY+/42gDQHILh65k2SBYG64f5xgnv3a0ASC5qV6r9v1ucugeM9zASXIZyZ1rGOuT9L6C55TDUziwjOZIZyC9kDRAymDIVtV/e4Zw8Ge1aageKa61NUAbQ7TeWUBryup8ZlsIm22wMlMXh7jskCK42Mn8wzwCkJa3BclVOkE7kgZLg1xA+HWFMm7NICaWEC3Q+66twlxv6GUbJKeAcGDG82PVcC+uwDS/n1NAuKW330H909MIuP3/GYehhAkX4D9VIehL1BW0kJKFNNnW4yqM46cz6lhMuC7WIiBYg8WXNMZJXkPCPAKCdZd8rIrQEVe4ttyhP9JHAcEaLK5WemDLmJ5DQLBujvdltMX+/2hiXLnj5FFHuHANvm2cmGf0vmOqjKe3SY72nM8j7xaDVbWf7ajOZmnOg0pRswLdc7wUwKHOtkJJz38AcLSILFZ1YSm1rJkM0coAs2fHaJEIs2eUMFvdKFtZQOudhoHPaYkwW0pokQgiNMLEugxatyCsoeF/YKI1/lvrFKFsiHcKyS9Ucl+0rk0i8gqM4Wagqstv1rAvvKERuuFc9WjQb/6LCipVABit2zFRjncUrDV8xhE6RF8cFXIe1Otzdc7zjRpB8W5U3qcdVUM/FTT+R542WO1TA4w7X9pWjFUL/1y31eqtPY1tC4wbb9qz9v/xACarEWG18Wb7p97tJ/3tn4k6JdHobC/VQlsEJvrfT2vYBqiq0dSxsYNu3bCC6lwyrkUw7oAH16B6z7PNMALAJYmxW63P7NicklFn+/x12n53nNTrb79B2SYgcLYJ6/TaljnrIgCadDzXVRjr4hw1J8Xz2HhQqLLPF2kipvfq4HoaQJsSr7jKcx+GMUoqoWzcVgBwE4AWFT6CVO+HVgaYBUJ/m3Lu/MmF5hH7xaXSexEXdyBkIvDaCHA7yoWLVhJ8S6TwFAPez6DpvoUtGiK4jSFmIkaC2VjGLyJvkjwcxj7iXSh7Z0QwPuf3acKprHDKVoC6DMAXlegcT/J/RGThYAzDnEF8ktcE1eMb2LgV1YhDSRlYKW99SPbFKlqcpF3vrCIIr8lZZlSDJT+dUL2jHOaaxbxe1DEUJd4Xk5yHnga1kvKd6vvaT3alXuFbdlf5Pc8Y6y8mYmnPESjHIygkBK8AwPMw++O7YV27B2t5fzSANvSPFb41WPwoycNE5LZK9LUXi7W3rD2HO0702rMwdmHW9mUNjG3OChg7hadzvgMwIaRLfaQhHkNdQHBwsjPBv++swEtpamElkOMB/MRZNVgDm3/BGLdRCdS6zLONodEWANMufuNQkeBLjKPDENSNDhoagTgCWQJiqi1tgCAIAQmPZFwEuzvfmPa9t26WEq58tUUe61FmT+oYqZDwtoZMfQjGIMsO+CYAv8hSYVstgpbxBsnrYNwzRwL4HIBznbYPVljjz1KSGZD8XAWCIDDZM4sV7C0sMTpEI62lGcNZK/rzRORfvRSouvSZ2BmHYwD8N4DdUdko7qWcRPu9JP+UweRsEJtLReRuRx1OFQ7qqggI3SpMIKPsUhUhoKHGfup2+qkRxrvnA8g2jiNMMLS+rK77E3YeH1VBMxMA+BNMcLU0AcF6ABxKcqSIrO6nPAJWk3A5yV3Qv0HEkBwnTg6bv8LkyOgCsKJGBu/24RgAt5DsrNCvfxORH2wEix+PgRIQHO+DqQAO18uvAZiTstrpQVD1ue8C2Bxlv28CWAKTArozPZkIBTPnBGiRaPIFC3YNC/XnS1B3hIR1YNdqxB0rIwgIQiDu4NVJI0YYkbBuktQ3nxij/YTpF799Tbxm8TkLWuQ1tN5ZwOwZpRQhoSAi8zUs7t/QMyrcfgA+LyJXVUmAIgB+BuBE7dNPk7wYQHGQJzBpVmEudDQ82wI4RbU8aUzDrr5erCJk2m+0KYAPVanHvSo81iJQ2fJ/RHKx82wjgC10/GWptW2bHnSIX6V3TIDxKa+EJ2C2NNw29PW799fKFgDOVaNMW796GLX2FhVWl3ab4O4a6zwgKmfLlDTB1V4Z9bbvvgvAqxXuiXVs7g+TiC1A7Ymu0vorgtn+OBnAr2rUIvRWcIhcIc5R+a91RxSRrpz84JAq92wKs/XlNQfDWINgichHYfbVAKBNRFZW0B6EMO5MO8Ko2y1zseevaPazdZ+3A1paoqkXLPp6UKi/QOoamuLOlTG7QQgCiISZ6xEpX2SpSEbLI0AK0jT2hEAmHjHlgvlfWXjWtD9maBJKJOtE5O8kL4Sxt4icPphFcg6AlWnMXoWMQESeUavyQ2ACxewvIv/QfokG6Xc/WuvrBpAa7RD6oAIDuDXnCpEVGLBVD3f1hi7q+V0VVpphxvUAwMMw9ifIIZTkaUPnIJ3jtp920AMZK8O06wJgPoB/JFbvmRoppG+HZI2hWoUJOycPQznQWpgoN9Rv8W8Y9frrMHYgyXba/49SAaG32yeSUcdWmPDvq3RlPqCwGTitpsEVMGvcsYuqzKeVnm0OHwQVJjpUQLDE8Td2C6GSCgzAd3R1EjvCwc0i8rt04YKCWWaSTbvw9Z+GI8Z9n3GxKe5YEQGigoFIj7qR0doDiJDQuwFSAIC4fVkJiDcLG0bdOP2ChaehRaK1ho0JIq+M/LsA/uP0C2EiB56obctUp2vfuBb7MwdIxdqfqIPxkx6j59Eoq/2lAgN4G8YwKg9zdQO7ZB196SM3z4Y9KqnLLeP77zwpv9dTG9YHsvopqCD4WKPkVVU0GnYMPK6Co1QYF5ap/gK1x/CPHcG20u+PisjrGkHwnoxxatv9QTX8K/WiT9PooV21TwBwyfpaHNhYMf2grQxzHB7DVUBw1HhbANhTB/t/7Gorjag6WxLbAjjWkeRFpflvpRjYGOGgDQFmSzz1oteuCUeMOyluX1pCHBMShO4bVCCghPVB0DgqDJrGhEHT6FDqR4RSqBOAsQoM7qwpMOqO2d0RyYjxl0y9YMHZmD2jlBQS7KRSNdyZDrG3BOArmvgkK7RtpGX82ZGw30+yQTUUg5l5JEOmSgXmalff3xSRJTkFhPUxhpMELMhYAVGFogtE5DbHCny4zPU8/eTaPfyviPyqhn6KAZyKsvEnU76B6Dz5gWoB8kYaFKVLEwG8L4N+2bJud67dliGo2xX3Vkrnao1fQgAPINtTgjDG3eM3goWCh0duDYK9dhDKFth/VcGgmkHaCY7qzzKTazUL4rpGLW0I0CLRtAvmXxiOGP/paPWSIiAFowWw0zCOIYEEzWNDqWsURt2L4q5V98SdK/4Yd66+Oe5a8yCj0pKgfmQQNI0OjTaBznskAOMg7lhRCpvGnDft/Fc+jdkzSmhrCxNCgt0quEUnvpslbRqMW2aqFsHmcBCRN1De194KZfX3YI6smAyfmkYIS47G4XIRuaYGpmGfr3T0BRF6ZqnLqoMVWGeLyNl2S2yQtGF9aRBKVdrsZgy8AsAJruo6B8aIyFyYbI3unr4rgEYqRNQqWFrX0YNV0xVlMH3AeCVZ3AWzhZW13QSUbWSkhr4UmNDI9yM9ZLVg49ynrzbOve3BMBcQ7ACY4Vy7PWNFYCX7klpEfyyxWumGsehdd7K0tYVokWjq+QuPDprGnhG3LytBEoGJyEgaRwWQsCvuWv1LRMWD18jKHeafOeXA+WdOOXb+mZt/ZMFZk/ctFvBOdq05Nu5qv1XqGkXqGoMe2gQRAaMgLnbEUjfiZ9MvWfROtLREmNkWZvTHJSl98tkqK+YkcRJnpTNYVw9u4hf3sMTAEmEbw+IsEflGjczVPp92NKIcdru3sGnBpQIxtyvJA0RkluNey35sAzeCuV6oIKza+j8I4EgR+SpqT8Zjt+ouU61jwWGm1P9/LCIvwmxp1TRWVUD/cEad7HbJGwCetL78ABag7OYXZczZI1UQimqYN1Bt4akVxt56mfdOYCY3NoGNx2HHaV5kjfMGPdd5jcjwQSGF2duEI+/Wy8sAPFqBOdqJ9V4Yi2g3d/k/UuMIkIJZszi9dd5YhsEVLHURjIOe1oaMguaxYdy15p4gxNdeOW3SE2t/a2WAnSCYA6AN8esiiwH8EcAft7hw0WFxWPhR0Dhq27hzZVTeqpAApe5ImsY0Rx2dPwM5A7PWVYHqZPs/mFwAWzpM8gCSUyrEN7Bl3Yuyqv69SiwHK/MQVN9TXAXjMnaxiDzubCdVe84S7Ee1Dyp5KNyRQcCrEWmBiUk/H8bLYEIK8bKxLe4WkXt1vznv3rdtw7MAzs9YFdp63OW0QdYjEZWc/fQQgOdU8J+KdY1QrRfLEyLyZzXcLSpdqOmbiEgXyZMB3Ajj9msDpT0GoFXnWC1aF0uXRqkGIW3c2m/1ZxFZmaBrv4fJu8EU2kUAOwHYSUSeqtGoeLwaIv8RwDHonyRUtQ+A8hYpMxZypZxjpBPAN5XmJ8e6vef5rMWixxAXEJxBMRlGRQ4Az2msgCx3PUugjkio3wDgBichSpk5zLorxOzZpfjCL/2/sGnslHjNkhIkKPQQDprGhuxcffX8R+45EXNajHHhs28Tc2bGa6Mprq0xBXMQAHPwSsvk2zY/f+G+hZi/DxrHHBR3rigLCRKEccfKKGwac+D0i14/5tXZm9/ouj/qVkFBCdwfAJzurLKblLhem8Hs7P//gTHieweAna1h5iBzd7ST3W6JuMSASiheBPAMgPtFZKES2rAGwz5b3jMicn0thK7GNpyjjP9rMPvaSSJt/z6D5C9hAs7k9eG29XmhljY4DLUrB3EOqzD/attT1TxALOO/WERuJHmMMm6m1IMAvkDyBwCe66Wve6Rj/S71aBqDsrvzQhFp17FUa1TGCMYlcVOkG1eK8/4jnfbEKMeKCCr0zxEAnkJt7o42UNrpMBFjR2Dg3DzTtLc2KN2BMFtCXSgnR1sJ48WxGsACEbkkxztWA/hZHoPNQey67THAAgJgfOGb9e+nHQJSyphgAHBAYlW6GsAdSjBjV1OI2VKadsGr40ieHHetIiQoT1zGUdA0Now7VrbNP2vzLxjmzxAtFQatGayRahcKr50tSya2Pn1UIza5J2wYuXvctTp238E4ZszoDBjJP8Ls1In4J534rjBwsAoIzGAMIiLLSb6oAsIUGH/8+Rhce5KWKN4mIp/LQQVDVfH2xiK7UVW9lVZmSXV/LQR2pKpRr4cJjrRJgoHY1eoYAF8UkXN7kSejXt9RSQsSpRDNVSpsja6gnXiH1sdlTDaXxwSUty+ywi3n1YY0aRv+oqvA7TP6qQDgVBE5sbf5RHQuhGqT80ZiLBX6EMjnaIfpBxmC1hf1yBI0sso+CiadfS1j3AYam0vyfAAX9EGLUE0QG6vCiDsOAqWtu6kWJAvtMNumeTyOJmpckSx6tU4qdS8sDF1kSeHbOdeeqcA4bEjZTVEOa2sHy+Mi8vo6q5DWu3Q1L8eGzWM3Qanbneyx1DUF7Fozr75z9RfNVgQkGbvASQa1bsbF2VJC652Ft2fvvDpgxycZFdsR1gHQFYtIyK7VCAoN75ly0RvvgQgTtgi2rv8G8Gaij96dGR66J5F6Qc8jAEzvBdNbX6jTPqx3+jN0Em0VbHv7EDUtEpGiiHTqOe1Y66JlU3bX4PlR0lweS1R4SyO2VpX8FU1GE9foWUIbLlrflXakEclOXcWlrQDt+z9pI0HaPkfZoPeTCSE8KcSuBPCmPsMc36Gk4ZWvzKiTXXV/SoMR9SV1eZzYDw+quUlXQFHzfhyWQ6uSZlcT56CBe5LcssZxbvf+6wBcjrKLdNwLGvxalXHycZ0bRTtOdO4QwHH6zmKi3d0q9L1aAw2y87Q7Y65GiblKn4th+AgIFls6f7+cpeJynt8OJvGNe89D6e84KDaTKvgoGBMSsAfnL9RLVOo++6XZ263ELIQ9thPKajXahCXWg6CnkDCjhFYWXj1zy/+w1PmjoGFUADhMXRBJwwgJEB0LANhxpiRWP4GIrIaJjpfsl3doPSoRKTeE72AWEKxWIHL60x6W8fXVjbFB0xGPITkyxzGKZHOtCa+USF2pRDIZ1tkS7UkATqgS06LPcFbQEcy+e1qgJWvoeRjJMxJ9XiQ5E8CXUbahSDJBAnhRjP1NPfK7CwYqSC1L6ScbJbVZtQh9UpfrPI2dg70tB8YVcUtUT/qUFrOi2v0lmG2Iw5yxVBMdVRfp/9cLTaEdh48j3fjSjpP9SV5sXad127KB5Pdgtl4AY0CYbHeI6lFP3XkyxpmHeebrSK9BGLpYZ4tBJ8fmDiF6s8KEsde3dlY69tpTafwIsyXe6sKlY0pc8x52dwjI0NgmMpa6pjBuX/7ipq++9YeFra0BZiOpObAGcmNVrdYN4BER6U7ZL41BSnTRwh+jY8UpkKAZjGgMIUVY6gYpJs/C7FTr5hhme+UDTl+MgjHweiOLcGpfLXQubZaiGhwOsITvcGdllZeQFDU98XzkdxEtiMjzJP+iquhkEh9LuE8leSVMIp+BNCiz3/tW1QRIBkEmgAs1adidOu7eg3KugSw1r90uANLzXGShXrOo3gDgKyhvNyW1CJ8neZFq0eoGwXg6yqExhQH6VkfD7MHXuiq2eV1uU9uljyL/VoO7pXkSsl3PYxgDwmNJPqDX91XamxXwytKdv1dZpNjrY2FcvPNuAUUw7qc/F5H/qdFGyWNj0SA4q2GrKh3jqEjf0mussGqeljLY5q5D4FrNb91h53YS1m/CuEgn5kEs9Y0gwpv+/fM9i8CsAChLpk4ApxNgtj3uBHAfgMdIHqq/les3W2LMgiw6c+pCMv5n0DACoK7iyIBRN0Sw3ZRL548HhEgnCC8liDJgDDjXmWw2w6X21ZvOT+P0WjRMU6M2qlA1GcYmI8+xpWqlumoQEGzf/ihDO2aJ7DQAnxpoLQLKHjF/cgSdOIM4xwAOBDALJprnUSnzyWUogfbNrxJjMw9iJ3dIKaUP3HTIX9V+2lBxPKwKP0TZCLqam2YeZpylCd2f5KQaNH7SkwSsNVhcU4MmwX67O1SQzsp1Y8fP1gA+pUcl4cAai68AMMdh6NXaM6mGeTpdz/t6VjqEBQRn5W0NyqyA0AXj29xg1YQZ5UxMEK8YaXuvO5kJJZFsKfVNZYatikRGJUBwn97rCgehCgCHArhKNRx2n21HADdpytqkEBMAFCK4F1KwCZ2MEiEqAcB4FOsNw5+1TipdOIzeneybZKhBYwAFDSDU4fw0XveIG/uiZt3IEddw2GA+3TVqXeyq505V16YxZPsdT9c97QFb7VjGKiJrAJxTgfDbeZiMP1GpnQGAH4rI3PQIpVW/hYjI0zDxTdLqZbUIJ5GcgNpDIvcrfQKwC4wRXiVhpVaGniYUjQJwsON5lbd+dv4HIvIKjEtsXm8IN4rr2Y7AyApCQsmZJ0GVcXKRiLxeoxCVd64W9dzuWenQ1iDsRvJBAE/q6vw9+vsomFjmT5F8hOQhCY2DHXAjE+V2ohxutYxnVEBA/A6r6e+xAuzuQIzCK3ovUxj2qfq33We2wZhGAPjCuquduwAIIaW5YASwh396LIUGhIYArhVeEliZQlhGpmgOQPIkGJuFpwBc59zyCZitiidI3kpyUxvQZJiNs7yHOOdaYVWcP8kgiJbAbgtgZi/j79ciJFjV8zUAfgujqu/OINQ24FOhgmajqGU8DBNPIOylwLk2E2YG47RMagKAL23AtL52nhxZgeHaa/+tQsSuAHZOHO/S345HduAne/3DOfqUGdoMq8W8FMZTJHdAMY07cROAn+o3LlUQEuw4yQp01w1jl/IPAN/TBUotYyPoxeExVAUEmCiBewPYRolno0O0ttJre8Dkjk+bGIWUVUopS2qNyYakds5EOyzGhbi9K2N1DpRT04YpRH+bdVq300FUEtIORomcTwQkQMy4UsjgtHzudc6kFke1+B0YT47tYFTqFqNhXMq2gQnp+oH1oN7Oq3blenhHX8utpQ1Wrd+GsgdKnPHMt2ognH1po2Uan4fJQVDvMLa8KzqrLatTIfTDItLR2zo6XiJ36IIgTYtgtS2nqM1PnlU6+/n7W41bVihkuyAowoR0f1ZEnhSRZxLHUyLyrApp85GeTMoKpTM070pXDfTT1RpJLw0WqVspXwFwjX5rQfXw2EmaKzrG7oLJi+PahXED0RmPjVxA+CXMfv5LMBavnQ4Rm6fXHocJRIOUAVvKkHJTiUog0pUwnhaQhNQFpaC5IWXm2Hq+klg1wFGzvbSuxuIuUXGiGRKu9XRcWy3GCCSopD6tqyQ0OASBMPvHz8K4OC5IaCGe1/r9FcAdSpzXhzFPAesmY3KP/hBSwirv6O0ROquZrHt6CItW8BKRFUpkxWHEdBhKBKO2thk36weqn6z9jroXHg3geyhnm7T1KyE93LUl7lZb9hsAB1n3YWceVuunNNV8qJESf4aeam03aVcJJlXyF3P2Uy0rSUms3JNHAUAHyakAdkfPkM1uXgfovFuo7rlBxmEFs3udZ5PtjWC2Sw/Svqmr0t66ClqjvwC4CeX4MVnj19XGxlrG52BsGVY4mgKi5zZUMj+CpbndOsYO03ng0uuBmqsFz0qHsICgEvb+jiruYf19FUw+gV0AvFtEbkus6O0kX50otxFG7Z9Y0Wt+cgRvgUTCMDCW+iYEKG2h90oKMfm+/l3nENJ6mO2Mq9bdjz0IAAUsbAUJyzYIOqFY6kJksxI+kyoFj06RkFenaTdE5CoYz4pdYAyILH6jas5dReRwTUPL9WSLsMLpLzchk/1/TT+8Y2XGO3p72LwKq5TYdaPntoOgZ6jdFSkrduvyuCajXpagfUbPyzPaYOuyMucKOlNIsGNTRL4FY9T1W22j3VpIuubZa50qWB4hIsdrIK6kx06pQj/ZNiX3ia0W4XoAr2f0U52jYQSAJRn9ZIWdLidgWLXx3ZlYuUui/pH2z+4wLohByr32+9yiW0uScKuMHdspq424ucJ4tWPKBn3rSLQv2acdFbQBAuAbMO6khZR3WcGgPSFMWoPsS2HC3V+kCzRBz20o9xCYWAc/BrCniHxLPbuS32FFot/6a64u96x0aKLgrNAJEySDJC3RbYBxH+uyFvgZ+5FvOwTUrug3WYeoKhNmyHns7gDEXXGQEhYAYj8AN1t7BUcqD0TkDpJfgLH03txZPXxdDbbWdXWEULBwf7BkbBDMpgBQqAOi0lLUdS8CAMwCnYiK9t2bOgKCvbY4gyIEMPEEYpJNzk9L1Wd5bXCe9SAc2D44E8DPsW4kPjpEBehdsiT7zNkAfoH+CTFLZww9rURuTxi7DyZWnaLanKfsGEkIr3NJ7gbjupXVfvstv6uMMuu++X3opx5Cgq4uHwbwCZJTAOynQuUOMOG8oczehrr+p4i87M5TRyi1zLhb7YPGZfRTrGXB2l04zy4juQ9MfI+s9lt6cD3KsUHS3rM4z/bGWmpg7AXqM8pqF5GVJO+CpmPO2GIQpQGopJVz7E1uVMYbVmiv1QAeCmOHkVY/JvvUXTRo384jubtqJdLK6IZGqnXGr/UYCzUz5pkkz9ExspuWNU6fX6pC25MAnnLCWIeOQOT2+Z0V2t6X+fpKX+eHxyAWECzBIVlHsuQQhEaYULDzVTrPmoDzE4MGMLYL/+wxCGeb3+qjxhdKXLNYwvpNGK11dQzY3QlB9JE9vvTIt/+NWRFAsa6O1o1RRK5WX+PdUCkOQisDzAInNy2YIgjeF3etKQskIrGE9WFcKr2w8LRpSwEK0pn2NinbMYtStAq2fgWNMb+p89MyFQysSnfA4RCGpUpEct3fy3csUSI1UG15rleUyxDol3K+YxmARwain1Kej+yWmea4+J0eldoSZM0/5zu83FuhRUTmJ+Zw1v2d/dVPOlefzHHfSpiopuin99rgVXnKmwezxYo+9O2rjiBey/N2nASaXOzf1fqhWkh0FWQeG2i64zHEthjcMaYf+TVHYt+0woe31y1xcgO27JIyhIhWBnPPHL+CkIelvolYO5glYLEjCprHbvvm9Hd8FLNnx2jtuferTDgUkeUicpeI3J8RJMm0TYQh+dWgaUwzGJfKVoqkFOohwruNMJGaGQ66NeBqFVY5qwtWmCRTnEuv21XB+v64iZDUaYesh3f05ghc5pjnvgwCHeR5z/rop+Q4tgKvE9K6UqjruFoAmkHST0GNYyfoh3fW/H1ytFdqua8PfRvkGCclJ2R1IeMIbSbeah4nOdrUm8OHWh7KGoQUuFLz1hnqPZeRvqDMc5Tz297paqe7NKBQ/AdIcDgYCyQoz6hSN8NC/fnbtL7w55dmYRXAwA237Fhgl/M3JCdF650FzJbS9Avn7YCw8ZS4a1UMMFzbBCJk1xrGCG80mxRzmFh5xiRHqgo02S9vJVTZqKJ5eLWSQLEeNAnRxvyOvrjY5X12ffRThfrFw7Wf8rx3IL5NDe2NN+R3SfQB+2OsbECXVY+hoEFwGL7FTjnUaG/C5Jp3BYndSG62boTDgyLlxDdG7csXo1DvWmMHLHbE0jBiy+7Gkb+ACDELRBuTmoQeuRh6CgcsYPaM0sTWp0fG0nS9hHXNiIpYqz0gI2kYibjU9fDCMyY9bLJFtkQpfbIHyqllLR61WoyMLrHl2GRXazakgODh4eHh4dHfAsKLKFvX7pxgfklYZnmPU0YEY1h26LpRyYRovbMw/6zpyyDyk6BhlIBxmQlLEMYdK6KgaXTL9IveuAotcwK0SITWOwsm62KKOosUtDFEW1uI2VLa/PyFE5qaN7k1rG/ePe5aHfVIJw1AgkACCS8yAshdaaFmgbLvdexc+0eWNsXJbDkWJm4EYHIyvLahBIQqaslCBUEnb/lhlfJ7dTjl96nuqprtaxluHwY2yJWj+i54NauHh8dQhGQwuRAm7sHOMG4624vI22nuSzZBB8mDYZKCWH/qEMBfReTwdWwESMGsWTIdnxvN5oanJKybzFKXiVxUvicKmseGcdeae4IQX3vltE2fcLQEAXaCYA6ANsSugeEWFy46LA4LPwoKjdvGnSsjSFBmAoyjoGlMGHWsuHvBmVNmYBbE3b5wiHw9TFz0LVFOutIBYDsRWZhm8+D0w74wMSUEwB9E5DifxGTABCAZKMOopCX4QD3j4eHhMVjRwwbBTVNL8lEVEMbBuMbchvRwp5ZR3g/j7rKFIyQcTHIHAM/1YKoiRFtb8GrLlsunnr/wK0FDw82MihEYy9qtAJEwbl8eSePIA+Ji10PTLn7jeiGvW43ljyw5Q1a5Is5mlyzapL6I9zEIP8+wcJQIEHeu6ikcgDEK9cJiV3tQF5wEEWJmW1rwmBLJIx3hwK7+78kSDhLC1v7O3/dnaRzWB+MkuS1MqOdkNskYxpf7HhG5vUKbMlfVTm6MA2HcDfsabtUGXFkCE24WMOmOJ6AcIc6t+5MiMidDWLPt3wwmgmFDQoNjy3hCRH7vCho286YV6Ejuot/0XTCRMkeg7KI2TwXJewA8aL1UvEDo4eEx5DQIStwKyiQ/h3K2uEtF5HT7W4VnLgRwBsqRFQsAfiEiX0olmm0M0SLRtAvmXxiMnHhGvHppEZKITsY4RhAGQeNosNgJlroWAXzZMJIgILmpCLYN6kdMQBAg7lhJExCphzaCCMIoaBhRiNuXfmb+2Vtci7a2EC0tUQbjux8mmI39PQRwvIj8pkIf2Gdvg0kRTQB7i8jD65thON/jHMCJ7rAunhSRXWtdiTsM+DEYd9P+xvYwMQEer3LfDBG5K9m/TvtPgEnulYW3AEy2luJWSNYyjoAJdDMjp/DzPEz0xivUf98LCR4eHhs1stKEAiaWt4129kFVn2YRPPvM1TAxzG00uBjAp0luh3JM+jJaEKON4fyzpp0ZrVl6bThyQh3AEujERJYgAGPG7csjFjspYf3koGHUAUHjmGOCxpEfDhpG7CNhYULcvTqOO1ZGJqaCBD00BxLEQdOYQtSx4tvzz97iWrTeWUgRDmzGyKNVOLC2BwGMj/gtWSGSHc+HSQD20ctzUfbz3lCWw0UV1jrRMzRrl3O9L+hKlNfXo+hoC4LEtWT9CeD71mYhwwYgzmh/t55X91SgCUmOJHkNgP8DcIhTj6xwyDbU7fYwWfweJXmYDbnrSYyHh8eQERCcgESvwARFIUyUtz0sI814JhSRF2Eilbkx8BsBXJyeV16IFsRoZbDgjM0/G61Z9rOgeXwBQSBgHLlvgEgIEWHUHcedq6K4Y0UUd6yM2L0mYqloNAYiYYJzlySsD6S+KeSapacvOGvq+cYFckYpyeD13ADgQvRMFCS6KlwDswWRmolPyzgC5fDMt2sEysIG3JO24VCzDhng8nt7wNFApR02VfOuAE7WlXrWKr/Se4LE9x8Bk1DpM+iZdtnNspgMh2z70QojWwP4K8n/8kKCh4fHUNMguNf/4KzmPmGTE2UVpoT2XF2h2djpEYAPk/yYqnIL6wgJswxDnn/mZl+O1iw7VYK6jqBpTAgwBhklsiwFKiyEKhCEGolxbSUAlgAgaB5XAILXo65Vx7561pRL0cYwKRxYBqBM5hwVhtxcE4sAXFklwZI1TDveuTbHETI8BmbsxgBmqeYmrjVQT1LIhQlL/T4dv5XSLmfVp6BjJAZwNcn3eyHBw8NjqAkIsSMg2IQ+LSRHo5zkJUlgI5iwoM/CxOa3woEl5FeQ3FKFhDDxMCEAZraFC86a/INSqXPfuNjxZ6lrDoKmMSEkFBUUSnqOyweitb+BsRTqJGgaW0BYV2JX+9Xx6rf3XHjWtD+abQVJ2x4oiEhRY9mfmahzAGCWZkUL0jQBNrwpyZ1gkrwQJo7Evesmjxp2iLGuWr7aUaph7BLGiPaCdA1VLoS6tXCoCngllFMy9/jUSM+it055zvWrdc7E3g3Sw8NjY0MhazWlWwYLSP4FwHEwyZFaROQq1QKkEXK7ijsHwDEwqWItsZwA4LckDwTQta71uRBzEKGN4aIWeQLAkdMufuNQxKUvATgsaBo9GhICcQSyBMRU2/zAOCtICMZFsLvzDXa33ywlXPnqWRNN3HFjDJlmWGi9FqYBuA49LeULMO6Kv6pmcKYM5iSUs99dqyGgUw0avQDab7B2MZ8l+QsRuT8hfNaivflqlfslY76kadVsit+pAE4QkcsrzBkPDw+PjUdASOAnKiAQwNdJ/q9dESVX1Db2uIgsJXkyTD70CGXV614w6Y8/qqvudd3rWiSyiZbmi9wB4I4p586fHNQV94tLHe9FXNyBkIkARoCgCFbG4FsihacY8H4Wmu5beNrYpWsFg5mIIamaA+vOORHArQAmoWfO+Q4AX3SSpiCljED7YhJMimeqxuV/E5qY4QbLNF+AybQnOZi1dXNcCRNgapec77IunD8guXeN9RQA3Zp9cx/0TPmbFDI6AfwSJnukwNjkHA+gOUNIsG3+OIDLsQFCOXt4eHgMHJUvR467T9MVk+TxlsFWeC7U8w/0mW49F/X8e8f6PHt/diZDtGbsK7eygNY70wWctgrPmXfad29K8hGtUylR1y/U0M6LWcaVVds18N/Ntu/sRL8z0dZ/6X21JruxRn0PJcpj4n1n9KEN79MyYlaHff+J+myDnj+b0f5Iz6/qfds7ZcQp98YkW1LquCvJ+fp7lHjOlrNKBUj4bQYPD4+hJCBYBnikQ/ReINlohYcsBuKEob09QaTt+c8kN7EMrSLxbG0NDNO/s5DK+Ge2hWhlAW0MUaEcG3pX/96B5NOJOlnh4Icuo60iPG2hTCAi2UFyG5t9zQsInKUpxJv0nHYkM8PVa9n71yAgWAb9NsmJzrjNKyDsWqFc+/x4/ebNWu96Z25EJLv0Pnt067mkwcKwIceEh4eHx0BqEf7pEM4z8jBQPU9IYcT2/LyGJl4rkORnVpTUvAxVBAP9fybJJRmag5udlKiSgwnf4PTLFRtaezDIBISz+yCU1iIguO+80inrMzkFhGkq3KW9z7bt51YocITaepKjSbZXqdtuXkDw8PDY2JDHBsEGAfoWjNEeAXyH5BwA87LC9DrxFJaQPAzA7TAuhEUYY74IJuvh3STPA/A9EWl3GFxUOX5A9dgCSpADNRQskdwUxg3zC3pLDLPnbOv0FwAt2kZmvd8xbjwMJpRxDGAFgHOVeXrXRoNNSU6F8Qpw9+Ctx0GXiLzWT++yBotfUDuZB1HdTZE6Rt6Aiao4LaNcAvgigL1UCLxVRN7Q37tJfhImUFJXoo0hgOUw4Zh9ql0PD48hqUWwq7qrnVXR35yVlOR4dnNnxVlM2bd9huSnSNYlNAqFStsZKZqCtc8418eQ/AbJ1xP7yrGzQmxz1MZBFY1KQHIUyZedFecpg0F7MEg0CO571ujq3D3a9foqkvslxklvNQhuPR7SMj5XRYMwj2Sj3nt9xr3JZ0hyMcnfkPy45nvw8PDwGLYCgihT3ESZrCWW33AZUg4hYaQyYpegxwkG8zjJr5DcvIIA4KYZDrO2A0huR/IcZQRJJuK+84KE1iEP8/2V8/z9leoxjAWEanYDJHlUPwoIbl2OdmxnKgkI1qBx74TwmiUkJNu6nOTfSJ5KcnunjxqS6as9PDw8hroW4SMOIe0m+d48K+fEiv6bJDsdgh6lEN+lJG8i+WWSu5MclaOO40juS/I0NY7sSBFGIodBvGWt0/NoKRzGe4LTB+0kd8wjXAxTASHOOCwjPryfBQSrHXqO5Ckpq/+kgFBw2nOe019RlTaVUtq9huRvNQPkoNAmeXh4eKxvxvNjh9AusmrWHEKCOMaLeyYMH7MEBYvXSD6gLpI/I3k5ye+T/IUaFj6sVuxpxmtRCkH/HcnpeQm50/Z91GK9O+FaFw7C7zSYNQj2mSN6KSBEOQSI1zJ+7yEgJN57fsrYYQ5hwe3jds0k6YUEDw+PYSMgWBV/vTJri3/ZFX6eVbRLNEn+l3ozuAS36BDdYi9U10VHIEg+/xDJD6XVJYf2ZDvdYrHM7VcuQ/YCwnrRINj/FzjbPFGFLQzmFBBc4fVDiTFZcjRQecaexZe8kODh4TGchARLRCeTXOgQzb87Bl95hITAYTTNJE8i+WgGwU07uh1f8+RRSinn7ySPc+of1CLMkJyqRokW96qgNCjsDjZCDQJ7aYMQO1tQUx1D0VqEhDQBwbrzuvYyp5N8JaXvSjkEEHvfu72Q4OHhMZyEBEtE91AjLcsg/kqyuRaCmNAmBCQPJXklyZfYN8QknyL5PZJ7Zr0zJ6OdTvI/Ttn/IfmOvMLQMBYQukkuyziWqDfAvr0UENrVfuCYXggpqTYISSHYERQ+p4aIHSn9GFWJy3CLFxA8PDyGq5BwIMnVDoG+m+R4l1HlYThJAqpW4HuR/DrJX6uNwYLEuyyRXklyroaE/jnJL5F8V4LQSy2rfetuqREX5zrvm0tyi8FM9AdRoKRL1XB0Ez0njzEVxlU1AWGVxrWAaodqERLSNAg2sqP1jqmzEUOdum1L8osk56iBayVNhd1K6bAeOT5QkoeHx3ASEixxneGEGybJJ5zwsoUamPJaN8aM30eQ3EzDGe9McieSW5GcZLc30upYC2G2URT17/eTfNMh+i+T3HqwrwgHkYDw7T4InnkEhEk6ZnZRbUWU0+vBjtP5+q6j9du+rALgPD1e0lwL56YIsBPVm+XFCkKCfc/hXovg4eExnIWE/ZzwxTaYzDFJwl8LE3LiHeRa+duQyrUEV0pri/59asIl8ulavB42EgHh4UQf5z5yCgiztexG57skj1pzMbgCwkSnzZfUoEWw33RBop+y8ITeV6+HO06mk1zhaAzS+uFTtWjUPDw8PAYD+qzy1JDDBRG5D8ABAJ7Tn8YBuFHdEZs1bXKYdzUvIhSRSERKeqYTsCl5iE0/rfeXRCSuHKp5Ha1BoG2ZrGGkL4cJoRzAhImeISKv2jTRQ+T7lxJ9nPvIWf4aLbvT+S7JI1l2dy8EogDAd2HSRAeoPc32Un2mW8/uEQHYgeTHRaRbj5LzbEelYQwTctmHWPbw8Njo0C8rGkdIeIbk/gB+BeAoJYynAjiY5OkicruzkoprjU2vDJ8OU2BeIaACYxHL8Eh+BsBFACbpewoAfgzg/2kbgyEiHFjNykSSH6mly2DyC7wkIk865WSVvwfJo1HOvZGn7JUA/l5je0IRWan5Qm6ogSHbsfOCChaFFKHZ5o24Xg0qrwcwDybvwpYALgEw2hEmkwK4qODivs/Dw8NjeCHhkXC2E0zI4hqS27r390Zd724d9Gb/PKnJ0OBHtyXquliT8GBDp2/uRf9U22LoK17QPnmwH9wc07AFyXfn3WJI2I38I0ed7BbDK9qOceo2Gee0YVisAcLyGCkuc4x2xVMJDw+PjQX9yvR0G0F0pX0+zJbDv5xbPgPg3yQvI7mVq66uxW5Atxu2JrmZ3XrIKRQUnK2LWKM5XgfgXgAfcB65BcBeInK9ZTxDNBMfdWWf9yjpOci5Irbq9Txlx1o+ATTmKFsy6nEqTHbOvPVrEJFlANq0zKjCvbZ+EwDYXCFxhiYl0uv/JyJLdWvKaxA8PDw8Eu5jpycMGKmuideQfF+aJiJNYHBWiQeo+9ibJLeyq8g0gSDF+ryR5FEkb01ZZb5I8vhkGzbivu9vDULk9JM40TT7S4NgV+Lba/6NShqENU6Ib0m0+7KcmRnnqdGhaNClZSnJw7LqGVUJxBRpSO53bmwaKA8PD4/1wahcpj2N5I80jkESj5D8b1UrhxU0ANYa/jzn2Ra91pBFhDVS4wEkL9YkPmkx+8+2fvl5oywOYwHhpUEgILSTnOyOM8eIdaxuAWRFWMxK1nR0igdCb3JMxD7UsoeHx8aOAV0hqxpfAAQiMh/AKSR/COBkAJ8EYN3U9tBjFoBnST4A4D4ATwB4RUSWo6yKBsnlKKuPl6pVeclhkJsA2AbA7gDeB2AfGIOyJOYCuArAVSLytiXmQ8hLwar47dFXxClne0g/1df9234HSVyXtHfqdlMgIsvVYPE6d1xktUOfK4jILeqa+0sYLxzo8+52hqTU1/ZzqEcRxrD150NsPHl4eAwjrDejKUdQsEx+EoDjABwPYG+k20NEABYDWABgEYA3ALwJYD8Ah+g9NwB4GWZPeDM9T4XZJ05DB4C7AVwL4BYRWe2s8uKhsE+szK5EchaA1gF4xesAJgN4HMC7BqD8HQGMAPBwlfu2EpF5KhTETvtDtYe5G8YOJgtvA9hc+2rt+CS5DYDZAGbCeGCkCTJZc+d2AN8RkX954cDDw8MLCLUxrx6uhXptNwCHA/gggF0BjOnn176tzOY2AH8VkRdcZgogGkoGZA6DPBbAOUh3weutBiEA8ISIfJbkJQAOVUGur2p0y3Q7YVxkQwA3oWywKIn7lgI4RkRW2BgY7hhT7dWOAK4G0JBov23HUzCGs9aFtocGSZ//iAqj7wTwDvTUusUAlgN4EcA9AP4oIg8ky/Hw8PDwAkLtGoUwEXQGuq+8B4C9dHW6rRLmsTmYXBHAMtUyvADgURUMHhORxUkhZahoDDwGRIhFQisxGkYrNVK1G10AVgFYYbennHEtQ9TrxcPDwwsIG4QgB2kref1toh6WQH8WRv0LmEA1/4AJsLMUwFsisqTCO+LhQrwH0u8+j3vpQJddTbizwbR6W0beMWOFXZjAXV5r4OHh4TFQwoLr5phxzxmOhfphGffUlMfBw6OasOWE9g7dMN++dzw8PIYiBp2ff3Kl5hBggTEYKwEYpf8LgFFqYBjqb7TBkPzn9ejHcUn4UMkeHh4eg3YVZwMl7adBbV5yfOH9Ss7Dw8PDw8MLC9zMBjby8PDw8PDw8OhTsiYPDw8PDw+PIS4keOHAw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDw8PDoxr+P69wdzRXCCY4AAAAAElFTkSuQmCC"""

@capture_router.get("/brand/logo-navy.png")
async def brand_logo_navy():
    data = _b64.b64decode(_LOGO_NAVY_B64)
    return _RawResponse(content=data, media_type="image/png",
                        headers={"Cache-Control": "public, max-age=31536000, immutable"})
