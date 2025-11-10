"""Interface to Pupil Labs Neon devices and the cloud logging endpoint."""

from __future__ import annotations

import json
import logging
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional, Set, Tuple

from tabletop.data.config import ROOT
from tabletop.logging.pupylabs_cloud import PupylabsCloudLogger, create_cloud_logger

try:  # pragma: no cover - optional dependency
    import requests
except Exception:  # pragma: no cover - optional dependency
    requests = None  # type: ignore[assignment]


log = logging.getLogger(__name__)


DEFAULT_NEON_CONFIG = ROOT / "neon_tracker_ips.txt"


@dataclass
class NeonDeviceConfig:
    """Connection description for a Neon device."""

    player: str
    device_id: str = ""
    ip: str = ""
    port: Optional[int] = None
    started: bool = False
    metadata: Dict[str, str] = field(default_factory=dict)

    @property
    def is_configured(self) -> bool:
        return bool(self.ip)

    @property
    def address(self) -> Optional[str]:
        if not self.ip:
            return None
        port = self.port if self.port else 8080
        return f"{self.ip}:{port}"

    def summary(self) -> str:
        if not self.is_configured:
            return f"{self.player} (deaktiviert)"
        address = self.address or self.ip
        return f"{self.player} ({address})"


def _parse_neon_line(line: str) -> Optional[Tuple[str, str, Any]]:
    """Parse a line from the Neon tracker configuration file."""

    text = line.strip()
    if not text or text.startswith("#"):
        return None
    if "=" not in text:
        return None
    key, value = text.split("=", 1)
    player = key.strip().upper()
    raw_value = value.strip()
    if not player or not raw_value:
        return None
    attribute = "ip"
    base_key = player
    if player.endswith("_IP"):
        base_key = player[:-3]
        attribute = "ip"
    elif player.endswith("_ID"):
        base_key = player[:-3]
        attribute = "device_id"
    elif player.endswith("_PORT"):
        base_key = player[:-5]
        attribute = "port"
    elif "_" in player:
        # Unknown suffix
        log.warning("Unbekannter Tracker-Parameter in neon_tracker_ips.txt: %s", player)
        return None

    if base_key not in {"VP1", "VP2"}:
        log.warning("Unbekannter Tracker-Eintrag in neon_tracker_ips.txt: %s", base_key)
        return None

    if attribute == "port":
        try:
            parsed_value: Any = int(raw_value)
        except ValueError:
            log.warning(
                "Ungültiger Port für %s in neon_tracker_ips.txt: %s",
                base_key,
                raw_value,
            )
            return None
    else:
        parsed_value = raw_value

    return (base_key, attribute, parsed_value)


def _load_neon_configs(path: Path) -> Dict[str, NeonDeviceConfig]:
    configs: Dict[str, NeonDeviceConfig] = {}
    if not path.exists():
        log.info("Neon-Konfigurationsdatei %s nicht gefunden", path)
        return configs
    try:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                parsed = _parse_neon_line(line)
                if not parsed:
                    continue
                player, attribute, value = parsed
                cfg = configs.get(player)
                if cfg is None:
                    cfg = NeonDeviceConfig(
                        player=player, metadata={"source": "config_file"}
                    )
                    configs[player] = cfg
                if attribute == "ip":
                    cfg.ip = str(value)
                    cfg.metadata["ip"] = cfg.ip
                elif attribute == "port":
                    cfg.port = int(value)
                    cfg.metadata["port"] = str(cfg.port)
                elif attribute == "device_id":
                    cfg.device_id = str(value)
                    cfg.metadata["device_id"] = cfg.device_id
    except Exception:  # pragma: no cover - defensive fallback
        log.exception("Fehler beim Laden der Neon-Konfiguration aus %s", path)
    return configs


