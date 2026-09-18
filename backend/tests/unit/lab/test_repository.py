"""Unit tests for the Telco Digital Lab repository."""

from datetime import UTC, datetime, timedelta

import pytest

from netops_sentinel.lab import (
    AccountStatus,
    AuthenticationOutcome,
    DuplicateLabEntityError,
    LabEntityNotFoundError,
    RadiusEvent,
    ServiceType,
    Session,
    Subscriber,
    TelcoLabRepository,
)


def build_repository() -> TelcoLabRepository:
    repository = TelcoLabRepository()
    repository.add_subscriber(
        Subscriber(
            subscriber_id="DEMO-000001",
            service=ServiceType.FTTH,
            account_status=AccountStatus.ACTIVE,
            bandwidth_profile="100M/20M",
        )
    )
    return repository


def test_repository_returns_subscriber() -> None:
    repository = build_repository()

    subscriber = repository.get_subscriber("DEMO-000001")

    assert subscriber.subscriber_id == "DEMO-000001"


def test_repository_rejects_duplicate_subscriber() -> None:
    repository = build_repository()
    subscriber = repository.get_subscriber("DEMO-000001")

    with pytest.raises(DuplicateLabEntityError):
        repository.add_subscriber(subscriber)


def test_repository_raises_for_missing_subscriber() -> None:
    repository = TelcoLabRepository()

    with pytest.raises(LabEntityNotFoundError):
        repository.get_subscriber("DEMO-MISSING")


def test_repository_sets_current_session() -> None:
    repository = build_repository()

    repository.set_session(
        Session(
            subscriber_id="DEMO-000001",
            online=False,
            traffic_bytes=0,
        )
    )

    session = repository.get_session("DEMO-000001")

    assert session.online is False


def test_repository_rejects_session_for_unknown_subscriber() -> None:
    repository = TelcoLabRepository()

    with pytest.raises(LabEntityNotFoundError):
        repository.set_session(
            Session(
                subscriber_id="DEMO-MISSING",
                online=False,
            )
        )


def test_radius_events_are_returned_chronologically() -> None:
    repository = build_repository()
    base_time = datetime(2026, 9, 17, 12, 0, tzinfo=UTC)

    repository.add_radius_event(
        RadiusEvent(
            event_id="RAD-0002",
            subscriber_id="DEMO-000001",
            timestamp=base_time + timedelta(minutes=5),
            outcome=AuthenticationOutcome.FAILED,
            diagnostic="Invalid username or password",
        )
    )
    repository.add_radius_event(
        RadiusEvent(
            event_id="RAD-0001",
            subscriber_id="DEMO-000001",
            timestamp=base_time,
            outcome=AuthenticationOutcome.SUCCESS,
            diagnostic="Authentication successful",
        )
    )

    events = repository.list_radius_events("DEMO-000001")

    assert tuple(event.event_id for event in events) == (
        "RAD-0001",
        "RAD-0002",
    )


def test_radius_failures_exclude_successful_events() -> None:
    repository = build_repository()
    timestamp = datetime(2026, 9, 17, 12, 0, tzinfo=UTC)

    repository.add_radius_event(
        RadiusEvent(
            event_id="RAD-0001",
            subscriber_id="DEMO-000001",
            timestamp=timestamp,
            outcome=AuthenticationOutcome.SUCCESS,
            diagnostic="Authentication successful",
        )
    )
    repository.add_radius_event(
        RadiusEvent(
            event_id="RAD-0002",
            subscriber_id="DEMO-000001",
            timestamp=timestamp + timedelta(minutes=1),
            outcome=AuthenticationOutcome.FAILED,
            diagnostic="Invalid username or password",
        )
    )

    failures = repository.list_radius_failures("DEMO-000001")

    assert len(failures) == 1
    assert failures[0].event_id == "RAD-0002"
