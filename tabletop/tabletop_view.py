"""Widget definitions for the minimal Bluffing Eyes tabletop demo."""

from __future__ import annotations

from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout


class TabletopRoot(BoxLayout):
    """Root widget providing simple controls for two players."""

    status_text = StringProperty("Status: Bereit")

    def start_p1(self) -> None:
        """Update the status to reflect that player 1 has started."""

        self.status_text = "Status: Gestartet für P1"

    def start_p2(self) -> None:
        """Update the status to reflect that player 2 has started."""

        self.status_text = "Status: Gestartet für P2"
