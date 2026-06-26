#!/data/data/com.termux/files/usr/bin/env bash
#
# JARVIS V6 — One-tap starter for Termux (Android) and any Linux shell.
#
# Re-runnable and self-healing: installs deps if missing, clones or updates the
# repo, switches to the right folder, and starts the mobile web interface.
# Designed so the user only ever has to run ONE command.
#
# First-time use (paste into Termux):
#   pkg install -y git >/dev/null 2>&1; \
#   git clone https://github.com/jonaskopsch14-code/JARVIS.git 2>/dev/null; \
#   bash ~/JARVIS/jarvis_v6/start.sh
#
# After that, just:  bash ~/JARVIS/jarvis_v6/start.sh

set -u
BRANCH="claude/night-shift-overclock-protocol-57fpsq"
PORT="${JARVIS_WEB_PORT:-8765}"

say() { printf '\n\033[1;36m▶ %s\033[0m\n' "$*"; }
err() { printf '\n\033[1;31m✖ %s\033[0m\n' "$*"; }

# --- 1. Make sure python + git exist (Termux uses pkg) ----------------------
if ! command -v python >/dev/null 2>&1; then
  say "Installiere Python …"
  if command -v pkg >/dev/null 2>&1; then pkg install -y python git; fi
fi
if ! command -v python >/dev/null 2>&1; then
  err "Python fehlt. In Termux bitte ausführen:  pkg install -y python git"
  exit 1
fi

# --- 2. Locate the repo (this script lives in jarvis_v6/) -------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || { err "Verzeichnis nicht gefunden."; exit 1; }

# --- 3. Update to the latest code (best-effort; ignore if offline) ----------
if command -v git >/dev/null 2>&1 && [ -d ../.git ]; then
  say "Hole neueste Version …"
  git -C .. fetch --quiet origin "$BRANCH" 2>/dev/null && \
  git -C .. checkout --quiet "$BRANCH" 2>/dev/null && \
  git -C .. pull --quiet origin "$BRANCH" 2>/dev/null || \
  say "(Konnte nicht aktualisieren — fahre mit lokaler Version fort.)"
fi

# --- 4. Keep the phone awake so the night shift survives (Termux only) ------
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock 2>/dev/null

# --- 5. Sanity check: the app files must be here ----------------------------
if [ ! -f webapp.py ]; then
  err "webapp.py nicht gefunden in $SCRIPT_DIR — Download unvollständig?"
  exit 1
fi

# --- 6. Start ---------------------------------------------------------------
say "Starte JARVIS V6 …"
printf '\n\033[1;32m'
printf '════════════════════════════════════════════════\n'
printf '  Gleich öffnest du im BROWSER:\n'
printf '      http://127.0.0.1:%s\n' "$PORT"
printf '  (Dieses Termux-Fenster offen lassen!)\n'
printf '════════════════════════════════════════════════\n'
printf '\033[0m\n'
exec python webapp.py
