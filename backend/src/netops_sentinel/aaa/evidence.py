"""AAA evidence derivation for NetOps Sentinel."""

from collections.abc import Mapping
from typing import Any

from netops_sentinel.aaa.models import AAANormalizationResult
from netops_sentinel.aaa.normalizer import AAADiagnosticNormalizer
from netops_sentinel.core.evidence import Evidence, EvidenceKind, EvidenceStore


class InvalidAAAEvidenceError(ValueError):
    """Raised when evidence cannot be processed as an AAA diagnostic."""


class AAAEvidenceProcessor:
    """Convert raw AAA diagnostic evidence into normalized derived evidence."""

    RAW_EVIDENCE_TYPE = "aaa_diagnostic"
    DERIVED_EVIDENCE_TYPE = "normalized_aaa_condition"
    DERIVED_SOURCE = "aaa.normalizer"

    def __init__(self, normalizer: AAADiagnosticNormalizer | None = None) -> None:
        self._normalizer = normalizer or AAADiagnosticNormalizer()

    def process(
        self,
        raw_evidence: Evidence,
        evidence_store: EvidenceStore,
    ) -> Evidence:
        """Normalize raw AAA evidence and append its derived evidence."""

        message = self._extract_message(raw_evidence)
        result = self._normalizer.normalize(message)

        return evidence_store.append(
            incident_id=raw_evidence.incident_id,
            source=self.DERIVED_SOURCE,
            evidence_type=self.DERIVED_EVIDENCE_TYPE,
            kind=EvidenceKind.DERIVED,
            payload=self._build_payload(result),
            parent_evidence_ids=(raw_evidence.evidence_id,),
        )

    def _extract_message(self, evidence: Evidence) -> str:
        """Validate raw AAA evidence and extract its diagnostic message."""

        if evidence.kind is not EvidenceKind.RAW:
            raise InvalidAAAEvidenceError("AAA input evidence must be raw evidence.")

        if evidence.evidence_type != self.RAW_EVIDENCE_TYPE:
            raise InvalidAAAEvidenceError(
                f"Expected evidence type '{self.RAW_EVIDENCE_TYPE}', "
                f"received '{evidence.evidence_type}'."
            )

        message = evidence.payload.get("message")

        if not isinstance(message, str) or not message.strip():
            raise InvalidAAAEvidenceError(
                "AAA diagnostic evidence must contain a non-empty string 'message'."
            )

        return message

    @staticmethod
    def _build_payload(
        result: AAANormalizationResult,
    ) -> Mapping[str, Any]:
        """Build the structured payload for derived AAA evidence."""

        return {
            "condition": result.condition.value,
            "matched_rule": result.matched_rule,
            "normalized_message": result.normalized_message,
        }
