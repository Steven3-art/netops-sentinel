"""Tests for the deterministic mock model provider."""

import asyncio

from netops_sentinel.models import (
    MockModelProvider,
    ModelProvider,
)


def test_mock_provider_satisfies_model_provider_protocol() -> None:
    provider: ModelProvider = MockModelProvider()

    assert isinstance(provider, MockModelProvider)


def test_classify_connectivity_request() -> None:
    provider = MockModelProvider()

    result = asyncio.run(
        provider.classify(
            text="Customer has no Internet access.",
            labels=(
                "CHECK_STATUS",
                "CHECK_CONNECTIVITY",
                "PASSWORD_ACTION",
            ),
        )
    )

    assert result.label == "CHECK_CONNECTIVITY"
    assert result.confidence == 1.0


def test_classify_password_request() -> None:
    provider = MockModelProvider()

    result = asyncio.run(
        provider.classify(
            text="Please reset the customer password.",
            labels=(
                "CHECK_STATUS",
                "CHECK_CONNECTIVITY",
                "PASSWORD_ACTION",
            ),
        )
    )

    assert result.label == "PASSWORD_ACTION"


def test_classify_falls_back_to_first_label() -> None:
    provider = MockModelProvider()

    result = asyncio.run(
        provider.classify(
            text="Ambiguous request.",
            labels=("CHECK_STATUS", "CHECK_CONNECTIVITY"),
        )
    )

    assert result.label == "CHECK_STATUS"


def test_classify_requires_labels() -> None:
    provider = MockModelProvider()

    try:
        asyncio.run(
            provider.classify(
                text="Customer status.",
                labels=(),
            )
        )
    except ValueError as exc:
        assert str(exc) == "At least one classification label is required."
    else:
        raise AssertionError("Expected ValueError.")


def test_reason_returns_expected_deterministic_decision() -> None:
    provider = MockModelProvider()

    result = asyncio.run(
        provider.reason(
            instruction="Select the next investigation step.",
            context={"expected_decision": "subscriber.get_status"},
        )
    )

    assert result.decision == "subscriber.get_status"
    assert result.rationale == "Deterministic mock reasoning."


def test_reason_has_safe_default() -> None:
    provider = MockModelProvider()

    result = asyncio.run(
        provider.reason(
            instruction="Select the next investigation step.",
            context={},
        )
    )

    assert result.decision == "continue_investigation"


def test_generate_returns_operator_facing_text() -> None:
    provider = MockModelProvider()

    result = asyncio.run(
        provider.generate(
            instruction="Draft an operator response.",
            context={
                "diagnosis": "INVALID_CREDENTIALS",
                "action": "credential reset",
            },
        )
    )

    assert "INVALID_CREDENTIALS" in result.text
    assert "credential reset" in result.text
