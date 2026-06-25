"""
JARVIS V6 — Night-Shift Overclock Protocol
Multithreaded foundation wrapper + autonomous reporting sequencer.

This module is the heart of Architectural Layer 7. It provides:

  * NightShiftSupervisor   — owns a bounded worker pool, runs the registered
                             overnight tasks, collects their real results.
  * Scheduler              — sleeps efficiently until the configured wake time
                             (default 16:00 the following day), then triggers
                             the wake sequence and the spoken briefing.
  * NightShiftTask + tasks — pluggable units of work (supplier crawl, cache
                             purge, mailbox hygiene, market trends, store
                             optimisation). They are SAFE BY DEFAULT: anything
                             that would mutate your mailbox, store or ad
                             accounts runs in dry-run until you supply real
                             credentials and flip `dry_run=False`.
  * Briefing               — fills the German executive-briefing template from
                             the REAL task results (no fabricated numbers).

Design notes (deliberate deviations from a literal reading of the spec):
  * There is NO infinite busy-loop hogging "full multithreaded power" all
    night. That wastes CPU/GPU instead of optimising them. Idle time is spent
    sleeping; work is dispatched to a bounded ThreadPoolExecutor. This is what
    actually keeps the machine cool and the fans quiet overnight.
  * The 16:00 briefing reports what the tasks genuinely did. If the mailbox
    task ran in dry-run, the briefing says so rather than inventing a number.

The GUI (dashboard_gui.py) drives this module; you can also run it headless.
"""

from __future__ import annotations

import logging
import os
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, time as dtime, timedelta
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional

LOG = logging.getLogger("jarvis_v6")


# ---------------------------------------------------------------------------
# System state — broadcast to the GUI so the Arc Reactor can react.
# ---------------------------------------------------------------------------
class SystemState(str, Enum):
    BOOTING = "booting"          # initialising
    NIGHT_SHIFT = "night_shift"  # dimmed, working through the task queue
    SLEEPING = "sleeping"        # work done, waiting for the wake clock
    WAKING = "waking"            # wake sequence: pop to front, full brightness
    BRIEFING = "briefing"        # delivering the spoken executive summary
    IDLE = "idle"                # ready for the next command
    STOPPED = "stopped"


# ---------------------------------------------------------------------------
# Configuration.
# ---------------------------------------------------------------------------
@dataclass
class NightShiftConfig:
    """All knobs in one place. Read from env where it makes sense."""

    # The wake clock. Default 16:00, as specified.
    wake_hour: int = int(os.getenv("JARVIS_WAKE_HOUR", "16"))
    wake_minute: int = int(os.getenv("JARVIS_WAKE_MINUTE", "0"))

    # Bounded parallelism. Defaults to a sensible slice of the box, never
    # "all cores pinned to 100%". Optimising resources != saturating them.
    max_workers: int = int(os.getenv("JARVIS_MAX_WORKERS", str(min(8, (os.cpu_count() or 4)))))

    # How long the scheduler sleeps between wake-clock checks. 30s is plenty:
    # it keeps the thread asleep (near-zero CPU) yet stays accurate to the
    # second once the window is near.
    poll_seconds: float = float(os.getenv("JARVIS_POLL_SECONDS", "30"))

    # Master safety switch. While True, no task is allowed to mutate external
    # systems (mailbox, store, ad accounts). Flip to False only once you have
    # wired in credentials and accept unattended changes.
    dry_run: bool = os.getenv("JARVIS_DRY_RUN", "1") != "0"

    # Where the cache-purge task is allowed to operate. Restricted on purpose.
    cache_dirs: List[Path] = field(default_factory=lambda: [
        Path.home() / ".cache" / "jarvis_v6",
        Path(__file__).resolve().parent / ".jarvis_cache",
    ])

    # Mailbox-hygiene credentials (IMAP). Empty host => task is skipped.
    imap_host: str = os.getenv("JARVIS_IMAP_HOST", "")
    imap_user: str = os.getenv("JARVIS_IMAP_USER", "")
    imap_password: str = os.getenv("JARVIS_IMAP_PASSWORD", "")
    imap_port: int = int(os.getenv("JARVIS_IMAP_PORT", "993"))
    imap_inbox: str = os.getenv("JARVIS_IMAP_INBOX", "INBOX")
    imap_trash: str = os.getenv("JARVIS_IMAP_TRASH", "Trash")

    # Supplier crawl: comma-separated source URLs.
    supplier_sources: List[str] = field(default_factory=lambda: [
        s.strip() for s in os.getenv("JARVIS_SUPPLIER_SOURCES", "").split(",") if s.strip()
    ])

    # Market trends: local JSON feed (until a live trends/ads API is wired in).
    trends_feed: str = os.getenv("JARVIS_TRENDS_FEED", "")
    winners_top_n: int = int(os.getenv("JARVIS_WINNERS_TOP_N", "2"))

    # Fashion Aura store: local catalogue JSON + Shopify key (empty => skipped).
    store_products_file: str = os.getenv("JARVIS_STORE_PRODUCTS", "")
    store_api_key: str = os.getenv("JARVIS_STORE_API_KEY", "")

    # Dashboard output directory (leads, suppliers, winners, store drafts).
    dashboard_dir: Path = field(default_factory=lambda: (
        Path(__file__).resolve().parent / ".jarvis_dashboard"
    ))

    # Where qualified leads are written for the dashboard to surface.
    leads_file: Path = field(default_factory=lambda: (
        Path(__file__).resolve().parent / ".jarvis_dashboard" / "leads.json"
    ))

    def next_wake(self, now: Optional[datetime] = None) -> datetime:
        """Return the next datetime at which the wake clock fires."""
        now = now or datetime.now()
        target = datetime.combine(now.date(), dtime(self.wake_hour, self.wake_minute))
        if target <= now:
            target += timedelta(days=1)
        return target


