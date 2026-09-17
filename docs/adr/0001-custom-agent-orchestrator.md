# ADR-0001: Use a Custom Explicit Agent Orchestrator

- Status: Accepted
- Date: 2026-09-16

## Context

NetOps Sentinel is an agentic AI system for telecom network operations and
troubleshooting.

The agent must investigate incidents through an explicit iterative workflow:

1. observe the current incident state;
2. reason about the available evidence;
3. select an approved diagnostic tool;
4. execute the tool;
5. record the resulting evidence;
6. update the investigation state;
7. replan when additional evidence is required;
8. produce a diagnosis or request an authorized action.

The system must also enforce operational safety boundaries independently of
model output. Read-only operations may execute automatically, while
state-changing operations require explicit human approval.

For the initial implementation, the investigation lifecycle must remain easy
to inspect, test, benchmark, and demonstrate.

Several agent orchestration frameworks could implement this workflow.
However, introducing a framework at the foundation stage would also introduce
additional abstractions before the project's orchestration requirements are
fully understood.

## Decision

NetOps Sentinel will initially use a custom explicit agent orchestrator
implemented as a controlled state machine.

The orchestrator will own the investigation lifecycle and explicitly manage
transitions between states such as:

```text
OBSERVE
  -> REASON
  -> SELECT_TOOL
  -> EXECUTE
  -> RECORD_EVIDENCE
  -> REPLAN
  -> DIAGNOSE
  -> PROPOSE_ACTION
  -> WAIT_FOR_APPROVAL
  -> EXECUTE_ACTION
  -> VERIFY_RECOVERY
