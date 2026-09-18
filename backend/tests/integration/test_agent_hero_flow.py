"""End-to-end test for the agent-orchestrated hero scenario."""

from netops_sentinel.actions import (
    ActionType,
    ApprovalService,
)
from netops_sentinel.agent import AgentOrchestrator, AgentStatus
from netops_sentinel.core.domain import Incident, RootCause
from netops_sentinel.core.evidence import EvidenceStore
from netops_sentinel.lab import (
    HERO_SUBSCRIBER_ID,
    build_hero_invalid_credentials_lab,
)
from netops_sentinel.recovery import RecoveryStatus


def test_agent_orchestrates_hero_scenario_to_recovery() -> None:
    repository = build_hero_invalid_credentials_lab()
    evidence_store = EvidenceStore()
    approval_service = ApprovalService()

    orchestrator = AgentOrchestrator(
        repository=repository,
        evidence_store=evidence_store,
        approval_service=approval_service,
    )

    incident = Incident(
        incident_id="INC-HERO-0001",
        request=("Customer DEMO-100042 has no Internet access. All ONT indicators appear normal."),
        subscriber_id=HERO_SUBSCRIBER_ID,
    )

    waiting_state = orchestrator.investigate(
        incident=incident,
        subscriber_id=HERO_SUBSCRIBER_ID,
    )

    assert waiting_state.status is AgentStatus.WAITING_APPROVAL
    assert waiting_state.diagnosis is not None
    assert waiting_state.diagnosis.root_cause is RootCause.INVALID_CREDENTIALS

    assert waiting_state.proposed_action is not None
    assert waiting_state.proposed_action.action_type is ActionType.REQUEST_CREDENTIAL_RESET

    assert waiting_state.executed_tools == (
        "subscriber.get_status",
        "session.get_online_session",
        "radius.get_failures",
    )

    assert waiting_state.evidence_ids == (
        "EV-0001",
        "EV-0002",
        "EV-0003",
        "EV-0004",
    )

    assert repository.get_session(HERO_SUBSCRIBER_ID).online is False

    approval = approval_service.approve(
        waiting_state.proposed_action,
        approved_by="demo-operator",
    )

    resolved_state = orchestrator.resume_after_approval(
        state=waiting_state,
        approval=approval,
    )

    assert resolved_state.status is AgentStatus.RESOLVED
    assert resolved_state.approval == approval

    assert resolved_state.recovery_result is not None
    assert resolved_state.recovery_result.status is RecoveryStatus.RECOVERED

    assert resolved_state.evidence_ids == (
        "EV-0001",
        "EV-0002",
        "EV-0003",
        "EV-0004",
        "EV-0005",
        "EV-0006",
        "EV-0007",
    )

    assert resolved_state.executed_tools == (
        "subscriber.get_status",
        "session.get_online_session",
        "radius.get_failures",
        "session.get_online_session",
        "auth.get_state",
    )

    assert repository.get_session(HERO_SUBSCRIBER_ID).online is True
    assert repository.get_session(HERO_SUBSCRIBER_ID).traffic_bytes > 0
