"""Evidence-driven deterministic diagnosis engine."""

from collections.abc import Iterable

from netops_sentinel.aaa import NormalizedAAACondition
from netops_sentinel.core.domain import Diagnosis, RootCause
from netops_sentinel.core.evidence import Evidence, EvidenceStore
from netops_sentinel.diagnosis.rules import (
    DiagnosisFacts,
    evaluate_diagnosis_rules,
)


class DeterministicDiagnosisEngine:
    """Produce deterministic diagnoses from structured incident evidence."""

    def diagnose(
        self,
        *,
        incident_id: str,
        evidence_store: EvidenceStore,
    ) -> Diagnosis:
        """Diagnose an incident using only recorded evidence."""

        evidence = tuple(evidence_store.list_for_incident(incident_id))

        subscriber_evidence = self._latest_by_type(
            evidence,
            "subscriber_status",
        )
        session_evidence = self._latest_by_type(
            evidence,
            "online_session",
        )
        aaa_evidence = self._latest_by_type(
            evidence,
            "normalized_aaa_condition",
        )

        facts = DiagnosisFacts(
            subscriber_status=self._subscriber_status(subscriber_evidence),
            session_online=self._session_online(session_evidence),
            aaa_condition=self._aaa_condition(aaa_evidence),
        )

        result = evaluate_diagnosis_rules(facts)

        supporting_evidence_ids = self._supporting_evidence_ids(
            root_cause=result.root_cause,
            subscriber_evidence=subscriber_evidence,
            session_evidence=session_evidence,
            aaa_evidence=aaa_evidence,
        )

        return Diagnosis(
            incident_id=incident_id,
            root_cause=result.root_cause,
            summary=result.summary,
            confidence=result.confidence,
            supporting_evidence_ids=supporting_evidence_ids,
        )

    @staticmethod
    def _latest_by_type(
        evidence: Iterable[Evidence],
        evidence_type: str,
    ) -> Evidence | None:
        """Return the latest recorded evidence of a given type."""

        matching = tuple(item for item in evidence if item.evidence_type == evidence_type)

        return matching[-1] if matching else None

    @staticmethod
    def _subscriber_status(evidence: Evidence | None) -> str | None:
        """Extract subscriber account status from evidence."""

        if evidence is None:
            return None

        value = evidence.payload.get("account_status")
        return value if isinstance(value, str) else None

    @staticmethod
    def _session_online(evidence: Evidence | None) -> bool | None:
        """Extract online state without coercing malformed values."""

        if evidence is None:
            return None

        value = evidence.payload.get("online")
        return value if isinstance(value, bool) else None

    @staticmethod
    def _aaa_condition(
        evidence: Evidence | None,
    ) -> NormalizedAAACondition | None:
        """Extract a validated normalized AAA condition."""

        if evidence is None:
            return None

        value = evidence.payload.get("condition")

        if not isinstance(value, str):
            return None

        try:
            return NormalizedAAACondition(value)
        except ValueError:
            return None

    @staticmethod
    def _supporting_evidence_ids(
        *,
        root_cause: RootCause,
        subscriber_evidence: Evidence | None,
        session_evidence: Evidence | None,
        aaa_evidence: Evidence | None,
    ) -> tuple[str, ...]:
        """Select direct evidence supporting the chosen diagnosis."""

        if root_cause is RootCause.SUSPENDED:
            return (subscriber_evidence.evidence_id,) if subscriber_evidence is not None else ()

        if root_cause is RootCause.INVALID_CREDENTIALS:
            evidence = (
                subscriber_evidence,
                session_evidence,
                aaa_evidence,
            )
            return tuple(item.evidence_id for item in evidence if item is not None)

        return ()
