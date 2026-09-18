"""End-to-end integration test for the NetOps Sentinel hero recovery flow."""

from netops_sentinel.aaa import AAAEvidenceProcessor
from netops_sentinel.actions import (
    ActionRecommendationEngine,
    ApprovalService,
    ControlledActionExecutor,
    PolicyDecision,
    SafetyPolicy,
)
from netops_sentinel.core.domain import RootCause
from netops_sentinel.core.evidence import EvidenceStore
from netops_sentinel.diagnosis import DeterministicDiagnosisEngine
from netops_sentinel.lab import (
    HERO_SUBSCRIBER_ID,
    build_hero_invalid_credentials_lab,
)
from netops_sentinel.recovery import RecoveryStatus, RecoveryVerifier
from netops_sentinel.tools import (
    AuthenticationStateTool,
    OnlineSessionTool,
    RadiusFailuresTool,
    SubscriberStatusTool,
    ToolContext,
)


def test_hero_flow_diagnoses_acts_and_verifies_recovery() -> None:
    repository = build_hero_invalid_credentials_lab()
    evidence_store = EvidenceStore()

    context = ToolContext(
        incident_id="INC-HERO-0001",
        repository=repository,
        evidence_store=evidence_store,
    )

    SubscriberStatusTool().execute(
        subscriber_id=HERO_SUBSCRIBER_ID,
        context=context,
    )
    OnlineSessionTool().execute(
        subscriber_id=HERO_SUBSCRIBER_ID,
        context=context,
    )
    raw_aaa = RadiusFailuresTool().execute(
        subscriber_id=HERO_SUBSCRIBER_ID,
        context=context,
    )

    AAAEvidenceProcessor().process(
        raw_evidence=raw_aaa,
        evidence_store=evidence_store,
    )

    diagnosis = DeterministicDiagnosisEngine().diagnose(
        incident_id=context.incident_id,
        evidence_store=evidence_store,
    )

    assert diagnosis.root_cause is RootCause.INVALID_CREDENTIALS

    action = ActionRecommendationEngine().recommend(diagnosis)

    policy = SafetyPolicy()
    before_approval = policy.evaluate(action)

    assert before_approval.decision is PolicyDecision.HUMAN_APPROVAL_REQUIRED
    assert repository.get_session(HERO_SUBSCRIBER_ID).online is False

    approval_service = ApprovalService()
    approval = approval_service.approve(
        action,
        approved_by="demo-operator",
    )

    execution_evidence = ControlledActionExecutor(
        approval_service=approval_service,
        safety_policy=policy,
    ).execute(
        action=action,
        approval=approval,
        subscriber_id=HERO_SUBSCRIBER_ID,
        repository=repository,
        evidence_store=evidence_store,
    )

    assert execution_evidence.evidence_id == "EV-0005"

    post_session = OnlineSessionTool().execute(
        subscriber_id=HERO_SUBSCRIBER_ID,
        context=context,
    )

    post_authentication = AuthenticationStateTool().execute(
        subscriber_id=HERO_SUBSCRIBER_ID,
        context=context,
    )

    assert post_session.evidence_id == "EV-0006"
    assert post_authentication.evidence_id == "EV-0007"

    recovery = RecoveryVerifier().verify(
        session_evidence=post_session,
        authentication_evidence=post_authentication,
    )

    assert recovery.status is RecoveryStatus.RECOVERED
    assert recovery.supporting_evidence_ids == (
        "EV-0006",
        "EV-0007",
    )
