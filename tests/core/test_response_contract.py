from muscles.core import BaseResponse, HtmlResponse, JsonResponse, normalize_response


def test_normalize_response_keeps_base_response():
    response = BaseResponse(body=b"ok", status=202, headers={"X-Test": "1"}, content_type="text/plain")
    normalized = normalize_response(response)
    assert normalized is response
    assert normalized.headers["Content-Type"] == "text/plain"
    assert normalized.headers["Content-Length"] == "2"


def test_normalize_response_from_dict_to_json():
    normalized = normalize_response({"ok": True})
    assert isinstance(normalized, JsonResponse)
    assert normalized.status == 200
    assert normalized.headers["Content-Type"].startswith("application/json")
    assert normalized.body == b'{"ok": true}'


def test_normalize_response_from_string_to_html():
    normalized = normalize_response("<h1>Hello</h1>")
    assert isinstance(normalized, HtmlResponse)
    assert normalized.status == 200
    assert normalized.headers["Content-Type"].startswith("text/html")


def test_normalize_response_from_tuple():
    normalized = normalize_response(({"ok": True}, 201, {"X-Request-Id": "abc"}))
    assert isinstance(normalized, JsonResponse)
    assert normalized.status == 201
    assert normalized.headers["X-Request-Id"] == "abc"
