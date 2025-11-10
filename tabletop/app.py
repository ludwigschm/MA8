"""Minimal Kivy application bootstrap for the Bluffing Eyes tabletop demo."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from kivy.app import App
from kivy.lang import Builder

from .tabletop_view import TabletopRoot

_KV_PATH = Path(__file__).parent / "ui" / "layout.kv"


class TabletopApp(App):
    """Simple Kivy application that hosts the tabletop UI."""

    def build(self) -> TabletopRoot:
        Builder.load_file(str(_KV_PATH))
        return TabletopRoot()


def _compose_title(session: Optional[int], block: Optional[int], player: Optional[str]) -> str:
    base_title = "Bluffing Eyes"
    parts: list[str] = []
    if session is not None:
        parts.append(f"session={session}")
    if block is not None:
        parts.append(f"block={block}")
    if player:
        parts.append(f"player={player}")
    if parts:
        return f"{base_title} – {' '.join(parts)}"
    return base_title


def main(session: Optional[int], block: Optional[int], player: Optional[str]) -> None:
    """Run the Kivy application with the desired window title."""

    app = TabletopApp()
    app.title = _compose_title(session, block, player)
    app.run()
