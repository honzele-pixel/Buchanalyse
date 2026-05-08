"""
Kleiner Adapter fuer lokale LLM-Aufrufe.

Aktuell wird nur Ollama unterstuetzt.
Die Implementierung nutzt bewusst nur die Python-Standardbibliothek,
damit keine zusaetzlichen Abhaengigkeiten noetig sind.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from config import settings


class LocalLLMError(RuntimeError):
    """Fehler bei lokalen LLM-Aufrufen."""


def ollama_verfuegbar() -> bool:
    """Prueft, ob ein Ollama-Server erreichbar ist."""
    req = urllib.request.Request(
        f"{settings.OLLAMA_BASE_URL}/api/tags",
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError):
        return False


def ollama_generieren(
    *,
    prompt: str,
    system_prompt: str,
    model: str | None = None,
    temperature: float = 0.2,
) -> str:
    """Fuehrt einen nicht-streamenden Ollama-Generate-Aufruf aus."""
    payload = {
        "model": model or settings.LEKTOR_MODEL,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_ctx": settings.OLLAMA_NUM_CTX,
        },
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{settings.OLLAMA_BASE_URL}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=settings.OLLAMA_TIMEOUT_SECONDS) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise LocalLLMError(f"Ollama HTTP-Fehler {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise LocalLLMError(f"Ollama nicht erreichbar: {exc.reason}") from exc
    except TimeoutError as exc:
        raise LocalLLMError("Ollama-Zeitlimit erreicht") from exc

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError as exc:
        raise LocalLLMError(f"Ollama lieferte kein gueltiges JSON: {body[:500]}") from exc

    antwort = parsed.get("response", "").strip()
    if not antwort:
        raise LocalLLMError("Ollama lieferte keine Antwort")

    return antwort
