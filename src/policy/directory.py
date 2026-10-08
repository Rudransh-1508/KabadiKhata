"""Actor directory: principal id -> role. Filled by register() (tests) or load_from_store() (runtime).

Roles live in our own in-memory map so authorization never depends on a seed file.
"""
from __future__ import annotations

import re
import threading

ROLES = frozenset({"kabadiwala", "recycler", "brand", "auditor"})
ACTOR_UID_RE = re.compile(r'^Actor::"([A-Za-z0-9_.:@-]+)"$')
ACTOR_ID_RE = re.compile(r"^[A-Za-z0-9_.:@-]+$")

_lock = threading.Lock()
_roles: dict[str, str] = {}
_stores: list = []


def register(actor_id: str, role: str) -> None:
    if role not in ROLES:
        raise ValueError(f"unknown role {role!r}; expected one of {sorted(ROLES)}")
    if not isinstance(actor_id, str) or not ACTOR_ID_RE.match(actor_id):
        raise ValueError(f"invalid actor id {actor_id!r}")
    with _lock:
        _roles[actor_id] = role


def role_of(actor_id: str) -> str | None:
    with _lock:
        return _roles.get(actor_id)


def _read(store) -> int:
    n = 0
    for actor in store.list_actors():
        try:
            register(actor.actor_id, actor.role)
            n += 1
        except ValueError:
            continue  # an invalid row never becomes a principal
    return n


def load_from_store(store) -> int:
    """Additive: registers every actor in the store, never removes. Remembers the store for refresh()."""
    with _lock:
        if not any(s is store for s in _stores):
            _stores.append(store)
    return _read(store)


def refresh() -> int:
    with _lock:
        stores = list(_stores)
    return sum(_read(s) for s in stores)


def clear() -> None:
    """Tests only: drops actors and remembered stores."""
    with _lock:
        _roles.clear()
        _stores.clear()
