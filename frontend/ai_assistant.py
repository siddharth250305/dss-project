"""
ai_assistant.py
===============
Grok-powered AI assistant for the Cargo-Aware Drone Selection DSS.

Rendered as a **floating side panel**: a round teal launcher button sits in the
bottom-right corner of the page; clicking it slides a chat drawer in from the right.
The page content stays fully usable underneath — the widget reserves no page height
because it injects its launcher + drawer into the parent Streamlit document and pins
them with position:fixed.

It runs entirely in the browser using Puter.js
(https://developer.puter.com/tutorials/free-unlimited-grok-api/). No API key and no
backend call are needed — Puter uses a "user-pays" model, so each user authenticates with
a one-time Puter popup the first time they send a message.

Usage (typically on the Recommendation page):

    from ai_assistant import render_ai_assistant

    render_ai_assistant(
        recommendation_data=decision_result,   # dict, see the contract in INTEGRATION_GUIDE.md
        panel_width=400,                        # optional, px
        model="x-ai/grok-4-1-fast",             # optional, any model from the Puter list
        start_open=False,                       # optional, open the drawer on load
    )

`recommendation_data` is whatever your decision engine already returns / what you write to
the decision log. Pass it straight through; missing keys are handled gracefully.
"""

import json
import streamlit.components.v1 as components

# Any chat model from the Puter Grok list. grok-4-1-fast is responsive and cheap;
# swap for "x-ai/grok-4.3" for more elaborate answers.
DEFAULT_MODEL = "x-ai/grok-4-1-fast"

