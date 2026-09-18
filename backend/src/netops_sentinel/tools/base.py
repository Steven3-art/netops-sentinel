"""Shared contracts for NetOps Sentinel diagnostic tools."""

from dataclasses import dataclass

from netops_sentinel.core.evidence import EvidenceStore
from netops_sentinel.lab.repository import TelcoLabRepository


@dataclass(frozen=True, slots=True)
class ToolContext:
    """Runtime dependencies available to a diagnostic tool."""

    incident_id: str
    repository: TelcoLabRepository
    evidence_store: EvidenceStore
