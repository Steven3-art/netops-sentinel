"""Tests for the explicit agent orchestrator."""

import pytest

from netops_sentinel.actions import ApprovalService
from netops_sentinel.agent import (
    AgentOrchestrationError,
    AgentOrchestrator,
    AgentStatus,
)
from netops_sentinel.core.domain import Incident, RootCause
from netops_sentinel.core.evidence import EvidenceStore
from netops_sentinel.lab import (
    HERO_SUBSCRIBER_ID,
    build_hero_invalid_credentials_lab,
)


def build_orchestrator() -> tuple[AgentOrchestrator, ApprovalService]:
    """Build an orchestrator backed by the deterministic hero lab."""

    approval_service = ApprovalService()

    orchestrator = AgentOrchestrator(
        repository=build_hero_invalid_credentials_lab(),
        evidence_store=EvidenceStore(),
        approval_service=approval_service,
    )

    return orchestrator, approval_service


def test_investigation_stops_at_human_approval_boundary() -> None:
    orchestrator, _ = build_orchestrator()

    state = orchestrator.investigate(
        incident=Incident(
            incident_id="INC-HERO-0001",
            request="Subscriber has no Internet access.",
            subscriber_id=HERO_SUBSCRIBER_ID,
        ),
        subscriber_id=HERO_SUBSCRIBER_ID,
    )

    assert state.status is AgentStatus.WAITING_APPROVAL
    assert state.diagnosis is not None
    assert state.diagnosis.root_cause is RootCause.INVALID_CREDENTIALS
    assert state.proposed_action is not None
    assert state.executed_tools == (
        "subscriber.get_status",
        "session.get_online_session",
        "radius.get_failures",
    )


def test_resume_requires_waiting_approval_state() -> None:
    orchestrator, approval_service = build_orchestrator()

    waiting_state = orchestrator.investigate(
        incident=Incident(
            incident_id="INC-HERO-0001",
            request="Subscriber has no Internet access.",
            subscriber_id=HERO_SUBSCRIBER_ID,
        ),
        subscriber_id=HERO_SUBSCRIBER_ID,
    )

    assert waiting_state.proposed_action is not None

    approval = approval_service.approve(
        waiting_state.proposed_action,
        approved_by="demo-operator",
    )

    invalid_state = waiting_state.model_copy(update={"status": AgentStatus.RESOLVED})

    with pytest.raises(AgentOrchestrationError):
        orchestrator.resume_after_approval(
            state=invalid_state,
            approval=approval,
        )