# ---------------------------------------------------------------------------
# The system prompt. This is the canonical copy the running app uses.
# The human-readable reference version lives in GROK_SYSTEM_PROMPT.md.
# {RECOMMENDATION_CONTEXT} is replaced with the live mission JSON on every render.
# ---------------------------------------------------------------------------
BASE_SYSTEM_PROMPT = r"""
You are DSS Assistant, an AI helper built into the Cargo-Aware Drone Selection Decision
Support System (DSS) used to choose drones for missions at a small/medium port.

Your two jobs:
1. Summarise the drone recommendation currently on the operator's screen in clear, plain language.
2. Answer questions about (a) the specific mission, drones, scores, alerts and overrides in
   front of the operator, and (b) how the DSS itself works.

WHO YOU ARE TALKING TO
Port Operators, Security Supervisors, Maintenance Staff and System Administrators. Assume the
reader is NOT technical. Short sentences, no jargon. If you must use a term like "weighted
score", explain it in half a sentence.

RULES YOU MUST NEVER BREAK (grounding / no guessing)
- When you summarise or answer about THIS mission, use ONLY the data in the CURRENT
  RECOMMENDATION CONTEXT block at the bottom. That block is the single source of truth.
- Never invent drone names, scores, numbers, rejection reasons, sensor types or weather
  values. If a value is not in the context, say plainly that it is not available.
- If the context is empty, say so and offer to answer general questions about how the system works.
- You advise; you do not decide. The operator always makes the final call. Say a drone is
  "recommended", never that it "will" be deployed.
- If asked to do something outside drone selection, politely steer back to the DSS.

HOW THE DSS REACHES A RECOMMENDATION (answer from this)
The system runs every drone through two stages.

Stage 1 - Hard filtering (10 rules, automatic rejection). Any drone failing one rule is
removed before scoring. Rejection happens when:
- Battery endurance < required flight time x 1.2 (a 20% safety margin).
- Current wind speed > the drone's wind-resistance rating.
- Mission needs night vision and the drone lacks it.
- Mission needs a thermal sensor and the drone lacks it.
- Maintenance status is Poor or Grounded.
- Cargo-zone distance > the drone's maximum flight radius.
- Safety risk is Critical and there is no supervisor approval on record.
- The drone lacks regulatory certification for this mission type.
- No qualified operator is currently available.
- Weather is Storm or Heavy Rain.
Each rejected drone gets a plain-language reason; pass it on if asked.

Stage 2 - Weighted multi-criteria scoring (MCDM). Drones passing all 10 rules are scored.
There are 21 criteria; 19 are scored and 2 (Maintenance Status, Available Operators) act
only as hard filters. Each criterion is normalised to 0-1, multiplied by its weight, and
summed - the Weighted Sum Model. Total Score = sum of (weight_i x normalised_value_i). The
highest total score is recommended.

The 19 scored criteria sit in 5 groups (default weights; an administrator can change them):
- Drone Capability (52%): flight radius 8%, battery endurance 11% (highest single weight,
  because running out of battery is the biggest operational risk), payload 6%, camera 5%,
  night vision 4%, thermal 4%, max flight height 4%, wind resistance 8%, charging time 2%.
- Mission Requirements (20%): urgency 8%, cargo-zone distance 6%, historical reliability 6%.
- Environmental Conditions (15%): weather 5%, wind speed 7%, obstacle density 3%.
- Safety Constraints (10% scored): safety risk level 6%, regulatory compliance 4%.
- Operational Constraints (3%): daily missions 2%, budget 1%.

Normalisation: numeric criteria use min-max scaling against the CURRENT fleet - best scores
1.0, worst scores 0. Because the reference is the current fleet, scores from different
sessions are NOT directly comparable; mention this if someone compares across missions.
Categorical maps are fixed, e.g. camera SD=0.33/HD=0.67/4K=1.0; weather Clear=1.0/
Cloudy=0.75/Rain=0.40/Heavy Rain=0.10.

Safety alerts: raised separately from scoring when thresholds are crossed - high wind
(>=80% of resistance), low visibility (<2000 m), precipitation, battery fatigue (>=3
missions today), high obstacle density. Alerts are advisory; they warn but do not by
themselves reject a drone.

Override + audit: the operator can accept the recommendation or override it by choosing a
different drone, but an override requires a written justification. Every input, score,
ranked list, rejected drone, alert, override and timestamp is written to a permanent
decision log so any decision can be reviewed later.

HOW TO SUMMARISE A RECOMMENDATION (your main job)
When asked to summarise, produce a short brief (skip any part the context lacks):
1. Headline - which drone is recommended and its score, one line.
2. Why it won - the 2-3 criteria that contributed most, in plain words.
3. Watch-outs - any safety alerts, most severe first, one line each. If none, say conditions look clear.
4. What was ruled out - how many drones were rejected and the most common reason, only if present.
5. Override - if overridden, state which drone was chosen instead and the reason given.
Keep it under ~150 words unless asked for more. Lead with the decision, then the reasoning.
If there is a Critical alert, put it first and flag it clearly.

STYLE
- Plain language, calm and professional - this is a safety-relevant operations tool.
- Use a short bulleted list only when it genuinely helps; otherwise write in sentences.
- Be concise by default; expand only when asked.
- State numbers verbatim from the context. Round only if you say you are rounding.
- No emoji in alert text where it could read as flippant about a safety risk.

---
CURRENT RECOMMENDATION CONTEXT (the screen the operator is viewing - your only source of
truth for this mission; JSON):

{RECOMMENDATION_CONTEXT}
"""


def _build_system_prompt(recommendation_data) -> str:
    """Inject the live mission JSON into the base prompt."""
    if recommendation_data:
        context = json.dumps(recommendation_data, indent=2, default=str)
    else:
        context = "(No recommendation is currently loaded. Answer general questions about the DSS only.)"
    return BASE_SYSTEM_PROMPT.replace("{RECOMMENDATION_CONTEXT}", context)


