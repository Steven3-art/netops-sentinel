# Contributing to NetOps Sentinel

Thank you for your interest in contributing to NetOps Sentinel.

NetOps Sentinel is an evidence-driven agentic AI project for telecom network
operations and troubleshooting.

## Development Principles

The project follows several core engineering principles:

- Synthetic by design.
- Rules determine facts; AI determines investigation strategy.
- Diagnoses must be supported by explicit evidence.
- Mutating actions require explicit human approval.
- Recovery must be verified after an approved action.
- External AI providers must remain behind a provider abstraction.

## Development Environment

NetOps Sentinel currently targets Python 3.12.

Create and activate a virtual environment, then install the project in
editable mode with development dependencies:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
