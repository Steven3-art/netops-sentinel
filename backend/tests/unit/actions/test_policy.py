"""Tests for deterministic action safety policy."""

from netops_sentinel.actions import (
    ActionType,
    PolicyDecision,
    ProposedAction,
    SafetyPolicy,
)
from netops_sentinel.core.domain import ActionSafetyLevel, RootCause


def build_action(
    safety_level: ActionSafetyLevel,
) -> ProposedAction:
    """Build a deterministic proposed action for policy tests."""

    return ProposedAction(
        incident_id="INC-0001",
        action_type=ActionType.ESCALATE_FOR_INVESTIGATION,
        summary="Test action.",
        safety_level=safety_level,
        root_cause=RootCause.UNKNOWN,
    )


def test_read_action_is_allowed_without_approval() -> None:
    evaluation = SafetyPolicy().evaluate(build_action(ActionSafetyLevel.LEVEL_0_READ))

    assert evaluation.decision is PolicyDecision.ALLOWED


def test_recommendation_is_allowed_without_approval() -> None:
    evaluation = SafetyPolicy().evaluate(build_action(ActionSafetyLevel.LEVEL_1_RECOMMEND))

    assert evaluation.decision is PolicyDecision.ALLOWED


def test_mutation_requires_explicit_human_approval() -> None:
    evaluation = SafetyPolicy().evaluate(build_action(ActionSafetyLevel.LEVEL_2_MUTATE))

    assert evaluation.decision is PolicyDecision.HUMAN_APPROVAL_REQUIRED
    assert evaluation.safety_level is ActionSafetyLevel.LEVEL_2_MUTATE


def test_approved_mutation_is_allowed() -> None:
    evaluation = SafetyPolicy().evaluate(
        build_action(ActionSafetyLevel.LEVEL_2_MUTATE),
        approved=True,
    )

    assert evaluation.decision is PolicyDecision.ALLOWED
    assert "approval" in evaluation.reason.lower()
