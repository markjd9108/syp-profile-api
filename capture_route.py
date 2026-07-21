# Between-Sessions Curriculum — capture page route (FastAPI)
# Mounted from api_server.py via: app.include_router(capture_router)
# Mirrors the /generate-hosted -> /p/<slug> pattern:
#   POST /generate-capture  -> { "url": "<base>/c/<token>" }   (called by the Make Weekly Send scenario)
#   GET  /c/{token}         -> the hosted response page (opened by the participant)
# The page carries BOTH languages with an EN/VI toggle so participants complete in whichever
# they prefer. Correct answers are never sent here; grading happens in Make on submit.

import os, json, secrets
from urllib.parse import parse_qs
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

capture_router = APIRouter()

PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "https://syp-profile-api-production.up.railway.app").rstrip("/")
CAPTURE_WEBHOOK_URL = "https://hook.eu2.make.com/kr0hxwi8c4vu74slpmciqggo0k7wgkd7"

# Store rendered pages on the same Railway volume the profiles use, so links survive redeploys.
CAPTURE_STORE_DIR = os.environ.get("CAPTURE_STORE_DIR", "/data/captures")
try:
    os.makedirs(CAPTURE_STORE_DIR, exist_ok=True)
except Exception:
    CAPTURE_STORE_DIR = os.path.join(os.path.dirname(__file__), "capture_store")
    os.makedirs(CAPTURE_STORE_DIR, exist_ok=True)

UI = {
    "en": {"practice_heading": "This week's practice", "practice_q": "Did you complete this week's practice?",
           "yes": "Yes", "no": "Not yet", "reflection_heading": "Reflection",
           "reflection_placeholder": "Write a line or two (optional)",
           "kc_heading": "Three quick knowledge checks", "kc_sub": "Pick one answer for each.",
           "submit": "Send my response", "error": "Please choose Yes or Not yet and answer all three questions.",
           "footer": "The Performance Lens · This link is private to you, please do not share it.",
           "thanks_title": "Thank you", "thanks_body": "Your response for this week has been recorded.",
           "switch": "Tiếng Việt"},
    "vi": {"practice_heading": "Phần thực hành tuần này", "practice_q": "Bạn đã hoàn thành phần thực hành tuần này chưa?",
           "yes": "Rồi", "no": "Chưa", "reflection_heading": "Câu hỏi suy ngẫm",
           "reflection_placeholder": "Viết vài dòng (không bắt buộc)",
           "kc_heading": "Ba câu hỏi kiến thức nhanh", "kc_sub": "Chọn một đáp án cho mỗi câu.",
           "submit": "Gửi phản hồi", "error": "Vui lòng chọn Rồi hoặc Chưa và trả lời cả ba câu hỏi.",
           "footer": "The Performance Lens · Đường link này là riêng của bạn, vui lòng không chia sẻ.",
           "thanks_title": "Cảm ơn bạn", "thanks_body": "Phản hồi của bạn cho tuần này đã được ghi nhận.",
           "switch": "English"},
}


def _lang_obj(b, lang):
    if b.get("practice_" + lang) or b.get("kc1q_" + lang):
        def kc(n):
            return {"q": b.get("kc%sq_%s" % (n, lang), ""), "A": b.get("kc%sa_%s" % (n, lang), ""),
                    "B": b.get("kc%sb_%s" % (n, lang), ""), "C": b.get("kc%sc_%s" % (n, lang), "")}
        return {"practice_prompt": b.get("practice_" + lang, ""),
                "reflection_prompt": b.get("reflect_" + lang, ""), "kcs": [kc(1), kc(2), kc(3)]}
    return None


@capture_router.post("/generate-capture")
async def generate_capture(request: Request):
    raw = (await request.body()).decode("utf-8")
    b = {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}
    default = "en" if b.get("default_language", "vi").lower() == "en" else "vi"
    payload = {"participant_id": b.get("participant_id", ""), "client": b.get("client", ""),
               "program_gap": b.get("program_gap", ""), "module": b.get("module", ""),
               "week": b.get("week", ""), "send_date": b.get("send_date", ""),
               "default_language": default, "en": _lang_obj(b, "en"), "vi": _lang_obj(b, "vi")}
    token = secrets.token_hex(24)
    with open(os.path.join(CAPTURE_STORE_DIR, token + ".html"), "w", encoding="utf-8") as f:
        f.write(_render(token, payload))
    return JSONResponse({"url": PUBLIC_BASE_URL + "/c/" + token})


