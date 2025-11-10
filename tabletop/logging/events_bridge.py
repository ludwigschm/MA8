from __future__ import annotations

"""Compatibility helpers for the now-disabled cloud logging pipeline."""

from typing import Dict


def init_client(
    base_url: str,
    api_key: str,
    timeout_s: float = 2.0,
    max_retries: int = 3,
) -> None:
    """Retained for API compatibility – no longer performs any work."""

    return None


def push_async(event: Dict) -> None:
    """Drop *event* silently now that cloud logging has been removed."""

    return None
