"""No-op stubs for the legacy round logging helpers."""

from typing import Any, Dict, List, Optional

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


def init_round_log(app: Any) -> None:
    """Preserved for compatibility – the game no longer writes CSV files."""

    setattr(app, "round_log_path", None)
    setattr(app, "round_log_buffer", [])
    setattr(app, "round_log_fieldnames", list(ROUND_LOG_HEADER))
    setattr(app, "round_log_last_flush", 0.0)


def round_log_action_label(app: Any, action: str, payload: Dict[str, Any]) -> str:
    """Return a human readable label for UI purposes."""

    return str(action)


def write_round_log(
    app: Any,
    actor: str,
    action: str,
    payload: Dict[str, Any],
    player: int,
    *,
    action_label: Optional[str] = None,
) -> None:
    """Logging disabled – keep the signature but drop all behaviour."""

    return None


def flush_round_log(app: Any, *, force: bool = False, wait: bool = True) -> None:
    """Compatibility shim – nothing to flush anymore."""

    return None


def close_round_log(app: Any) -> None:
    """Compatibility shim – nothing to close anymore."""

    setattr(app, "round_log_path", None)
