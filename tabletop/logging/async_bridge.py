"""Synchronous helper used as a compatibility shim.

Historically the tabletop project forwarded bridge related callbacks to a
background worker.  With the eye-tracking pipeline removed we no longer need to
queue the calls, but a number of call sites still import :func:`enqueue`.

To keep those sites simple while guaranteeing that nothing is executed on a
background thread, :func:`enqueue` now invokes the callback immediately.  This
keeps the public surface intact and makes the helper effectively a no-op when
``fn`` is ``None``.
"""

from typing import Callable, Optional


def enqueue(fn: Optional[Callable[[], None]]) -> None:
    """Execute *fn* immediately when provided."""

    if fn is None:
        return
    fn()
