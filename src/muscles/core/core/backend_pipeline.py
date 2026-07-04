from __future__ import annotations

import inspect
from dataclasses import is_dataclass
from typing import Any, Callable

from ..exceptions import ApplicationException
from .dependency import Dependency


class BackendPipeline:
    """
    Transport-neutral backend pipeline shared by runtime adapters.

    It owns handler argument binding, dependency resolution, guards, route-level
    security and middleware execution. Transports still own protocol request
    parsing and protocol response serialization.
    """

    def __init__(self, dependency_resolver: Callable[[type], Any] | None = None, container=None):
        self.dependency_resolver = dependency_resolver
        self.container = container

    def header_lookup(self, headers, name):
        wanted = name.replace("_", "-").lower()
        for key, value in (headers or {}).items():
            if key.replace("_", "-").lower() == wanted:
                return value
        return None

    def coerce_value(self, annotation, value):
        if annotation is inspect._empty or value is None:
            return value
        try:
            if annotation in (str, int, float, bool):
                return annotation(value)
        except Exception as exc:
            raise ApplicationException(status=422, reason=f"Invalid value for {annotation}", body=str(exc))
        return value

    def coerce_body(self, annotation, payload):
        if annotation is inspect._empty:
            return payload
        if annotation in (dict, list, str, int, float, bool):
            return payload
        try:
            if hasattr(annotation, "model_validate"):
                return annotation.model_validate(payload)
            if hasattr(annotation, "parse_obj"):
                return annotation.parse_obj(payload)
            if inspect.isclass(annotation) and is_dataclass(annotation):
                return annotation(**(payload or {}))
            if inspect.isclass(annotation) and isinstance(payload, dict):
                return annotation(**payload)
        except Exception as exc:
            raise ApplicationException(status=422, reason="Request body validation failed", body=str(exc))
        return payload

    def resolve_dependency(self, annotation, request=None):
        if annotation is inspect._empty:
            return None

        scoped_container = getattr(request, "container", None)
        for candidate in (scoped_container, self.container):
            if candidate is None or not hasattr(candidate, "resolve"):
                continue
            try:
                return candidate.resolve(annotation)
            except Exception:
                pass

        if self.dependency_resolver is not None:
            try:
                return self.dependency_resolver(annotation)
            except Exception:
                return None

        try:
            return Dependency.resolve(annotation)
        except Exception:
            return None

    def build_handler_kwargs(self, handler, request, route_params):
        signature = inspect.signature(handler)
        kwargs = {}
        for name, param in signature.parameters.items():
            if name == "self" or param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue
            if name == "request":
                kwargs[name] = request
                continue
            if name in route_params:
                kwargs[name] = self.coerce_value(param.annotation, route_params[name])
                continue

            dependency = self.resolve_dependency(param.annotation, request=request)
            if dependency is not None:
                kwargs[name] = dependency
                continue

            if name == "body":
                kwargs[name] = self.coerce_body(param.annotation, getattr(request, "json", None))
                continue

            query = getattr(request, "query", {}) or {}
            if name in query:
                kwargs[name] = self.coerce_value(param.annotation, query[name])
                continue

            header_value = self.header_lookup(getattr(request, "headers", {}) or {}, name)
            if header_value is not None:
                kwargs[name] = self.coerce_value(param.annotation, header_value)
                continue

            cookies = getattr(request, "cookies", {}) or {}
            if name in cookies:
                kwargs[name] = self.coerce_value(param.annotation, cookies[name])
                continue

            if param.default is inspect._empty:
                raise ApplicationException(status=422, reason=f"Missing required handler argument `{name}`")
        return kwargs

    def get_middlewares(self, request):
        itinerary = getattr(request, "itinerary", None)
        if itinerary is None or not hasattr(itinerary, "get_middlewares"):
            return []
        return itinerary.get_middlewares()

    def run_guards(self, request):
        itinerary = getattr(request, "itinerary", None)
        if itinerary is None or not hasattr(itinerary, "get_guards"):
            return None
        is_auth_disabled = getattr(itinerary, "is_auth_disabled", None)
        if is_auth_disabled and is_auth_disabled(request.route):
            return None
        for guard in itinerary.get_guards(request):
            response = guard(request)
            if response is not None:
                return response
        return None

    async def run_guards_async(self, request):
        itinerary = getattr(request, "itinerary", None)
        if itinerary is None or not hasattr(itinerary, "get_guards"):
            return None
        is_auth_disabled = getattr(itinerary, "is_auth_disabled", None)
        if is_auth_disabled and is_auth_disabled(request.route):
            return None
        for guard in itinerary.get_guards(request):
            response = guard(request)
            if inspect.isawaitable(response):
                response = await response
            if response is not None:
                return response
        return None

    def run_security(self, request):
        is_auth_disabled = getattr(getattr(request, "itinerary", None), "is_auth_disabled", None)
        if is_auth_disabled and is_auth_disabled(request.route):
            return
        handler = request.route["handler"]
        for security in getattr(handler, "security", []) or []:
            if not hasattr(security, "authenticate_header"):
                continue
            result = security.authenticate_header(self.header_lookup(getattr(request, "headers", {}), "Authorization"))
            if result is None:
                raise ApplicationException(status=401, reason="Unauthorized")
            if isinstance(result, dict):
                request.actor = result.get("user")

    async def run_security_async(self, request):
        return self.run_security(request)

    def call_handler(self, request, route_params, controller_factory=None):
        handler = request.route["handler"]
        kwargs = self.build_handler_kwargs(handler, request, route_params)
        if hasattr(handler, "controller"):
            controller = controller_factory(handler) if controller_factory else handler.controller()
            return handler(controller, **kwargs)
        return handler(**kwargs)

    async def call_handler_async(self, request, route_params, controller_factory=None):
        result = self.call_handler(request, route_params, controller_factory=controller_factory)
        if inspect.isawaitable(result):
            return await result
        return result

    def call_route_handler(self, request, route_params, controller_factory=None):
        def call_next(req):
            return self.call_handler(req, route_params, controller_factory=controller_factory)

        next_call = call_next
        for middleware in reversed(self.get_middlewares(request)):
            current_next = next_call

            def wrapped(req, middleware=middleware, current_next=current_next):
                return middleware(req, current_next)

            next_call = wrapped
        return next_call(request)

    async def call_route_handler_async(self, request, route_params, controller_factory=None):
        async def call_next(req):
            return await self.call_handler_async(req, route_params, controller_factory=controller_factory)

        next_call = call_next
        for middleware in reversed(self.get_middlewares(request)):
            current_next = next_call

            async def wrapped(req, middleware=middleware, current_next=current_next):
                if getattr(middleware, "is_cors_middleware", False):
                    response = await current_next(req)
                    return middleware.apply(response, req)
                response = middleware(req, current_next)
                if inspect.isawaitable(response):
                    return await response
                return response

            next_call = wrapped
        return await next_call(request)
