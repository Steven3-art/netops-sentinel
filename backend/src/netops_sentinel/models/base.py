"""Model-provider contracts for NetOps Sentinel."""

from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from netops_sentinel.core.domain import NonEmptyString


class ClassificationResult(BaseModel):
    """Structured result returned by a model classification request."""

    model_config = ConfigDict(frozen=True)

    label: NonEmptyString
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: NonEmptyString


class ReasoningResult(BaseModel):
    """Structured result returned by a model reasoning request."""

    model_config = ConfigDict(frozen=True)

    decision: NonEmptyString
    rationale: NonEmptyString


class GenerationResult(BaseModel):
    """Structured result returned by a model generation request."""

    model_config = ConfigDict(frozen=True)

    text: NonEmptyString


class ModelProvider(Protocol):
    """Contract implemented by model backends."""

    async def classify(
        self,
        *,
        text: str,
        labels: tuple[str, ...],
        context: dict[str, Any] | None = None,
    ) -> ClassificationResult:
        """Classify text into one of the supplied labels."""
        ...

    async def reason(
        self,
        *,
        instruction: str,
        context: dict[str, Any],
    ) -> ReasoningResult:
        """Produce a structured reasoning decision."""
        ...

    async def generate(
        self,
        *,
        instruction: str,
        context: dict[str, Any],
    ) -> GenerationResult:
        """Generate operator-facing text."""
        ...
