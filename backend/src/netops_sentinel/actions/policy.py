"""Deterministic safety policy for proposed actions."""

from netops_sentinel.actions.models import (
    PolicyDecision,
    PolicyEvaluation,
    ProposedAction,
)
from netops_sentinel.core.domain import ActionSafetyLevel


class SafetyPolicy:
    """Enforce backend safety rules independently of any AI model."""

    def evaluate(
        self,
        action: ProposedAction,
        *,
        approved: bool = False,
    ) -> PolicyEvaluation:
        """Evaluate whether a proposed action may proceed."""

        if action.safety_level is ActionSafetyLevel.LEVEL_2_MUTATE:
            if not approved:
                return PolicyEvaluation(
                    decision=PolicyDecision.HUMAN_APPROVAL_REQUIRED,
                    safety_level=action.safety_level,
                    reason=("Mutating actions require explicit human approval before execution."),
                )

            return PolicyEvaluation(
                decision=PolicyDecision.ALLOWED,
                safety_level=action.safety_level,
                reason="Explicit human approval was provided.",
            )

        return PolicyEvaluation(
            decision=PolicyDecision.ALLOWED,
            safety_level=action.safety_level,
            reason="This action does not require mutation approval.",
        )
