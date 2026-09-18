"""Tests for subscriber diagnostic tools."""

import pytest

from netops_sentinel.core.evidence import EvidenceKind, EvidenceStore
from netops_sentinel.lab import (
    HERO_SUBSCRIBER_ID,
    LabEntityNotFoundError,
    build_hero_invalid_credentials_lab,
)
from netops_sentinel.tools import SubscriberStatusTool, ToolContext


def test_subscriber_status_creates_raw_evidence() -> None:
    repository = build_hero_invalid_credentials_lab()
    evidence_store = EvidenceStore()
    context = ToolContext(
        incident_id="INC-0001",
        repository=repository,
        evidence_store=evidence_store,
    )

    evidence = SubscriberStatusTool().execute(
        subscriber_id=HERO_SUBSCRIBER_ID,
        context=context,
    )

    assert evidence.evidence_id == "EV-0001"
    assert evidence.incident_id == "INC-0001"
    assert evidence.kind is EvidenceKind.RAW
    assert evidence.source == "subscriber.get_status"
    assert evidence.evidence_type == "subscriber_status"
    assert evidence.payload["subscriber_id"] == HERO_SUBSCRIBER_ID
    assert evidence.payload["service"] == "ftth"
    assert evidence.payload["account_status"] == "active"
    assert evidence.payload["bandwidth_profile"] == "100M/20M"


def test_subscriber_status_is_recorded_in_evidence_store() -> None:
    repository = build_hero_invalid_credentials_lab()
    evidence_store = EvidenceStore()
    context = ToolContext(
        incident_id="INC-0001",
        repository=repository,
        evidence_store=evidence_store,
    )

    evidence = SubscriberStatusTool().execute(
        subscriber_id=HERO_SUBSCRIBER_ID,
        context=context,
    )

    assert evidence_store.get(evidence.evidence_id) == evidence


def test_subscriber_status_propagates_missing_subscriber() -> None:
    context = ToolContext(
        incident_id="INC-0001",
        repository=build_hero_invalid_credentials_lab(),
        evidence_store=EvidenceStore(),
    )

    with pytest.raises(LabEntityNotFoundError):
        SubscriberStatusTool().execute(
            subscriber_id="DEMO-MISSING",
            context=context,
        )
