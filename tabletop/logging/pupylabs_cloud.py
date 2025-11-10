from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Optional, Tuple

try:  # pragma: no cover - optional dependency
    import requests
except Exception:  # pragma: no cover - optional dependency
    requests = None  # type: ignore[assignment]


class PupylabsCloudLogger:
    """Minimal HTTP client for forwarding events to the Pupylabs cloud."""

    def __init__(
        self,
        session: requests.Session,
        base_url: str,
        api_key: str,
        timeout_s: float = 2.0,
        max_retries: int = 3,
    ) -> None:
        self._log = logging.getLogger(__name__)
        self.sess = session
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout_s
        self.max_retries = max_retries

    def send(self, event: Dict[str, Any]) -> None:
        """Send *event* to the ingestion endpoint with retry handling."""

        payload = dict(event) if event is not None else {}
        url = f"{self.base_url}/v1/events/ingest"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        delay = 0.1
        for attempt in range(self.max_retries + 1):
            try:
                response = self.sess.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                status = response.status_code
                if 200 <= status < 300:
                    return
                if 500 <= status < 600:
                    raise RuntimeError(f"Server {status}")
                self._log.warning(
                    "Pupylabs ingest non-2xx: %s %s",
                    status,
                    (response.text or "")[:200],
                )
                return
            except Exception as exc:  # pragma: no cover - defensive logging
                if attempt >= self.max_retries:
                    self._log.error(
                        "Pupylabs ingest failed after retries: %r",
                        exc,
                    )
                    return
                time.sleep(delay)
                delay = min(delay * 2, 1.0)

    def close(self) -> None:
        try:
            self.sess.close()
        except Exception:  # pragma: no cover - defensive fallback
            pass


def _resolve_credentials(
    base_url: Optional[str], api_key: Optional[str]
) -> Tuple[Optional[str], Optional[str]]:
    resolved_base = base_url or os.getenv("PUPILLABS_BASE_URL") or os.getenv(
        "PUPIL_LABS_BASE_URL"
    )
    resolved_key = api_key or os.getenv("PUPILLABS_API_KEY") or os.getenv(
        "PUPIL_LABS_API_KEY"
    )
    return resolved_base, resolved_key


def create_cloud_logger(
    *,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    timeout_s: float = 2.0,
    max_retries: int = 3,
) -> Tuple[Optional[PupylabsCloudLogger], Optional["requests.Session"]]:
    """Create a cloud logger and its underlying session when configured."""

    if requests is None:  # pragma: no cover - optional dependency
        return (None, None)

    resolved_base, resolved_key = _resolve_credentials(base_url, api_key)
    if not resolved_base or not resolved_key:
        return (None, None)

    session = requests.Session()
    logger = PupylabsCloudLogger(
        session,
        resolved_base,
        resolved_key,
        timeout_s=timeout_s,
        max_retries=max_retries,
    )
    return (logger, session)


__all__ = ["PupylabsCloudLogger", "create_cloud_logger"]
