"""Tests for the deterministic investigation planner."""

from netops_sentinel.agent import (
    DeterministicPlanner,
    PlannerDecisionType,
)
from netops_sentinel.core.evidence import EvidenceKind, EvidenceStore


def test_planner_requests_subscriber_status_first() -> None:
    decision = DeterministicPlanner().next_step(
        incident_id="INC-0001",
        evidence_store=EvidenceStore(),
    )

    assert decision.decision_type is PlannerDecisionType.EXECUTE_TOOL
    assert decision.tool_name == "subscriber.get_status"


def test_planner_requests_session_after_subscriber_status() -> None:
    store = EvidenceStore()
    store.append(
        incident_id="INC-0001",
        kind=EvidenceKind.RAW,
        source="subscriber.get_status",
        evidence_type="subscriber_status",
        payload={"account_status": "active"},
    )

    decision = DeterministicPlanner().next_step(
        incident_id="INC-0001",
        evidence_store=store,
    )

    assert decision.tool_name == "session.get_online_session"


def test_planner_requests_radius_after_session() -> None:
    store = EvidenceStore()

    store.append(
        incident_id="INC-0001",
        kind=EvidenceKind.RAW,
        source="subscriber.get_status",
        evidence_type="subscriber_status",
        payload={"account_status": "active"},
    )
    store.append(
        incident_id="INC-0001",
        kind=EvidenceKind.RAW,
        source="session.get_online_session",
        evidence_type="online_session",
        payload={"online": False},
    )

    decision = DeterministicPlanner().next_step(
        incident_id="INC-0001",
        evidence_store=store,
    )

    assert decision.tool_name == "radius.get_failures"


def test_planner_requests_diagnosis_when_required_evidence_exists() -> None:
    store = EvidenceStore()

    store.append(
        incident_id="INC-0001",
        kind=EvidenceKind.RAW,
        source="subscriber.get_status",
        evidence_type="subscriber_status",
        payload={"account_status": "active"},
    )

    store.append(
        incident_id="INC-0001",
        kind=EvidenceKind.RAW,
        source="session.get_online_session",
        evidence_type="online_session",
        payload={"online": False},
    )

    raw_aaa = store.append(
        incident_id="INC-0001",
        kind=EvidenceKind.RAW,
        source="radius.get_failures",
        evidence_type="aaa_diagnostic",
        payload={"message": "Invalid username or password"},
    )

    store.append(
        incident_id="INC-0001",
        kind=EvidenceKind.DERIVED,
        source="aaa.normalizer",
        evidence_type="normalized_aaa_condition",
        payload={"condition": "invalid_credentials"},
        parent_evidence_ids=(raw_aaa.evidence_id,),
    )

    decision = DeterministicPlanner().next_step(
        incident_id="INC-0001",
        evidence_store=store,
    )

    assert decision.decision_type is PlannerDecisionType.DIAGNOSE
    assert decision.tool_name is None
