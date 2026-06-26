"""
JARVIS V6 — Mobile web interface.

A phone-friendly control panel for the Night-Shift Overclock Protocol, served
by the Python standard library alone (http.server) — no Flask, no build step,
runs anywhere Python runs (incl. Termux on Android, a Raspberry Pi or a small
VPS). Open it in your phone browser.

It exposes:
  GET  /                 the responsive dashboard (animated Arc Reactor in CSS)
  GET  /api/status       current system state + last briefing + counts
  GET  /api/dashboard    leads / winners / suppliers / drafts
  GET  /api/preflight    live-readiness report
  GET  /api/config       current settings (secrets masked)
  POST /api/config       save settings to .env (no manual file editing)
  POST /api/start        start the night shift
  GET  /api/voice        JARVIS's opening line (pick up the phone)
  POST /api/voice        one conversation turn: {text} -> {reply, intent, end, action}

The browser handles the wake flourish: when the state turns to WAKING/BRIEFING
the page flares the reactor to full brightness, plays a sound cue (Web Audio)
and speaks the German briefing via the SpeechSynthesis API.

Security note: this serves a credentials form, so it binds to 127.0.0.1 by
default. Only expose it (JARVIS_WEB_HOST=0.0.0.0) on a network you trust, and
ideally behind a tunnel/VPN. An optional shared token (JARVIS_WEB_TOKEN) gates
the API when set.
"""

from __future__ import annotations

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, urlparse

from main import (
    NightShiftConfig, NightShiftSupervisor, SystemState, preflight,
)
from integrations.dashboard import load_dashboard
from voice import brain_for_app

# Settings the mobile form is allowed to write to .env. Secrets are masked on read.
EDITABLE_KEYS = [
    "JARVIS_DRY_RUN", "JARVIS_WAKE_HOUR", "JARVIS_WAKE_MINUTE",
    "JARVIS_IMAP_HOST", "JARVIS_IMAP_USER", "JARVIS_IMAP_PASSWORD",
    "JARVIS_IMAP_PORT", "JARVIS_IMAP_INBOX", "JARVIS_IMAP_TRASH",
    "JARVIS_SUPPLIER_SOURCES", "JARVIS_TRENDS_FEED", "JARVIS_WINNERS_TOP_N",
    "JARVIS_STORE_PRODUCTS", "JARVIS_STORE_DOMAIN", "JARVIS_STORE_API_KEY",
    "JARVIS_STORE_CONFIRM_LIVE",
]
SECRET_KEYS = {"JARVIS_IMAP_PASSWORD", "JARVIS_STORE_API_KEY"}


def _env_path() -> Path:
    return Path(os.getenv("JARVIS_ENV_FILE", str(Path(__file__).resolve().parent / ".env")))


