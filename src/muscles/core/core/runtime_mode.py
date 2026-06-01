from __future__ import annotations

import os
from enum import Enum


class RuntimeMode(str, Enum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


def _normalize_mode(value: str | None, default: RuntimeMode = RuntimeMode.PRODUCTION) -> RuntimeMode:
    if value is None:
        return default
    normalized = str(value).strip().lower()
    if normalized in ("dev", "development"):
        return RuntimeMode.DEVELOPMENT
    if normalized in ("test", "testing"):
        return RuntimeMode.TEST
    if normalized in ("prod", "production"):
        return RuntimeMode.PRODUCTION
    raise ValueError(f"Invalid runtime mode `{value}`")


def _read_config_mode(config) -> str | None:
    if config is None:
        return None
    if isinstance(config, dict):
        return config.get("main", {}).get("ENV")
    getter = getattr(config, "get", None)
    if callable(getter):
        return getter("main.ENV", None)
    return None


def resolve_runtime_mode(config=None, override: str | None = None, env_key: str = "MUSCLES_ENV") -> RuntimeMode:
    if override is not None:
        return _normalize_mode(override)
    env_value = os.environ.get(env_key)
    if env_value is not None:
        return _normalize_mode(env_value)
    config_value = _read_config_mode(config)
    return _normalize_mode(config_value)


def app_runtime_mode(app=None, override: str | None = None) -> RuntimeMode:
    config = getattr(app, "config", None) if app is not None else None
    return resolve_runtime_mode(config=config, override=override)


def is_development(app=None, override: str | None = None) -> bool:
    return app_runtime_mode(app=app, override=override) == RuntimeMode.DEVELOPMENT


def is_test(app=None, override: str | None = None) -> bool:
    return app_runtime_mode(app=app, override=override) == RuntimeMode.TEST


def is_production(app=None, override: str | None = None) -> bool:
    return app_runtime_mode(app=app, override=override) == RuntimeMode.PRODUCTION
