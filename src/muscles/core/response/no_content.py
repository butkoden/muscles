from __future__ import annotations

from .base import BaseResponse


class NoContentResponse(BaseResponse):
    def __init__(self, headers: dict[str, str] | None = None):
        super().__init__(
            body=b"",
            status=204,
            headers=headers or {},
            content_type="application/octet-stream",
        )