@capture_router.get("/c/{token}")
async def capture_page(token: str):
    path = os.path.join(CAPTURE_STORE_DIR, token + ".html")
    if not os.path.exists(path):
        return HTMLResponse("This link has expired or is not valid.", status_code=404)
    with open(path, encoding="utf-8") as f:
        return HTMLResponse(f.read())


def _render(token, p):
    has_both = bool(p["en"] and p["vi"])
    content = {"en": p["en"] or p["vi"], "vi": p["vi"] or p["en"]}
    langbar = '<div class="langbar"><button id="langbtn" type="button"></button></div>' if has_both else ""
    meta = {"token": token, "participant_id": p["participant_id"], "client": p["client"],
            "program_gap": p["program_gap"], "module": p["module"], "week": str(p["week"]),
            "send_date": p["send_date"]}
    html = PAGE
    for k, v in {"%%LANG%%": p["default_language"], "%%WEEK%%": str(p["week"]), "%%LANGBAR%%": langbar,
                 "%%PAYLOAD%%": json.dumps(meta), "%%CONTENT%%": json.dumps(content),
                 "%%UI%%": json.dumps(UI), "%%HASBOTH%%": "true" if has_both else "false",
                 "%%HOOK%%": json.dumps(CAPTURE_WEBHOOK_URL), "%%DEFAULT%%": json.dumps(p["default_language"])}.items():
        html = html.replace(k, v)
    return html


