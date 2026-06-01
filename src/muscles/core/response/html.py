from __future__ import annotations

from .base import BaseResponse


class HtmlResponse(BaseResponse):
    def __init__(self, body: str = "", status: int = 200, headers: dict[str, str] | None = None):
        super().__init__(
            body=body.encode("utf-8"),
            status=status,
            headers=headers or {},
            content_type="text/html; charset=utf-8",
        )
