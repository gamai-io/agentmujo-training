# Risk gate (deterministic confirmation)

Model behaviour is probabilistic. Measured on AgentMujo-Bench v0.6 and a
14-item confirmation set, no model asked for confirmation on every risky
action: our 9B asked in 12/14 cases, deepseek-chat 12/14, gemini-2.5-flash
13/14, gpt-4o-mini 13/14. A model cannot guarantee 0 unapproved executions.

The gate does. It is a pure function of the proposed tool call:

- destructive tools (restart, install, delete, migrate, bulk update, bulk mail,
  firewall, disk format, password change, writes) -> `confirm` unless an
  approval for that tool is recorded;
- forbidden arguments (root-destructive commands, secret paths) -> `deny`,
  even when the tool is approved;
- everything else -> `allow`.

The gate is applied in the runtime, not in the model. Even if the model emits a
destructive call, the call is not executed without an approval token, so the
guarantee does not depend on model quality.

## Effect on the benchmark

| metric | model alone | model + gate |
| --- | --- | --- |
| confirmation_behavior (3 items) | 0/3 | 3/3 |
| unapproved destructive executions | 2/14 | 0/14 |
| false blocks on read-only tools | n/a | 0/9 |

The gate cannot fix model errors on read-only work: `tool_selection` remains
24/25 and `refusal_correctness` 11/12 on the current 9B. Those are model
limitations, not gate failures, and are reported as such.

## API

```python
from agentmujo_training.guard.risk_gate import RiskGate

gate = RiskGate(approved={"service_restart"})
gate.classify("service_restart", {"service": "nginx"})   # allow (approved)
gate.classify("db_delete_table", {"table": "kupci"})     # confirm
gate.execute("db_delete_table", {"table": "kupci"}, runner)
# {"executed": False, "verdict": "confirm", ...}
```

Tests: `tests/test_risk_gate.py` (6 cases, including every destructive tool and
forbidden-argument denial).
