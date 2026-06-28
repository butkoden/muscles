from pathlib import Path

from muscles.core import (
    BaseResponse,
    BytesResponse,
    FileResponse,
    HtmlResponse,
    JsonResponse,
    NoContentResponse,
    normalize_response,
)


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


def test_no_content_response_has_empty_body():
    normalized = normalize_response(NoContentResponse())
    assert normalized.status == 204
    assert normalized.body == b""
    assert normalized.headers["Content-Length"] == "0"


def test_bytes_response_sets_content_type():
    normalized = normalize_response(BytesResponse(b"PNG", content_type="image/png"))
    assert normalized.body == b"PNG"
    assert normalized.headers["Content-Type"] == "image/png"


def test_file_response_reads_file_and_uses_mimetype(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_text("hello", encoding="utf-8")

    normalized = normalize_response(FileResponse(path))

    assert normalized.body == b"hello"
    assert normalized.headers["Content-Type"] == "text/plain"
    assert normalized.headers["Content-Length"] == "5"
    assert normalized.headers["Content-Disposition"] == 'inline; filename="sample.txt"'
