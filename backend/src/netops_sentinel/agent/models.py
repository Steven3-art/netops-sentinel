"""State models for the NetOps Sentinel agent orchestrator."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from netops_sentinel.actions import Approval, ProposedAction
from netops_sentinel.core.domain import Diagnosis, NonEmptyString
from netops_sentinel.recovery import RecoveryResult


class AgentStatus(StrEnum):
    """Lifecycle states of an agent investigation."""

    CREATED = "created"
    INVESTIGATING = "investigating"
    DIAGNOSING = "diagnosing"
    RECOMMENDING = "recommending"
    WAITING_APPROVAL = "waiting_approval"
    EXECUTING = "executing"
    VERIFYING_RECOVERY = "verifying_recovery"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    FAILED = "failed"


class InvestigationState(BaseModel):
    """Immutable snapshot of an agent investigation."""

    model_config = ConfigDict(frozen=True)

    incident_id: NonEmptyString
    subscriber_id: NonEmptyString
    status: AgentStatus = AgentStatus.CREATED
    executed_tools: tuple[NonEmptyString, ...] = ()
    evidence_ids: tuple[NonEmptyString, ...] = ()
    diagnosis: Diagnosis | None = None
    proposed_action: ProposedAction | None = None
    approval: Approval | None = None
    recovery_result: RecoveryResult | None = None
    step_count: int = 0
