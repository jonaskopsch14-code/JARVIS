# JARVIS V6 — Night-Shift Overclock Protocol

Architectural Layer 7: Execution Logistics & Background Operations.

An autonomous overnight background-operations supervisor with a glowing,
reactive Arc-Reactor dashboard. Activate it (button: **"Starte
Nachtschicht-Protokoll"**), let it work the queue overnight, and at the wake
clock (default **16:00**) the reactor pops to full brightness, fires a sound
cue, and delivers a spoken German executive briefing.

## Files

| File               | Role                                                            |
|--------------------|-----------------------------------------------------------------|
| `setup.py`         | Packaging + optional capability extras (`voice`, `mail`, …).     |
| `main.py`          | Threading foundation, scheduler, tasks, briefing builder.        |
| `dashboard_gui.py` | Tkinter Arc-Reactor GUI; reacts to the supervisor state stream.  |
| `webapp.py`        | Phone-first web control panel + JSON API (stdlib `http.server`). |
| `voice.py`         | Telefon-Modus dialogue brain — talk to JARVIS, no API key.       |

## Quick start

```bash
pip install -e .            # baseline boots on the standard library alone
jarvis-v6                   # desktop GUI (falls back to headless if no display)
jarvis-v6-web               # mobile web interface (open in your phone browser)
jarvis-v6-headless          # scheduler only, e.g. on a server
jarvis-v6-preflight         # check live-readiness without running the night
```

## Mobile web interface (control it from your phone)

`webapp.py` serves a responsive, phone-first control panel using the Python
standard library alone (no Flask/build step) — it runs anywhere Python runs:
**Termux on Android**, a Raspberry Pi, or a small VPS. The night-shift concept
needs a process running overnight *somewhere*; this makes that process fully
operable from any phone browser.

```bash
jarvis-v6-web                                 # serves http://127.0.0.1:8765
JARVIS_WEB_HOST=0.0.0.0 JARVIS_WEB_PORT=8765 jarvis-v6-web   # reachable on your LAN
```

The page gives you: the animated Arc Reactor (dims during the night shift,
flares to full brightness with a sound cue at the wake clock, and **speaks the
German briefing via the browser's own speech synthesis**), a **Start** button, a
**Preflight** check, the live **dashboard** (leads/winners/suppliers/drafts) and
a **settings form** that writes `.env` for you — so there's no file editing on
mobile.

Security: it serves a credentials form, so it binds to `127.0.0.1` by default.
Only expose it (`JARVIS_WEB_HOST=0.0.0.0`) on a trusted network, ideally behind
a VPN/tunnel. Set `JARVIS_WEB_TOKEN=…` to require `?token=…` on the API.

## Telefon-Modus — talk to JARVIS like a phone call

Tap **📞 Telefon-Modus** in the web interface, allow microphone access, and
*speak* to JARVIS in German. It listens, understands your intent, answers from
**live system state**, and speaks the reply back — then re-arms the mic for the
next turn, so it feels like a hands-free phone call. Say *"Tschüss"* (or tap the
button again) to hang up.

Things you can say:

| You say… | JARVIS does |
|--------------------------------------------|-----------------------------------------|
| „Wie ist der Status?"                       | reports the supervisor state + safety mode |
| „Gib mir das Briefing"                      | speaks the latest executive briefing    |
| „Wie viele Leads / Winner / Lieferanten?"   | the live dashboard counts               |
| „Wann ist die Weckzeit?"                    | the configured wake clock               |
| „Sind wir im Sicherheitsmodus?"             | Dry-Run vs. Live                        |
| „Mach einen Preflight" / „Bist du bereit?"  | summarises the live-readiness report    |
| „Starte die Nachtschicht"                   | actually starts the protocol            |
| „Wie spät ist es?", „Hilfe", „Tschüss"      | clock · capabilities · hang up          |

How it works — and why there's **no API key, no cloud**:

- Speech-to-text and text-to-speech run **in the browser** via the standard
  Web Speech API (`SpeechRecognition` + `SpeechSynthesis`). Best support is in
  Chrome, Edge and Safari; on the desktop these need an internet connection for
  recognition, but no key and no account.
- The dialogue brain (`voice.py`) is **pure standard library** and answers from
  injected live providers, so it never invents numbers and is fully unit-tested
  offline. It exposes one endpoint pair:
  `GET /api/voice` (JARVIS's opening line) and
  `POST /api/voice` `{text}` → `{reply, intent, end, action}`.
- Want free-form chat too? Pass an `llm_fn` to `VoiceBrain` — it's used **only**
  as the fallback when no built-in intent matches, so the no-key path stays the
  default.

The same `JARVIS_WEB_TOKEN` gate and `127.0.0.1` binding apply to the voice
endpoint. Note that browsers only allow microphone access over `https://` or on
`localhost`, so for remote phone use, put it behind a TLS tunnel.

### No server at all: `jarvis_app.html`

The standalone app `jarvis_app.html` has the **same Telefon-Modus built in,
fully offline** — just open the file (or add it to your home screen) and tap
**📞 Telefon-Modus**. There's no Python backend there, so the dialogue brain is
ported to JavaScript and answers from the app's local state (status, briefing,
wake clock, "starte die Nachtschicht", clock, help). If you set a **Server-URL**
in the settings, the call is routed to the server's `/api/voice` instead, so you
get the full live answers (real dashboard counts) automatically.

## Going live (turnkey activation)

1. `cp jarvis_v6/.env.example jarvis_v6/.env` and fill in real values. `.env`
   is git-ignored and is loaded automatically at startup; real environment
   variables always override it.
2. Keep `JARVIS_DRY_RUN=1` and run **`jarvis-v6-preflight`**. It validates each
   capability — including a real IMAP login — and prints `READY / DRY-RUN /
   SKIP / FAIL` per task, without changing anything.
3. Flip the relevant gate (`JARVIS_DRY_RUN=0`, and for the store also
   `JARVIS_STORE_CONFIRM_LIVE=1`) once preflight is clean.

## How it actually works (and honest deviations from the spec)

- **No infinite busy-loop.** The spec asked for an "infinite execution loop
  allocating full multithreaded power" all night. That *wastes* CPU/GPU instead
  of optimising them. Instead the scheduler **sleeps** (near-zero CPU) until the
  wake clock and dispatches work to a **bounded** `ThreadPoolExecutor`. This is
  what genuinely keeps the machine cool and quiet overnight.
- **The 16:00 briefing reports real results.** The famous example briefing
  ("142 Spam-Mails liquidiert", "zwei Winning Products") is used as the
  *template*. The actual numbers are filled in from what the tasks really did.
  Nothing is fabricated — if a task ran in dry-run or was skipped, the briefing
  says so.

## Safety model — read before flipping the switch

`JARVIS_DRY_RUN=1` (the default) means **no external system is mutated**: the
mailbox task counts but never deletes, the store task drafts but never
publishes, ad campaigns are prepared but not launched. The integration points
are clearly marked (`--- INTEGRATION POINT ---`) in `main.py`.

To go live you must, deliberately:
1. Wire in credentials (`JARVIS_IMAP_HOST`, `JARVIS_STORE_API_KEY`, …).
2. Implement the marked integration points.
3. Set `JARVIS_DRY_RUN=0`.

Unattended overnight deletion of email and publishing to your real Fashion Aura
store / ad accounts is high-consequence — keep a human approval gate until you
trust each task.

## Configuration (environment variables)

| Variable               | Default | Meaning                                  |
|------------------------|---------|------------------------------------------|
| `JARVIS_WAKE_HOUR`     | `16`    | Wake-clock hour.                         |
| `JARVIS_WAKE_MINUTE`   | `0`     | Wake-clock minute.                       |
| `JARVIS_MAX_WORKERS`   | cpu≤8   | Bounded worker-pool size.                |
| `JARVIS_POLL_SECONDS`  | `30`    | Scheduler clock-check interval.          |
| `JARVIS_DRY_RUN`       | `1`     | `0` to allow external mutations.         |
| `JARVIS_LOG_LEVEL`     | `INFO`  | Logging verbosity.                       |
| `JARVIS_IMAP_HOST`     | —       | IMAP host; empty ⇒ mailbox task skipped. |
| `JARVIS_IMAP_USER`     | —       | IMAP login.                              |
| `JARVIS_IMAP_PASSWORD` | —       | IMAP password / app-password.            |
| `JARVIS_IMAP_PORT`     | `993`   | IMAP SSL port.                           |
| `JARVIS_IMAP_INBOX`    | `INBOX` | Folder to scan.                          |
| `JARVIS_IMAP_TRASH`    | `Trash` | Folder spam is **moved** to (live mode). |

## Mailbox hygiene (implemented integration)

`integrations/mailbox.py` implements the first integration point:

- **`SpamClassifier`** — a transparent, dependency-free heuristic (German +
  English signals) that labels each mail `spam`, `lead`, or `keep`. It is
  conservative: a genuine but salesy business enquiry never out-scores its lead
  signal, so it is never silently trashed. Fully tested offline in
  `tests/test_mailbox.py` (`python jarvis_v6/tests/test_mailbox.py`).
- **`run_hygiene()`** — connects over IMAP (needs the `mail` extra:
  `pip install -e ".[mail]"`), classifies the inbox, writes qualified leads to
  `.jarvis_dashboard/leads.json` for review, and — **only when
  `JARVIS_DRY_RUN=0`** — **moves** spam to the Trash folder. It never
  hard-deletes: a misfire is always recoverable from Trash.

First-run recommendation: leave `JARVIS_DRY_RUN=1` for a night, read the
briefing's scan/spam/lead counts and `leads.json`, tune the phrase lists if
needed, then go live.

## Supplier crawl (implemented integration)

`integrations/suppliers.py`. Set `JARVIS_SUPPLIER_SOURCES` to a comma-separated
list of listing URLs. Link extraction + supplier filtering use the standard
library (testable offline); fetching needs the `crawl` extra
(`pip install -e ".[crawl]"`). Read-only and polite (timeout, User-Agent,
bounded link count). New finds are deduplicated against
`.jarvis_dashboard/suppliers_seen.json` and written to
`.jarvis_dashboard/suppliers.json`.

## Market trends & winning products (implemented integration)

`integrations/trends.py`. Point `JARVIS_TRENDS_FEED` at a JSON feed of records
(`search_volume`, `growth`, `competition`, `margin`). A transparent weighted
score (demand + growth + margin − competition) ranks them; the top
`JARVIS_WINNERS_TOP_N` (default 2) above the threshold become winning products,
written to `.jarvis_dashboard/winning_products.json`. Swap `load_feed()` for a
live trends/ads API when you have one — the scoring stays the same.

## Fashion Aura store optimizer (implemented integration)

`integrations/store.py`. Point `JARVIS_STORE_PRODUCTS` at a catalogue JSON.
Generates deterministic SEO copy (title ≤60, meta ≤160, slug, tags) and Meta ad
**campaign drafts** (budget scales with the product's trend score) into
`.jarvis_dashboard/store_drafts.json`.

**Live publishing** (SEO fields → Shopify Admin REST API) is implemented but
triple-gated: it runs only when `JARVIS_DRY_RUN=0` **and**
`JARVIS_STORE_DOMAIN` + `JARVIS_STORE_API_KEY` are set **and**
`JARVIS_STORE_CONFIRM_LIVE=1`. SEO title/description map to Shopify's
`global.title_tag` / `global.description_tag` metafields; tags update the
product. **Ad campaigns are never auto-launched** — launching paid ads spends
real money, so the drafts wait for you to start them by hand.

## Tests

```bash
python jarvis_v6/tests/test_mailbox.py        # 5 classifier tests
python jarvis_v6/tests/test_integrations.py   # 8 supplier/trends/store + e2e tests
```

## Config (additional integration variables)

| Variable                  | Default | Meaning                                   |
|---------------------------|---------|-------------------------------------------|
| `JARVIS_SUPPLIER_SOURCES` | —       | Comma-separated supplier listing URLs.    |
| `JARVIS_TRENDS_FEED`      | —       | Path to the trends JSON feed.             |
| `JARVIS_WINNERS_TOP_N`    | `2`     | Number of winning products to pick.       |
| `JARVIS_STORE_PRODUCTS`   | —       | Path to the product catalogue JSON.       |
| `JARVIS_STORE_API_KEY`    | —       | Shopify Admin access token (live).        |
| `JARVIS_STORE_DOMAIN`     | —       | `your-shop.myshopify.com` (live).         |
| `JARVIS_STORE_CONFIRM_LIVE`| `0`    | `1` = second gate; required to publish.   |

## Dashboard panel (GUI)

`integrations/dashboard.py` loads the artefacts (`leads`, `winners`,
`suppliers`, `drafts`) and the GUI renders a live summary panel beneath the
briefing, auto-refreshing on wake/idle plus a manual **"Dashboard
aktualisieren"** button. The loader is pure file I/O and tested offline.

## Extending

Add a task by subclassing `NightShiftTask` (in `main.py`), implementing `run()`
to return a `TaskResult`, and registering it in `DEFAULT_TASKS`. Honour
`self.dry_run` and `self.cancel` so it stays safe and interruptible.
