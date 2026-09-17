"""Evidence models and in-memory evidence storage."""

from collections import defaultdict
from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from netops_sentinel.core.domain import NonEmptyString, utc_now


class EvidenceKind(StrEnum):
    """Origin classification for investigation evidence."""

    RAW = "raw"
    DERIVED = "derived"


class Evidence(BaseModel):
    """Immutable evidence collected during an investigation."""

    model_config = ConfigDict(frozen=True)

    evidence_id: NonEmptyString
    incident_id: NonEmptyString
    source: NonEmptyString
    evidence_type: NonEmptyString
    kind: EvidenceKind
    payload: Mapping[str, Any]
    parent_evidence_ids: tuple[NonEmptyString, ...] = ()
    collected_at: datetime = Field(default_factory=utc_now)


class EvidenceNotFoundError(LookupError):
    """Raised when an evidence identifier does not exist."""


class DuplicateEvidenceError(ValueError):
    """Raised when an evidence identifier already exists."""


class EvidenceStore:
    """Append-only in-memory store for investigation evidence."""

    def __init__(self) -> None:
        self._evidence_by_id: dict[str, Evidence] = {}
        self._incident_index: dict[str, list[str]] = defaultdict(list)
        self._next_sequence = 1

    def next_id(self) -> str:
        """Return the next stable evidence identifier."""

        evidence_id = f"EV-{self._next_sequence:04d}"
        self._next_sequence += 1
        return evidence_id

    def append(
        self,
        *,
        incident_id: NonEmptyString,
        source: NonEmptyString,
        evidence_type: NonEmptyString,
        kind: EvidenceKind,
        payload: Mapping[str, Any],
        parent_evidence_ids: tuple[NonEmptyString, ...] = (),
        evidence_id: NonEmptyString | None = None,
    ) -> Evidence:
        """Append immutable evidence and return the stored record."""

        resolved_id = evidence_id or self.next_id()

        if resolved_id in self._evidence_by_id:
            raise DuplicateEvidenceError(f"Evidence '{resolved_id}' already exists.")

        self._validate_parent_evidence(
            incident_id=incident_id,
            kind=kind,
            parent_evidence_ids=parent_evidence_ids,
        )

        evidence = Evidence(
            evidence_id=resolved_id,
            incident_id=incident_id,
            source=source,
            evidence_type=evidence_type,
            kind=kind,
            payload=dict(payload),
            parent_evidence_ids=parent_evidence_ids,
        )

        self._evidence_by_id[resolved_id] = evidence
        self._incident_index[incident_id].append(resolved_id)

        return evidence

    def get(self, evidence_id: str) -> Evidence:
        """Return evidence by identifier."""

        try:
            return self._evidence_by_id[evidence_id]
        except KeyError as exc:
            raise EvidenceNotFoundError(f"Evidence '{evidence_id}' was not found.") from exc

    def list_for_incident(self, incident_id: str) -> tuple[Evidence, ...]:
        """Return evidence for an incident in insertion order."""

        evidence_ids = self._incident_index.get(incident_id, [])
        return tuple(self._evidence_by_id[evidence_id] for evidence_id in evidence_ids)

    def _validate_parent_evidence(
        self,
        *,
        incident_id: str,
        kind: EvidenceKind,
        parent_evidence_ids: tuple[str, ...],
    ) -> None:
        if kind is EvidenceKind.RAW and parent_evidence_ids:
            raise ValueError("Raw evidence cannot reference parent evidence.")

        if kind is EvidenceKind.DERIVED and not parent_evidence_ids:
            raise ValueError("Derived evidence must reference parent evidence.")

        for parent_id in parent_evidence_ids:
            parent = self.get(parent_id)

            if parent.incident_id != incident_id:
                raise ValueError(
                    "Derived evidence cannot reference evidence from another incident."
                )
