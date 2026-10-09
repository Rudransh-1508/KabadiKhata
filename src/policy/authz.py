"""Authorization entry point. Every API handler and the agent's write go through is_allowed().

STUB until the Cedar policies land (Sat 12:00): same signature and Decision shape, hard-coded rules
that mirror policies.cedar for the agent. The real version evaluates policies.cedar with cedarpy.
"""
from __future__ import annotations

from dataclasses import dataclass

AGENT = 'Agent::"kabadi-agent"'
AGENT_FORBIDDEN = {"approve_flag", "issue_certificate", "read_receipt_pii"}


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str

    def to_denial(self, action: str) -> dict:
        """Body for an HTTP 403; the console renders it as the red 'Denied by Cedar policy' banner."""
        return {"denied_by": "cedar", "action": action, "reason": self.reason}


def is_allowed(principal: str, action: str, resource: dict, context: dict | None = None) -> Decision:
    context = context or {}
    if principal == AGENT:
        if action in AGENT_FORBIDDEN:
            return Decision(False, f"agent is forbidden from {action}")
        if action == "create_receipt":
            if context.get("consistency_ok") is True:
                return Decision(True, "agent may create a receipt after consistency passed")
            return Decision(False, "consistency check has not passed")
        return Decision(False, "default deny")
    # Non-agent principals: permissive stub so integration isn't blocked. Cedar replaces this.
    return Decision(True, "stub: allowed until Cedar policies are wired")
