# Security Policy

## Security Principles

NetOps Sentinel is an experimental agentic AI project for telecom network
operations and troubleshooting.

The project follows a **synthetic-by-design** security model.

No real operator data, customer data, credentials, production topology,
production telemetry, proprietary source code, confidential procedures,
or other non-public operational information belongs in this repository.

## Synthetic Data Requirement

All telecom data committed to this repository must be synthetic.

This includes, but is not limited to:

- subscriber identifiers;
- AAA and RADIUS events;
- authentication histories;
- session information;
- IP addresses used as operational examples;
- QoS measurements;
- network events and alarms;
- topology information;
- incident histories;
- support requests and emails;
- diagnostic scenarios.

Synthetic scenarios may model realistic telecom behavior, but they must not
contain copied production records or information that identifies a real
subscriber, employee, system, network, or operator environment.

## Secrets

Secrets must never be committed to the repository.

Examples include:

- API keys;
- access tokens;
- passwords;
- private keys;
- database credentials;
- cloud credentials;
- authentication cookies.

Local secrets must be stored in `.env` or another explicitly ignored local
configuration mechanism.

`.env.example` contains configuration names and safe example values only.

## Agent Safety

NetOps Sentinel separates diagnostic reasoning from authorization.

The agent must not be trusted as the sole authority for sensitive actions.

Actions are classified into three safety levels:

- `LEVEL_0_READ` — read-only diagnostic operations;
- `LEVEL_1_RECOMMEND` — recommendations without state mutation;
- `LEVEL_2_MUTATE` — state-changing operations requiring explicit human approval.

The backend must enforce authorization independently of model output.

## Evidence and Auditability

Diagnostic conclusions should be grounded in structured evidence produced by
approved tools.

Evidence should be traceable to the tool invocation that produced it.

Model-generated statements must not be treated as authoritative operational
facts when they are not supported by evidence.

## External Services

Credentials for services such as Nebius, NVIDIA-related endpoints, LangSmith,
or future integrations must be supplied through local environment configuration
or an appropriate secret-management system.

Credentials must not be embedded in source code, tests, synthetic datasets,
documentation, screenshots, examples, or Git history.

## Reporting Security Issues

Do not publish credentials, confidential data, or exploitable security details
in a public issue.

Security reporting instructions will be expanded before the first public
release.
