"""LLM-Anbindung: lokales Denken über Ollama, mit Tool-Calling.

`LLM` ist die schmale Schnittstelle. `OllamaClient` spricht den lokalen
Ollama-Server; `ScriptedLLM` ist ein Test-Double (skriptbare Antworten), damit
der Assistent ohne Modell/Netz getestet werden kann.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Protocol


class LLM(Protocol):
    def chat(self, messages: List[dict], tools: Optional[List[dict]] = None) -> dict:
        """Gibt eine Assistant-Message zurück: {role, content, tool_calls?}."""
        ...


class OllamaClient:
    """Client für den lokalen Ollama-Server (/api/chat)."""

    def __init__(self, model: str, url: str = "http://127.0.0.1:11434",
                 temperature: float = 0.6):
        self.model = model
        self.url = url.rstrip("/")
        self.temperature = temperature

    def chat(self, messages: List[dict], tools: Optional[List[dict]] = None) -> dict:
        import httpx  # lazy: nur zur Laufzeit auf dem PC nötig
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        if tools:
            payload["tools"] = tools
        try:
            r = httpx.post(f"{self.url}/api/chat", json=payload, timeout=120.0)
            r.raise_for_status()
            data = r.json()
        except Exception as exc:  # noqa: BLE001
            return {"role": "assistant",
                    "content": f"(Ollama nicht erreichbar: {exc})", "tool_calls": []}
        msg = data.get("message", {}) or {}
        return {
            "role": "assistant",
            "content": msg.get("content", "") or "",
            "tool_calls": msg.get("tool_calls", []) or [],
        }


class ScriptedLLM:
    """Test-Double: gibt vorgegebene Antworten/Tool-Aufrufe der Reihe nach zurück.

    `script` ist eine Liste von dicts wie:
        {"content": "Text"}                         → normale Antwort
        {"tool": "weather", "args": {"city": "x"}}  → ein Tool-Aufruf
    """

    def __init__(self, script: List[dict]):
        self.script = list(script)
        self.calls: List[dict] = []

    def chat(self, messages: List[dict], tools: Optional[List[dict]] = None) -> dict:
        self.calls.append({"messages": list(messages), "tools": tools})
        step = self.script.pop(0) if self.script else {"content": "Fertig, Sir."}
        if "tool" in step:
            return {"role": "assistant", "content": "", "tool_calls": [
                {"function": {"name": step["tool"], "arguments": step.get("args", {})}}
            ]}
        return {"role": "assistant", "content": step.get("content", ""), "tool_calls": []}
