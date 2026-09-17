"""Unit tests for core domain models."""

import pytest
from pydantic import ValidationError

from netops_sentinel.core.domain import (
    ActionSafetyLevel,
    Diagnosis,
    Incident,
    InvestigationStatus,
    RootCause,
)


def test_incident_uses_safe_initial_status() -> None:
    """New incidents start in the open state."""

    incident = Incident(
        incident_id="INC-0001",
        request="Check connectivity for DEMO-100042.",
        subscriber_id="DEMO-100042",
    )

    assert incident.status is InvestigationStatus.OPEN


def test_incident_rejects_blank_request() -> None:
    """Incident requests cannot be blank."""

    with pytest.raises(ValidationError):
        Incident(
            incident_id="INC-0001",
            request="   ",
        )


def test_diagnosis_requires_valid_confidence() -> None:
    """Diagnosis confidence must remain between zero and one."""

    with pytest.raises(ValidationError):
        Diagnosis(
            incident_id="INC-0001",
            root_cause=RootCause.INVALID_CREDENTIALS,
            summary="Authentication failed because of invalid credentials.",
            confidence=1.1,
            supporting_evidence_ids=("EV-0001",),
        )


def test_diagnosis_can_reference_supporting_evidence() -> None:
    """A diagnosis can explicitly cite its supporting evidence."""

    diagnosis = Diagnosis(
        incident_id="INC-0001",
        root_cause=RootCause.INVALID_CREDENTIALS,
        summary="Authentication failed because of invalid credentials.",
        confidence=0.97,
        supporting_evidence_ids=("EV-0001", "EV-0002"),
    )

    assert diagnosis.supporting_evidence_ids == ("EV-0001", "EV-0002")


def test_mutating_actions_have_explicit_safety_level() -> None:
    """The domain exposes a distinct safety level for mutations."""

    assert ActionSafetyLevel.LEVEL_2_MUTATE.value == "level_2_mutate"
