"""Deterministic investigation planner."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from netops_sentinel.core.domain import NonEmptyString
from netops_sentinel.core.evidence import EvidenceStore


class PlannerDecisionType(StrEnum):
    """Types of decisions produced by the investigation planner."""

    EXECUTE_TOOL = "execute_tool"
    DIAGNOSE = "diagnose"


class PlannerDecision(BaseModel):
    """Structured decision produced by the planner."""

    model_config = ConfigDict(frozen=True)

    decision_type: PlannerDecisionType
    tool_name: NonEmptyString | None = None


class DeterministicPlanner:
    """Select the next investigation step from available evidence."""

    def next_step(
        self,
        *,
        incident_id: str,
        evidence_store: EvidenceStore,
    ) -> PlannerDecision:
        """Select the next tool or request diagnosis."""

        evidence = evidence_store.list_for_incident(incident_id)
        evidence_types = {item.evidence_type for item in evidence}

        if "subscriber_status" not in evidence_types:
            return PlannerDecision(
                decision_type=PlannerDecisionType.EXECUTE_TOOL,
                tool_name="subscriber.get_status",
            )

        if "online_session" not in evidence_types:
            return PlannerDecision(
                decision_type=PlannerDecisionType.EXECUTE_TOOL,
                tool_name="session.get_online_session",
            )

        if "normalized_aaa_condition" not in evidence_types:
            return PlannerDecision(
                decision_type=PlannerDecisionType.EXECUTE_TOOL,
                tool_name="radius.get_failures",
            )

        return PlannerDecision(
            decision_type=PlannerDecisionType.DIAGNOSE,
        )
