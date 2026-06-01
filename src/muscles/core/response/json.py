from __future__ import annotations

import json
from typing import Any

from .base import BaseResponse


class JsonResponse(BaseResponse):
    def __init__(self, body: Any = None, status: int = 200, headers: dict[str, str] | None = None):
        payload = b"null" if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
        super().__init__(
            body=payload,
            status=status,
            headers=headers or {},
            content_type="application/json; charset=utf-8",
        )
