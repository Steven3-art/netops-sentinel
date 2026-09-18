"""Domain models for the synthetic Telco Digital Lab."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress

from netops_sentinel.core.domain import NonEmptyString, utc_now


class ServiceType(StrEnum):
    """Synthetic telecom service types."""

    FTTH = "ftth"


class AccountStatus(StrEnum):
    """Synthetic subscriber account states."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    DISABLED = "disabled"


class AuthenticationOutcome(StrEnum):
    """Outcome of a synthetic AAA authentication event."""

    SUCCESS = "success"
    FAILED = "failed"


class Subscriber(BaseModel):
    """Synthetic telecom subscriber."""

    model_config = ConfigDict(frozen=True)

    subscriber_id: NonEmptyString
    service: ServiceType
    account_status: AccountStatus
    bandwidth_profile: NonEmptyString


class AAAAccount(BaseModel):
    """Synthetic AAA account associated with a subscriber."""

    model_config = ConfigDict(frozen=True)

    subscriber_id: NonEmptyString
    status: AccountStatus
    authentication_enabled: bool = True


class RadiusEvent(BaseModel):
    """Synthetic RADIUS authentication event."""

    model_config = ConfigDict(frozen=True)

    event_id: NonEmptyString
    subscriber_id: NonEmptyString
    timestamp: datetime = Field(default_factory=utc_now)
    outcome: AuthenticationOutcome
    diagnostic: NonEmptyString


class Session(BaseModel):
    """Synthetic subscriber network session."""

    model_config = ConfigDict(frozen=True)

    subscriber_id: NonEmptyString
    online: bool
    ip_address: IPvAnyAddress | None = None
    started_at: datetime | None = None
    traffic_bytes: int = Field(default=0, ge=0)
