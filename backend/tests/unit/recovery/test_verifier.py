"""Tests for evidence-based recovery verification."""

from netops_sentinel.core.evidence import EvidenceKind, EvidenceStore
from netops_sentinel.recovery import RecoveryStatus, RecoveryVerifier


def test_recovery_requires_online_traffic_and_successful_authentication() -> None:
    store = EvidenceStore()

    session = store.append(
        incident_id="INC-0001",
        kind=EvidenceKind.RAW,
        source="session.get_online_session",
        evidence_type="online_session",
        payload={
            "online": True,
            "traffic_bytes": 4096,
        },
    )

    authentication = store.append(
        incident_id="INC-0001",
        kind=EvidenceKind.RAW,
        source="auth.get_state",
        evidence_type="authentication_state",
        payload={"outcome": "success"},
    )

    result = RecoveryVerifier().verify(
        session_evidence=session,
        authentication_evidence=authentication,
    )

    assert result.status is RecoveryStatus.RECOVERED
    assert result.supporting_evidence_ids == ("EV-0001", "EV-0002")


def test_online_without_traffic_is_not_recovered() -> None:
    store = EvidenceStore()

    session = store.append(
        incident_id="INC-0001",
        kind=EvidenceKind.RAW,
        source="session.get_online_session",
        evidence_type="online_session",
        payload={
            "online": True,
            "traffic_bytes": 0,
        },
    )

    authentication = store.append(
        incident_id="INC-0001",
        kind=EvidenceKind.RAW,
        source="auth.get_state",
        evidence_type="authentication_state",
        payload={"outcome": "success"},
    )

    result = RecoveryVerifier().verify(
        session_evidence=session,
        authentication_evidence=authentication,
    )

    assert result.status is RecoveryStatus.NOT_RECOVERED
    assert result.supporting_evidence_ids == ()