# ---------------------------------------------------------------------------
# Task result + base class.
# ---------------------------------------------------------------------------
@dataclass
class TaskResult:
    name: str
    ok: bool
    summary: str                       # human-readable, used in the briefing
    metrics: Dict[str, int] = field(default_factory=dict)
    dry_run: bool = False
    duration_s: float = 0.0
    error: Optional[str] = None


class NightShiftTask:
    """Base class for an overnight unit of work.

    Subclasses implement `run()` and return a TaskResult. They must honour
    `self.dry_run` and `self.cancel` (a threading.Event) for cooperative
    shutdown. Keep tasks idempotent — they may be retried.
    """

    #: Stable identifier, also shown in the GUI task list.
    name: str = "task"

    def __init__(self, config: NightShiftConfig, cancel: threading.Event):
        self.config = config
        self.cancel = cancel

    @property
    def dry_run(self) -> bool:
        return self.config.dry_run

    def run(self) -> TaskResult:  # pragma: no cover - overridden
        raise NotImplementedError

    # Convenience for cooperative, interruptible "work".
    def _sleep(self, seconds: float) -> None:
        # Wait on the cancel event instead of a hard sleep so Ctrl-C / shutdown
        # is honoured immediately.
        self.cancel.wait(timeout=seconds)


# ---------------------------------------------------------------------------
# Concrete tasks. Each is a real, runnable skeleton with the integration point
# clearly marked. They never fabricate results.
# ---------------------------------------------------------------------------
class CachePurgeTask(NightShiftTask):
    """Purge JARVIS's own cache directories. Actually runs (on your own
    dirs), but honours dry_run so the first night is observe-only."""

    name = "cache_purge"

    def run(self) -> TaskResult:
        freed = 0
        removed = 0
        for d in self.config.cache_dirs:
            if self.cancel.is_set():
                break
            if not d.exists():
                continue
            for item in d.rglob("*"):
                if self.cancel.is_set():
                    break
                try:
                    size = item.stat().st_size if item.is_file() else 0
                except OSError:
                    size = 0
                if self.dry_run:
                    freed += size
                    removed += 1
                    continue
                try:
                    if item.is_file() or item.is_symlink():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                    freed += size
                    removed += 1
                except OSError as exc:
                    LOG.warning("cache purge skipped %s: %s", item, exc)
        mb = freed // (1024 * 1024)
        verb = "would free" if self.dry_run else "freed"
        return TaskResult(
            name=self.name,
            ok=True,
            summary=f"Cache-Bereinigung: {verb} ~{mb} MB ({removed} Objekte).",
            metrics={"freed_mb": mb, "objects": removed},
            dry_run=self.dry_run,
        )


