"""Stub implementation of the legacy Pupil bridge.

The original project integrated tightly with Pupil Labs hardware, managing
recordings and forwarding events.  For the "plain game" variant we keep a very
small compatibility layer so that the rest of the codebase can run unchanged
while all eye-tracking behaviour is effectively disabled.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Set, Tuple


@dataclass
class NeonDeviceConfig:
    """Minimal dataclass kept for backwards compatibility with call sites."""

    player: str
    device_id: str = ""
    ip: str = ""
    port: Optional[int] = None

    @property
    def is_configured(self) -> bool:  # pragma: no cover - compatibility shim
        return False

    @property
    def address(self) -> Optional[str]:  # pragma: no cover - compatibility shim
        return None

    def summary(self) -> str:  # pragma: no cover - compatibility shim
        return f"{self.player}(deaktiviert)"


class PupilBridge:
    """No-op drop-in replacement for the hardware bridge."""

    def __init__(self) -> None:
        self._connected: Set[str] = set()
        self._recording: Set[str] = set()

    # ------------------------------------------------------------------
    # Lifecycle helpers
    def connect(self) -> None:
        """Pretend to connect to devices (no-op)."""

    def close(self) -> None:
        """Release any resources (no-op)."""

    # ------------------------------------------------------------------
    # Device discovery helpers
    def connected_players(self) -> Set[str]:
        return set(self._connected)

    def is_connected(self, player: str) -> bool:
        return player in self._connected

    # ------------------------------------------------------------------
    # Recording helpers
    def ensure_recordings(
        self,
        *,
        session: Optional[int] = None,
        block: Optional[int] = None,
        players: Optional[Iterable[str]] = None,
        force: bool = False,
    ) -> None:
        return None

    def start_recording(self, session: int, block: int, player: str) -> None:
        self._recording.add(player)

    def stop_recording(self, player: str) -> None:
        self._recording.discard(player)

    # ------------------------------------------------------------------
    # Event helpers
    def send_event(
        self,
        name: str,
        player: str,
        payload: Optional[Dict[str, object]] = None,
        *,
        priority: str = "normal",
    ) -> None:
        return None

    def send_host_mirror(
        self,
        player: str,
        event_id: str,
        t_local_ns: int,
        *,
        extra: Optional[Dict[str, object]] = None,
    ) -> None:
        return None

    def event_queue_load(self) -> Tuple[int, int]:
        return (0, 0)

    def estimate_time_offset(self, player: str) -> Optional[float]:
        return None

    # ------------------------------------------------------------------
    # Compatibility helpers expected by tests/other modules
    def ensure_capabilities(self) -> None:  # pragma: no cover - compatibility shim
        return None

    def ensure_time_sync(self) -> None:  # pragma: no cover - compatibility shim
        return None

    def register_player(self, player: str) -> None:  # pragma: no cover
        self._connected.add(player)

    def unregister_player(self, player: str) -> None:  # pragma: no cover
        self._connected.discard(player)
