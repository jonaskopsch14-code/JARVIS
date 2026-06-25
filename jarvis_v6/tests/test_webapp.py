"""Tests for the mobile web interface: pure .env editing + a live HTTP smoke
test against a real (ephemeral-port) server. Standard library only."""

import json
import sys
import tempfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from webapp import EDITABLE_KEYS, create_server, masked_config, update_env_file  # noqa: E402


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.status, json.loads(r.read().decode("utf-8"))


def _post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.status, json.loads(r.read().decode("utf-8"))


def test_update_env_file_inserts_and_replaces():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / ".env"
        p.write_text("# header\nJARVIS_DRY_RUN=1\nJARVIS_IMAP_HOST=old\n", encoding="utf-8")
        update_env_file(p, {"JARVIS_IMAP_HOST": "imap.new.de", "JARVIS_WAKE_HOUR": "16",
                            "NOT_ALLOWED": "x"})
        text = p.read_text(encoding="utf-8")
        assert "JARVIS_IMAP_HOST=imap.new.de" in text
        assert "JARVIS_WAKE_HOUR=16" in text          # appended
        assert "JARVIS_DRY_RUN=1" in text             # preserved
        assert "# header" in text                     # comment preserved
        assert "NOT_ALLOWED" not in text              # non-editable rejected


def test_masked_config_hides_secrets(monkeypatch=None):
    import os
    os.environ["JARVIS_IMAP_PASSWORD"] = "supersecret"
    os.environ["JARVIS_IMAP_HOST"] = "imap.example.com"
    try:
        cfg = masked_config()
        assert cfg["JARVIS_IMAP_PASSWORD"] == "***gesetzt***"
        assert cfg["JARVIS_IMAP_HOST"] == "imap.example.com"
        assert set(cfg.keys()) == set(EDITABLE_KEYS)
    finally:
        del os.environ["JARVIS_IMAP_PASSWORD"]


def test_http_server_status_dashboard_preflight_and_index():
    httpd, app = create_server(host="127.0.0.1", port=0)  # port 0 = ephemeral
    host, port = httpd.server_address
    import threading
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    base = f"http://{host}:{port}"
    try:
        # Index page renders.
        with urllib.request.urlopen(base + "/", timeout=5) as r:
            assert r.status == 200 and b"JARVIS" in r.read()
        # Status JSON.
        code, status = _get(base + "/api/status")
        assert code == 200 and "state" in status and "counts" in status
        # Dashboard JSON.
        code, dash = _get(base + "/api/dashboard")
        assert code == 200 and "counts" in dash
        # Preflight JSON.
        code, pf = _get(base + "/api/preflight")
        assert code == 200 and isinstance(pf["rows"], list) and pf["rows"]
        # Start the (dry-run) protocol via the API.
        code, started = _post(base + "/api/start", {})
        assert code == 200 and started["started"] is True
    finally:
        httpd.shutdown()


if __name__ == "__main__":
    funcs = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in funcs:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {fn.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(funcs) - failed}/{len(funcs)} passed")
    sys.exit(1 if failed else 0)
