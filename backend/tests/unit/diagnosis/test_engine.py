"""Unit tests for the deterministic diagnosis engine."""

from netops_sentinel.core.domain import RootCause
from netops_sentinel.core.evidence import EvidenceKind, EvidenceStore
from netops_sentinel.diagnosis import DeterministicDiagnosisEngine


def test_engine_returns_unknown_without_evidence() -> None:
    diagnosis = DeterministicDiagnosisEngine().diagnose(
        incident_id="INC-0001",
        evidence_store=EvidenceStore(),
    )

    assert diagnosis.root_cause is RootCause.UNKNOWN
    assert diagnosis.confidence == 0.0
    assert diagnosis.supporting_evidence_ids == ()


def test_engine_diagnoses_suspended_account() -> None:
    evidence_store = EvidenceStore()

    subscriber = evidence_store.append(
        incident_id="INC-0001",
        kind=EvidenceKind.RAW,
        source="subscriber.get_status",
        evidence_type="subscriber_status",
        payload={
            "subscriber_id": "DEMO-000001",
            "account_status": "suspended",
        },
    )

    diagnosis = DeterministicDiagnosisEngine().diagnose(
        incident_id="INC-0001",
        evidence_store=evidence_store,
    )

    assert diagnosis.root_cause is RootCause.SUSPENDED
    assert diagnosis.confidence == 1.0
    assert diagnosis.supporting_evidence_ids == (subscriber.evidence_id,)


def test_engine_does_not_infer_invalid_credentials_without_aaa_evidence() -> None:
    evidence_store = EvidenceStore()

    evidence_store.append(
        incident_id="INC-0001",
        kind=EvidenceKind.RAW,
        source="subscriber.get_status",
        evidence_type="subscriber_status",
        payload={"account_status": "active"},
    )
    evidence_store.append(
        incident_id="INC-0001",
        kind=EvidenceKind.RAW,
        source="session.get_online_session",
        evidence_type="online_session",
        payload={"online": False},
    )

    diagnosis = DeterministicDiagnosisEngine().diagnose(
        incident_id="INC-0001",
        evidence_store=evidence_store,
    )

    assert diagnosis.root_cause is RootCause.UNKNOWN
    assert diagnosis.supporting_evidence_ids == ()


def test_engine_uses_latest_relevant_evidence() -> None:
    evidence_store = EvidenceStore()

    evidence_store.append(
        incident_id="INC-0001",
        kind=EvidenceKind.RAW,
        source="subscriber.get_status",
        evidence_type="subscriber_status",
        payload={"account_status": "suspended"},
    )
    latest = evidence_store.append(
        incident_id="INC-0001",
        kind=EvidenceKind.RAW,
        source="subscriber.get_status",
        evidence_type="subscriber_status",
        payload={"account_status": "active"},
    )

    diagnosis = DeterministicDiagnosisEngine().diagnose(
        incident_id="INC-0001",
        evidence_store=evidence_store,
    )

    assert diagnosis.root_cause is RootCause.UNKNOWN
    assert latest.evidence_id == "EV-0002"


def test_engine_ignores_evidence_from_other_incidents() -> None:
    evidence_store = EvidenceStore()

    evidence_store.append(
        incident_id="INC-OTHER",
        kind=EvidenceKind.RAW,
        source="subscriber.get_status",
        evidence_type="subscriber_status",
        payload={"account_status": "suspended"},
    )

    diagnosis = DeterministicDiagnosisEngine().diagnose(
        incident_id="INC-0001",
        evidence_store=evidence_store,
    )

    assert diagnosis.root_cause is RootCause.UNKNOWN
