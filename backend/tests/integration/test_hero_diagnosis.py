"""Integration test for the deterministic hero diagnosis flow."""

from netops_sentinel.aaa import AAAEvidenceProcessor
from netops_sentinel.core.domain import RootCause
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


def test_hero_flow_diagnoses_invalid_credentials() -> None:
    repository = build_hero_invalid_credentials_lab()
    evidence_store = EvidenceStore()

    context = ToolContext(
        incident_id="INC-HERO-0001",
        repository=repository,
        evidence_store=evidence_store,
    )

    subscriber_evidence = SubscriberStatusTool().execute(
        subscriber_id=HERO_SUBSCRIBER_ID,
        context=context,
    )
    session_evidence = OnlineSessionTool().execute(
        subscriber_id=HERO_SUBSCRIBER_ID,
        context=context,
    )
    raw_aaa_evidence = RadiusFailuresTool().execute(
        subscriber_id=HERO_SUBSCRIBER_ID,
        context=context,
    )

    normalized_aaa_evidence = AAAEvidenceProcessor().process(
        raw_evidence=raw_aaa_evidence,
        evidence_store=evidence_store,
    )

    diagnosis = DeterministicDiagnosisEngine().diagnose(
        incident_id=context.incident_id,
        evidence_store=evidence_store,
    )

    assert subscriber_evidence.evidence_id == "EV-0001"
    assert session_evidence.evidence_id == "EV-0002"
    assert raw_aaa_evidence.evidence_id == "EV-0003"
    assert normalized_aaa_evidence.evidence_id == "EV-0004"

    assert diagnosis.root_cause is RootCause.INVALID_CREDENTIALS
    assert diagnosis.confidence == 1.0
    assert diagnosis.supporting_evidence_ids == (
        "EV-0001",
        "EV-0002",
        "EV-0004",
    )

    assert normalized_aaa_evidence.parent_evidence_ids == ("EV-0003",)
