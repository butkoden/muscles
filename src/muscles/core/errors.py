from __future__ import annotations

import traceback
from typing import Any


ERROR_TITLES = {
    400: "Bad Request",
    409: "Conflict",
    422: "Unprocessable Entity",
    500: "Internal Server Error",
}


def _extract_path(instance: Any) -> str:
    if not instance:
        return ""
    if isinstance(instance, str):
        return instance
    path = getattr(instance, "path", None)
    if path:
        return str(path)
    request = getattr(instance, "request", None)
    if request is not None:
        return _extract_path(request)
    return ""


def _normalize_status(default_status: int, exception: Exception | BaseException | None) -> int:
    status = default_status
    if exception is not None and hasattr(exception, "status"):
        try:
            status = int(getattr(exception, "status"))
        except Exception:
            status = default_status
    return 500 if status is None else int(status)


def _extract_detail(exception: BaseException | Exception | None) -> str:
    if exception is None:
        return "Unknown error"
    if hasattr(exception, "reason") and getattr(exception, "reason") is not None:
        return str(getattr(exception, "reason"))
    return str(exception)


def _extract_trace(exception: BaseException | Exception | None, include_trace: bool) -> list[str] | None:
    if not include_trace or exception is None:
        return None
    tb = getattr(exception, "__traceback__", None)
    if tb is None:
        return traceback.format_exc().splitlines() if exception is not None else None
    return traceback.format_exception(type(exception), exception, tb)


def _normalize_error_type(status: int, exception: BaseException | Exception | None) -> str:
    if getattr(exception, "error_type", None):
        return str(getattr(exception, "error_type"))
    return f"https://muscles.dev/problems/{status}"


def normalize_problem_payload(
    exception: BaseException | Exception | None,
    request: Any | None = None,
    *,
    default_status: int = 500,
    include_trace: bool = False,
) -> dict[str, Any]:
    status = _normalize_status(default_status, exception)
    title = ERROR_TITLES.get(status, "Request Error")
    detail = _extract_detail(exception)
    problem_type = _normalize_error_type(status, exception)
    instance = _extract_path(request)
    payload: dict[str, Any] = {
        "type": problem_type,
        "title": title,
        "status": status,
        "detail": detail,
        "instance": instance,
    }
    if include_trace:
        payload["trace"] = _extract_trace(exception, True)
    return payload
