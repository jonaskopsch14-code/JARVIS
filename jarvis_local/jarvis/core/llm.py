"""LLM-Backends.

Der Agent-Loop spricht nur gegen das :class:`LLMBackend`-Protokoll. In Produktion
ist das :class:`OllamaBackend` (Qwen3-8B, natives Tool-Calling). Für Tests und den
Text-Modus ohne GPU gibt es :class:`ScriptedBackend`.

Nachrichten- und Tool-Call-Format sind bewusst Ollama-/OpenAI-kompatibel::

    {"role": "assistant", "content": "...", "tool_calls": [
        {"function": {"name": "memory_write", "arguments": {"text": "..."}}}
    ]}
"""
from __future__ import annotations

from typing import Any, Callable, Protocol, runtime_checkable


Message = dict[str, Any]


@runtime_checkable
class LLMBackend(Protocol):
    def chat(self, messages: list[Message], tools: list[dict[str, Any]] | None = None) -> Message:
        """Nimmt den Verlauf + Tool-Schemas, liefert eine Assistant-Nachricht."""
        ...


class OllamaBackend:
    """Lokales LLM über Ollama (natives Function-Calling).

    Der ``ollama``-Import erfolgt erst beim Aufruf, damit das Paket importierbar
    bleibt, wenn Ollama (noch) nicht installiert ist.
    """

    def __init__(
        self,
        model: str = "qwen3:8b",
        host: str = "http://localhost:11434",
        temperature: float = 0.0,
        num_ctx: int = 16384,
        think: bool = False,
    ) -> None:
        self.model = model
        self.host = host
        self.temperature = temperature
        self.num_ctx = num_ctx
        self.think = think  # Qwen-"Thinking" für Tool-Use meist aus (Leitfaden Caveat)

    def chat(self, messages: list[Message], tools: list[dict[str, Any]] | None = None) -> Message:
        try:
            import ollama  # type: ignore
        except ImportError as exc:  # pragma: no cover - nur ohne Ollama
            raise RuntimeError(
                "Das Paket 'ollama' ist nicht installiert. `pip install ollama` und "
                "sicherstellen, dass der Ollama-Dienst auf dem Windows-PC läuft."
            ) from exc

        client = ollama.Client(host=self.host)
        resp = client.chat(
            model=self.model,
            messages=messages,
            tools=tools or None,
            think=self.think,
            options={"temperature": self.temperature, "num_ctx": self.num_ctx},
        )
        msg = resp["message"]
        # In ein reines dict normalisieren (ollama liefert ein Mapping-artiges Objekt).
        out: Message = {"role": "assistant", "content": msg.get("content", "") or ""}
        if msg.get("tool_calls"):
            out["tool_calls"] = [
                {"function": {"name": tc["function"]["name"], "arguments": dict(tc["function"]["arguments"])}}
                for tc in msg["tool_calls"]
            ]
        return out


class ScriptedBackend:
    """Deterministisches Backend für Tests und den Text-Demo-Modus.

    ``responder`` bekommt (messages, tools) und gibt eine Assistant-Nachricht
    zurück. Alternativ eine feste Liste von Antworten, die der Reihe nach
    ausgegeben werden.
    """

    def __init__(
        self,
        responder: Callable[[list[Message], list[dict[str, Any]] | None], Message] | None = None,
        scripted: list[Message] | None = None,
    ) -> None:
        if responder is None and scripted is None:
            raise ValueError("Entweder 'responder' oder 'scripted' angeben.")
        self._responder = responder
        self._scripted = list(scripted or [])
        self._i = 0
        self.calls: list[list[Message]] = []

    def chat(self, messages: list[Message], tools: list[dict[str, Any]] | None = None) -> Message:
        self.calls.append([dict(m) for m in messages])
        if self._responder is not None:
            return self._responder(messages, tools)
        if self._i < len(self._scripted):
            msg = self._scripted[self._i]
            self._i += 1
            return msg
        return {"role": "assistant", "content": ""}


def tool_call(name: str, **arguments: Any) -> Message:
    """Hilfsfunktion: eine Assistant-Nachricht, die genau ein Tool aufruft."""
    return {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": name, "arguments": arguments}}]}


def final(content: str) -> Message:
    return {"role": "assistant", "content": content}
