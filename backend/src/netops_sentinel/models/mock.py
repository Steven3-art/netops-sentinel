"""Deterministic model provider for local development and tests."""

from typing import Any

from netops_sentinel.models.base import (
    ClassificationResult,
    GenerationResult,
    ReasoningResult,
)


class MockModelProvider:
    """Deterministic provider requiring no external model service."""

    async def classify(
        self,
        *,
        text: str,
        labels: tuple[str, ...],
        context: dict[str, Any] | None = None,
    ) -> ClassificationResult:
        """Classify text deterministically for local development."""

        del context

        if not labels:
            raise ValueError("At least one classification label is required.")

        normalized_text = text.casefold()

        selected_label = self._select_label(
            normalized_text=normalized_text,
            labels=labels,
        )

        return ClassificationResult(
            label=selected_label,
            confidence=1.0,
            rationale="Deterministic mock classification.",
        )

    async def reason(
        self,
        *,
        instruction: str,
        context: dict[str, Any],
    ) -> ReasoningResult:
        """Return a deterministic reasoning decision."""

        del instruction

        decision = str(context.get("expected_decision", "continue_investigation"))

        return ReasoningResult(
            decision=decision,
            rationale="Deterministic mock reasoning.",
        )

    async def generate(
        self,
        *,
        instruction: str,
        context: dict[str, Any],
    ) -> GenerationResult:
        """Generate deterministic operator-facing text."""

        del instruction

        diagnosis = context.get("diagnosis", "unknown")
        action = context.get("action", "manual investigation")

        return GenerationResult(text=(f"Diagnosis: {diagnosis}. Recommended action: {action}."))

    @staticmethod
    def _select_label(
        *,
        normalized_text: str,
        labels: tuple[str, ...],
    ) -> str:
        """Select a label using conservative deterministic keywords."""

        keyword_preferences = (
            ("password", "PASSWORD_ACTION"),
            ("credential", "PASSWORD_ACTION"),
            ("last authentication", "LAST_AUTHENTICATION"),
            ("authentication history", "AUTH_HISTORY"),
            ("connection history", "AUTH_HISTORY"),
            ("billing", "BILLING_EVIDENCE"),
            ("status", "CHECK_STATUS"),
            ("internet", "CHECK_CONNECTIVITY"),
            ("connectivity", "CHECK_CONNECTIVITY"),
            ("connection", "CHECK_CONNECTIVITY"),
        )

        available_labels = set(labels)

        for keyword, candidate in keyword_preferences:
            if keyword in normalized_text and candidate in available_labels:
                return candidate

        return labels[0]
