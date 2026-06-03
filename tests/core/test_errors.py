from muscles.core import normalize_problem_payload
from muscles.core import RequestErrorException, ActionError


class DummyRequest:
    path = "/api/test"


def test_normalize_problem_payload_for_domain_error():
    payload = normalize_problem_payload(RequestErrorException(status=422, reason="Invalid body"), request=DummyRequest())
    assert payload["status"] == 422
    assert payload["type"] == "https://muscles.dev/problems/422"
    assert payload["title"] == "Unprocessable Entity"
    assert payload["detail"] == "Invalid body"
    assert payload["instance"] == "/api/test"
    assert set(payload.keys()) == {"type", "title", "status", "detail", "instance"}


def test_normalize_problem_payload_fallbacks_to_internal_for_generic_exception():
    payload = normalize_problem_payload(Exception("boom"))
    assert payload["status"] == 500
    assert payload["type"] == "https://muscles.dev/problems/500"
    assert payload["title"] == "Internal Server Error"
    assert payload["detail"] == "boom"


def test_normalize_problem_payload_with_action_error_custom_type():
    payload = normalize_problem_payload(ActionError(status=409, reason="Conflict", error_type="https://example.test/errors/conflict"))
    assert payload["type"] == "https://example.test/errors/conflict"
    assert payload["status"] == 409
