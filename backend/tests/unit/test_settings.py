"""Tests for NetOps Sentinel application settings."""

import pytest
from pydantic import ValidationError

from netops_sentinel.config import Environment, LogLevel, ModelProvider, Settings


def test_settings_use_safe_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default settings must support safe local development."""

    monkeypatch.delenv("NETOPS_ENVIRONMENT", raising=False)
    monkeypatch.delenv("NETOPS_LOG_LEVEL", raising=False)
    monkeypatch.delenv("NETOPS_MODEL_PROVIDER", raising=False)

    settings = Settings(_env_file=None)

    assert settings.netops_environment is Environment.DEVELOPMENT
    assert settings.netops_log_level is LogLevel.INFO
    assert settings.netops_model_provider is ModelProvider.MOCK
    assert settings.langsmith_tracing is False
    assert settings.nebius_api_key is None


def test_environment_variables_override_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Environment variables must override application defaults."""

    monkeypatch.setenv("NETOPS_ENVIRONMENT", "test")
    monkeypatch.setenv("NETOPS_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("NETOPS_MODEL_PROVIDER", "nebius")
    monkeypatch.setenv("LANGSMITH_TRACING", "true")

    settings = Settings(_env_file=None)

    assert settings.netops_environment is Environment.TEST
    assert settings.netops_log_level is LogLevel.DEBUG
    assert settings.netops_model_provider is ModelProvider.NEBIUS
    assert settings.langsmith_tracing is True


def test_invalid_model_provider_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unknown model providers must fail configuration validation."""

    monkeypatch.setenv("NETOPS_MODEL_PROVIDER", "unsupported-provider")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_api_keys_are_masked_in_settings_representation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """API keys must not be exposed by the settings representation."""

    fake_nebius_key = "synthetic-nebius-secret"
    fake_langsmith_key = "synthetic-langsmith-secret"

    monkeypatch.setenv("NEBIUS_API_KEY", fake_nebius_key)
    monkeypatch.setenv("LANGSMITH_API_KEY", fake_langsmith_key)

    settings = Settings(_env_file=None)
    settings_repr = repr(settings)

    assert settings.nebius_api_key is not None
    assert settings.langsmith_api_key is not None

    assert settings.nebius_api_key.get_secret_value() == fake_nebius_key
    assert settings.langsmith_api_key.get_secret_value() == fake_langsmith_key

    assert fake_nebius_key not in settings_repr
    assert fake_langsmith_key not in settings_repr
