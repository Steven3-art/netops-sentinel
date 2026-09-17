# ADR-0006: Use a Model Provider Abstraction

- Status: Accepted
- Date: 2026-09-17

## Context

NetOps Sentinel uses language-model capabilities for tasks such as investigation
reasoning, incident classification, tool-selection support, replanning, and
response generation.

The hackathon implementation is intended to use NVIDIA Nemotron through Nebius
Token Factory.

However, the core NetOps Sentinel architecture should not depend directly on a
specific model API, SDK, authentication mechanism, or external service.

Directly coupling the agent orchestrator to Nebius-specific implementation
details would make local development, automated testing, failure simulation,
and future provider changes unnecessarily difficult.

The project also needs to remain testable when external model access is
temporarily unavailable.

## Decision

NetOps Sentinel will access language-model capabilities through an explicit
model-provider abstraction.

The initial provider contract will expose a small set of application-oriented
capabilities such as:

```text
reason(...)
classify(...)
generate(...)
