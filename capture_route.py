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
<title>Between-Sessions - Week %%WEEK%%</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{--navy:#1F3A5F;--navy-2:#2c507e;--navy-ink:#16304d;--gold:#b0842f;--gold-line:#ecdcb6;
--line:#e7ebf2;--ink:#22344a;--grey:#5f6f84;--grey-2:#8a97a8;--good:#1a7f55;--good-soft:#e7f4ee;--good-line:#bfe3d1;
--bad:#c0392b;--bad-soft:#fdecea;--shadow-sm:0 1px 2px rgba(31,58,95,.07);--shadow:0 1px 2px rgba(31,58,95,.05),0 12px 30px rgba(31,58,95,.08);--radius:18px}
*{box-sizing:border-box}
body{margin:0;background:linear-gradient(180deg,#f3f6fb,#e9edf4);background-attachment:fixed;color:var(--ink);
line-height:1.65;-webkit-font-smoothing:antialiased;font-family:'Inter',-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif}
button,textarea{font-family:inherit}
.btn,.opt,.tap,.send{transition:all .16s ease}
.wrap{max-width:680px;margin:0 auto;padding:26px 18px 90px}
.head{margin:4px 2px 18px}.head .wk{font-size:11px;font-weight:800;letter-spacing:.07em;text-transform:uppercase;color:var(--gold)}
.head h1{font-size:23px;font-weight:800;letter-spacing:-.02em;color:var(--navy-ink);margin:4px 0 0}
.card{background:#fff;border:1px solid var(--line);border-radius:var(--radius);padding:24px 26px;margin:14px 0;box-shadow:var(--shadow)}
.card h2{display:flex;align-items:center;gap:11px;margin:0 0 12px;font-size:17px;font-weight:700;letter-spacing:-.01em;color:var(--navy-ink)}
.card h2::before{content:"";width:4px;height:19px;border-radius:3px;background:var(--gold);flex:none}
.hint{font-size:13px;color:var(--grey-2);margin:2px 0 14px}
label.fld{display:block;font-weight:700;color:var(--navy-ink);margin:14px 0 8px;font-size:15px}
label.fld:first-of-type{margin-top:0}
textarea{width:100%;min-height:74px;border:1.5px solid var(--line);border-radius:12px;padding:13px;font-size:15px;resize:vertical;color:var(--ink);background:#fff}
textarea:focus{outline:none;border-color:var(--navy);box-shadow:0 0 0 3px rgba(31,58,95,.1)}
textarea::placeholder{color:var(--grey-2)}
.taprow{display:flex;gap:10px;flex-wrap:wrap;margin-top:8px}
.tap{flex:1;min-width:120px;border:1.5px solid var(--line);background:#fff;border-radius:12px;padding:13px;font-weight:600;cursor:pointer;text-align:center;font-size:15px;color:var(--navy)}
.tap:hover{border-color:var(--navy-2);transform:translateY(-1px);box-shadow:var(--shadow-sm)}
.tap.sel{background:var(--navy);color:#fff;border-color:var(--navy);box-shadow:var(--shadow-sm)}
.scene{background:#f5f8fc;border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin:14px 0;box-shadow:var(--shadow-sm)}
.stitle{display:flex;align-items:center;font-size:11.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--grey);margin:0 -18px 12px;padding:0 18px 11px;border-bottom:1px solid var(--line);font-weight:700}
.stitle::before{content:"";width:9px;height:9px;border-radius:50%;background:#e0655a;box-shadow:15px 0 0 #e6b95c,30px 0 0 #63b563;margin-right:40px}
.scene.good{background:var(--good-soft);border-color:var(--good-line)}
.scene.good .stitle{border-bottom-color:var(--good-line)}
.bubble{background:#fff;border:1px solid var(--line);border-radius:14px;padding:10px 14px;margin:8px 0;font-size:15px;box-shadow:var(--shadow-sm)}
.bubble b{color:var(--navy-ink)}.bubble.lead{border-left:3px solid var(--navy)}.bubble.col{border-left:3px solid var(--grey-2)}
.scenenote{font-size:14px;color:var(--grey);font-style:italic;margin-top:12px;padding-top:12px;border-top:1px dashed var(--line)}
.simblock{margin:0 0 18px}
.q{margin:0 0 10px;font-weight:600;color:var(--navy-ink);font-size:15.5px}.q .qnum{font-weight:800;color:var(--navy)}
.opt{display:block;border:1.5px solid var(--line);border-radius:12px;padding:12px 15px;margin:8px 0;cursor:pointer;font-size:15px;background:#fff}
.opt:hover{border-color:var(--navy-2);background:#fafbfd}
.opt.sel{border-color:var(--navy);background:#eef2f8;box-shadow:inset 0 0 0 1px var(--navy)}
.opt.good{border-color:var(--good);background:var(--good-soft)}.opt.bad{border-color:var(--bad);background:var(--bad-soft)}
.opt .lbl{font-weight:800;color:var(--navy);margin-right:8px}
.simwhy{display:none;font-size:13.5px;color:var(--grey);background:#f4f7fb;border-left:3px solid var(--navy-2);border-radius:8px;padding:11px 14px;margin-top:8px}
.simwhy.show{display:block}.verdict{font-weight:800}.verdict.v-good{color:var(--good)}.verdict.v-bad{color:var(--bad)}
.revealwrap{margin:16px 0 4px}
.btn{border:1px solid var(--line);background:#fff;color:var(--navy);font-weight:600;padding:9px 16px;border-radius:999px;cursor:pointer;font-size:13.5px}
.btn:hover{border-color:var(--navy-2)}.btn.small{font-size:13px;padding:8px 14px}
.reveal{display:none;margin-top:12px}.reveal.show{display:block}
.goodcap{font-size:14px;color:var(--grey);margin:12px 2px 0}
.yourturn{border-top:1px solid var(--line);margin-top:18px;padding-top:16px}
.yourturn label{display:block;font-weight:700;color:var(--navy-ink);margin-bottom:8px}
.send{background:linear-gradient(180deg,var(--navy-2),var(--navy));color:#fff;border:none;border-radius:999px;padding:15px 36px;font-weight:700;font-size:16px;cursor:pointer;display:block;margin:26px auto 0;box-shadow:0 8px 20px rgba(31,58,95,.24)}
.send:hover{transform:translateY(-1px)}.send:disabled{opacity:.55}
.err{color:var(--bad);font-size:13.5px;text-align:center;margin-top:12px;display:none}
.note{font-size:12px;color:var(--grey-2);text-align:center;margin-top:16px}
.scoreline{font-size:15px;color:var(--navy-ink);font-weight:600;margin:2px 0 4px}
.resitem{border:1px solid var(--line);border-left-width:4px;border-radius:12px;padding:14px 16px;margin:10px 0}
.resitem.ok{border-left-color:var(--good);background:#f4faf7}.resitem.no{border-left-color:var(--bad);background:#fdf5f4}
.resline{font-weight:800;font-size:13.5px;margin:6px 0 2px}.resitem.ok .resline{color:var(--good)}.resitem.no .resline{color:var(--bad)}
.rescorrect{font-size:14px;color:var(--navy-ink);font-weight:600;margin:2px 0 6px}
.reswhy{font-size:13.5px;color:var(--grey);background:#f4f7fb;border-left:3px solid var(--navy-2);border-radius:8px;padding:11px 14px;margin-top:4px}
.thanks{text-align:center;padding:36px 22px}
.thanks::before{content:"\2713";display:flex;width:58px;height:58px;margin:0 auto 16px;border-radius:50%;background:var(--good-soft);color:var(--good);align-items:center;justify-content:center;font-size:28px;font-weight:800}
.thanks h2{font-size:21px;justify-content:center}.thanks h2::before{display:none}
</style></head><body><div class="wrap">
<div class="head"><div class="wk">Week %%WEEK%% &middot; Communication</div><h1>Your check-in</h1></div>

<form id="form">
  <div class="card">
    <h2>Your week</h2>
    <label class="fld">Were you able to try it this week?</label>
    <div class="taprow">
      <div class="tap" data-v="Y" onclick="tap(this)">Yes, a few times</div>
      <div class="tap" data-v="P" onclick="tap(this)">A little</div>
      <div class="tap" data-v="N" onclick="tap(this)">Not this week</div>
    </div>
    <label class="fld" id="story_label" style="margin-top:18px"></label>
    <textarea id="story" placeholder="Share as much or as little as you like (optional)"></textarea>
  </div>

  <div class="card">
    <h2>Simulation &middot; spot the gap</h2>
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

  <div class="card"><h2>Quick knowledge checks</h2>
    <p class="hint">A few short questions, one answer each.</p><div id="checks"></div></div>

  <div class="card"><h2>Reflection</h2><div id="reflection"></div></div>

  <button type="submit" class="send" id="send">Send my response</button>
  <p class="err" id="err">Please answer the knowledge-check questions before sending.</p>
  <p class="note">The Performance Lens &middot; This link is private to you, please do not share it.</p>
</form>

<div id="postsubmit" style="display:none">
  <div class="card"><h2>How you did</h2><p class="scoreline" id="scoreline"></p>
    <p class="hint">Your answers are saved. Here is how each one landed, and the why behind it.</p>
    <div id="resultlist"></div></div>
  <div class="card thanks"><h2>Thank you</h2><p>Your response for this week has been recorded. See you Monday.</p></div>
</div>

<script>
var C=%%CONTENT%%, SUBMIT=%%SUBMIT%%;
var state={completion:"",sim:{},checks:{}};
var L=['A','B','C'];
function el(id){return document.getElementById(id)}
function tap(t){state.completion=t.getAttribute('data-v');t.parentNode.querySelectorAll('.tap').forEach(function(x){x.classList.remove('sel')});t.classList.add('sel')}

// story + reflection
el('story_label').textContent=C.story_prompt;
var refWrap=el('reflection');
C.reflection.forEach(function(r,i){var lab=document.createElement('label');lab.className='fld';lab.textContent=r;
  var ta=document.createElement('textarea');ta.id='ref'+i;ta.placeholder='Write a line or two (optional)';
  refWrap.appendChild(lab);refWrap.appendChild(ta)});

// simulation
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

// knowledge checks (no answer key present)
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
  el('scoreline').textContent='You got '+res.correct+' of '+res.total+' right.';
  el('form').style.display='none';el('postsubmit').style.display='block';window.scrollTo({top:0,behavior:'smooth'})}
</script></body></html>"""
