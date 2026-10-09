"""Authorization entry point. Every API handler and the agent's write go through is_allowed().

Evaluates policies.cedar (default deny) with cedarpy. Fails closed: an unknown principal,
a malformed request, a missing policy file or any Cedar error is a deny, never an allow.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import cedarpy
from cedarpy import Decision as CedarDecision

from policy import directory

log = logging.getLogger("kk.authz")

AGENT = 'Agent::"kabadi-agent"'
_AGENT_ID = "kabadi-agent"
_AGENT_RE = re.compile(r'^Agent::"([A-Za-z0-9_.:@-]+)"$')
_RESOURCE_TYPES = {"Receipt", "Chain", "Certificate", "Flag", "Radar", "Photo", "Directory", "Actor"}
_REF_ATTR = {"Receipt": "collector", "Chain": "collector", "Certificate": "buyer"}

_POLICY_DIR = Path(__file__).parent


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str

    def to_denial(self, action: str) -> dict:
        """Body for an HTTP 403; the console renders it as the red 'Denied by Cedar policy' banner."""
        return {"denied_by": "cedar", "action": action, "reason": self.reason}


def _deny(reason: str) -> Decision:
    return Decision(False, reason)


@lru_cache(maxsize=1)
def _load() -> tuple[str, str, frozenset]:
    """Policy and schema text, read once. Raises if a file is missing."""
    policies = (_POLICY_DIR / "policies.cedar").read_text(encoding="utf-8")
    schema = (_POLICY_DIR / "schema.cedarschema").read_text(encoding="utf-8")
    actions = frozenset(re.findall(r"^action\s+(\w+)", schema, flags=re.M))
    if not policies.strip() or not actions:
        raise ValueError("empty policy or schema")
    return policies, schema, actions


def _uid(type_: str, id_: str) -> dict:
    return {"type": type_, "id": id_}


def _principal(principal: str, action: str = "") -> tuple[dict, str, list[dict]] | str:
    """(uid, role, parents) for a known principal, or a denial reason string.

    Only `register` accepts a principal not yet in the directory: a new Kabadiwala signing up
    from the bot. The self-registration policy still restricts it to its own Actor.
    """
    if principal == AGENT:
        return _uid("Agent", _AGENT_ID), "agent", []
    if not isinstance(principal, str):
        return "malformed principal"
    m = directory.ACTOR_UID_RE.match(principal)
    if not m:
        return "malformed or unknown principal"
    actor_id = m.group(1)
    role = directory.role_of(actor_id)
    if role is None:
        directory.refresh()
        role = directory.role_of(actor_id)
    if role is None and action == "register":
        role = "kabadiwala"
    if role is None:
        return "unknown principal"
    return _uid("Actor", actor_id), role, [_uid("Role", role)]


def _evaluate(principal: str, action: str, resource: dict, context: dict | None) -> Decision:
    try:
        policies, schema, actions = _load()
    except Exception as exc:  # missing or unreadable file
        log.error("policy files unavailable: %s", exc)
        return _deny("policy unavailable")

    if not isinstance(action, str) or action not in actions:
        return _deny(f"unknown action {action!r}")

    who = _principal(principal, action)
    if isinstance(who, str):
        return _deny(who)
    p_uid, role, parents = who

    if not isinstance(resource, dict):
        return _deny("malformed resource")
    rtype = resource.get("type")
    if rtype is None and p_uid["type"] == "Agent" and action == "create_receipt":
        rtype = "Receipt"
    if rtype not in _RESOURCE_TYPES:
        return _deny("malformed resource: missing or unknown type")
    rid = resource.get("id", "-")
    if not isinstance(rid, str) or not rid:
        return _deny("malformed resource id")

    entities: dict[tuple, dict] = {}
    attrs: dict = {}
    ref_attr = _REF_ATTR.get(rtype)
    if ref_attr and resource.get(ref_attr) is not None:
        ref = resource[ref_attr]
        m = directory.ACTOR_UID_RE.match(ref) if isinstance(ref, str) else None
        if not m:
            return _deny(f"malformed {ref_attr}: expected Actor::\"<id>\"")
        ref_uid = _uid("Actor", m.group(1))
        attrs[ref_attr] = {"__entity": ref_uid}
        entities[("Actor", m.group(1))] = {"uid": ref_uid, "attrs": {}, "parents": []}

    entities[(p_uid["type"], p_uid["id"])] = {"uid": p_uid, "attrs": {}, "parents": parents}
    if parents:
        entities[("Role", role)] = {"uid": parents[0], "attrs": {}, "parents": []}
    if rtype == "Actor":  # the API passes the reference form Actor::"<id>" as the id
        m = directory.ACTOR_UID_RE.match(rid)
        if not m:
            return _deny("malformed resource id")
        rid = m.group(1)
    r_uid = _uid(rtype, rid)
    entities[(rtype, rid)] = {"uid": r_uid, "attrs": attrs, "parents": []}

    request = {
        "principal": p_uid,
        "action": _uid("Action", action),
        "resource": r_uid,
        "context": context if isinstance(context, dict) else {},
    }
    try:
        result = cedarpy.is_authorized(request, policies, list(entities.values()))
        errors = list(result.diagnostics.errors)
        decision = result.decision
        reasons = list(result.diagnostics.reasons)
    except Exception as exc:
        log.error("cedar evaluation failed: %s", exc)
        return _deny("policy error: evaluation failed")

    if errors:
        # Includes a missing or wrongly typed context attribute; an error is never an allow.
        return _deny("policy error: " + "; ".join(str(e) for e in errors)[:200])
    if decision == CedarDecision.Allow:
        return Decision(True, "allowed by policy")
    if reasons:
        return _deny("forbidden by policy")
    return _deny(f"no policy permits {role} to {action}")


def is_allowed(principal: str, action: str, resource: dict, context: dict | None = None) -> Decision:
    try:
        return _evaluate(principal, action, resource, context)
    except Exception as exc:  # never raise, never allow
        log.error("authz failure: %s", exc)
        return _deny("policy error: internal failure")
