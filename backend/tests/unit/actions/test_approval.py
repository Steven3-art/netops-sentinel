"""Tests for explicit human approval records."""

import pytest

from netops_sentinel.actions import (
    ActionType,
    ApprovalMismatchError,
    ApprovalNotFoundError,
    ApprovalService,
    ProposedAction,
)
from netops_sentinel.core.domain import ActionSafetyLevel, RootCause


def build_action(
    *,
    incident_id: str = "INC-0001",
    action_type: ActionType = ActionType.REQUEST_CREDENTIAL_RESET,
) -> ProposedAction:
    """Build a deterministic proposed action."""

    return ProposedAction(
        incident_id=incident_id,
        action_type=action_type,
        summary="Test action.",
        safety_level=ActionSafetyLevel.LEVEL_2_MUTATE,
        root_cause=RootCause.INVALID_CREDENTIALS,
    )


def test_approval_is_recorded() -> None:
    service = ApprovalService()
    action = build_action()

    approval = service.approve(
        action,
        approved_by="demo-operator",
    )

    assert approval.approval_id == "APR-0001"
    assert approval.incident_id == action.incident_id
    assert approval.action_type is action.action_type
    assert approval.approved_by == "demo-operator"
    assert service.get("APR-0001") == approval


def test_missing_approval_is_rejected() -> None:
    service = ApprovalService()

    with pytest.raises(ApprovalNotFoundError):
        service.get("APR-MISSING")


def test_approval_cannot_authorize_another_incident() -> None:
    service = ApprovalService()

    approval = service.approve(
        build_action(incident_id="INC-0001"),
        approved_by="demo-operator",
    )

    with pytest.raises(ApprovalMismatchError):
        service.validate(
            action=build_action(incident_id="INC-0002"),
            approval=approval,
        )


def test_approval_cannot_authorize_another_action_type() -> None:
    service = ApprovalService()

    approval = service.approve(
        build_action(),
        approved_by="demo-operator",
    )

    with pytest.raises(ApprovalMismatchError):
        service.validate(
            action=build_action(action_type=ActionType.ESCALATE_FOR_INVESTIGATION),
            approval=approval,
        )
