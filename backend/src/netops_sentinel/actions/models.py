"""Action and safety models for NetOps Sentinel."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from netops_sentinel.core.domain import (
    ActionSafetyLevel,
    NonEmptyString,
    RootCause,
    utc_now,
)


class ActionType(StrEnum):
    """Actions that NetOps Sentinel may propose."""

    REQUEST_CREDENTIAL_RESET = "request_credential_reset"
    ESCALATE_FOR_INVESTIGATION = "escalate_for_investigation"


class PolicyDecision(StrEnum):
    """Possible outcomes of the deterministic safety policy."""

    ALLOWED = "allowed"
    HUMAN_APPROVAL_REQUIRED = "human_approval_required"


class ProposedAction(BaseModel):
    """Immutable action proposed from an evidence-backed diagnosis."""

    model_config = ConfigDict(frozen=True)

    incident_id: NonEmptyString
    action_type: ActionType
    summary: NonEmptyString
    safety_level: ActionSafetyLevel
    root_cause: RootCause
    supporting_evidence_ids: tuple[NonEmptyString, ...] = ()
    created_at: datetime = Field(default_factory=utc_now)


class PolicyEvaluation(BaseModel):
    """Immutable result of evaluating an action against safety policy."""

    model_config = ConfigDict(frozen=True)

    decision: PolicyDecision
    safety_level: ActionSafetyLevel
    reason: NonEmptyString