class SupplierCrawlTask(NightShiftTask):
    """Crawl/collect new suppliers. INTEGRATION POINT: plug your sources in
    below. Ships as a no-network stub so the baseline boots offline."""

    name = "supplier_crawl"

    def run(self) -> TaskResult:
        cfg = self.config
        if not cfg.supplier_sources:
            return TaskResult(
                name=self.name, ok=True,
                summary="Lieferanten-Crawl: keine Quellen konfiguriert (übersprungen).",
                metrics={"suppliers_found": 0}, dry_run=self.dry_run,
            )
        # --- INTEGRATION POINT (implemented) ------------------------------
        from integrations.suppliers import crawl  # lazy: optional 'crawl' extra
        report = crawl(
            cfg.supplier_sources,
            seen_file=cfg.dashboard_dir / "suppliers_seen.json",
            out_file=cfg.dashboard_dir / "suppliers.json",
            cancel=self.cancel,
        )
        # ------------------------------------------------------------------
        if report.error:
            return TaskResult(
                name=self.name, ok=False,
                summary=f"Lieferanten-Crawl fehlgeschlagen: {report.error}",
                metrics=report.as_metrics(), dry_run=self.dry_run, error=report.error,
            )
        return TaskResult(
            name=self.name, ok=True,
            summary=(f"Lieferanten-Crawl: {report.new} neue Lieferanten gefunden "
                     f"({report.found} geprüft, {report.sources_ok} Quellen)."),
            metrics=report.as_metrics(), dry_run=self.dry_run,
        )


class MarketTrendTask(NightShiftTask):
    """Compile marketing trend logs and identify candidate winning products.
    INTEGRATION POINT: connect your analytics/ads data source."""

    name = "market_trends"

    def run(self) -> TaskResult:
        cfg = self.config
        if not cfg.trends_feed:
            return TaskResult(
                name=self.name, ok=True,
                summary="Markttrends: kein Daten-Feed konfiguriert (übersprungen).",
                metrics={"winning_products": 0, "trends_logged": 0}, dry_run=self.dry_run,
            )
        # --- INTEGRATION POINT (implemented) ------------------------------
        from integrations.trends import run_analysis
        report = run_analysis(
            feed_file=Path(cfg.trends_feed),
            out_file=cfg.dashboard_dir / "winning_products.json",
            top_n=cfg.winners_top_n,
        )
        # ------------------------------------------------------------------
        return TaskResult(
            name=self.name, ok=True,
            summary=(f"Markttrends analysiert: {report.analysed} Datensätze, "
                     f"{len(report.winners)} Winning Products identifiziert."),
            metrics=report.as_metrics(), dry_run=self.dry_run,
        )


class MailboxHygieneTask(NightShiftTask):
    """Mailbox hygiene: classify spam, surface qualified business enquiries.
    SAFE BY DEFAULT — in dry_run it counts but never deletes."""

    name = "mailbox_hygiene"

    def run(self) -> TaskResult:
        cfg = self.config
        if not cfg.imap_host:
            return TaskResult(
                name=self.name, ok=True,
                summary="Postfach-Hygiene: kein IMAP-Konto konfiguriert (übersprungen).",
                metrics={"spam": 0, "leads": 0}, dry_run=self.dry_run,
            )
        # --- INTEGRATION POINT (implemented) ------------------------------
        from integrations.mailbox import run_hygiene  # lazy: optional 'mail' extra
        report = run_hygiene(
            host=cfg.imap_host, user=cfg.imap_user, password=cfg.imap_password,
            port=cfg.imap_port, inbox=cfg.imap_inbox, trash_folder=cfg.imap_trash,
            leads_file=cfg.leads_file, dry_run=self.dry_run, cancel=self.cancel,
        )
        # ------------------------------------------------------------------
        if report.error:
            return TaskResult(
                name=self.name, ok=False,
                summary=f"Postfach-Hygiene fehlgeschlagen: {report.error}",
                metrics=report.as_metrics(), dry_run=self.dry_run, error=report.error,
            )
        action = "markiert (Dry-Run, nichts verschoben)" if self.dry_run \
            else "in den Papierkorb verschoben"
        return TaskResult(
            name=self.name, ok=True,
            summary=(f"Postfach bereinigt: {report.scanned} Mails gescannt, "
                     f"{report.spam} Spam-Mails {action}, "
                     f"{report.leads} qualifizierte Geschäftsanfragen im Dashboard."),
            metrics=report.as_metrics(), dry_run=self.dry_run,
        )


