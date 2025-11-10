from tabletop.startup import ensure_trackers_recording_sequential


class DummyBridge:
    def __init__(self, *, active=None):
        self.started_calls = []
        self.wait_calls = []
        self._active = set(active or [])

    def connected_players(self):
        return {"VP1", "VP2"}

    def is_connected(self, player):
        return True

    def is_recording(self, player):
        return player in self._active

    def start_recording(self, session, block, player):
        self.started_calls.append((player, session, block))
        self._active.add(player)

    def wait_until_recording(self, player, *, timeout=5.0, poll_interval=0.2):
        self.wait_calls.append((player, timeout, poll_interval))
        return player in self._active


def test_ensure_trackers_recording_sequential_order():
    bridge = DummyBridge()

    result = ensure_trackers_recording_sequential(
        bridge,
        session=3,
        block=2,
        players=["VP1", "VP2"],
    )

    assert result == ["VP1", "VP2"]
    assert bridge.started_calls == [("VP1", 3, 2), ("VP2", 3, 2)]
    assert bridge.wait_calls == [("VP1", 5.0, 0.2), ("VP2", 5.0, 0.2)]


def test_ensure_trackers_recording_skips_existing():
    bridge = DummyBridge(active={"VP1"})

    result = ensure_trackers_recording_sequential(
        bridge,
        session=1,
        block=1,
        players=["VP1", "VP2"],
    )

    assert result == ["VP1", "VP2"]
    assert bridge.started_calls == [("VP2", 1, 1)]
    assert bridge.wait_calls == [("VP2", 5.0, 0.2)]
