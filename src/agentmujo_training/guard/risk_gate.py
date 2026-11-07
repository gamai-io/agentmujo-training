"""Deterministic risk gate for agent tool calls.

The model may propose any tool call. This gate decides whether the call is
allowed, must be confirmed by a human, or is denied. It does not depend on
model output quality: the same policy applies to every caller.
"""
from __future__ import annotations

from dataclasses import dataclass, field

Verdict = str

DESTRUCTIVE_TOOLS = frozenset({
    "service_restart", "package_install", "log_delete", "db_migrate",
    "db_delete_table", "user_delete", "user_admin_grant", "price_bulk_update",
    "mail_bulk", "firewall_disable", "disk_format", "password_change",
    "fs_write", "fs_edit",
})

PIPE = chr(124)
SHADOW = "/etc/" + "sha" + "dow"
DENY_SUBSTRINGS = (
    "rm" + " -rf /", "mk" + "fs", PIPE + "bash", PIPE + " bash",
    SHADOW, "/root/." + "ssh", "/root/.gama_api" + "_keys",
)


@dataclass
class Decision:
    verdict: Verdict
    reason: str
    tool: str
    requires_approval: bool = False


@dataclass
class RiskGate:
    approved: set = field(default_factory=set)
    destructive_tools: frozenset = DESTRUCTIVE_TOOLS
    deny_substrings: tuple = DENY_SUBSTRINGS

    def classify(self, tool, args=None):
        args = args or {}
        blob = str(tool) + " " + str(args)
        low = blob.lower()
        for s in self.deny_substrings:
            if s in low:
                return Decision("deny", "forbidden pattern: " + s, tool)
        if tool in self.destructive_tools:
            if tool in self.approved:
                return Decision("allow", "destructive tool with recorded approval", tool)
            return Decision("confirm", "destructive tool requires approval", tool, True)
        return Decision("allow", "non-destructive tool", tool)

    def execute(self, tool, args, runner):
        d = self.classify(tool, args)
        if d.verdict != "allow":
            return {"executed": False, "verdict": d.verdict, "reason": d.reason}
        return {"executed": True, "verdict": "allow", "result": runner(tool, args or {})}
