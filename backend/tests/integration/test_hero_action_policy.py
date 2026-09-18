"""Integration test for hero diagnosis, recommendation, and safety policy."""

from netops_sentinel.aaa import AAAEvidenceProcessor
from netops_sentinel.actions import (
    ActionRecommendationEngine,
    ActionType,
    PolicyDecision,
    SafetyPolicy,
)
from netops_sentinel.core.domain import ActionSafetyLevel, RootCause
from netops_sentinel.core.evidence import EvidenceStore
from netops_sentinel.diagnosis import DeterministicDiagnosisEngine
from netops_sentinel.lab import (
    HERO_SUBSCRIBER_ID,
    build_hero_invalid_credentials_lab,
)
from netops_sentinel.tools import (
    OnlineSessionTool,
    RadiusFailuresTool,
    SubscriberStatusTool,
    ToolContext,
)


def test_hero_mutation_is_blocked_until_human_approval() -> None:
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
    raw_aaa_evidence = RadiusFailuresTool().execute(
        subscriber_id=HERO_SUBSCRIBER_ID,
        context=context,
    )

    AAAEvidenceProcessor().process(
        raw_evidence=raw_aaa_evidence,
        evidence_store=evidence_store,
    )

    diagnosis = DeterministicDiagnosisEngine().diagnose(
        incident_id=context.incident_id,
        evidence_store=evidence_store,
    )

    action = ActionRecommendationEngine().recommend(diagnosis)
    evaluation = SafetyPolicy().evaluate(action)

    assert diagnosis.root_cause is RootCause.INVALID_CREDENTIALS
    assert action.action_type is ActionType.REQUEST_CREDENTIAL_RESET
    assert action.safety_level is ActionSafetyLevel.LEVEL_2_MUTATE

    assert evaluation.decision is PolicyDecision.HUMAN_APPROVAL_REQUIRED

    assert repository.get_session(HERO_SUBSCRIBER_ID).online is False
