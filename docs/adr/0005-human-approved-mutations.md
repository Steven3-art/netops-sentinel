# ADR-0005: Require Human Approval for State-Changing Actions

- Status: Accepted
- Date: 2026-09-17

## Context

NetOps Sentinel investigates telecom incidents by calling approved tools,
collecting evidence, forming diagnoses, and proposing operational actions.

Some tools are read-only and can safely inspect the synthetic Telco Digital
Lab. Other tools may modify system state.

For example, an investigation may determine that a credential reset is an
appropriate remediation. The agent may recommend that operation, but model
output alone must not authorize its execution.

Relying only on prompt instructions such as "ask before performing sensitive
actions" would not provide a sufficient application-level safety boundary.

NetOps Sentinel therefore requires an authorization mechanism that operates
independently of language-model behavior.

## Decision

NetOps Sentinel will classify agent-accessible operations into explicit safety
levels.

The initial safety model contains three levels:

```text
LEVEL_0_READ
LEVEL_1_RECOMMEND
LEVEL_2_MUTATE
