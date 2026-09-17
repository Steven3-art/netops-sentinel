# ADR-0004: Use Evidence-Driven Diagnosis

- Status: Accepted
- Date: 2026-09-17

## Context

NetOps Sentinel investigates telecom incidents by interacting with diagnostic
tools and correlating observations from multiple technical domains.

A language model can assist with investigation strategy and reasoning, but a
model-generated statement alone must not be treated as an authoritative
operational fact.

The system therefore needs a mechanism that clearly distinguishes:

- incident input;
- tool execution;
- observed technical facts;
- normalized technical conditions;
- agent hypotheses;
- final diagnoses;
- proposed actions.

Without this separation, it would be difficult to determine why a diagnosis was
produced, reproduce an investigation, evaluate agent behavior, or audit a
proposed operational action.

## Decision

NetOps Sentinel will use an Evidence Store as a first-class part of the
investigation lifecycle.

Approved diagnostic tool executions will produce structured evidence records.

Each evidence record will receive a stable identifier within its investigation,
for example:

```text
EV-0001
EV-0002
EV-0003