class StoreOptimizerTask(NightShiftTask):
    """Optimise the Fashion Aura store backend: SEO copy, campaign drafts.
    SAFE BY DEFAULT — in dry_run it prepares drafts but publishes nothing."""

    name = "store_optimizer"

    def run(self) -> TaskResult:
        cfg = self.config
        if not cfg.store_products_file:
            return TaskResult(
                name=self.name, ok=True,
                summary="Fashion Aura: kein Produktkatalog konfiguriert (übersprungen).",
                metrics={"products_seo": 0, "campaigns": 0}, dry_run=self.dry_run,
            )
        # --- INTEGRATION POINT (implemented) ------------------------------
        from integrations.store import load_products, optimize_store
        from integrations.trends import load_feed, pick_winning_products
        products = load_products(Path(cfg.store_products_file))
        winners = (pick_winning_products(load_feed(Path(cfg.trends_feed)), top_n=cfg.winners_top_n)
                   if cfg.trends_feed else [])
        report = optimize_store(
            products, winners=winners,
            out_file=cfg.dashboard_dir / "store_drafts.json",
            dry_run=self.dry_run, shopify_api_key=cfg.store_api_key,
        )
        # ------------------------------------------------------------------
        if report.error and not self.dry_run:
            return TaskResult(
                name=self.name, ok=False,
                summary=f"Fashion Aura: {report.error}",
                metrics=report.as_metrics(), dry_run=self.dry_run, error=report.error,
            )
        if self.dry_run:
            state = "als Entwurf vorbereitet (Dry-Run, nicht veröffentlicht)"
        else:
            state = f"hochgeladen ({report.published} veröffentlicht)"
        return TaskResult(
            name=self.name, ok=True,
            summary=(f"Fashion Aura: {report.products_seo} Produkttexte SEO-optimiert {state}, "
                     f"{report.campaigns} Werbekampagnen erstellt."),
            metrics=report.as_metrics(), dry_run=self.dry_run,
        )


DEFAULT_TASKS = [
    CachePurgeTask,
    SupplierCrawlTask,
    MarketTrendTask,
    MailboxHygieneTask,
    StoreOptimizerTask,
]


# ---------------------------------------------------------------------------
# Briefing builder — fills the German template from REAL results.
# ---------------------------------------------------------------------------
class Briefing:
    @staticmethod
    def build(results: List[TaskResult]) -> str:
        by = {r.name: r for r in results}
        lines = ["Guten Tag, Jonas. Das Nachtschicht-Protokoll wurde abgeschlossen."]

        mail = by.get("mailbox_hygiene")
        if mail:
            lines.append(mail.summary)

        store = by.get("store_optimizer")
        trends = by.get("market_trends")
        if trends:
            lines.append(trends.summary)
        if store:
            lines.append(store.summary)

        cache = by.get("cache_purge")
        if cache:
            lines.append(cache.summary)

        failed = [r for r in results if not r.ok]
        if failed:
            lines.append("Achtung: " + "; ".join(f"{r.name} fehlgeschlagen ({r.error})" for r in failed) + ".")

        any_dry = any(r.dry_run for r in results)
        status = "stabil im Sicherheitsmodus (Dry-Run)" if any_dry else "stabil bei 100%"
        lines.append(f"Systemstatus ist {status}. Ich bin bereit für deine nächsten Anweisungen.")
        return " ".join(lines)


# ---------------------------------------------------------------------------
# Text-to-speech — optional, degrades to printing.
# ---------------------------------------------------------------------------
def speak(text: str) -> None:
    try:
        import pyttsx3  # type: ignore
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception as exc:  # noqa: BLE001 - TTS is best-effort
        LOG.info("TTS unavailable (%s); briefing follows:\n%s", exc, text)


# ---------------------------------------------------------------------------
# Supervisor — owns the worker pool and the night-shift run.
# ---------------------------------------------------------------------------
StateCallback = Callable[[SystemState, dict], None]