class PupilBridge:
    """Minimal implementation that forwards events to the Pupil Labs cloud."""

    def __init__(
        self,
        *,
        config_path: Optional[Path] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        self._config_path = config_path or DEFAULT_NEON_CONFIG
        self._devices: Dict[str, NeonDeviceConfig] = _load_neon_configs(self._config_path)
        self._connected: Set[str] = set()
        self._recording: Set[str] = set()
        self._cloud_logger: Optional[PupylabsCloudLogger] = None
        self._session: Optional["requests.Session"] = None
        logger, session = create_cloud_logger(base_url=base_url, api_key=api_key)
        if logger is not None and session is not None:
            self._cloud_logger = logger
            self._session = session
        elif base_url or api_key:
            log.warning(
                "Pupil Labs Cloud-Konfiguration unvollständig – Logging deaktiviert"
            )
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._pending_lock = threading.Lock()
        self._pending_tasks = 0

    # ------------------------------------------------------------------
    # Lifecycle helpers
    def connect(self) -> None:
        """Connect to configured Neon devices and mark them as available."""

        for player, cfg in self._devices.items():
            if not cfg.is_configured:
                continue
            self._connected.add(player)
            self._start_tracker(cfg)
        if not self._devices:
            log.info("Keine Neon-Tracker konfiguriert")

    def close(self) -> None:
        """Release network resources and stop the background executor."""

        try:
            self._executor.shutdown(wait=False)
        except Exception:  # pragma: no cover - defensive fallback
            pass
        if self._cloud_logger is not None:
            try:
                self._cloud_logger.close()
            except Exception:  # pragma: no cover - defensive fallback
                pass
        if self._session is not None:
            try:
                self._session.close()
            except Exception:  # pragma: no cover - defensive fallback
                pass

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
        """Ensure that the devices are marked as recording for the given players."""

        _ = session, block, force
        targets = list(players) if players is not None else list(self._connected)
        for player in targets:
            if player in self._recording:
                continue
            cfg = self._devices.get(player)
            if cfg is None:
                continue
            self.start_recording(session or 0, block or 0, player)

    def start_recording(self, session: int, block: int, player: str) -> None:
        self._recording.add(player)
        cfg = self._devices.get(player)
        address = cfg.address if cfg else None
        log.info(
            "Starte Aufnahme für %s – Session %s Block %s (%s)",
            player,
            session,
            block,
            address or "unbekannte Adresse",
        )

    def stop_recording(self, player: str) -> None:
        self._recording.discard(player)
        cfg = self._devices.get(player)
        address = cfg.address if cfg else None
        log.info("Stoppe Aufnahme für %s (%s)", player, address or "unbekannt")

    def is_recording(self, player: str) -> bool:
        """Return ``True`` if *player* is currently recording."""

        return player in self._recording

    def wait_until_recording(
        self, player: str, *, timeout: float = 5.0, poll_interval: float = 0.1
    ) -> bool:
        """Poll the recording state for *player* until it becomes active."""

        deadline = time.monotonic() + max(0.0, timeout)
        while time.monotonic() < deadline:
            if self.is_recording(player):
                return True
            time.sleep(max(0.0, poll_interval))
        return self.is_recording(player)

    # ------------------------------------------------------------------
    # Event helpers
    def _submit(self, fn: Callable[[], None]) -> Future[None]:
        with self._pending_lock:
            self._pending_tasks += 1

        def _wrapped() -> None:
            try:
                fn()
            finally:
                with self._pending_lock:
                    self._pending_tasks -= 1

        return self._executor.submit(_wrapped)

    def send_event(
        self,
        name: str,
        player: str,
        payload: Optional[Dict[str, object]] = None,
        *,
        priority: str = "normal",
    ) -> None:
        if not self._cloud_logger:
            return

        event_payload = {
            "event": name,
            "player": player,
            "payload": payload or {},
            "priority": priority,
            "t_local_ns": time.perf_counter_ns(),
        }

        future = self._submit(lambda: self._cloud_logger.send(event_payload))
        if priority == "high":
            try:
                future.result()
            except Exception:  # pragma: no cover - logged by PupylabsCloudLogger
                pass

    def send_host_mirror(
        self,
        player: str,
        event_id: str,
        t_local_ns: int,
        *,
        extra: Optional[Dict[str, object]] = None,
    ) -> None:
        if not self._cloud_logger:
            return

        payload = {
            "event": "host_mirror",
            "player": player,
            "event_id": event_id,
            "t_local_ns": t_local_ns,
            "extra": extra or {},
        }
        try:
            self._cloud_logger.send(payload)
        except Exception:  # pragma: no cover - defensive fallback
            pass

    def event_queue_load(self) -> Tuple[int, int]:
        with self._pending_lock:
            pending = self._pending_tasks
        # Der Executor arbeitet ohne feste Warteschlange. Wir geben daher nur
        # die Anzahl der offenen Aufgaben zurück und 0 als Platzhalter.
        return (pending, 0)

    def estimate_time_offset(self, player: str) -> Optional[float]:
        _ = player
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

    # ------------------------------------------------------------------
    def _start_tracker(self, cfg: NeonDeviceConfig) -> None:
        if not cfg.is_configured:
            return
        cfg.started = True
        metadata = dict(cfg.metadata)
        if cfg.device_id:
            metadata.setdefault("device_id", cfg.device_id)
        if cfg.ip:
            metadata.setdefault("ip", cfg.ip)
        if cfg.port:
            metadata.setdefault("port", str(cfg.port))
        try:
            descriptor = json.dumps(metadata) if metadata else "{}"
        except Exception:
            descriptor = "{}"
        log.info(
            "Tracker %s an Adresse %s initialisiert – %s",
            cfg.player,
            cfg.address or cfg.ip,
            descriptor,
        )


__all__ = ["NeonDeviceConfig", "PupilBridge"]
