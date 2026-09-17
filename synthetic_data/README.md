# NetOps Sentinel Synthetic Data

## Synthetic by Design

The NetOps Sentinel Telco Digital Lab is built exclusively from synthetic data.

This directory must never contain production telecom data.

Its purpose is to provide reproducible and safe scenarios for developing,
testing, demonstrating, and evaluating the NetOps Sentinel agent.

## Intended Data

Synthetic datasets may represent:

- FTTH subscribers;
- subscriber account states;
- AAA accounts;
- RADIUS authentication events;
- online and offline sessions;
- authentication and activity histories;
- QoS measurements;
- network events;
- alarms;
- incidents;
- diagnostic evidence;
- support requests.

## Identifier Convention

Synthetic identifiers should make their artificial nature obvious whenever
practical.

Examples:

```text
DEMO-00042
SUB-DEMO-100042
INC-DEMO-0001
EV-0001
