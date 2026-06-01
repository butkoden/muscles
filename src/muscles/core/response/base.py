from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BaseResponse:
    body: Any = b""
    status: int = 200
    headers: dict[str, str] = field(default_factory=dict)
    content_type: str = "application/octet-stream"
    redirect: str | None = None

    def as_bytes(self) -> bytes:
        if isinstance(self.body, bytes):
            return self.body
        if self.body is None:
            return b""
        return str(self.body).encode("utf-8")

    def with_content_length(self) -> "BaseResponse":
        payload = self.as_bytes()
        if "Content-Length" not in self.headers:
            self.headers["Content-Length"] = str(len(payload))
        if "Content-Type" not in self.headers:
            self.headers["Content-Type"] = self.content_type
        return self
