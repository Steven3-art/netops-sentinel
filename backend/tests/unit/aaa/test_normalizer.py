"""Unit tests for deterministic AAA diagnostic normalization."""

import pytest

from netops_sentinel.aaa import (
    AAADiagnosticNormalizer,
    NormalizedAAACondition,
)


@pytest.fixture
def normalizer() -> AAADiagnosticNormalizer:
    """Return an AAA diagnostic normalizer."""

    return AAADiagnosticNormalizer()


@pytest.mark.parametrize(
    ("raw_message", "expected_condition"),
    [
        (
            "Invalid username or password",
            NormalizedAAACondition.INVALID_CREDENTIALS,
        ),
        (
            "Subscriber blacklisted",
            NormalizedAAACondition.BLACKLISTED,
        ),
        (
            "No authentication attempt",
            NormalizedAAACondition.NO_AUTHENTICATION,
        ),
        (
            "Account suspended",
            NormalizedAAACondition.SUSPENDED,
        ),
        (
            "Unknown subscriber",
            NormalizedAAACondition.ACCOUNT_NOT_FOUND,
        ),
        (
            "Online with traffic",
            NormalizedAAACondition.ONLINE_WITH_TRAFFIC,
        ),
        (
            "Online without traffic",
            NormalizedAAACondition.ONLINE_NO_TRAFFIC,
        ),
        (
            "External account block",
            NormalizedAAACondition.EXTERNAL_ACCOUNT_BLOCK,
        ),
    ],
)
def test_known_diagnostics_are_normalized(
    normalizer: AAADiagnosticNormalizer,
    raw_message: str,
    expected_condition: NormalizedAAACondition,
) -> None:
    """Known synthetic diagnostics map to deterministic conditions."""

    result = normalizer.normalize(raw_message)

    assert result.condition is expected_condition
    assert result.matched_rule is not None


def test_normalization_is_case_insensitive(
    normalizer: AAADiagnosticNormalizer,
) -> None:
    """Diagnostic matching is independent of letter casing."""

    result = normalizer.normalize("AUTHENTICATION FAILED: BAD CREDENTIALS")

    assert result.condition is NormalizedAAACondition.INVALID_CREDENTIALS
    assert result.matched_rule == "aaa.invalid_credentials"


def test_normalization_collapses_whitespace(
    normalizer: AAADiagnosticNormalizer,
) -> None:
    """Repeated whitespace does not alter deterministic matching."""

    result = normalizer.normalize("  Account    suspended  ")

    assert result.normalized_message == "account suspended"
    assert result.condition is NormalizedAAACondition.SUSPENDED


def test_normalization_handles_synthetic_punctuation(
    normalizer: AAADiagnosticNormalizer,
) -> None:
    """Common separators are normalized before rule matching."""

    result = normalizer.normalize("Authentication failed: bad credentials.")

    assert result.condition is NormalizedAAACondition.INVALID_CREDENTIALS


def test_unknown_diagnostic_remains_unknown(
    normalizer: AAADiagnosticNormalizer,
) -> None:
    """Unrecognized diagnostics must never be guessed."""

    result = normalizer.normalize("Synthetic AAA response requiring further investigation.")

    assert result.condition is NormalizedAAACondition.UNKNOWN
    assert result.matched_rule is None


@pytest.mark.parametrize(
    "raw_message",
    [
        "",
        " ",
        "\t",
        "\n",
    ],
)
def test_blank_diagnostic_is_rejected(
    normalizer: AAADiagnosticNormalizer,
    raw_message: str,
) -> None:
    """Blank diagnostics are invalid observations."""

    with pytest.raises(ValueError, match="cannot be blank"):
        normalizer.normalize(raw_message)


def test_partial_word_does_not_trigger_rule(
    normalizer: AAADiagnosticNormalizer,
) -> None:
    """Rule matching does not match fragments inside larger words."""

    result = normalizer.normalize("The account is unsuspended.")

    assert result.condition is NormalizedAAACondition.UNKNOWN