def render_ai_assistant(recommendation_data=None, panel_width: int = 400,
                        model: str = DEFAULT_MODEL, start_open: bool = False,
                        height: int = 0) -> None:
    """
    Render the Grok chat assistant as a floating side panel on the current page.

    A round teal launcher button is pinned to the bottom-right corner; clicking it
    slides a chat drawer in from the right. The widget itself reserves no page height
    (it injects the launcher + drawer into the parent document with position:fixed),
    so it never pushes the page content around.

    Parameters
    ----------
    recommendation_data : dict | None
        The decision-engine result for the mission on screen. See INTEGRATION_GUIDE.md
        for the expected (but flexible) shape. Pass None to offer general help only.
    panel_width : int
        Drawer width in pixels (capped to 92% of the viewport on small screens).
    model : str
        Any model from the Puter Grok list (e.g. "x-ai/grok-4-1-fast", "x-ai/grok-4.3").
    start_open : bool
        If True, the drawer is open on first load instead of collapsed to the button.
    height : int
        Kept for backwards compatibility; ignored — the floating widget is height-less.
    """
    system_prompt = _build_system_prompt(recommendation_data)

    # Safe JS string literals (handles quotes, newlines, unicode).
    system_prompt_js = json.dumps(system_prompt)
    model_js = json.dumps(model)
    has_context_js = "true" if recommendation_data else "false"
    start_open_js = "true" if start_open else "false"

    html = _WIDGET_TEMPLATE \
        .replace("__SYSTEM_PROMPT__", system_prompt_js) \
        .replace("__MODEL__", model_js) \
        .replace("__HAS_CONTEXT__", has_context_js) \
        .replace("__PANEL_WIDTH__", str(int(panel_width))) \
        .replace("__START_OPEN__", start_open_js)

    # height=0: the visible UI lives in the parent document (position:fixed),
    # so the injector iframe takes no vertical space in the page flow.
    components.html(html, height=0, scrolling=False)


