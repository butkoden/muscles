from muscles.core.route_contract import build_route_aliases, canonical_alias_pairs, normalize_path


def test_normalize_path_merges_fragments():
    assert normalize_path("", "/", "api", "v1") == "/api/v1"


def test_build_route_aliases_contains_canonical_and_compatibility_aliases():
    payload = build_route_aliases(prefix="/api", schema_url="schema", swagger_url="/swagger", openapi_url="/openapi.json", docs_url="/docs")
    assert payload["canonical"]["openapi"] == "/api/openapi.json"
    assert payload["canonical"]["docs"] == "/api/docs"
    assert payload["canonical"]["redoc"] == "/api/redoc"
    assert payload["canonical"]["healthz"] == "/api/healthz"
    assert payload["canonical"]["ready"] == "/api/ready"
    assert payload["canonical"]["live"] == "/api/live"
    assert payload["aliases"]["/api/schema"] == "/api/openapi.json"
    assert payload["aliases"]["/api/swagger"] == "/api/docs"
    assert payload["aliases"]["/api/health"] == "/api/healthz"


def test_canonical_alias_pairs_groups_aliases_by_canonical_route():
    payload = canonical_alias_pairs(prefix="/api", schema_url="schema", swagger_url="/swagger", openapi_url="/openapi.json", docs_url="/docs")
    assert payload["/api/openapi.json"] == ["/api/schema"]
    assert payload["/api/docs"] == ["/api/swagger"]
    assert payload["/api/healthz"] == ["/api/health"]
