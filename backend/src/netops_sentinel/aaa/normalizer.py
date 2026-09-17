"""Deterministic normalization of synthetic AAA diagnostics."""

import re
from dataclasses import dataclass

from netops_sentinel.aaa.models import (
    AAANormalizationResult,
    NormalizedAAACondition,
)


@dataclass(frozen=True, slots=True)
class _NormalizationRule:
    """Internal deterministic AAA normalization rule."""

    rule_id: str
    condition: NormalizedAAACondition
    phrases: tuple[str, ...]


class AAADiagnosticNormalizer:
    """Normalize synthetic AAA messages into deterministic conditions."""

    _RULES: tuple[_NormalizationRule, ...] = (
        _NormalizationRule(
            rule_id="aaa.invalid_credentials",
            condition=NormalizedAAACondition.INVALID_CREDENTIALS,
            phrases=(
                "invalid credentials",
                "invalid username or password",
                "authentication failed bad credentials",
                "bad credentials",
            ),
        ),
        _NormalizationRule(
            rule_id="aaa.blacklisted",
            condition=NormalizedAAACondition.BLACKLISTED,
            phrases=(
                "subscriber blacklisted",
                "account blacklisted",
            ),
        ),
        _NormalizationRule(
            rule_id="aaa.no_authentication",
            condition=NormalizedAAACondition.NO_AUTHENTICATION,
            phrases=(
                "no authentication attempt",
                "no radius request",
                "no authentication request",
            ),
        ),
        _NormalizationRule(
            rule_id="aaa.suspended",
            condition=NormalizedAAACondition.SUSPENDED,
            phrases=(
                "account suspended",
                "subscriber suspended",
            ),
        ),
        _NormalizationRule(
            rule_id="aaa.account_not_found",
            condition=NormalizedAAACondition.ACCOUNT_NOT_FOUND,
            phrases=(
                "account not found",
                "unknown subscriber",
                "subscriber not found",
            ),
        ),
        _NormalizationRule(
            rule_id="aaa.online_with_traffic",
            condition=NormalizedAAACondition.ONLINE_WITH_TRAFFIC,
            phrases=(
                "online with traffic",
                "active session with traffic",
            ),
        ),
        _NormalizationRule(
            rule_id="aaa.online_no_traffic",
            condition=NormalizedAAACondition.ONLINE_NO_TRAFFIC,
            phrases=(
                "online no traffic",
                "online without traffic",
                "active session without traffic",
            ),
        ),
        _NormalizationRule(
            rule_id="aaa.external_account_block",
            condition=NormalizedAAACondition.EXTERNAL_ACCOUNT_BLOCK,
            phrases=(
                "external account block",
                "blocked by external account system",
            ),
        ),
    )

    def normalize(self, raw_message: str) -> AAANormalizationResult:
        """Normalize a raw synthetic AAA diagnostic."""

        normalized_message = self._normalize_text(raw_message)

        if not normalized_message:
            raise ValueError("AAA diagnostic message cannot be blank.")

        for rule in self._RULES:
            if any(self._contains_phrase(normalized_message, phrase) for phrase in rule.phrases):
                return AAANormalizationResult(
                    raw_message=raw_message,
                    normalized_message=normalized_message,
                    condition=rule.condition,
                    matched_rule=rule.rule_id,
                )

        return AAANormalizationResult(
            raw_message=raw_message,
            normalized_message=normalized_message,
            condition=NormalizedAAACondition.UNKNOWN,
            matched_rule=None,
        )

    @staticmethod
    def _normalize_text(message: str) -> str:
        """Normalize casing, punctuation, and whitespace."""

        normalized = message.strip().casefold()
        normalized = re.sub(r"[_:/\-]+", " ", normalized)
        normalized = re.sub(r"[^\w\s]", " ", normalized)
        return " ".join(normalized.split())

    @staticmethod
    def _contains_phrase(message: str, phrase: str) -> bool:
        """Match a normalized phrase using explicit word boundaries."""

        pattern = rf"(?<!\w){re.escape(phrase)}(?!\w)"
        return re.search(pattern, message) is not None