# ---------------------------------------------------------------------------
# Injector. This HTML runs inside Streamlit's (zero-height) component iframe,
# but its script reaches into the PARENT document and appends a fixed-position
# launcher button + slide-in drawer there, so the chat floats over the whole
# app instead of sitting in the page flow.
# Aesthetic: port-operations console — deep maritime navy, teal assistant,
# amber for safety. IBM Plex Sans / Mono.
# ---------------------------------------------------------------------------
_WIDGET_TEMPLATE = r"""
<script>
(function () {
  var SYSTEM_PROMPT = __SYSTEM_PROMPT__;
  var MODEL         = __MODEL__;
  var HAS_CONTEXT   = __HAS_CONTEXT__;
  var PANEL_WIDTH   = __PANEL_WIDTH__;
  var START_OPEN    = __START_OPEN__;

  // Reach into the parent Streamlit document so the panel can float over the
  // whole page. Falls back to the local document if that is blocked.
  var win, doc;
  try { win = window.parent; doc = win.document; if (!doc) throw 0; }
  catch (e) { win = window; doc = document; }

  // Persist state (history + open flag) across Streamlit reruns.
  var S = win.__dssAssistant = win.__dssAssistant || {};
  if (!S.history) S.history = [{ role: "system", content: SYSTEM_PROMPT }];
  else S.history[0] = { role: "system", content: SYSTEM_PROMPT }; // refresh live context

  // --- inject fonts once ---
  if (!doc.getElementById('dssx-fonts')) {
    var f = doc.createElement('link');
    f.id = 'dssx-fonts'; f.rel = 'stylesheet';
    f.href = 'https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500&display=swap';
    doc.head.appendChild(f);
  }
  // --- inject Puter.js once (into the parent so win.puter is available) ---
  if (!doc.getElementById('dssx-puter') && typeof win.puter === 'undefined') {
    var p = doc.createElement('script');
    p.id = 'dssx-puter'; p.src = 'https://js.puter.com/v2/';
    doc.head.appendChild(p);
  }

  // --- inject styles once ---
  if (!doc.getElementById('dssx-style')) {
    var st = doc.createElement('style');
    st.id = 'dssx-style';
    st.textContent = [
      "#dssx-root{font-family:'IBM Plex Sans',system-ui,sans-serif}",
      ".dssx-fab{position:fixed;right:24px;bottom:24px;width:56px;height:56px;border-radius:50%;",
        "background:#0e9c91;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;",
        "box-shadow:0 8px 22px rgba(14,156,145,.45);z-index:2147483000;",
        "transition:transform .2s ease,opacity .2s ease,background .2s ease}",
      ".dssx-fab:hover{transform:scale(1.07);background:#0b7c73}",
      ".dssx-fab svg{width:26px;height:26px;stroke:#fff;fill:none}",
      ".dssx-fab.dssx-gone{opacity:0;transform:scale(.4);pointer-events:none}",

      ".dssx-panel{position:fixed;top:0;right:0;height:100vh;width:" + PANEL_WIDTH + "px;max-width:92vw;",
        "background:#f7f9fb;box-shadow:-10px 0 34px rgba(15,39,64,.24);z-index:2147483001;",
        "display:flex;flex-direction:column;transform:translateX(112%);",
        "transition:transform .3s cubic-bezier(.4,0,.2,1);border-left:1px solid #e1e8ef}",
      ".dssx-panel.dssx-open{transform:translateX(0)}",

      ".dssx-head{background:linear-gradient(135deg,#0f2740 0%,#163b5c 100%);color:#eaf2f8;",
        "padding:13px 16px;display:flex;align-items:center;gap:10px}",
      ".dssx-dot{width:9px;height:9px;border-radius:50%;background:#0e9c91;box-shadow:0 0 0 4px rgba(14,156,145,.22)}",
      ".dssx-head h1{font-size:14px;font-weight:600;margin:0;letter-spacing:.2px}",
      ".dssx-head .sub{font-size:10.5px;color:#9fb6cc;margin-top:1px;font-family:'IBM Plex Mono',monospace}",
      ".dssx-head .grow{flex:1}",
      ".dssx-x{background:none;border:none;color:#9fb6cc;cursor:pointer;padding:4px;display:flex;border-radius:6px}",
      ".dssx-x:hover{color:#eaf2f8;background:rgba(255,255,255,.08)}",
      ".dssx-x svg{width:18px;height:18px;stroke:currentColor;fill:none}",

      ".dssx-log{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:12px}",
      ".dssx-msg{max-width:88%;padding:10px 13px;border-radius:13px;font-size:13.5px;line-height:1.55;",
        "white-space:normal;word-wrap:break-word}",
      ".dssx-msg.u{align-self:flex-end;background:#0f2740;color:#fff;border-bottom-right-radius:4px}",
      ".dssx-msg.b{align-self:flex-start;background:#fff;border:1px solid #dfe6ee;color:#1b2733;border-bottom-left-radius:4px}",
      ".dssx-msg.b .who{font-size:9.5px;font-weight:600;color:#0b7c73;font-family:'IBM Plex Mono',monospace;",
        "margin-bottom:5px;text-transform:uppercase;letter-spacing:.5px}",
      ".dssx-msg.b p{margin:0 0 8px}.dssx-msg.b p:last-child{margin-bottom:0}",
      ".dssx-msg.b ul{margin:6px 0;padding-left:20px}.dssx-msg.b li{margin:2px 0}",
      ".dssx-msg.b strong{font-weight:600;color:#0f2740}",
      ".dssx-msg.b code{font-family:'IBM Plex Mono',monospace;background:#eef3f7;padding:1px 5px;border-radius:5px;font-size:12px}",
      ".dssx-typing{display:inline-flex;gap:4px;align-items:center}",
      ".dssx-typing span{width:6px;height:6px;border-radius:50%;background:#5d6b7a;animation:dssxb 1s infinite}",
      ".dssx-typing span:nth-child(2){animation-delay:.15s}.dssx-typing span:nth-child(3){animation-delay:.3s}",
      "@keyframes dssxb{0%,60%,100%{opacity:.25}30%{opacity:1}}",

      ".dssx-chips{display:flex;flex-wrap:wrap;gap:7px;padding:0 14px 8px}",
      ".dssx-chip{font-size:11.5px;border:1px solid #dfe6ee;background:#fff;color:#1b2733;",
        "padding:6px 11px;border-radius:18px;cursor:pointer;transition:.15s;font-family:inherit}",
      ".dssx-chip:hover{border-color:#0e9c91;color:#0b7c73;background:#f0fbfa}",
      ".dssx-chip.p{background:#0e9c91;color:#fff;border-color:#0e9c91}",
      ".dssx-chip.p:hover{background:#0b7c73;color:#fff}",

      ".dssx-bar{display:flex;gap:8px;padding:11px 12px;border-top:1px solid #dfe6ee;background:#fff}",
      ".dssx-q{flex:1;border:1px solid #dfe6ee;border-radius:10px;padding:10px 12px;font-size:13.5px;",
        "font-family:inherit;resize:none;outline:none;max-height:110px;color:#1b2733}",
      ".dssx-q:focus{border-color:#0e9c91;box-shadow:0 0 0 3px rgba(14,156,145,.13)}",
      ".dssx-send{border:none;background:#0f2740;color:#fff;border-radius:10px;padding:0 14px;cursor:pointer;",
        "display:flex;align-items:center;justify-content:center}",
      ".dssx-send:hover{background:#163b5c}.dssx-send:disabled{opacity:.45;cursor:not-allowed}",
      ".dssx-send svg{width:18px;height:18px;stroke:#fff;fill:none}",
      ".dssx-err{color:#c0392b;background:#fdecea;border:1px solid #f3c4be;padding:9px 12px;border-radius:10px;font-size:12.5px}"
    ].join('');
    doc.head.appendChild(st);
  }

  // SVG glyphs
  var ICON_CHAT = '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>';
  var ICON_X    = '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
  var ICON_SEND = '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>';

  // --- tiny, safe markdown renderer (escape first, then format) ---
  function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  function fmt(t){
    t = esc(t);
    t = t.replace(/`([^`]+)`/g,'<code>$1</code>');
    t = t.replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');
    var lines = t.split('\n'), html='', inUl=false;
    for (var i=0;i<lines.length;i++){
      var ln = lines[i];
      var m = ln.match(/^\s*[-*]\s+(.*)$/);
      if (m){ if(!inUl){html+='<ul>';inUl=true;} html+='<li>'+m[1]+'</li>'; }
      else { if(inUl){html+='</ul>';inUl=false;}
             if(ln.trim()==='') continue;
             html+='<p>'+ln+'</p>'; }
    }
    if(inUl) html+='</ul>';
    return html || '<p></p>';
  }

  // If the widget is already injected (Streamlit rerun), the system prompt was
  // refreshed above; keep the live DOM + chat history and stop here.
  if (doc.getElementById('dssx-root')) return;

  // --- build the launcher + drawer ---
  var root = doc.createElement('div');
  root.id = 'dssx-root';
  root.innerHTML =
    '<button class="dssx-fab" id="dssx-fab" title="Ask the DSS Assistant">' + ICON_CHAT + '</button>' +
    '<aside class="dssx-panel" id="dssx-panel" role="dialog" aria-label="DSS Assistant">' +
      '<div class="dssx-head">' +
        '<span class="dssx-dot"></span>' +
        '<div><h1>DSS Assistant</h1><div class="sub">grok &middot; recommendation analysis</div></div>' +
        '<span class="grow"></span>' +
        '<button class="dssx-x" id="dssx-close" title="Close" aria-label="Close panel">' + ICON_X + '</button>' +
      '</div>' +
      '<div class="dssx-log" id="dssx-log"></div>' +
      '<div class="dssx-chips" id="dssx-chips"></div>' +
      '<div class="dssx-bar">' +
        '<textarea class="dssx-q" id="dssx-q" rows="1" placeholder="Ask about this recommendation, a rejected drone, an alert, or how scoring works..."></textarea>' +
        '<button class="dssx-send" id="dssx-send" title="Send">' + ICON_SEND + '</button>' +
      '</div>' +
    '</aside>';
  doc.body.appendChild(root);

  var fabEl   = doc.getElementById('dssx-fab');
  var panelEl = doc.getElementById('dssx-panel');
  var closeEl = doc.getElementById('dssx-close');
  var logEl   = doc.getElementById('dssx-log');
  var qEl     = doc.getElementById('dssx-q');
  var sendEl  = doc.getElementById('dssx-send');
  var chipsEl = doc.getElementById('dssx-chips');

  function openPanel(){ panelEl.classList.add('dssx-open'); fabEl.classList.add('dssx-gone'); S.open=true; qEl.focus(); }
  function closePanel(){ panelEl.classList.remove('dssx-open'); fabEl.classList.remove('dssx-gone'); S.open=false; }
  fabEl.onclick = openPanel;
  closeEl.onclick = closePanel;

  function addUser(text){
    var d=doc.createElement('div'); d.className='dssx-msg u'; d.textContent=text;
    logEl.appendChild(d); logEl.scrollTop=logEl.scrollHeight;
  }
  function addBot(){
    var d=doc.createElement('div'); d.className='dssx-msg b';
    d.innerHTML='<div class="who">DSS Assistant</div><div class="body">'
      +'<span class="dssx-typing"><span></span><span></span><span></span></span></div>';
    logEl.appendChild(d); logEl.scrollTop=logEl.scrollHeight;
    return d.querySelector('.body');
  }
  function showError(body,msg){ body.innerHTML='<div class="dssx-err">'+esc(msg)+'</div>'; }

  var busy=false;
  function ask(text){
    if(busy || !text.trim()) return;
    busy=true; sendEl.disabled=true;
    addUser(text);
    S.history.push({ role:"user", content:text });
    qEl.value=''; qEl.style.height='auto';
    var body = addBot();

    if(typeof win.puter === 'undefined'){
      showError(body,'Puter.js is still loading. Please try again in a moment.');
      busy=false; sendEl.disabled=false; return;
    }

    (async function(){
      try{
        var resp = await win.puter.ai.chat(S.history, { model: MODEL, stream: true });
        var acc='';
        for await (var part of resp){
          if(part && part.text){ acc += part.text; body.innerHTML = fmt(acc);
            logEl.scrollTop = logEl.scrollHeight; }
        }
        if(!acc){ // some models return non-streaming; fall back
          var r = await win.puter.ai.chat(S.history, { model: MODEL });
          acc = (r && r.message && r.message.content) ? r.message.content : '(no response)';
          body.innerHTML = fmt(acc);
        }
        S.history.push({ role:"assistant", content: acc });
      }catch(e){
        showError(body, 'Could not reach Grok: ' + (e && e.message ? e.message : e)
          + '  (A Puter sign-in popup may need to be allowed on first use.)');
      }finally{
        busy=false; sendEl.disabled=false; logEl.scrollTop=logEl.scrollHeight;
      }
    })();
  }

  // suggestion chips
  var chips = HAS_CONTEXT
    ? [['Summarise this recommendation','p'],
       ['Why was this drone chosen?',''],
       ['Are there any safety concerns?',''],
       ['Why were the other drones rejected?',''],
       ['Should I override this?','']]
    : [['How does the DSS choose a drone?','p'],
       ['What are the 10 hard filter rules?',''],
       ['How is the score calculated?',''],
       ['What triggers a safety alert?','']];
  chips.forEach(function(c){
    var label=c[0], cls=c[1];
    var b=doc.createElement('button'); b.className='dssx-chip'+(cls?' '+cls:'');
    b.textContent=label; b.onclick=function(){ ask(label); }; chipsEl.appendChild(b);
  });

  sendEl.onclick=function(){ ask(qEl.value); };
  qEl.addEventListener('keydown',function(e){
    if(e.key==='Enter' && !e.shiftKey){ e.preventDefault(); ask(qEl.value); }
  });
  qEl.addEventListener('input',function(){ qEl.style.height='auto';
    qEl.style.height=Math.min(qEl.scrollHeight,110)+'px'; });

  // greeting
  var greet = addBot();
  greet.innerHTML = fmt(HAS_CONTEXT
    ? "I can see the current recommendation. Ask me to **summarise it**, explain why a drone was chosen or rejected, or walk through any safety alert."
    : "No recommendation is loaded right now. I can still explain **how the DSS works** — the filter rules, the scoring model, or what triggers a safety alert.");

  if (START_OPEN || S.open) openPanel();
})();
</script>
"""
