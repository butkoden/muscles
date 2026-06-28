from __future__ import annotations

from .base import BaseResponse


class BytesResponse(BaseResponse):
    def __init__(
        self,
        body: bytes = b"",
        status: int = 200,
        headers: dict[str, str] | None = None,
        content_type: str = "application/octet-stream",
    ):
        super().__init__(
            body=body,
            status=status,
            headers=headers or {},
            content_type=content_type,
        )
