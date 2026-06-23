"""MemoryDataSink MVP: best-effort pub/sub for events and curves.

- Bounded queue (drop on overload -> DS-SINK-OVERLOAD)
- Never blocks ResultStore / L4
- History not guaranteed after disconnect (use ResultStore for facts)
"""

from __future__ import annotations

from collections import deque
from typing import Any, Iterator, Optional



class MemoryDataSink:
    """In-memory bounded sink for L4 events and preview curves."""

    def __init__(self, max_events: int = 1024):
        self._events: dict[str, deque] = {}  # run_id -> deque of dicts
        self._max = max_events
        self._subs: dict[str, list] = {}  # simple for subscribe

    def publish_run_event(self, event: Any) -> None:
        """Publish RunEvent (or dict). Best effort. Drop if full."""
        run_id = getattr(event, "run_id", None) or (event.get("run_id") if isinstance(event, dict) else "unknown")
        q = self._events.setdefault(run_id, deque(maxlen=self._max))
        if hasattr(event, "model_dump"):
            ev = event.model_dump()
        elif isinstance(event, dict):
            ev = event
        else:
            ev = {"run_id": getattr(event, "run_id", "unknown"), "code": getattr(event, "code", str(event))}
        if len(q) >= self._max:
            q.popleft()
            # per design: emit overload warning (DS-SINK-OVERLOAD) so tests can assert
            ov = {"run_id": run_id, "code": "DS-SINK-OVERLOAD", "message": "queue full, dropped", "severity": "warning"}
            q.append(ov)
        q.append(ev)

    def publish_curve(self, run_id: str, channel: str, payload: Any) -> None:
        """Preview curve (e.g. live IQ). Dropped if slow consumer."""
        key = f"{run_id}:{channel}"
        q = self._events.setdefault(key, deque(maxlen=self._max // 4))
        if len(q) >= q.maxlen:
            q.popleft()
        q.append({"channel": channel, "payload": payload})

    def subscribe(self, run_id: str) -> Iterator[dict]:
        """Simple iterator over buffered events. New events after subscribe not auto pushed in MVP."""
        q = self._events.get(run_id, deque())
        for e in list(q):
            yield e

    def get_events(self, run_id: str) -> list[dict]:
        return list(self._events.get(run_id, []))

    def clear(self, run_id: Optional[str] = None) -> None:
        if run_id:
            self._events.pop(run_id, None)
        else:
            self._events.clear()
