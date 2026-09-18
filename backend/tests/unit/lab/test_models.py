"""Unit tests for Telco Digital Lab models."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from netops_sentinel.lab import (
    AccountStatus,
    AuthenticationOutcome,
    RadiusEvent,
    ServiceType,
    Session,
    Subscriber,
)


def test_subscriber_is_created_with_synthetic_service_state() -> None:
    subscriber = Subscriber(
        subscriber_id="DEMO-000001",
        service=ServiceType.FTTH,
        account_status=AccountStatus.ACTIVE,
        bandwidth_profile="100M/20M",
    )

    assert subscriber.subscriber_id == "DEMO-000001"
    assert subscriber.service is ServiceType.FTTH
    assert subscriber.account_status is AccountStatus.ACTIVE


def test_subscriber_rejects_blank_identifier() -> None:
    with pytest.raises(ValidationError):
        Subscriber(
            subscriber_id=" ",
            service=ServiceType.FTTH,
            account_status=AccountStatus.ACTIVE,
            bandwidth_profile="100M/20M",
        )


def test_session_rejects_negative_traffic() -> None:
    with pytest.raises(ValidationError):
        Session(
            subscriber_id="DEMO-000001",
            online=True,
            ip_address="198.51.100.42",
            started_at=datetime(2026, 9, 17, 12, 0, tzinfo=UTC),
            traffic_bytes=-1,
        )


def test_radius_event_preserves_deterministic_timestamp() -> None:
    timestamp = datetime(2026, 9, 17, 12, 0, tzinfo=UTC)

    event = RadiusEvent(
        event_id="RAD-0001",
        subscriber_id="DEMO-000001",
        timestamp=timestamp,
        outcome=AuthenticationOutcome.FAILED,
        diagnostic="Invalid username or password",
    )

    assert event.timestamp == timestamp
