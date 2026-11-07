from __future__ import annotations

from .response import BaseResponse, normalize_response


class CorsMiddleware:
    is_cors_middleware = True

    def __init__(
        self,
        allow_origins: list[str] | tuple[str, ...] | str = "*",
        allow_methods: list[str] | tuple[str, ...] | str = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"),
        allow_headers: list[str] | tuple[str, ...] | str = "*",
        allow_credentials: bool = False,
        max_age: int | None = None,
    ):
        self.allow_origins = [allow_origins] if isinstance(allow_origins, str) else list(allow_origins)
        self.allow_methods = [allow_methods] if isinstance(allow_methods, str) else list(allow_methods)
        self.allow_headers = [allow_headers] if isinstance(allow_headers, str) else list(allow_headers)
        self.allow_credentials = allow_credentials
        self.max_age = max_age

    def _origin(self, request):
        origin = getattr(request, "origin", None)
        if origin and ("*" in self.allow_origins or origin in self.allow_origins):
            return origin
        return "*" if "*" in self.allow_origins else None

    def _headers(self, request):
        headers = {
            "Access-Control-Allow-Methods": ", ".join(self.allow_methods),
            "Access-Control-Allow-Headers": ", ".join(self.allow_headers),
        }
        origin = self._origin(request)
        if origin is not None:
            headers["Access-Control-Allow-Origin"] = origin
        if self.allow_credentials:
            headers["Access-Control-Allow-Credentials"] = "true"
        if self.max_age is not None:
            headers["Access-Control-Max-Age"] = str(self.max_age)
        return headers

    def apply(self, response, request):
        append_header = getattr(response, "header_append", None)
        if callable(append_header):
            for key, value in self._headers(request).items():
                append_header((key, value))
            return response

        response = normalize_response(response, request=request)
        response.headers.update(self._headers(request))
        return response

    def preflight_response(self, request):
        return BaseResponse(body=b"", status=204, headers=self._headers(request), content_type="text/plain").with_content_length()

    def __call__(self, request, call_next):
        return self.apply(call_next(request), request)


def cors(**kwargs) -> CorsMiddleware:
    return CorsMiddleware(**kwargs)
