"""Deterministic action recommendation engine."""

from netops_sentinel.actions.models import ActionType, ProposedAction
from netops_sentinel.core.domain import ActionSafetyLevel, Diagnosis, RootCause


class ActionRecommendationEngine:
    """Recommend controlled actions from deterministic diagnoses."""

    def recommend(self, diagnosis: Diagnosis) -> ProposedAction:
        """Produce an action recommendation without executing it."""

        if diagnosis.root_cause is RootCause.INVALID_CREDENTIALS and diagnosis.confidence == 1.0:
            return ProposedAction(
                incident_id=diagnosis.incident_id,
                action_type=ActionType.REQUEST_CREDENTIAL_RESET,
                summary=("Request a credential reset for the affected synthetic subscriber."),
                safety_level=ActionSafetyLevel.LEVEL_2_MUTATE,
                root_cause=diagnosis.root_cause,
                supporting_evidence_ids=diagnosis.supporting_evidence_ids,
            )

        return ProposedAction(
            incident_id=diagnosis.incident_id,
            action_type=ActionType.ESCALATE_FOR_INVESTIGATION,
            summary=(
                "Escalate the incident for additional investigation before "
                "taking a mutating action."
            ),
            safety_level=ActionSafetyLevel.LEVEL_1_RECOMMEND,
            root_cause=diagnosis.root_cause,
            supporting_evidence_ids=diagnosis.supporting_evidence_ids,
        )
