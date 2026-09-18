"""Tests for controlled synthetic action execution."""

import pytest

from netops_sentinel.actions import (
    ActionExecutionError,
    ActionType,
    ApprovalService,
    ControlledActionExecutor,
    ProposedAction,
    SafetyPolicy,
)
from netops_sentinel.core.domain import ActionSafetyLevel, RootCause
from netops_sentinel.core.evidence import EvidenceStore
from netops_sentinel.lab import (
    HERO_SUBSCRIBER_ID,
    build_hero_invalid_credentials_lab,
)


def build_action(
    action_type: ActionType = ActionType.REQUEST_CREDENTIAL_RESET,
) -> ProposedAction:
    """Build a deterministic action for execution tests."""

    return ProposedAction(
        incident_id="INC-0001",
        action_type=action_type,
        summary="Test action.",
        safety_level=ActionSafetyLevel.LEVEL_2_MUTATE,
        root_cause=RootCause.INVALID_CREDENTIALS,
    )


def test_approved_credential_reset_changes_synthetic_state() -> None:
    repository = build_hero_invalid_credentials_lab()
    evidence_store = EvidenceStore()
    approval_service = ApprovalService()
    action = build_action()

    approval = approval_service.approve(
        action,
        approved_by="demo-operator",
    )

    evidence = ControlledActionExecutor(
        approval_service=approval_service,
        safety_policy=SafetyPolicy(),
    ).execute(
        action=action,
        approval=approval,
        subscriber_id=HERO_SUBSCRIBER_ID,
        repository=repository,
        evidence_store=evidence_store,
    )

    assert evidence.source == "credentials.execute_reset"
    assert evidence.payload["status"] == "success"

    session = repository.get_session(HERO_SUBSCRIBER_ID)
    assert session.online is True
    assert session.traffic_bytes == 4096

    events = repository.list_radius_events(HERO_SUBSCRIBER_ID)
    assert events[-1].outcome.value == "success"


def test_executor_rejects_unsupported_mutation() -> None:
    repository = build_hero_invalid_credentials_lab()
    approval_service = ApprovalService()

    action = build_action(ActionType.ESCALATE_FOR_INVESTIGATION)
    approval = approval_service.approve(
        action,
        approved_by="demo-operator",
    )

    with pytest.raises(ActionExecutionError):
        ControlledActionExecutor(
            approval_service=approval_service,
            safety_policy=SafetyPolicy(),
        ).execute(
            action=action,
            approval=approval,
            subscriber_id=HERO_SUBSCRIBER_ID,
            repository=repository,
            evidence_store=EvidenceStore(),
        )