PAGE = """<!DOCTYPE html><html lang="%%LANG%%"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Between-Sessions - Week %%WEEK%%</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{--ink:#1F3A5F;--line:#e4e8ef;--bg:#f6f8fb;--soft:#eef2f8;--muted:#6b7686}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,system-ui,Arial,sans-serif;line-height:1.55}
.wrap{max-width:640px;margin:0 auto;padding:16px 16px 64px}
.langbar{display:flex;justify-content:flex-end;margin:4px 0 8px}
.langbar button{border:1px solid var(--line);background:#fff;border-radius:999px;padding:6px 14px;font-size:13px;font-weight:600;color:var(--ink);cursor:pointer;font-family:inherit}
.card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px 18px;margin:14px 0}
h1{font-size:20px;margin:2px 0 10px}h2{font-size:16px;margin:0 0 8px}
.prompt{background:var(--soft);border-radius:10px;padding:14px;font-weight:500}
.toggle{display:flex;gap:10px;margin-top:6px}.toggle button{flex:1;padding:12px;border:1.5px solid var(--line);background:#fff;border-radius:10px;font-size:15px;font-weight:600;color:var(--ink);cursor:pointer;font-family:inherit}
.toggle button[aria-pressed="true"]{background:var(--ink);color:#fff;border-color:var(--ink)}
textarea{width:100%;min-height:90px;border:1.5px solid var(--line);border-radius:10px;padding:12px;font-family:inherit;font-size:15px;color:var(--ink)}
.opt{display:flex;gap:10px;border:1.5px solid var(--line);border-radius:10px;padding:11px 12px;cursor:pointer;margin-bottom:8px}
.opt.sel{border-color:var(--ink);background:var(--soft)}.opt .k{font-weight:700}
.submit{width:100%;padding:15px;border:0;border-radius:12px;background:var(--ink);color:#fff;font-size:16px;font-weight:700;cursor:pointer;font-family:inherit}
.submit:disabled{opacity:.55}.foot{color:var(--muted);font-size:12px;text-align:center;margin-top:20px}
.done{display:none;text-align:center;padding:34px 12px}.err{color:#b4342b;font-size:13px;margin-top:8px;display:none}
</style></head><body><div class="wrap">
%%LANGBAR%%
<form id="f">
  <div class="card"><h2 id="t_practice_heading"></h2>
    <p class="prompt" id="c_practice"></p>
    <p style="font-size:12px;color:var(--muted);margin-top:14px" id="t_practice_q"></p>
    <div class="toggle"><button type="button" id="py" aria-pressed="false"></button>
    <button type="button" id="pn" aria-pressed="false"></button></div></div>
  <div class="card"><h2 id="t_reflection_heading"></h2>
    <p id="c_reflection"></p><textarea id="reflection"></textarea></div>
  <div class="card"><h2 id="t_kc_heading"></h2>
    <p style="font-size:13px;color:var(--muted)" id="t_kc_sub"></p><div id="kcs"></div></div>
  <button type="submit" class="submit" id="submit"></button>
  <p class="err" id="err"></p><p class="foot" id="t_footer"></p>
</form>
<div class="done" id="done"><h1 id="t_thanks_title"></h1><p id="t_thanks_body"></p></div>
</div><script>
var PAYLOAD=%%PAYLOAD%%,CONTENT=%%CONTENT%%,UI=%%UI%%,HAS_BOTH=%%HASBOTH%%,HOOK=%%HOOK%%,lang=%%DEFAULT%%;
var state={pc:"",ans:{}};
function t(id,val){document.getElementById(id).textContent=val;}
function render(){
  var c=CONTENT[lang],u=UI[lang];
  t('t_practice_heading',u.practice_heading);document.getElementById('c_practice').textContent=c.practice_prompt||'';
  t('t_practice_q',u.practice_q);t('py',u.yes);t('pn',u.no);
  t('t_reflection_heading',u.reflection_heading);document.getElementById('c_reflection').textContent=c.reflection_prompt||'';
  document.getElementById('reflection').placeholder=u.reflection_placeholder;
  t('t_kc_heading',u.kc_heading);t('t_kc_sub',u.kc_sub);t('submit',u.submit);
  t('err',u.error);t('t_footer',u.footer);t('t_thanks_title',u.thanks_title);t('t_thanks_body',u.thanks_body);
  if(HAS_BOTH)t('langbtn',u.switch);
  var wrap=document.getElementById('kcs');wrap.innerHTML='';
  (c.kcs||[]).forEach(function(kc,i){var n=i+1,d=document.createElement('div');
    d.innerHTML='<p style="font-weight:600">'+n+'. '+kc.q+'</p><div id="kc'+n+'"></div>';wrap.appendChild(d);
    ['A','B','C'].forEach(function(k){if(!kc[k])return;var l=document.createElement('label');l.className='opt';
      if(state.ans['kc'+n]===k)l.classList.add('sel');
      l.innerHTML='<input type="radio" name="kc'+n+'" value="'+k+'"'+(state.ans['kc'+n]===k?' checked':'')+' style="margin-top:3px"><span class="k">'+k+'</span><span>'+kc[k]+'</span>';
      l.querySelector('input').addEventListener('change',function(){state.ans['kc'+n]=k;d.querySelectorAll('.opt').forEach(function(o){o.classList.remove('sel')});l.classList.add('sel')});
      document.getElementById('kc'+n).appendChild(l)})});
  document.getElementById('py').setAttribute('aria-pressed',state.pc==='Y');
  document.getElementById('pn').setAttribute('aria-pressed',state.pc==='N');
}
function setPC(v){state.pc=v;document.getElementById('py').setAttribute('aria-pressed',v==='Y');document.getElementById('pn').setAttribute('aria-pressed',v==='N')}
document.getElementById('py').onclick=function(){setPC('Y')};document.getElementById('pn').onclick=function(){setPC('N')};
if(HAS_BOTH)document.getElementById('langbtn').onclick=function(){lang=lang==='en'?'vi':'en';render()};
document.getElementById('f').addEventListener('submit',function(e){e.preventDefault();var err=document.getElementById('err');
  if(state.pc===""||Object.keys(state.ans).length<(CONTENT[lang].kcs||[]).length){err.style.display='block';return}err.style.display='none';
  var btn=document.getElementById('submit');btn.disabled=true;
  var body=new URLSearchParams({token:PAYLOAD.token,participant_id:PAYLOAD.participant_id,client:PAYLOAD.client,program_gap:PAYLOAD.program_gap,module:PAYLOAD.module,week:PAYLOAD.week,send_date:PAYLOAD.send_date,practice_completed:state.pc,reflection_submitted:document.getElementById('reflection').value.trim()?"Y":"N",reflection_text:document.getElementById('reflection').value.trim(),kc1_answer:state.ans.kc1||"",kc2_answer:state.ans.kc2||"",kc3_answer:state.ans.kc3||""}).toString();
  fetch(HOOK,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:body}).then(function(){document.getElementById('f').style.display='none';var lb=document.querySelector('.langbar');if(lb)lb.style.display='none';document.getElementById('done').style.display='block';window.scrollTo(0,0);}).catch(function(){btn.disabled=false;err.style.display='block';});});
render();
</script></body></html>"""
