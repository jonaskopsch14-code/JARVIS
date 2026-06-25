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

## Quick start

```bash
pip install -e .            # baseline boots on the standard library alone
jarvis-v6                   # GUI (falls back to headless if no display)
jarvis-v6-headless          # scheduler only, e.g. on a server
```

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

## Extending

Add a task by subclassing `NightShiftTask` (in `main.py`), implementing `run()`
to return a `TaskResult`, and registering it in `DEFAULT_TASKS`. Honour
`self.dry_run` and `self.cancel` so it stays safe and interruptible.
