"""Tests for deterministic diagnosis rules."""

from netops_sentinel.aaa import NormalizedAAACondition
from netops_sentinel.core.domain import RootCause
from netops_sentinel.diagnosis import DiagnosisFacts, evaluate_diagnosis_rules


def test_suspended_account_has_priority() -> None:
    result = evaluate_diagnosis_rules(
        DiagnosisFacts(
            subscriber_status="suspended",
            session_online=False,
            aaa_condition=NormalizedAAACondition.INVALID_CREDENTIALS,
        )
    )

    assert result.root_cause is RootCause.SUSPENDED
    assert result.confidence == 1.0


def test_invalid_credentials_requires_complete_evidence() -> None:
    result = evaluate_diagnosis_rules(
        DiagnosisFacts(
            subscriber_status="active",
            session_online=False,
            aaa_condition=NormalizedAAACondition.INVALID_CREDENTIALS,
        )
    )

    assert result.root_cause is RootCause.INVALID_CREDENTIALS
    assert result.confidence == 1.0


def test_missing_aaa_evidence_returns_unknown() -> None:
    result = evaluate_diagnosis_rules(
        DiagnosisFacts(
            subscriber_status="active",
            session_online=False,
        )
    )

    assert result.root_cause is RootCause.UNKNOWN
    assert result.confidence == 0.0


def test_online_subscriber_does_not_match_invalid_credentials() -> None:
    result = evaluate_diagnosis_rules(
        DiagnosisFacts(
            subscriber_status="active",
            session_online=True,
            aaa_condition=NormalizedAAACondition.INVALID_CREDENTIALS,
        )
    )

    assert result.root_cause is RootCause.UNKNOWN


def test_empty_facts_return_unknown() -> None:
    result = evaluate_diagnosis_rules(DiagnosisFacts())

    assert result.root_cause is RootCause.UNKNOWN
    assert result.confidence == 0.0
