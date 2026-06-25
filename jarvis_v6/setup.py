"""
JARVIS V6 — Night-Shift Overclock Protocol
==========================================

Environment setup / packaging for the JARVIS V6 background-operations suite
(Architectural Layer 7: Execution Logistics & Background Operations).

This installs the package and declares its dependencies. The core scheduler,
threading foundation and Arc-Reactor GUI run on the Python standard library
alone (so the baseline always boots); the heavier capabilities — text-to-speech,
mail access, store/ad-platform integrations — are optional extras you enable
when you wire in real credentials.

Usage
-----
    # Editable install with the baseline only:
    pip install -e .

    # With a capability bundle, e.g. voice + mail:
    pip install -e ".[voice,mail]"

    # Everything:
    pip install -e ".[all]"

After install, the console entry points are available:
    jarvis-v6            # launch the supervisor (GUI + scheduler)
    jarvis-v6-headless   # launch the scheduler without the GUI
"""

from pathlib import Path

from setuptools import find_packages, setup

HERE = Path(__file__).parent
LONG_DESCRIPTION = (HERE / "README.md").read_text(encoding="utf-8") \
    if (HERE / "README.md").exists() else __doc__

# ---------------------------------------------------------------------------
# Optional capability extras.
#
# These are kept OUT of the baseline on purpose: the night-shift supervisor and
# the Arc-Reactor GUI must boot with nothing but the standard library, so a
# missing third-party package can never take the whole system down. Each task
# module checks for its own dependency at runtime and degrades to a safe
# "skipped / dry-run" result if the extra is not installed.
# ---------------------------------------------------------------------------
EXTRAS = {
    # Text-to-speech for the 16:00 executive briefing.
    "voice": ["pyttsx3>=2.90"],
    # IMAP/SMTP mail hygiene (the stdlib already ships imaplib/smtplib, but a
    # higher-level client makes the integration far less error-prone).
    "mail": ["imap-tools>=1.0"],
    # Supplier crawling / market-trend collection.
    "crawl": ["httpx>=0.27", "beautifulsoup4>=4.12"],
    # Fashion Aura store backend (Shopify Admin API is the common case; swap the
    # client in store_optimizer for WooCommerce/etc.).
    "store": ["ShopifyAPI>=12.0"],
    # A richer GUI toolkit if you want to move off Tkinter later.
    "qt": ["PySide6>=6.6"],
}
EXTRAS["all"] = sorted({pkg for group in EXTRAS.values() for pkg in group})

setup(
    name="jarvis-v6",
    version="6.0.0",
    description=(
        "JARVIS V6 — Night-Shift Overclock Protocol: an autonomous overnight "
        "background-operations supervisor with an Arc-Reactor dashboard."
    ),
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author="Jonas Kopsch",
    license="MIT",
    python_requires=">=3.9",
    packages=find_packages(include=["jarvis_v6", "jarvis_v6.*"]),
    py_modules=["main", "dashboard_gui", "webapp"],
    # Baseline: standard library only. Real intent — keep the foundation
    # bulletproof. Capability dependencies live in EXTRAS above.
    install_requires=[],
    extras_require=EXTRAS,
    entry_points={
        "console_scripts": [
            "jarvis-v6=main:main",
            "jarvis-v6-web=webapp:run_web",
            "jarvis-v6-headless=main:run_headless",
            "jarvis-v6-preflight=main:run_preflight",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Topic :: Office/Business",
        "Topic :: System :: Monitoring",
    ],
)