class NightShiftSupervisor:
    def __init__(
        self,
        config: Optional[NightShiftConfig] = None,
        task_classes: Optional[List[type]] = None,
        on_state: Optional[StateCallback] = None,
    ):
        self.config = config or NightShiftConfig()
        self.task_classes = task_classes or DEFAULT_TASKS
        self.on_state = on_state or (lambda state, info: None)
        self.cancel = threading.Event()
        self.results: List[TaskResult] = []
        self._thread: Optional[threading.Thread] = None

    # -- state broadcast -----------------------------------------------------
    def _emit(self, state: SystemState, **info) -> None:
        LOG.info("state -> %s %s", state.value, info or "")
        try:
            self.on_state(state, info)
        except Exception:  # noqa: BLE001 - never let a GUI callback kill the run
            LOG.exception("on_state callback failed")

    # -- task execution ------------------------------------------------------
    def run_tasks(self) -> List[TaskResult]:
        """Run all tasks concurrently in a bounded pool. Returns real results."""
        self._emit(SystemState.NIGHT_SHIFT, tasks=[t.name for t in self.task_classes])
        results: List[TaskResult] = []
        tasks = [cls(self.config, self.cancel) for cls in self.task_classes]
        with ThreadPoolExecutor(max_workers=self.config.max_workers,
                                thread_name_prefix="jarvis") as pool:
            futures = {pool.submit(self._guarded, t): t for t in tasks}
            for fut in as_completed(futures):
                res = fut.result()
                results.append(res)
                self._emit(SystemState.NIGHT_SHIFT, completed=res.name, ok=res.ok)
        self.results = results
        return results

    def _guarded(self, task: NightShiftTask) -> TaskResult:
        """Run one task, turning any exception into a failed TaskResult so one
        crashing task never brings down the night shift."""
        start = time.monotonic()
        try:
            res = task.run()
        except Exception as exc:  # noqa: BLE001
            LOG.exception("task %s crashed", task.name)
            res = TaskResult(task.name, ok=False, summary=f"{task.name} fehlgeschlagen",
                             error=str(exc), dry_run=self.config.dry_run)
        res.duration_s = round(time.monotonic() - start, 2)
        return res

    # -- the full overnight cycle -------------------------------------------
    def run_cycle(self, wake_callback: Optional[Callable[[str], None]] = None) -> List[TaskResult]:
        """Run tasks, then sleep until the wake clock, then deliver the briefing.

        wake_callback receives the briefing text at 16:00 (the GUI uses it to
        pop the reactor to full brightness + sound cue). If omitted, the
        briefing is spoken/printed here.
        """
        self._emit(SystemState.BOOTING)
        results = self.run_tasks()

        target = self.config.next_wake()
        self._emit(SystemState.SLEEPING, wake_at=target.isoformat())
        self._sleep_until(target)
        if self.cancel.is_set():
            self._emit(SystemState.STOPPED)
            return results

        # ---- Wake sequence -------------------------------------------------
        self._emit(SystemState.WAKING, wake_at=target.isoformat())
        briefing = Briefing.build(results)
        self._emit(SystemState.BRIEFING, text=briefing)
        if wake_callback is not None:
            wake_callback(briefing)
        else:
            speak(briefing)
        self._emit(SystemState.IDLE)
        return results

    def _sleep_until(self, target: datetime) -> None:
        """Sleep efficiently until `target`, waking periodically only to check
        the clock (and to notice a cancel request promptly)."""
        while not self.cancel.is_set():
            remaining = (target - datetime.now()).total_seconds()
            if remaining <= 0:
                return
            # Near-zero CPU: the thread is blocked in wait(), not spinning.
            self.cancel.wait(timeout=min(self.config.poll_seconds, max(0.1, remaining)))

    # -- lifecycle -----------------------------------------------------------
    def start_async(self, wake_callback: Optional[Callable[[str], None]] = None) -> threading.Thread:
        """Run the cycle on a background daemon thread (used by the GUI)."""
        self._thread = threading.Thread(
            target=self.run_cycle, kwargs={"wake_callback": wake_callback},
            name="jarvis-supervisor", daemon=True,
        )
        self._thread.start()
        return self._thread

    def stop(self) -> None:
        self.cancel.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)
        self._emit(SystemState.STOPPED)


# ---------------------------------------------------------------------------
# Entry points.
# ---------------------------------------------------------------------------
def _configure_logging() -> None:
    logging.basicConfig(
        level=os.getenv("JARVIS_LOG_LEVEL", "INFO"),
        format="%(asctime)s  %(levelname)-7s  %(name)s: %(message)s",
    )


def run_headless() -> None:
    """Run the supervisor without the GUI (e.g. on a server / cron)."""
    _configure_logging()
    LOG.info("JARVIS V6 — Night-Shift Protocol (headless)")
    NightShiftSupervisor().run_cycle()


def main() -> None:
    """Default entry point: launch the GUI supervisor if a display is
    available, otherwise fall back to headless."""
    _configure_logging()
    try:
        from dashboard_gui import launch  # local import; GUI is optional
    except Exception as exc:  # noqa: BLE001
        LOG.warning("GUI unavailable (%s) — running headless.", exc)
        run_headless()
        return
    launch()


if __name__ == "__main__":
    main()
