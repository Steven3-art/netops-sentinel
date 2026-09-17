# ADR-0002: Use a Synthetic Telco Digital Lab

- Status: Accepted
- Date: 2026-09-16

## Context

NetOps Sentinel requires a telecom environment in which an agent can investigate
incidents, call diagnostic tools, collect evidence, identify root causes, and
verify recovery.

A useful development and evaluation environment must represent telecom concepts
such as:

- subscribers and service profiles;
- AAA accounts;
- RADIUS authentication events;
- online and offline sessions;
- authentication and activity histories;
- QoS measurements;
- network events and alarms;
- incident histories;
- diagnostic and remediation workflows.

Using real production telecom data would introduce unacceptable confidentiality,
privacy, security, intellectual-property, and reproducibility risks.

Production data is also unsuitable as the foundation of a public and
reproducible hackathon project.

## Decision

NetOps Sentinel will use a synthetic Telco Digital Lab as its development,
demonstration, testing, and evaluation environment.

All operational data committed to the repository must be artificially generated
for the project.

The lab will model realistic telecom behavior without reproducing a real
operator environment.

Synthetic entities may include:

- FTTH subscribers;
- subscriber accounts;
- AAA accounts;
- RADIUS events;
- sessions;
- traffic histories;
- QoS metrics;
- network events;
- incidents;
- support requests;
- diagnostic evidence.

Synthetic identifiers should make their artificial nature clear whenever
practical.

Examples include:

```text
DEMO-00042
SUB-DEMO-100042
INC-DEMO-0001
EV-0001
