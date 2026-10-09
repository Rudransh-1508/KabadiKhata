"""Auditor decisions on Flags. Code decides (rules), the human approves (here), the LLM explains.

Pure domain logic: no store, no HTTP. The API maps FlagDenied -> 403, InvalidDecision -> 422,
FlagAlreadyDecided -> 409.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from common.models import Flag
from policy import authz, directory

DECISIONS = {"inspect": "inspection_requested", "dismiss": "dismissed"}
NOTE_MAX = 500


class FlagDecisionError(Exception):
    """Base class for every refusal from decide_flag."""


class FlagDenied(FlagDecisionError):
    """Cedar said no. `decision.to_denial("approve_flag")` is the 403 body."""

    def __init__(self, decision: authz.Decision):
        super().__init__(decision.reason)
        self.decision = decision


class InvalidDecision(FlagDecisionError):
    """The decision is not 'inspect' or 'dismiss'."""


class FlagAlreadyDecided(FlagDecisionError):
    def __init__(self, status: str):
        super().__init__(f"flag already {status}")
        self.status = status


def _clean_note(note: Optional[str]) -> Optional[str]:
    if not isinstance(note, str):
        return None
    note = note.strip()
    return note[:NOTE_MAX] if note else None


def decide_flag(flag: Flag, principal: str, decision: str, note: Optional[str] = None,
                now: Optional[datetime] = None) -> Flag:
    """Return a new Flag with the Auditor's decision recorded; the input is never mutated."""
    if not isinstance(decision, str) or decision not in DECISIONS:
        raise InvalidDecision(f"decision must be one of {sorted(DECISIONS)}")
    verdict = authz.is_allowed(principal, "approve_flag", {"type": "Flag", "id": flag.flag_id})
    if not verdict.allowed:
        raise FlagDenied(verdict)
    if flag.status != "open":
        raise FlagAlreadyDecided(flag.status)

    when = now or datetime.now(timezone.utc)
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    m = directory.ACTOR_UID_RE.match(principal)
    if m is None:  # Cedar allowed a principal that is not an Actor: fail closed
        raise FlagDenied(authz.Decision(False, "approve_flag requires an Actor principal"))
    actor_id = m.group(1)
    return flag.model_copy(
        update={
            "status": DECISIONS[decision],
            "decided_by": actor_id,
            "decided_ts": when,
            "decision_note": _clean_note(note),
        },
        deep=True,
    )
