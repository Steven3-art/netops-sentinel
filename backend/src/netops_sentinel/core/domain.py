"""Core domain models for NetOps Sentinel."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


def utc_now() -> datetime:
    """Return the current UTC timestamp."""

    return datetime.now(UTC)


class InvestigationStatus(StrEnum):
    """Lifecycle states of an incident investigation."""

    OPEN = "open"
    INVESTIGATING = "investigating"
    WAITING_APPROVAL = "waiting_approval"
    VERIFYING_RECOVERY = "verifying_recovery"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    FAILED = "failed"


class RootCause(StrEnum):
    """Initial normalized root-cause taxonomy."""

    INVALID_CREDENTIALS = "invalid_credentials"
    BLACKLISTED = "blacklisted"
    NO_AUTHENTICATION = "no_authentication"
    SUSPENDED = "suspended"
    ACCOUNT_NOT_FOUND = "account_not_found"
    ONLINE_WITH_TRAFFIC = "online_with_traffic"
    ONLINE_NO_TRAFFIC = "online_no_traffic"
    EXTERNAL_ACCOUNT_BLOCK = "external_account_block"
    UNKNOWN = "unknown"


class ActionSafetyLevel(StrEnum):
    """Safety classification applied to agent actions."""

    LEVEL_0_READ = "level_0_read"
    LEVEL_1_RECOMMEND = "level_1_recommend"
    LEVEL_2_MUTATE = "level_2_mutate"


class Incident(BaseModel):
    """A synthetic telecom incident submitted for investigation."""

    model_config = ConfigDict(frozen=True)

    incident_id: NonEmptyString
    request: NonEmptyString
    subscriber_id: NonEmptyString | None = None
    status: InvestigationStatus = InvestigationStatus.OPEN
    created_at: datetime = Field(default_factory=utc_now)


class Diagnosis(BaseModel):
    """Evidence-backed diagnosis produced by an investigation."""

    model_config = ConfigDict(frozen=True)

    incident_id: NonEmptyString
    root_cause: RootCause
    summary: NonEmptyString
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_evidence_ids: tuple[NonEmptyString, ...] = ()
    created_at: datetime = Field(default_factory=utc_now)
