from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


CANONICAL_ROUTES = {
    "openapi": "/openapi.json",
    "docs": "/docs",
    "redoc": "/redoc",
    "healthz": "/healthz",
    "ready": "/ready",
    "live": "/live",
}
CANONICAL_ALIASES = {
    "schema": CANONICAL_ROUTES["openapi"],
    "swagger": CANONICAL_ROUTES["docs"],
    "health": CANONICAL_ROUTES["healthz"],
}


def normalize_path(*parts: str) -> str:
    """Build stable absolute path from fragments."""
    chunks = [str(part or "").strip("/") for part in parts]
    joined = "/".join(chunk for chunk in chunks if chunk)
    if not joined:
        return "/"
    return f"/{joined}"


def build_route_aliases(
    prefix: str = "/",
    schema_url: str = "schema",
    swagger_url: str = "/swagger",
    openapi_url: str = "/openapi.json",
    docs_url: str = "/docs",
) -> dict[str, dict[str, str]]:
    canonical = {
        name: normalize_path(prefix, path)
        for name, path in CANONICAL_ROUTES.items()
    }

    aliases: dict[str, str] = {
        normalize_path(prefix, schema_url): canonical["openapi"],
        normalize_path(prefix, swagger_url): canonical["docs"],
        normalize_path(prefix, openapi_url): canonical["openapi"],
        normalize_path(prefix, docs_url): canonical["docs"],
        normalize_path(prefix, "schema"): canonical["openapi"],
        normalize_path(prefix, "swagger"): canonical["docs"],
        normalize_path(prefix, "health"): canonical["healthz"],
        normalize_path(prefix, "healthz"): canonical["healthz"],
    }

    return {"canonical": canonical, "aliases": aliases}


def canonical_alias_pairs(prefix: str = "/", schema_url: str = "schema", swagger_url: str = "/swagger",
                          openapi_url: str = "/openapi.json", docs_url: str = "/docs") -> dict[str, list[str]]:
    """Return canonical route -> compatibility aliases list."""
    mapping = build_route_aliases(prefix=prefix, schema_url=schema_url, swagger_url=swagger_url,
                                 openapi_url=openapi_url, docs_url=docs_url)
    aliases_by_canonical: dict[str, list[str]] = {path: [] for path in mapping["canonical"].values()}
    for alias, canonical in mapping["aliases"].items():
        if alias == canonical:
            continue
        aliases_by_canonical.setdefault(canonical, []).append(alias)
    for paths in aliases_by_canonical.values():
        paths.sort()
    return aliases_by_canonical


@dataclass
class ContractRoute:
    path: str
    canonical: str
    aliases: list[str]
    handler: Callable
