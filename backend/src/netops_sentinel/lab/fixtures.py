"""Deterministic fixtures for the synthetic Telco Digital Lab."""

from datetime import UTC, datetime, timedelta

from netops_sentinel.lab.models import (
    AAAAccount,
    AccountStatus,
    AuthenticationOutcome,
    RadiusEvent,
    ServiceType,
    Session,
    Subscriber,
)
from netops_sentinel.lab.repository import TelcoLabRepository

HERO_SUBSCRIBER_ID = "DEMO-100042"


def build_hero_invalid_credentials_lab() -> TelcoLabRepository:
    """Build the deterministic invalid-credentials hero scenario."""

    repository = TelcoLabRepository()

    repository.add_subscriber(
        Subscriber(
            subscriber_id=HERO_SUBSCRIBER_ID,
            service=ServiceType.FTTH,
            account_status=AccountStatus.ACTIVE,
            bandwidth_profile="100M/20M",
        )
    )

    repository.add_aaa_account(
        AAAAccount(
            subscriber_id=HERO_SUBSCRIBER_ID,
            status=AccountStatus.ACTIVE,
            authentication_enabled=True,
        )
    )

    repository.set_session(
        Session(
            subscriber_id=HERO_SUBSCRIBER_ID,
            online=False,
            ip_address=None,
            started_at=None,
            traffic_bytes=0,
        )
    )

    base_time = datetime(2026, 9, 17, 12, 0, tzinfo=UTC)

    for sequence in range(12):
        repository.add_radius_event(
            RadiusEvent(
                event_id=f"RAD-{sequence + 1:04d}",
                subscriber_id=HERO_SUBSCRIBER_ID,
                timestamp=base_time + timedelta(minutes=sequence),
                outcome=AuthenticationOutcome.FAILED,
                diagnostic="Invalid username or password",
            )
        )

    return repository
