"""Tests for deterministic Telco Digital Lab fixtures."""

from netops_sentinel.lab import (
    HERO_SUBSCRIBER_ID,
    AccountStatus,
    AuthenticationOutcome,
    ServiceType,
    build_hero_invalid_credentials_lab,
)


def test_hero_scenario_has_active_ftth_subscriber() -> None:
    repository = build_hero_invalid_credentials_lab()

    subscriber = repository.get_subscriber(HERO_SUBSCRIBER_ID)

    assert subscriber.service is ServiceType.FTTH
    assert subscriber.account_status is AccountStatus.ACTIVE
    assert subscriber.bandwidth_profile == "100M/20M"


def test_hero_scenario_has_enabled_active_aaa_account() -> None:
    repository = build_hero_invalid_credentials_lab()

    account = repository.get_aaa_account(HERO_SUBSCRIBER_ID)

    assert account.status is AccountStatus.ACTIVE
    assert account.authentication_enabled is True


def test_hero_scenario_is_offline() -> None:
    repository = build_hero_invalid_credentials_lab()

    session = repository.get_session(HERO_SUBSCRIBER_ID)

    assert session.online is False
    assert session.ip_address is None
    assert session.traffic_bytes == 0


def test_hero_scenario_has_twelve_failed_authentications() -> None:
    repository = build_hero_invalid_credentials_lab()

    failures = repository.list_radius_failures(HERO_SUBSCRIBER_ID)

    assert len(failures) == 12
    assert all(event.outcome is AuthenticationOutcome.FAILED for event in failures)
    assert all(event.diagnostic == "Invalid username or password" for event in failures)


def test_hero_scenario_is_deterministic() -> None:
    first = build_hero_invalid_credentials_lab()
    second = build_hero_invalid_credentials_lab()

    assert first.get_subscriber(HERO_SUBSCRIBER_ID) == second.get_subscriber(HERO_SUBSCRIBER_ID)
    assert first.get_session(HERO_SUBSCRIBER_ID) == second.get_session(HERO_SUBSCRIBER_ID)
    assert first.list_radius_events(HERO_SUBSCRIBER_ID) == second.list_radius_events(
        HERO_SUBSCRIBER_ID
    )
