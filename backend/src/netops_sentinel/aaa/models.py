"""AAA diagnostic normalization models."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from netops_sentinel.core.domain import NonEmptyString


class NormalizedAAACondition(StrEnum):
    """Deterministic technical conditions produced from AAA observations."""

    INVALID_CREDENTIALS = "invalid_credentials"
    BLACKLISTED = "blacklisted"
    NO_AUTHENTICATION = "no_authentication"
    SUSPENDED = "suspended"
    ACCOUNT_NOT_FOUND = "account_not_found"
    ONLINE_WITH_TRAFFIC = "online_with_traffic"
    ONLINE_NO_TRAFFIC = "online_no_traffic"
    EXTERNAL_ACCOUNT_BLOCK = "external_account_block"
    UNKNOWN = "unknown"


class AAANormalizationResult(BaseModel):
    """Result of deterministic AAA diagnostic normalization."""

    model_config = ConfigDict(frozen=True)

    raw_message: NonEmptyString
    normalized_message: NonEmptyString
    condition: NormalizedAAACondition
    matched_rule: str | None = None
