"""Helper utilities for initializing tracker recordings before UI launch."""

from __future__ import annotations

import logging
import time
from typing import Any, Iterable, Optional

log = logging.getLogger(__name__)


def ensure_trackers_recording_sequential(
    bridge: Any,
    *,
    session: Optional[int] = None,
    block: Optional[int] = None,
    players: Optional[Iterable[str]] = None,
    timeout: float = 5.0,
    poll_interval: float = 0.2,
) -> list[str]:
    """Start tracker recordings sequentially before the experiment loads."""

    if not bridge:
        return []

    started: list[str] = []
    session_value = session if session is not None else 0
    block_value = block if block is not None else 0

    candidates: list[str] = []
    if players is not None:
        candidates.extend([p for p in players if p])
    else:
        try:
            connected = getattr(bridge, "connected_players", None)
            if callable(connected):
                candidates.extend(sorted(connected()))
        except Exception:
            candidates = []

    if not candidates:
        return started

    for player in candidates:
        try:
            is_connected = getattr(bridge, "is_connected", None)
            if callable(is_connected) and not is_connected(player):
                continue
        except Exception:
            continue

        try:
            is_recording_fn = getattr(bridge, "is_recording", None)
            if callable(is_recording_fn) and is_recording_fn(player):
                started.append(player)
                continue
        except Exception:
            pass

        try:
            bridge.start_recording(session_value, block_value, player)
        except Exception:
            log.warning("Failed to start recording for %s", player)
            continue

        wait_fn = getattr(bridge, "wait_until_recording", None)
        if callable(wait_fn):
            try:
                ready = bool(wait_fn(player, timeout=timeout, poll_interval=poll_interval))
            except TypeError:
                ready = bool(wait_fn(player))
            except Exception:
                ready = False
        else:
            ready = True
            check_fn = getattr(bridge, "is_recording", None)
            if callable(check_fn):
                deadline = time.monotonic() + max(0.0, timeout)
                ready = False
                while time.monotonic() < deadline:
                    try:
                        if check_fn(player):
                            ready = True
                            break
                    except Exception:
                        break
                    time.sleep(max(0.0, poll_interval))
                else:
                    try:
                        ready = bool(check_fn(player))
                    except Exception:
                        ready = False

        if ready:
            started.append(player)
        else:
            log.warning("Recording for %s did not become active", player)

    return started


__all__ = ["ensure_trackers_recording_sequential"]
