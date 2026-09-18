"""Tests for deterministic action recommendations."""

from netops_sentinel.actions import (
    ActionRecommendationEngine,
    ActionType,
)
from netops_sentinel.core.domain import (
    ActionSafetyLevel,
    Diagnosis,
    RootCause,
)


def test_invalid_credentials_recommends_credential_reset() -> None:
    diagnosis = Diagnosis(
        incident_id="INC-0001",
        root_cause=RootCause.INVALID_CREDENTIALS,
        summary="Invalid credentials detected.",
        confidence=1.0,
        supporting_evidence_ids=("EV-0001", "EV-0002", "EV-0004"),
    )

    action = ActionRecommendationEngine().recommend(diagnosis)

    assert action.incident_id == "INC-0001"
    assert action.action_type is ActionType.REQUEST_CREDENTIAL_RESET
    assert action.safety_level is ActionSafetyLevel.LEVEL_2_MUTATE
    assert action.root_cause is RootCause.INVALID_CREDENTIALS
    assert action.supporting_evidence_ids == (
        "EV-0001",
        "EV-0002",
        "EV-0004",
    )


def test_uncertain_invalid_credentials_does_not_recommend_mutation() -> None:
    diagnosis = Diagnosis(
        incident_id="INC-0001",
        root_cause=RootCause.INVALID_CREDENTIALS,
        summary="Possible invalid credentials.",
        confidence=0.8,
        supporting_evidence_ids=("EV-0001",),
    )

    action = ActionRecommendationEngine().recommend(diagnosis)

    assert action.action_type is ActionType.ESCALATE_FOR_INVESTIGATION
    assert action.safety_level is ActionSafetyLevel.LEVEL_1_RECOMMEND


def test_unknown_diagnosis_recommends_investigation() -> None:
    diagnosis = Diagnosis(
        incident_id="INC-0001",
        root_cause=RootCause.UNKNOWN,
        summary="Insufficient evidence.",
        confidence=0.0,
    )

    action = ActionRecommendationEngine().recommend(diagnosis)

    assert action.action_type is ActionType.ESCALATE_FOR_INVESTIGATION
    assert action.safety_level is ActionSafetyLevel.LEVEL_1_RECOMMEND
    assert action.root_cause is RootCause.UNKNOWN
