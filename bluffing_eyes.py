"""Minimal CLI entry point for the Bluffing Eyes tabletop demo."""

from __future__ import annotations

import argparse
from typing import Sequence

from tabletop.app import main as app_main


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments for the tabletop demo."""

    parser = argparse.ArgumentParser(
        description="Start the minimal Bluffing Eyes tabletop application"
    )
    parser.add_argument("--session", type=int, default=None, help="Optional session ID")
    parser.add_argument("--block", type=int, default=None, help="Optional block number")
    parser.add_argument("--player", type=str, default=None, help="Optional player identifier")
    parser.add_argument(
        "--display",
        type=int,
        default=None,
        help="Display index (ignored by the minimal application)",
    )
    parser.add_argument(
        "--perf",
        action="store_true",
        help="Performance flag (accepted but ignored by the minimal application)",
    )
    parser.add_argument(
        "--single-block",
        action="store_true",
        help="Single block mode flag (accepted but ignored by the minimal application)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """Entry point that forwards CLI arguments to the Kivy application."""

    args = parse_args(argv)
    app_main(session=args.session, block=args.block, player=args.player)


if __name__ == "__main__":  # pragma: no cover - convenience wrapper
    main()