def update_env_file(path: Path, updates: dict) -> None:
    """Insert/replace KEY=VALUE lines in a .env file, preserving other lines.

    Pure file I/O, dependency-free and unit-testable. Only keys in
    EDITABLE_KEYS are written; empty values are still written (to clear a key).
    """
    path = Path(path)
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    remaining = {k: v for k, v in updates.items() if k in EDITABLE_KEYS}
    out = []
    for raw in lines:
        stripped = raw.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in remaining:
                out.append(f"{key}={remaining.pop(key)}")
                continue
        out.append(raw)
    for key, value in remaining.items():
        out.append(f"{key}={value}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def masked_config() -> dict:
    """Return current settings for the form; secrets reported as set/unset only."""
    result = {}
    for key in EDITABLE_KEYS:
        val = os.getenv(key, "")
        if key in SECRET_KEYS:
            result[key] = "***gesetzt***" if val else ""
        else:
            result[key] = val
    return result


class WebApp:
    """Holds the supervisor + the latest state for the HTTP handler to read."""

    def __init__(self, config: Optional[NightShiftConfig] = None):
        self.config = config or NightShiftConfig()
        self._lock = threading.Lock()
        self.state = SystemState.IDLE.value
        self.last_event: dict = {}
        self.briefing = ""
        self.running = False
        self.supervisor = NightShiftSupervisor(self.config, on_state=self._on_state)
        # The conversation brain ("Telefon-Modus"). Wired to this app's live
        # providers; no API key, pure standard library.
        self.brain = brain_for_app(self)

    def _on_state(self, state: SystemState, info: dict) -> None:
        with self._lock:
            self.state = state.value
            self.last_event = {k: str(v) for k, v in (info or {}).items()}
            if state == SystemState.BRIEFING and info.get("text"):
                self.briefing = info["text"]
            if state in (SystemState.IDLE, SystemState.STOPPED):
                self.running = False

    def start(self) -> bool:
        with self._lock:
            if self.running:
                return False
            self.running = True
            self.briefing = ""
        self.supervisor.cancel.clear()
        self.supervisor.start_async(wake_callback=lambda _t: None)
        return True

    def status(self) -> dict:
        data = load_dashboard(self.config.dashboard_dir)
        with self._lock:
            return {
                "state": self.state,
                "running": self.running,
                "briefing": self.briefing,
                "event": self.last_event,
                "wake_hour": self.config.wake_hour,
                "wake_minute": self.config.wake_minute,
                "dry_run": self.config.dry_run,
                "counts": data.counts,
            }

    def dashboard(self) -> dict:
        data = load_dashboard(self.config.dashboard_dir)
        return {"leads": data.leads, "winners": data.winners,
                "suppliers": data.suppliers, "drafts": data.drafts,
                "counts": data.counts}

    def preflight(self) -> dict:
        rows = preflight(self.config)
        return {"rows": [{"capability": c, "status": s, "detail": d} for c, s, d in rows]}

    def voice(self, text: str) -> dict:
        """Run one conversational turn: a recognised utterance in, a spoken
        reply out (the browser speaks it via the Web Speech API)."""
        return self.brain.reply(text).as_dict()

    def greeting(self) -> str:
        return self.brain.greeting()


def _make_handler(app: WebApp):
    token = os.getenv("JARVIS_WEB_TOKEN", "")

    class Handler(BaseHTTPRequestHandler):
        server_version = "JARVIS-V6-Web/1.0"

        def log_message(self, *args):  # quieter logs
            pass

        # -- helpers --------------------------------------------------------
        def _send_json(self, obj, code=200):
            body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_html(self, html, code=200):
            body = html.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _authed(self) -> bool:
            if not token:
                return True
            given = self.headers.get("X-JARVIS-Token", "")
            qs = parse_qs(urlparse(self.path).query)
            return given == token or qs.get("token", [""])[0] == token

        # -- routes ---------------------------------------------------------
        def do_GET(self):
            route = urlparse(self.path).path
            if route in ("/", "/index.html"):
                return self._send_html(INDEX_HTML)
            if route.startswith("/api/") and not self._authed():
                return self._send_json({"error": "unauthorized"}, 401)
            if route == "/api/status":
                return self._send_json(app.status())
            if route == "/api/dashboard":
                return self._send_json(app.dashboard())
            if route == "/api/preflight":
                return self._send_json(app.preflight())
            if route == "/api/config":
                return self._send_json(masked_config())
            if route == "/api/voice":
                # Pick up the phone: JARVIS's opening line.
                return self._send_json({"reply": app.greeting(), "intent": "greeting"})
            return self._send_json({"error": "not found"}, 404)

        def do_POST(self):
            route = urlparse(self.path).path
            if not self._authed():
                return self._send_json({"error": "unauthorized"}, 401)
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(length).decode("utf-8") if length else ""
            if route == "/api/start":
                started = app.start()
                return self._send_json({"started": started, "state": app.state})
            if route == "/api/voice":
                try:
                    payload = json.loads(raw) if raw.strip().startswith("{") else \
                        {k: v[0] for k, v in parse_qs(raw).items()}
                except ValueError:
                    return self._send_json({"error": "bad payload"}, 400)
                return self._send_json(app.voice(str(payload.get("text", ""))))
            if route == "/api/config":
                try:
                    payload = json.loads(raw) if raw.strip().startswith("{") else \
                        {k: v[0] for k, v in parse_qs(raw).items()}
                except ValueError:
                    return self._send_json({"error": "bad payload"}, 400)
                # Never overwrite a secret with the masked placeholder.
                updates = {k: v for k, v in payload.items()
                           if k in EDITABLE_KEYS and v != "***gesetzt***"}
                update_env_file(_env_path(), updates)
                return self._send_json({"saved": sorted(updates.keys()),
                                        "note": "Neustart nötig, damit Änderungen greifen."})
            return self._send_json({"error": "not found"}, 404)

    return Handler


def create_server(config: Optional[NightShiftConfig] = None,
                  host: Optional[str] = None, port: Optional[int] = None):
    """Build (httpd, app). Caller runs httpd.serve_forever()."""
    app = WebApp(config)
    host = host or os.getenv("JARVIS_WEB_HOST", "127.0.0.1")
    port = int(port if port is not None else os.getenv("JARVIS_WEB_PORT", "8765"))
    httpd = ThreadingHTTPServer((host, port), _make_handler(app))
    return httpd, app


def run_web() -> None:
    """Entry point: serve the mobile dashboard until interrupted."""
    import logging
    logging.basicConfig(level=os.getenv("JARVIS_LOG_LEVEL", "INFO"))
    httpd, _ = create_server()
    host, port = httpd.server_address
    print(f"JARVIS V6 Web läuft auf http://{host}:{port}  "
          f"(Strg+C zum Beenden)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()


# ---------------------------------------------------------------------------
# The single-page mobile UI. Pure HTML/CSS/JS, all data via the JSON API.
# ---------------------------------------------------------------------------
INDEX_HTML = r"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#05080d">
<title>JARVIS V6</title>
<style>
  :root { --glow:#00c8ff; --core:#d2f5ff; --bg:#05080d; }
  * { box-sizing:border-box; -webkit-tap-highlight-color:transparent; }
  body { margin:0; background:var(--bg); color:#bfefff;
         font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
         text-align:center; padding:18px 14px 40px; }
  h1 { font-size:15px; letter-spacing:3px; color:#7fe8ff; font-weight:600; margin:4px 0 16px; }
  /* Arc reactor */
  .reactor { width:min(70vw,260px); height:min(70vw,260px); margin:6px auto 10px;
             border-radius:50%; position:relative; transition:filter .8s, opacity .8s;
             filter:brightness(1); }
  .reactor.dim { filter:brightness(.25); opacity:.5; }
  .ring { position:absolute; inset:0; border-radius:50%; }
  .ring.outer { background:conic-gradient(from 0deg,#012a3d,#00c8ff,#012a3d,#00c8ff,#012a3d);
                animation:spin 6s linear infinite;
                box-shadow:0 0 40px 6px rgba(0,200,255,.55), inset 0 0 30px rgba(0,200,255,.4); }
  .ring.mid { inset:14%; background:#05080d;
              box-shadow:inset 0 0 24px rgba(0,200,255,.6); }
  .ring.coil { inset:22%; border-radius:50%;
               background:repeating-conic-gradient(#00c8ff 0 6deg,#022 6deg 18deg);
               opacity:.5; animation:spin 9s linear infinite reverse; }
  .core { position:absolute; inset:34%; border-radius:50%;
          background:radial-gradient(circle,#ffffff 0%,var(--core) 30%,var(--glow) 70%,#024 100%);
          box-shadow:0 0 50px 12px rgba(120,230,255,.85); animation:pulse 2.6s ease-in-out infinite; }
  @keyframes spin { to { transform:rotate(360deg); } }
  @keyframes pulse { 0%,100%{ transform:scale(.94); opacity:.85;} 50%{ transform:scale(1.04); opacity:1;} }
  .reactor.wake .core { animation:flare 1.2s ease-out; box-shadow:0 0 90px 26px rgba(160,240,255,1); }
  @keyframes flare { 0%{ transform:scale(.6); } 60%{ transform:scale(1.25);} 100%{ transform:scale(1);} }
  .state { font-size:13px; letter-spacing:2px; color:#7fe8ff; min-height:18px; }
  .briefing { font-size:13px; line-height:1.5; color:#cdeffb; margin:12px auto; max-width:520px;
              background:rgba(0,40,60,.35); border:1px solid rgba(0,200,255,.25);
              border-radius:12px; padding:12px; min-height:8px; }
  button { font:inherit; color:#7fe8ff; background:#0a2a3a; border:1px solid rgba(0,200,255,.4);
           border-radius:12px; padding:13px 16px; margin:5px 4px; min-width:46%;
           transition:background .15s; }
  button:active { background:#0f3d52; }
  button.primary { background:#0e3a50; font-weight:600; min-width:94%; }
  .row { display:flex; flex-wrap:wrap; justify-content:center; max-width:520px; margin:0 auto; }
  details { max-width:520px; margin:14px auto; text-align:left;
            border:1px solid rgba(0,200,255,.2); border-radius:12px; }
  summary { padding:12px; cursor:pointer; color:#7fe8ff; }
  .panel { padding:0 12px 12px; font-size:13px; }
  label { display:block; font-size:12px; color:#88c9dd; margin:9px 0 3px; }
  input,select { width:100%; padding:10px; border-radius:9px; border:1px solid rgba(0,200,255,.3);
                 background:#04141c; color:#dff; font:inherit; }
  .counts { font-size:12px; color:#9fd8e8; margin:8px 0; }
  .item { padding:6px 0; border-bottom:1px solid rgba(0,200,255,.12); font-size:12px; }
  .ok{color:#7CFC9A}.warn{color:#ffd479}.bad{color:#ff8080}.muted{color:#88a}
  .callhint { font-size:11px; max-width:520px; margin:2px auto 6px; line-height:1.4; }
  button.calling { background:#3a0e1c; border-color:rgba(255,90,120,.5); color:#ffd0d8;
                   animation:callpulse 1.4s ease-in-out infinite; }
  @keyframes callpulse { 0%,100%{ box-shadow:0 0 0 0 rgba(255,90,120,.4);} 50%{ box-shadow:0 0 0 10px rgba(255,90,120,0);} }
  .transcript { max-width:520px; margin:8px auto; text-align:left; font-size:13px; line-height:1.45; }
  .transcript .me  { color:#9fd8e8; margin:6px 0; }
  .transcript .jv  { color:#cdeffb; margin:6px 0; background:rgba(0,40,60,.35);
                     border:1px solid rgba(0,200,255,.22); border-radius:10px; padding:8px 10px; }
  .transcript .me b, .transcript .jv b { color:#7fe8ff; font-weight:600; }
</style>
</head>
<body>
  <h1>J A R V I S · V6</h1>
  <div class="reactor" id="reactor"><div class="ring outer"></div><div class="ring coil"></div>
    <div class="ring mid"></div><div class="core"></div></div>
  <div class="state" id="state">…</div>
  <div class="counts" id="counts"></div>
  <div class="briefing" id="briefing"></div>

  <div class="row">
    <button class="primary" id="startBtn" onclick="start()">Starte Nachtschicht-Protokoll</button>
    <button onclick="preflight()">Preflight prüfen</button>
    <button onclick="loadDash()">Dashboard aktualisieren</button>
  </div>

  <div class="row">
    <button class="primary" id="callBtn" onclick="toggleCall()">📞 Telefon-Modus starten</button>
  </div>
  <div class="callhint muted" id="callHint">Tippe „Telefon-Modus", erlaube das Mikrofon und sprich
    mit JARVIS — z.&nbsp;B. „Wie ist der Status?", „Gib mir das Briefing", „Starte die Nachtschicht".
    Zum Auflegen „Tschüss" sagen oder den Button erneut tippen.</div>
  <div class="transcript" id="transcript"></div>

  <details id="pf"><summary>Preflight-Status</summary><div class="panel" id="pfBody">—</div></details>

  <details><summary>Dashboard (Leads · Winner · Lieferanten)</summary>
    <div class="panel" id="dashBody">—</div></details>

  <details><summary>Einstellungen</summary>
    <div class="panel">
      <label>Sicherheitsmodus</label>
      <select id="JARVIS_DRY_RUN"><option value="1">Dry-Run (sicher)</option>
        <option value="0">LIVE (ändert echte Systeme)</option></select>
      <label>Weckzeit (Stunde / Minute)</label>
      <div class="row" style="gap:6px">
        <input id="JARVIS_WAKE_HOUR" inputmode="numeric" placeholder="16" style="min-width:0">
        <input id="JARVIS_WAKE_MINUTE" inputmode="numeric" placeholder="0" style="min-width:0"></div>
      <label>IMAP Host / User / Passwort</label>
      <input id="JARVIS_IMAP_HOST" placeholder="imap.gmail.com">
      <input id="JARVIS_IMAP_USER" placeholder="du@example.com" autocapitalize="off">
      <input id="JARVIS_IMAP_PASSWORD" type="password" placeholder="App-Passwort">
      <label>Trends-Feed / Produktkatalog (Pfade)</label>
      <input id="JARVIS_TRENDS_FEED" placeholder="/pfad/trends.json">
      <input id="JARVIS_STORE_PRODUCTS" placeholder="/pfad/products.json">
      <label>Shopify Domain / Token</label>
      <input id="JARVIS_STORE_DOMAIN" placeholder="shop.myshopify.com" autocapitalize="off">
      <input id="JARVIS_STORE_API_KEY" type="password" placeholder="Admin API Token">
      <label>Store live veröffentlichen?</label>
      <select id="JARVIS_STORE_CONFIRM_LIVE"><option value="0">Nein</option>
        <option value="1">Ja, bestätigt</option></select>
      <div class="row"><button class="primary" onclick="saveCfg()">Einstellungen speichern</button></div>
      <div class="muted" id="cfgMsg" style="font-size:11px"></div>
    </div>
  </details>

<script>
const $ = id => document.getElementById(id);
const CFG_KEYS = ["JARVIS_DRY_RUN","JARVIS_WAKE_HOUR","JARVIS_WAKE_MINUTE","JARVIS_IMAP_HOST",
  "JARVIS_IMAP_USER","JARVIS_IMAP_PASSWORD","JARVIS_TRENDS_FEED","JARVIS_STORE_PRODUCTS",
  "JARVIS_STORE_DOMAIN","JARVIS_STORE_API_KEY","JARVIS_STORE_CONFIRM_LIVE"];
const TOKEN = new URLSearchParams(location.search).get("token") || "";
const H = TOKEN ? {"X-JARVIS-Token":TOKEN,"Content-Type":"application/json"} : {"Content-Type":"application/json"};
let spoken = "", lastState = "";

async function api(path, opts){ const r = await fetch(path,{headers:H,...(opts||{})}); return r.json(); }

function setReactor(state){
  const r = $("reactor");
  const dim = (state==="night_shift"||state==="sleeping");
  r.classList.toggle("dim", dim);
  if((state==="waking"||state==="briefing") && lastState!==state){
    r.classList.remove("dim"); r.classList.add("wake"); soundCue();
    setTimeout(()=>r.classList.remove("wake"),1300);
  }
  lastState = state;
}
function soundCue(){
  try{ const a=new (window.AudioContext||window.webkitAudioContext)();
    const o=a.createOscillator(), g=a.createGain();
    o.connect(g); g.connect(a.destination); o.type="sine"; o.frequency.value=660;
    g.gain.setValueAtTime(.0001,a.currentTime); g.gain.exponentialRampToValueAtTime(.3,a.currentTime+.05);
    g.gain.exponentialRampToValueAtTime(.0001,a.currentTime+.9); o.start(); o.stop(a.currentTime+.9);
  }catch(e){}
}
function jarvisVoice(){
  const vs=(window.speechSynthesis&&window.speechSynthesis.getVoices())||[];
  const male=v=>/male|männlich|conrad|stefan|markus|daniel|david|uk english male|george|arthur/i.test(v.name);
  const de=vs.filter(v=>/^de/i.test(v.lang)), enGB=vs.filter(v=>/^en[-_]?gb/i.test(v.lang));
  return de.find(male)||enGB.find(male)||enGB[0]||de[0]||vs[0]||null;
}
function speak(text){
  if(!text || text===spoken || !window.speechSynthesis) return; spoken=text;
  const u=new SpeechSynthesisUtterance(text);
  const v=jarvisVoice(); if(v){ u.voice=v; u.lang=v.lang; } else { u.lang="de-DE"; }
  u.pitch=0.8; u.rate=0.96;   // tiefer/ruhiger = JARVIS
  window.speechSynthesis.speak(u);
}
const LABELS={booting:"INITIALISIERE…",night_shift:"NACHTSCHICHT AKTIV",sleeping:"WARTE AUF 16:00",
  waking:"WECK-SEQUENZ",briefing:"EXECUTIVE BRIEFING",idle:"SYSTEM BEREIT",stopped:"GESTOPPT"};

async function tick(){
  try{
    const s = await api("/api/status");
    $("state").textContent = LABELS[s.state]||s.state.toUpperCase();
    setReactor(s.state);
    const c=s.counts||{};
    $("counts").textContent = `Leads ${c.leads||0} · Winner ${c.winners||0} · Lieferanten ${c.suppliers||0} · Entwürfe ${c.drafts||0}`;
    if(s.briefing){ $("briefing").textContent = s.briefing; if(s.state==="briefing" && !inCall) speak(s.briefing); }
    $("startBtn").disabled = !!s.running;
    $("startBtn").textContent = s.running ? "Protokoll läuft…" : "Starte Nachtschicht-Protokoll";
  }catch(e){ $("state").textContent="OFFLINE"; }
}
async function start(){ await api("/api/start",{method:"POST",body:"{}"}); tick(); }
async function preflight(){
  const d = await api("/api/preflight");
  $("pf").open = true;
  $("pfBody").innerHTML = d.rows.map(r=>{
    const cls = r.status==="FAIL"?"bad":(r.status==="READY"?"ok":(r.status==="LIVE"?"warn":"muted"));
    return `<div class="item"><b>${r.capability}</b> <span class="${cls}">${r.status}</span><br><span class="muted">${r.detail}</span></div>`;
  }).join("");
}
async function loadDash(){
  const d = await api("/api/dashboard");
  const sec=(t,arr,fmt)=> arr.length? `<div style="margin-top:6px;color:#7fe8ff">${t}</div>`+arr.slice(0,5).map(fmt).join(""):"";
  $("dashBody").innerHTML =
    sec("Leads", d.leads, x=>`<div class="item">${x.from||"?"} — ${x.subject||""}</div>`)+
    sec("Winning Products", d.winners, x=>`<div class="item">${x.title||"?"} ${x.score!=null?("· "+x.score):""}</div>`)+
    sec("Lieferanten", d.suppliers, x=>`<div class="item">${x.name||x.url||"?"}</div>`)+
    (d.counts.leads+d.counts.winners+d.counts.suppliers===0?'<div class="muted">Noch keine Daten.</div>':"");
}
async function loadCfg(){
  const c = await api("/api/config");
  CFG_KEYS.forEach(k=>{ const el=$(k); if(!el) return;
    if(el.tagName==="SELECT"){ el.value = c[k]||el.value; }
    else { el.value = (c[k]==="***gesetzt***")? "" : (c[k]||""); if(c[k]==="***gesetzt***") el.placeholder="•••• gesetzt"; }
  });
}
async function saveCfg(){
  const body={}; CFG_KEYS.forEach(k=>{ const el=$(k); if(el && el.value!=="") body[k]=el.value; });
  const r = await api("/api/config",{method:"POST",body:JSON.stringify(body)});
  $("cfgMsg").textContent = "Gespeichert: "+(r.saved||[]).join(", ")+" — "+(r.note||"");
}
// ---- Telefon-Modus: zweiweg-Sprache über die Web Speech API ----------------
// Turn-basiert (Walkie-Talkie): JARVIS spricht, dann hört er zu, dann wieder.
// Das vermeidet, dass das Mikro die eigene Sprachausgabe als Eingabe aufnimmt.
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
let recog=null, inCall=false, listening=false, awaitingReply=false;

function addLine(who, text){
  const box=$("transcript");
  const div=document.createElement("div");
  div.className = who==="me" ? "me" : "jv";
  const safe=(text||"").replace(/&/g,"&amp;").replace(/</g,"&lt;");
  div.innerHTML = `<b>${who==="me"?"Du":"JARVIS"}:</b> ${safe}`;
  box.appendChild(div); div.scrollIntoView({block:"end", behavior:"smooth"});
}

// Speak and resolve when the utterance finishes (so we re-arm the mic after).
function speakAsync(text){
  return new Promise(res=>{
    if(!text || !window.speechSynthesis){ res(); return; }
    try{ window.speechSynthesis.cancel(); }catch(e){}
    const u=new SpeechSynthesisUtterance(text); u.lang="de-DE"; u.rate=1.02;
    u.onend=()=>res(); u.onerror=()=>res();
    window.speechSynthesis.speak(u);
  });
}
async function jarvisSay(text){ addLine("jv", text); await speakAsync(text); }

function listenOnce(){
  if(!inCall || !recog || listening) return;
  try{ recog.start(); listening=true; }catch(e){ /* already running */ }
}

async function handleUtterance(text){
  if(!text){ listenOnce(); return; }
  awaitingReply=true; addLine("me", text);
  let data;
  try{ data = await api("/api/voice",{method:"POST",body:JSON.stringify({text})}); }
  catch(e){ data={reply:"Verbindungsfehler — ich erreiche das System gerade nicht.", end:false}; }
  await jarvisSay(data.reply || "…");
  if(data.action==="started") tick();
  awaitingReply=false;
  if(data.end){ stopCall(); return; }
  listenOnce();
}

async function startCall(){
  if(!SR){ addLine("jv","Dein Browser unterstützt keine Spracherkennung. Bitte Chrome, Edge oder Safari nutzen.");
           speakAsync("Dein Browser unterstützt keine Spracherkennung."); return; }
  inCall=true;
  $("callBtn").classList.add("calling");
  $("callBtn").textContent="📞 Auflegen";
  recog=new SR(); recog.lang="de-DE"; recog.continuous=false;
  recog.interimResults=false; recog.maxAlternatives=1;
  recog.onresult=(e)=>{ listening=false; handleUtterance(e.results[0][0].transcript.trim()); };
  recog.onerror=(e)=>{ listening=false;
    if(inCall && !awaitingReply && e.error!=="aborted" && e.error!=="not-allowed")
      setTimeout(listenOnce, 500);
    if(e.error==="not-allowed"){ addLine("jv","Mikrofon-Zugriff verweigert."); stopCall(); }
  };
  recog.onend=()=>{ listening=false; if(inCall && !awaitingReply) setTimeout(listenOnce, 300); };
  let g; try{ g=await api("/api/voice"); }catch(_){ g={reply:"Hier ist JARVIS. Ich höre."}; }
  await jarvisSay(g.reply || "Hier ist JARVIS. Ich höre.");
  listenOnce();
}

function stopCall(){
  inCall=false; listening=false; awaitingReply=false;
  try{ recog && recog.abort(); }catch(e){}
  try{ window.speechSynthesis.cancel(); }catch(e){}
  $("callBtn").classList.remove("calling");
  $("callBtn").textContent="📞 Telefon-Modus starten";
}
function toggleCall(){ inCall ? stopCall() : startCall(); }

loadCfg(); loadDash(); tick(); setInterval(tick, 2000);
</script>
</body>
</html>"""


if __name__ == "__main__":
    run_web()
