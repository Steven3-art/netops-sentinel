# ADR-0003: Use Deterministic AAA Diagnostic Normalization

- Status: Accepted
- Date: 2026-09-16

## Context

NetOps Sentinel investigates telecom incidents using evidence collected from
multiple diagnostic sources.

AAA and RADIUS systems may expose raw events, status values, reason codes, and
diagnostic messages that represent known technical conditions.

Passing every raw AAA observation directly to a language model would introduce
unnecessary uncertainty into facts that can be interpreted deterministically.

It would also make tests less reproducible and could cause identical technical
events to receive inconsistent interpretations across investigations.

NetOps Sentinel therefore needs a clear boundary between deterministic
technical normalization and AI-assisted investigation reasoning.

## Decision

NetOps Sentinel will use a deterministic AAA diagnostic normalization layer.

A dedicated component, initially named `AAADiagnosticNormalizer`, will transform
supported synthetic AAA and RADIUS observations into normalized technical
conditions.

The normalization pipeline will follow this separation:

```text
RAW AAA EVIDENCE
        |
        v
DETERMINISTIC NORMALIZATION
        |
        v
NORMALIZED TECHNICAL CONDITION
        |
        v
AGENT CORRELATION AND REASONING
        |
        v
OPERATIONAL INTERPRETATION
        |
        v
RECOMMENDED WORKFLOW OR ACTION
