"""Adapter for game engine event logging."""

from __future__ import annotations

from typing import Any, Dict, Optional

from tabletop.engine import Phase as EnginePhase

__all__ = ["Events", "EnginePhase"]


class Events:
    """No-op replacement for the previous event logger integration."""

    def __init__(self, session_id: str, db_path: str, csv_path: Optional[str] = None):
        self._session_id = session_id

    def log(
        self,
        round_idx: int,
        phase: EnginePhase,
        actor: str,
        action: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Return a lightweight description without persisting anything."""

        return {
            "session": self._session_id,
            "round": round_idx,
            "phase": getattr(phase, "name", str(phase)),
            "actor": actor,
            "action": action,
            "payload": dict(payload or {}),
        }

    def close(self) -> None:  # pragma: no cover - kept for API compatibility
        """Preserved for compatibility; there is nothing left to close."""

        return None
