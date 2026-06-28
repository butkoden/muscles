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
