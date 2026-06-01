import os

import pytest

from muscles.core import RuntimeMode
from muscles.core import app_runtime_mode
from muscles.core import is_development
from muscles.core import is_production
from muscles.core import is_test
from muscles.core import resolve_runtime_mode


def test_runtime_mode_defaults_to_production(monkeypatch):
    monkeypatch.delenv("MUSCLES_ENV", raising=False)
    assert resolve_runtime_mode() == RuntimeMode.PRODUCTION


def test_runtime_mode_uses_env(monkeypatch):
    monkeypatch.setenv("MUSCLES_ENV", "development")
    assert resolve_runtime_mode() == RuntimeMode.DEVELOPMENT


def test_runtime_mode_uses_config_when_env_missing(monkeypatch):
    monkeypatch.delenv("MUSCLES_ENV", raising=False)
    config = {"main": {"ENV": "test"}}
    assert resolve_runtime_mode(config=config) == RuntimeMode.TEST


def test_runtime_mode_override_has_priority(monkeypatch):
    monkeypatch.setenv("MUSCLES_ENV", "production")
    config = {"main": {"ENV": "test"}}
    assert resolve_runtime_mode(config=config, override="development") == RuntimeMode.DEVELOPMENT


def test_runtime_mode_invalid_value():
    with pytest.raises(ValueError):
        resolve_runtime_mode(override="staging")


def test_runtime_mode_helpers(monkeypatch):
    monkeypatch.setenv("MUSCLES_ENV", "test")
    assert is_test() is True
    assert is_development() is False
    assert is_production() is False


def test_app_runtime_mode_from_config_object(monkeypatch):
    monkeypatch.delenv("MUSCLES_ENV", raising=False)

    class FakeConfig:
        def get(self, path, default=None):
            if path == "main.ENV":
                return "development"
            return default

    class FakeApp:
        config = FakeConfig()

    assert app_runtime_mode(FakeApp()) == RuntimeMode.DEVELOPMENT
