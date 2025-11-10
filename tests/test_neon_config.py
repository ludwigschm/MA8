from __future__ import annotations

import logging

from tabletop.pupil_bridge import _load_neon_configs


def test_load_neon_configs_supports_id_ip_port(tmp_path):
    cfg_path = tmp_path / "neon.txt"
    cfg_path.write_text(
        "\n".join(
            [
                "VP1_ID=abc123",
                "VP1_IP=10.0.0.1",
                "VP1_PORT=8081",
                "VP2=10.0.0.2",
            ]
        ),
        encoding="utf-8",
    )

    configs = _load_neon_configs(cfg_path)

    assert set(configs) == {"VP1", "VP2"}

    vp1 = configs["VP1"]
    assert vp1.device_id == "abc123"
    assert vp1.ip == "10.0.0.1"
    assert vp1.port == 8081
    assert vp1.metadata["device_id"] == "abc123"
    assert vp1.metadata["ip"] == "10.0.0.1"
    assert vp1.metadata["port"] == "8081"
    assert vp1.metadata["source"] == "config_file"

    vp2 = configs["VP2"]
    assert vp2.ip == "10.0.0.2"
    assert vp2.device_id == ""
    assert vp2.port is None


def test_load_neon_configs_ignores_invalid_port(tmp_path, caplog):
    cfg_path = tmp_path / "neon_invalid.txt"
    cfg_path.write_text(
        "\n".join(
            [
                "VP1_PORT=invalid",
                "VP1_IP=10.0.0.3",
            ]
        ),
        encoding="utf-8",
    )

    with caplog.at_level(logging.WARNING):
        configs = _load_neon_configs(cfg_path)

    assert "Ungültiger Port" in caplog.text
    vp1 = configs["VP1"]
    assert vp1.port is None
    assert vp1.ip == "10.0.0.3"
