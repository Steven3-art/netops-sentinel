"""Deterministic diagnosis rules for NetOps Sentinel."""

from dataclasses import dataclass

from netops_sentinel.aaa import NormalizedAAACondition
from netops_sentinel.core.domain import RootCause


@dataclass(frozen=True, slots=True)
class DiagnosisFacts:
    """Relevant facts extracted from incident evidence."""

    subscriber_status: str | None = None
    session_online: bool | None = None
    aaa_condition: NormalizedAAACondition | None = None


@dataclass(frozen=True, slots=True)
class RuleResult:
    """Result produced by a deterministic diagnosis rule."""

    root_cause: RootCause
    summary: str
    confidence: float


def evaluate_diagnosis_rules(facts: DiagnosisFacts) -> RuleResult:
    """Evaluate deterministic diagnosis rules in explicit priority order."""

    if facts.subscriber_status == "suspended":
        return RuleResult(
            root_cause=RootCause.SUSPENDED,
            summary="The subscriber account is currently suspended.",
            confidence=1.0,
        )

    if (
        facts.subscriber_status == "active"
        and facts.session_online is False
        and facts.aaa_condition is NormalizedAAACondition.INVALID_CREDENTIALS
    ):
        return RuleResult(
            root_cause=RootCause.INVALID_CREDENTIALS,
            summary=(
                "The subscriber is active and offline, with authentication "
                "failures caused by invalid credentials."
            ),
            confidence=1.0,
        )

    return RuleResult(
        root_cause=RootCause.UNKNOWN,
        summary="Available evidence is insufficient for a deterministic root cause.",
        confidence=0.0,
    )
