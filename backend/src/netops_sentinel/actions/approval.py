"""Explicit human approval records for controlled actions."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from netops_sentinel.actions.models import ActionType, ProposedAction
from netops_sentinel.core.domain import NonEmptyString, utc_now


class ApprovalNotFoundError(LookupError):
    """Raised when an approval record cannot be found."""


class ApprovalMismatchError(ValueError):
    """Raised when an approval does not authorize a proposed action."""


class Approval(BaseModel):
    """Immutable record of explicit human approval."""

    model_config = ConfigDict(frozen=True)

    approval_id: NonEmptyString
    incident_id: NonEmptyString
    action_type: ActionType
    approved_by: NonEmptyString
    approved_at: datetime = Field(default_factory=utc_now)


class ApprovalService:
    """Store and validate explicit human approvals."""

    def __init__(self) -> None:
        self._approvals: dict[str, Approval] = {}
        self._next_id = 1

    def approve(
        self,
        action: ProposedAction,
        *,
        approved_by: str,
    ) -> Approval:
        """Record explicit approval for a specific proposed action."""

        approval = Approval(
            approval_id=f"APR-{self._next_id:04d}",
            incident_id=action.incident_id,
            action_type=action.action_type,
            approved_by=approved_by,
        )

        self._approvals[approval.approval_id] = approval
        self._next_id += 1

        return approval

    def get(self, approval_id: str) -> Approval:
        """Return a recorded approval."""

        try:
            return self._approvals[approval_id]
        except KeyError as exc:
            raise ApprovalNotFoundError(f"Approval '{approval_id}' was not found.") from exc

    def validate(
        self,
        *,
        action: ProposedAction,
        approval: Approval,
    ) -> None:
        """Ensure an approval belongs to the exact proposed action context."""

        stored = self.get(approval.approval_id)

        if stored != approval:
            raise ApprovalMismatchError(
                "The supplied approval does not match the recorded approval."
            )

        if approval.incident_id != action.incident_id:
            raise ApprovalMismatchError("Approval incident does not match the proposed action.")

        if approval.action_type is not action.action_type:
            raise ApprovalMismatchError("Approval action type does not match the proposed action.")
