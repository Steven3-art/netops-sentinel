"""Tests for RADIUS diagnostic tools."""

from datetime import UTC, datetime, timedelta

from netops_sentinel.aaa import (
    AAAEvidenceProcessor,
    NormalizedAAACondition,
)
from netops_sentinel.core.evidence import EvidenceKind, EvidenceStore
from netops_sentinel.lab import (
    HERO_SUBSCRIBER_ID,
    AccountStatus,
    AuthenticationOutcome,
    RadiusEvent,
    ServiceType,
    Subscriber,
    TelcoLabRepository,
    build_hero_invalid_credentials_lab,
)
from netops_sentinel.tools import RadiusFailuresTool, ToolContext


def test_radius_failures_creates_raw_aaa_evidence() -> None:
    repository = build_hero_invalid_credentials_lab()
    evidence_store = EvidenceStore()
    context = ToolContext(
        incident_id="INC-0001",
        repository=repository,
        evidence_store=evidence_store,
    )

    evidence = RadiusFailuresTool().execute(
        subscriber_id=HERO_SUBSCRIBER_ID,
        context=context,
    )

    assert evidence.kind is EvidenceKind.RAW
    assert evidence.source == "radius.get_failures"
    assert evidence.evidence_type == "aaa_diagnostic"
    assert evidence.payload["subscriber_id"] == HERO_SUBSCRIBER_ID
    assert evidence.payload["failure_count"] == 12
    assert evidence.payload["latest_event_id"] == "RAD-0012"
    assert evidence.payload["message"] == "Invalid username or password"


def test_radius_failures_selects_latest_failure() -> None:
    repository = TelcoLabRepository()
    repository.add_subscriber(
        Subscriber(
            subscriber_id="DEMO-000001",
            service=ServiceType.FTTH,
            account_status=AccountStatus.ACTIVE,
            bandwidth_profile="100M/20M",
        )
    )

    base_time = datetime(2026, 9, 17, 12, 0, tzinfo=UTC)

    repository.add_radius_event(
        RadiusEvent(
            event_id="RAD-OLD",
            subscriber_id="DEMO-000001",
            timestamp=base_time,
            outcome=AuthenticationOutcome.FAILED,
            diagnostic="No authentication attempt",
        )
    )
    repository.add_radius_event(
        RadiusEvent(
            event_id="RAD-LATEST",
            subscriber_id="DEMO-000001",
            timestamp=base_time + timedelta(minutes=10),
            outcome=AuthenticationOutcome.FAILED,
            diagnostic="Invalid username or password",
        )
    )

    evidence = RadiusFailuresTool().execute(
        subscriber_id="DEMO-000001",
        context=ToolContext(
            incident_id="INC-0001",
            repository=repository,
            evidence_store=EvidenceStore(),
        ),
    )

    assert evidence.payload["failure_count"] == 2
    assert evidence.payload["latest_event_id"] == "RAD-LATEST"
    assert evidence.payload["message"] == "Invalid username or password"


def test_radius_failures_handles_no_failed_authentication() -> None:
    repository = TelcoLabRepository()
    repository.add_subscriber(
        Subscriber(
            subscriber_id="DEMO-000001",
            service=ServiceType.FTTH,
            account_status=AccountStatus.ACTIVE,
            bandwidth_profile="100M/20M",
        )
    )

    evidence = RadiusFailuresTool().execute(
        subscriber_id="DEMO-000001",
        context=ToolContext(
            incident_id="INC-0001",
            repository=repository,
            evidence_store=EvidenceStore(),
        ),
    )

    assert evidence.payload["failure_count"] == 0
    assert evidence.payload["latest_event_id"] is None
    assert evidence.payload["latest_timestamp"] is None
    assert evidence.payload["message"] == "No failed authentication event"


def test_radius_evidence_flows_through_aaa_normalizer() -> None:
    repository = build_hero_invalid_credentials_lab()
    evidence_store = EvidenceStore()
    context = ToolContext(
        incident_id="INC-0001",
        repository=repository,
        evidence_store=evidence_store,
    )

    raw_evidence = RadiusFailuresTool().execute(
        subscriber_id=HERO_SUBSCRIBER_ID,
        context=context,
    )

    derived_evidence = AAAEvidenceProcessor().process(
        raw_evidence=raw_evidence,
        evidence_store=evidence_store,
    )

    assert raw_evidence.evidence_id == "EV-0001"
    assert derived_evidence.evidence_id == "EV-0002"
    assert derived_evidence.kind is EvidenceKind.DERIVED
    assert derived_evidence.parent_evidence_ids == (raw_evidence.evidence_id,)
    assert derived_evidence.payload["condition"] == NormalizedAAACondition.INVALID_CREDENTIALS.value
