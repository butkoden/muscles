from muscles.core import BaseResponse, cors


class Request:
    method = "GET"
    origin = "https://app.example"


def test_cors_adds_response_headers():
    middleware = cors(allow_origins=["https://app.example"], allow_credentials=True)

    response = middleware(Request(), lambda request: BaseResponse(body=b"ok"))

    assert response.headers["Access-Control-Allow-Origin"] == "https://app.example"
    assert response.headers["Access-Control-Allow-Credentials"] == "true"


def test_cors_preflight_response():
    middleware = cors(allow_origins=["*"], allow_methods=["GET"])

    response = middleware.preflight_response(Request())

    assert response.status == 204
    assert response.headers["Access-Control-Allow-Methods"] == "GET"


def test_cors_preflight_allows_bearer_profile_request():
    middleware = cors(
        allow_origins=["http://example.test"],
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    response = middleware.preflight_response(Request())

    assert response.status == 204
    assert response.headers["Access-Control-Allow-Origin"] == "http://example.test"
    assert response.headers["Access-Control-Allow-Headers"] == "Authorization, Content-Type"
    assert "GET" in response.headers["Access-Control-Allow-Methods"]


def test_cors_preserves_protocol_responses_with_header_append():
    class ProtocolResponse:
        def __init__(self):
            self.headers = []

        def header_append(self, header):
            self.headers.append(header)

    response = ProtocolResponse()
    middleware = cors(allow_origins=["https://app.example"])

    result = middleware.apply(response, Request())

    assert result is response
    assert ("Access-Control-Allow-Origin", "https://app.example") in response.headers
