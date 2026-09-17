"""Unit tests for the evidence store."""

import pytest

from netops_sentinel.core.evidence import (
    DuplicateEvidenceError,
    EvidenceKind,
    EvidenceNotFoundError,
    EvidenceStore,
)


def test_store_generates_stable_evidence_ids() -> None:
    """Evidence identifiers are generated sequentially."""

    store = EvidenceStore()

    first = store.append(
        incident_id="INC-0001",
        source="subscriber.get_status",
        evidence_type="subscriber_status",
        kind=EvidenceKind.RAW,
        payload={"status": "ACTIVE"},
    )
    second = store.append(
        incident_id="INC-0001",
        source="session.get_online_session",
        evidence_type="session_state",
        kind=EvidenceKind.RAW,
        payload={"online": False},
    )

    assert first.evidence_id == "EV-0001"
    assert second.evidence_id == "EV-0002"


def test_store_lists_evidence_by_incident() -> None:
    """Incident evidence remains isolated and ordered."""

    store = EvidenceStore()

    first = store.append(
        incident_id="INC-0001",
        source="subscriber.get_status",
        evidence_type="subscriber_status",
        kind=EvidenceKind.RAW,
        payload={"status": "ACTIVE"},
    )
    store.append(
        incident_id="INC-0002",
        source="subscriber.get_status",
        evidence_type="subscriber_status",
        kind=EvidenceKind.RAW,
        payload={"status": "SUSPENDED"},
    )

    assert store.list_for_incident("INC-0001") == (first,)


def test_derived_evidence_requires_parent() -> None:
    """Derived evidence cannot exist without provenance."""

    store = EvidenceStore()

    with pytest.raises(ValueError, match="must reference parent evidence"):
        store.append(
            incident_id="INC-0001",
            source="aaa.normalizer",
            evidence_type="normalized_aaa_condition",
            kind=EvidenceKind.DERIVED,
            payload={"condition": "INVALID_CREDENTIALS"},
        )


def test_derived_evidence_can_reference_raw_evidence() -> None:
    """Derived evidence records its raw evidence provenance."""

    store = EvidenceStore()

    raw = store.append(
        incident_id="INC-0001",
        source="radius.get_failures",
        evidence_type="radius_failure",
        kind=EvidenceKind.RAW,
        payload={"message": "synthetic invalid credential failure"},
    )

    derived = store.append(
        incident_id="INC-0001",
        source="aaa.normalizer",
        evidence_type="normalized_aaa_condition",
        kind=EvidenceKind.DERIVED,
        payload={"condition": "INVALID_CREDENTIALS"},
        parent_evidence_ids=(raw.evidence_id,),
    )

    assert derived.parent_evidence_ids == ("EV-0001",)
    assert derived.evidence_id == "EV-0002"


def test_raw_evidence_cannot_have_parent() -> None:
    """Raw evidence cannot claim derivation from another record."""

    store = EvidenceStore()

    parent = store.append(
        incident_id="INC-0001",
        source="radius.get_failures",
        evidence_type="radius_failure",
        kind=EvidenceKind.RAW,
        payload={"message": "synthetic failure"},
    )

    with pytest.raises(ValueError, match="Raw evidence cannot reference"):
        store.append(
            incident_id="INC-0001",
            source="radius.get_failures",
            evidence_type="radius_failure",
            kind=EvidenceKind.RAW,
            payload={"message": "another synthetic failure"},
            parent_evidence_ids=(parent.evidence_id,),
        )


def test_derived_evidence_cannot_cross_incidents() -> None:
    """Evidence provenance cannot cross incident boundaries."""

    store = EvidenceStore()

    parent = store.append(
        incident_id="INC-0001",
        source="radius.get_failures",
        evidence_type="radius_failure",
        kind=EvidenceKind.RAW,
        payload={"message": "synthetic failure"},
    )

    with pytest.raises(ValueError, match="another incident"):
        store.append(
            incident_id="INC-0002",
            source="aaa.normalizer",
            evidence_type="normalized_aaa_condition",
            kind=EvidenceKind.DERIVED,
            payload={"condition": "INVALID_CREDENTIALS"},
            parent_evidence_ids=(parent.evidence_id,),
        )


def test_duplicate_evidence_id_is_rejected() -> None:
    """Evidence identifiers cannot be overwritten."""

    store = EvidenceStore()

    store.append(
        evidence_id="EV-CUSTOM",
        incident_id="INC-0001",
        source="subscriber.get_status",
        evidence_type="subscriber_status",
        kind=EvidenceKind.RAW,
        payload={"status": "ACTIVE"},
    )

    with pytest.raises(DuplicateEvidenceError):
        store.append(
            evidence_id="EV-CUSTOM",
            incident_id="INC-0001",
            source="subscriber.get_status",
            evidence_type="subscriber_status",
            kind=EvidenceKind.RAW,
            payload={"status": "SUSPENDED"},
        )


def test_missing_evidence_raises_domain_error() -> None:
    """Missing evidence produces an explicit store error."""

    store = EvidenceStore()

    with pytest.raises(EvidenceNotFoundError):
        store.get("EV-9999")
