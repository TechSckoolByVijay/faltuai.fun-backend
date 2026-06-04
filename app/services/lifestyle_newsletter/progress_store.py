"""
In-memory progress store for live generation updates.

Keyed by episode_id → list of timestamped messages.
No persistence — lives only for the duration of the server process.
Messages are pruned automatically after MAX_AGE seconds.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List

_MAX_AGE: int = 3600  # 1 hour — auto-prune


@dataclass
class ProgressEntry:
    ts: float
    msg: str
    type: str = "info"  # info | step | success | error


# Global in-memory store — keyed by episode_id
_store: Dict[int, List[ProgressEntry]] = {}


def add(episode_id: int, msg: str, type_: str = "info") -> None:
    """Append a progress message for the given episode."""
    if episode_id not in _store:
        _store[episode_id] = []
    _store[episode_id].append(ProgressEntry(ts=time.time(), msg=msg, type=type_))


def get(episode_id: int) -> List[dict]:
    """Return all progress messages for the episode as dicts."""
    return [
        {"ts": e.ts, "msg": e.msg, "type": e.type}
        for e in _store.get(episode_id, [])
    ]


def clear(episode_id: int) -> None:
    """Remove all progress messages for the episode (call after episode is displayed)."""
    _store.pop(episode_id, None)


def prune() -> None:
    """Remove entries older than MAX_AGE (call periodically if desired)."""
    cutoff = time.time() - _MAX_AGE
    stale = [eid for eid, entries in _store.items() if entries and entries[0].ts < cutoff]
    for eid in stale:
        _store.pop(eid, None)
