"""Unit tests for AAA evidence derivation."""

import pytest

from netops_sentinel.aaa.evidence import (
    AAAEvidenceProcessor,
    InvalidAAAEvidenceError,
)
from netops_sentinel.core.evidence import EvidenceKind, EvidenceStore


def test_processor_creates_derived_evidence_with_provenance() -> None:
    """Normalized AAA evidence references its raw source evidence."""

    store = EvidenceStore()
    processor = AAAEvidenceProcessor()

    raw = store.append(
        incident_id="INC-0001",
        source="radius.get_failures",
        evidence_type="aaa_diagnostic",
        kind=EvidenceKind.RAW,
        payload={"message": "Invalid username or password"},
    )

    derived = processor.process(raw, store)

    assert raw.evidence_id == "EV-0001"
    assert derived.evidence_id == "EV-0002"
    assert derived.kind is EvidenceKind.DERIVED
    assert derived.source == "aaa.normalizer"
    assert derived.evidence_type == "normalized_aaa_condition"
    assert derived.parent_evidence_ids == ("EV-0001",)
    assert derived.payload["condition"] == "invalid_credentials"
    assert derived.payload["matched_rule"] == "aaa.invalid_credentials"


def test_processor_preserves_unknown_condition() -> None:
    """Unknown diagnostics remain explicit derived evidence."""

    store = EvidenceStore()
    processor = AAAEvidenceProcessor()

    raw = store.append(
        incident_id="INC-0001",
        source="radius.get_failures",
        evidence_type="aaa_diagnostic",
        kind=EvidenceKind.RAW,
        payload={"message": "Synthetic unrecognized AAA response"},
    )

    derived = processor.process(raw, store)

    assert derived.payload["condition"] == "unknown"
    assert derived.payload["matched_rule"] is None
    assert derived.parent_evidence_ids == (raw.evidence_id,)


def test_processor_rejects_derived_input() -> None:
    """The processor only accepts raw AAA evidence."""

    store = EvidenceStore()
    processor = AAAEvidenceProcessor()

    raw = store.append(
        incident_id="INC-0001",
        source="radius.get_failures",
        evidence_type="aaa_diagnostic",
        kind=EvidenceKind.RAW,
        payload={"message": "Account suspended"},
    )

    derived = processor.process(raw, store)

    with pytest.raises(
        InvalidAAAEvidenceError,
        match="must be raw evidence",
    ):
        processor.process(derived, store)


def test_processor_rejects_wrong_evidence_type() -> None:
    """Unrelated raw evidence cannot enter the AAA normalization pipeline."""

    store = EvidenceStore()
    processor = AAAEvidenceProcessor()

    raw = store.append(
        incident_id="INC-0001",
        source="qos.get_metrics",
        evidence_type="qos_metrics",
        kind=EvidenceKind.RAW,
        payload={"message": "Account suspended"},
    )

    with pytest.raises(
        InvalidAAAEvidenceError,
        match="Expected evidence type",
    ):
        processor.process(raw, store)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"message": ""},
        {"message": "   "},
        {"message": 123},
        {"message": None},
    ],
)
def test_processor_rejects_invalid_message_payload(
    payload: dict[str, object],
) -> None:
    """AAA diagnostic evidence requires a non-empty string message."""

    store = EvidenceStore()
    processor = AAAEvidenceProcessor()

    raw = store.append(
        incident_id="INC-0001",
        source="radius.get_failures",
        evidence_type="aaa_diagnostic",
        kind=EvidenceKind.RAW,
        payload=payload,
    )

    with pytest.raises(
        InvalidAAAEvidenceError,
        match="non-empty string",
    ):
        processor.process(raw, store)


def test_derived_evidence_is_registered_in_incident_history() -> None:
    """Raw and derived evidence remain visible in investigation order."""

    store = EvidenceStore()
    processor = AAAEvidenceProcessor()

    raw = store.append(
        incident_id="INC-0001",
        source="radius.get_failures",
        evidence_type="aaa_diagnostic",
        kind=EvidenceKind.RAW,
        payload={"message": "Subscriber blacklisted"},
    )

    derived = processor.process(raw, store)

    history = store.list_for_incident("INC-0001")

    assert history == (raw, derived)
