"""Jarvis — persönlicher Sprach-Assistent (Iron-Man-Stil) für Windows.

Der Kern ist bewusst hardware-unabhängig: Sprache-rein (STT), Sprache-raus (TTS)
und das Denken (LLM) sind über schmale Schnittstellen austauschbar. So läuft
derselbe Assistent per Stimme (Windows) ODER im reinen Text-Modus (überall,
ohne Mikrofon) — das ist zugleich der Text-Fallback und die Testbarkeit.
"""

__version__ = "0.6.0"
