"""Tests for subscriber session diagnostic tools."""

import pytest

from netops_sentinel.core.evidence import EvidenceKind, EvidenceStore
from netops_sentinel.lab import (
    HERO_SUBSCRIBER_ID,
    LabEntityNotFoundError,
    build_hero_invalid_credentials_lab,
)
from netops_sentinel.tools import OnlineSessionTool, ToolContext


def test_online_session_creates_raw_offline_evidence() -> None:
    repository = build_hero_invalid_credentials_lab()
    evidence_store = EvidenceStore()
    context = ToolContext(
        incident_id="INC-0001",
        repository=repository,
        evidence_store=evidence_store,
    )

    evidence = OnlineSessionTool().execute(
        subscriber_id=HERO_SUBSCRIBER_ID,
        context=context,
    )

    assert evidence.evidence_id == "EV-0001"
    assert evidence.incident_id == "INC-0001"
    assert evidence.kind is EvidenceKind.RAW
    assert evidence.source == "session.get_online_session"
    assert evidence.evidence_type == "online_session"

    assert evidence.payload == {
        "subscriber_id": HERO_SUBSCRIBER_ID,
        "online": False,
        "ip_address": None,
        "started_at": None,
        "traffic_bytes": 0,
    }


def test_online_session_is_recorded_in_evidence_store() -> None:
    repository = build_hero_invalid_credentials_lab()
    evidence_store = EvidenceStore()
    context = ToolContext(
        incident_id="INC-0001",
        repository=repository,
        evidence_store=evidence_store,
    )

    evidence = OnlineSessionTool().execute(
        subscriber_id=HERO_SUBSCRIBER_ID,
        context=context,
    )

    assert evidence_store.get(evidence.evidence_id) == evidence


def test_online_session_propagates_missing_session() -> None:
    repository = build_hero_invalid_credentials_lab()

    with pytest.raises(LabEntityNotFoundError):
        OnlineSessionTool().execute(
            subscriber_id="DEMO-MISSING",
            context=ToolContext(
                incident_id="INC-0001",
                repository=repository,
                evidence_store=EvidenceStore(),
            ),
        )
