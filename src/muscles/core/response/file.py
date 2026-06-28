from __future__ import annotations

import mimetypes
from pathlib import Path

from .base import BaseResponse


class FileResponse(BaseResponse):
    def __init__(
        self,
        path: str | Path,
        status: int = 200,
        headers: dict[str, str] | None = None,
        content_type: str | None = None,
        as_attachment: bool = False,
        filename: str | None = None,
    ):
        file_path = Path(path)
        payload = file_path.read_bytes()
        resolved_content_type = content_type or mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        download_name = filename or file_path.name
        disposition = "attachment" if as_attachment else "inline"
        response_headers = dict(headers or {})
        response_headers.setdefault("Content-Disposition", f'{disposition}; filename="{download_name}"')
        super().__init__(
            body=payload,
            status=status,
            headers=response_headers,
            content_type=resolved_content_type,
        )
