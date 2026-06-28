from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .base import BaseResponse
from .bytes import BytesResponse
from .html import HtmlResponse
from .json import JsonResponse
from .no_content import NoContentResponse


def normalize_response(value: Any, request=None) -> BaseResponse:
    _ = request
    if isinstance(value, BaseResponse):
        return value.with_content_length()

    if isinstance(value, tuple):
        if len(value) == 3:
            body, status, headers = value
            response = normalize_response(body)
            response.status = int(status)
            response.headers.update(dict(headers or {}))
            return response.with_content_length()
        if len(value) == 2:
            body, status = value
            response = normalize_response(body)
            response.status = int(status)
            return response.with_content_length()
        raise ValueError("Tuple response must be (body, status) or (body, status, headers)")

    if isinstance(value, bytes):
        return BytesResponse(body=value).with_content_length()
    if isinstance(value, str):
        return HtmlResponse(body=value).with_content_length()
    if isinstance(value, Mapping):
        return JsonResponse(body=dict(value)).with_content_length()
    if value is None:
        return NoContentResponse().with_content_length()
    return BaseResponse(body=str(value).encode("utf-8"), status=200, headers={}, content_type="text/plain; charset=utf-8").with_content_length()
