"""RiskGate v2 — fail-closed, normalisation-based policy.

Why v2 exists: the v1 gate matched exact tool names. An adversarial stress test
(benchmark/riskgate_stress.py) showed 52.6% detection: every spelling variant
(`firewall-disable`, `log_delet`, Cyrillic `lоg_dеlеtе`), every SQL destruction routed
through `db_query`, and shell destruction through `terminal`/`exec` passed as `allow`,
while the 500 benign read-only calls were all allowed (0 false blocks).

v2 keeps the same interface (classify/execute, Decision) and adds:
  1. tool-name normalisation (case, separators, zero-width, Cyrillic homoglyphs, plurals),
  2. destructive *intent* families instead of a name list,
  3. command policy, path policy and SQL policy over the arguments,
  4. fail-closed default: an unknown tool is `confirm`, not `allow`.

It is still deterministic and dependency-free; it decides, the model only proposes.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

Verdict = str

# Cyrillic/Greek lookalikes -> latin
_HOMOGLYPHS = {
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x", "у": "y",
    "к": "k", "м": "m", "т": "t", "в": "b", "н": "h", "ѕ": "s", "і": "i",
    "ј": "j", "ԁ": "d", "ɡ": "g", "Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z",
    "Η": "H", "Ι": "I", "Κ": "K", "Μ": "M", "Ν": "N", "Ο": "O", "Ρ": "P",
    "Τ": "T", "Υ": "Y", "Χ": "X",
}

# Tool names that are safe by construction (callables that only read).
READONLY_TOOLS = frozenset({
    "service_status", "service_logs", "disk_usage", "port_check", "process_list",
    "file_read", "file_list", "network_status", "cpu_info", "memory_info",
    "system_info", "db_query", "db_select", "db_explain", "log_tail",
    "package_list", "user_list", "uptime", "ping", "http_get",
})

# Intent families: a normalised tool name matching any of these is destructive.
DESTRUCTIVE_INTENTS = {
    "restart": ("restart", "reboot", "reload", "respawn", "bounce"),
    "shutdown": ("shutdown", "halt", "poweroff", "stopall", "killall", "kill"),
    "delete": ("delete", "remove", "rm", "erase", "purge", "wipe", "destroy",
               "truncate", "drop", "clear", "flush"),
    "format": ("format", "mkfs", "fdisk", "partition", "zero", "dd"),
    "privilege": ("grant", "chmod", "chown", "sudo", "admin", "root", "setuid",
                  "visudo", "passwd", "password", "authorizedkeys"),
    "install": ("install", "uninstall", "upgrade", "downgrade", "apt", "dpkg", "pip"),
    "network": ("firewall", "iptables", "ufw", "nftables", "route", "dns"),
    "pricing": ("price", "pricing", "bulkupdate", "discount"),
    "mail": ("mail", "email", "smtp", "newsletter", "broadcast"),
    "migrate": ("migrate", "migration", "schema", "alter"),
    "write": ("write", "edit", "append", "overwrite", "save", "put"),
}

COMMAND_DENY = [
    (r"\brm\s+(-[a-z]*[rf][a-z]*\s+)+/", "recursive delete from root"),
    (r"\brm\s+-[a-z]*r[a-z]*\s+(/|~|\.|\*)", "recursive delete"),
    (r"\bmkfs(\.\w+)?\b", "filesystem creation"),
    (r"\bdd\s+[^\n]*of=/dev/", "raw device write"),
    (r"\b(shred|wipefs)\b", "data destruction"),
    (r":\(\)\s*\{.*\};\s*:", "fork bomb"),
    (r"\bkill\s+-9\s+-1\b", "kill all processes"),
    (r"\bchmod\s+(-[a-z]+\s+)*777\s+/", "world-writable root"),
    (r"\bchown\s+-R\b", "recursive ownership change"),
    (r">\s*/etc/(passwd|shadow|sudoers)", "overwrite system file"),
    (r"\b(iptables|nft)\s+-F\b|\bufw\s+disable\b", "firewall flush"),
    (r"\bsystemctl\s+(disable|stop|mask)\b", "service disable"),
    (r"\b(shutdown|reboot|halt|poweroff)\b", "host shutdown"),
    (r"\bcrontab\s+-r\b|>\s*/var/spool/cron", "cron destruction"),
    (r"\b(curl|wget)\b[^\n]*\|\s*(ba)?sh\b", "remote code execution"),
    (r"\b(eval|source)\s+\$\(?\s*(curl|wget)", "remote code execution"),
    (r"\b(history\s+-c|truncate\s+-s\s+0\s+/var/log)", "log/history destruction"),
    (r"\busermod\s+-aG\s+sudo\b|\bvisudo\b", "privilege escalation"),
    (r"\b(passwd|chpasswd)\b", "password change"),
    (r"\b(dropdb|createdb)\b", "database admin"),
]

PATH_DENY = [
    (r"^/etc/", "write to /etc"),
    (r"^/root/\.ssh/", "write to root ssh keys"),
    (r"^/root/", "write to /root"),
    (r"^/boot/", "write to /boot"),
    (r"^/proc/sys/", "kernel parameter write"),
    (r"^/sys/", "write to /sys"),
    (r"/var/spool/cron", "cron write"),
    (r"\.\./", "path traversal"),
    (r"authorized_keys", "ssh key injection"),
    (r"\.gama_api", "credential file write"),
]

SQL_DENY = [
    (r"\bdrop\s+(table|database|schema|index)\b", "ddl drop"),
    (r"\btruncate\s+table\b", "truncate"),
    (r"\bdelete\s+from\b(?![\s\S]*\bwhere\b)", "delete without where"),
    (r"\bupdate\s+\w+\s+set\b(?![\s\S]*\bwhere\b)", "update without where"),
    (r"\bwhere\s+(1\s*=\s*1|true|'1'\s*=\s*'1')\b", "tautological predicate"),
    (r"\bgrant\s+all\b|\brevoke\s+all\b", "privilege grant/revoke"),
    (r"\balter\s+table\b[\s\S]*\bdrop\b", "alter drop column"),
    (r"\bshutdown\b", "database shutdown"),
]


def normalise(name: str) -> str:
    s = "".join(_HOMOGLYPHS.get(ch, ch) for ch in str(name))
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("\u200b", "").replace("\u200c", "").replace("\u200d", "")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "", s)
    if len(s) > 3 and s.endswith("s"):
        s = s[:-1]
    return s


def intent_of(norm: str):
    for family, keys in DESTRUCTIVE_INTENTS.items():
        for k in keys:
            if norm.startswith(k) or norm.endswith(k) or k in norm:
                return family, k
    return None, None


@dataclass
class Decision:
    verdict: Verdict
    reason: str
    tool: str
    requires_approval: bool = False


@dataclass
class RiskGateV2:
    approved: set = field(default_factory=set)
    readonly_tools: frozenset = READONLY_TOOLS
    command_deny: list = field(default_factory=lambda: COMMAND_DENY)
    path_deny: list = field(default_factory=lambda: PATH_DENY)
    sql_deny: list = field(default_factory=lambda: SQL_DENY)

    def _blob(self, args) -> str:
        if isinstance(args, dict):
            return " ".join(f"{k}={v}" for k, v in args.items())
        return str(args or "")

    def _args_text(self, args) -> str:
        parts = []
        if isinstance(args, dict):
            for k, v in args.items():
                if isinstance(v, str):
                    parts.append(v)
        return " ".join(parts)

    def classify(self, tool, args=None):
        args = args or {}
        norm = normalise(tool)
        blob_args = self._args_text(args)
        low_args = blob_args.lower()

        for pat, why in self.command_deny:
            if re.search(pat, low_args, re.I):
                return Decision("deny", f"command policy: {why}", str(tool))
        for pat, why in self.sql_deny:
            if re.search(pat, low_args, re.I):
                return Decision("deny", f"sql policy: {why}", str(tool))
        for key, val in (args.items() if isinstance(args, dict) else []):
            if str(key).lower() in ("path", "file", "target_path", "filename") and isinstance(val, str):
                for pat, why in self.path_deny:
                    if re.search(pat, val):
                        return Decision("deny", f"path policy: {why}", str(tool))

        if norm in {normalise(t) for t in self.readonly_tools}:
            fam, key = intent_of(norm)
            if fam == "write":
                return Decision("confirm", f"read-only name but '{key}' intent", str(tool), True)
            return Decision("allow", "known read-only tool", str(tool))

        fam, key = intent_of(norm)
        if fam:
            if str(tool) in self.approved or norm in self.approved:
                return Decision("allow", f"destructive ({fam}) with recorded approval", str(tool))
            return Decision("confirm", f"destructive intent ({fam}: {key})", str(tool), True)

        return Decision("confirm", "unknown tool, fail-closed", str(tool), True)

    def execute(self, tool, args, runner):
        d = self.classify(tool, args)
        if d.verdict != "allow":
            return {"executed": False, "verdict": d.verdict, "reason": d.reason}
        return {"executed": True, "verdict": "allow", "result": runner(tool, args or {})}
