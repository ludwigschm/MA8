"""CSV logging helpers for round actions."""

from __future__ import annotations

import csv
import logging
import threading
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional


log = logging.getLogger(__name__)


ROUND_LOG_HEADER: List[str] = [
    "Session",
    "Bedingung",
    "Block",
    "Runde im Block",
    "Spieler 1",
    "VP",
    "Karte1 VP1",
    "Karte2 VP1",
    "Karte1 VP2",
    "Karte2 VP2",
    "Aktion",
    "Zeit",
    "Gewinner",
    "Punktestand VP1",
    "Punktestand VP2",
]


class RoundCsvLogger:
    """Thread-safe CSV writer for action logs."""

    def __init__(self, path: Path, *, fieldnames: Iterable[str] = ROUND_LOG_HEADER) -> None:
        self._path = Path(path)
        self._fieldnames = list(fieldnames)
        self._write_header = not self._path.exists()
        self._lock = threading.Lock()

    @property
    def path(self) -> Path:
        return self._path

    def log_row(self, row: Mapping[str, Any]) -> None:
        """Append *row* to the CSV file, creating it if necessary."""

        normalized = {key: row.get(key, "") for key in self._fieldnames}
        self._path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._lock:
                with open(self._path, "a", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=self._fieldnames)
                    if self._write_header:
                        writer.writeheader()
                        self._write_header = False
                    writer.writerow(
                        {key: _stringify(value) for key, value in normalized.items()}
                    )
        except Exception:  # pragma: no cover - defensive fallback
            log.exception("Fehler beim Schreiben des Runden-Logs %s", self._path)


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def round_log_action_label(action: str, payload: Mapping[str, Any]) -> str:
    """Create a concise, human readable label for the UI log."""

    base = action.replace("_", " ")
    if not payload:
        return base
    details = ", ".join(f"{key}={value}" for key, value in sorted(payload.items()))
    return f"{base} ({details})"


__all__ = ["ROUND_LOG_HEADER", "RoundCsvLogger", "round_log_action_label"]
