"""Unit tests for the AI UX Research Report Generator."""

import io
import json
from unittest.mock import MagicMock, patch

import pytest

from app import app, allowed_file, parse_uploaded_file


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ── allowed_file ─────────────────────────────────────────────────────────


@pytest.mark.parametrize("filename,expected", [
    ("data.txt", True),
    ("data.csv", True),
    ("data.json", True),
    ("data.TXT", True),
    ("data.CSV", True),
    ("data.JSON", True),
    ("data.pdf", False),
    ("data.xlsx", False),
    ("data.docx", False),
    ("noextension", False),
])
def test_allowed_file(filename, expected):
    assert allowed_file(filename) is expected


# ── parse_uploaded_file ───────────────────────────────────────────────────


def _make_file(content: bytes, filename: str):
    """Create a mock Werkzeug FileStorage object for testing.

    Args:
        content: The raw bytes the mock file should return when read.
        filename: The filename attribute of the mock (e.g. ``"test.csv"``).

    Returns:
        A :class:`unittest.mock.MagicMock` that mimics the subset of
        ``werkzeug.datastructures.FileStorage`` used by ``parse_uploaded_file``.
    """
    fs = MagicMock()
    fs.filename = filename
    fs.read.return_value = content
    return fs


def test_parse_txt():
    fs = _make_file(b"Hello world", "test.txt")
    result = parse_uploaded_file(fs)
    assert result == "Hello world"


def test_parse_csv():
    fs = _make_file(b"name,age\nAlice,30\nBob,25", "test.csv")
    result = parse_uploaded_file(fs)
    assert "name, age" in result
    assert "Alice, 30" in result
    assert "Bob, 25" in result


def test_parse_json_valid():
    data = {"interview": ["I love the product", "Navigation is confusing"]}
    fs = _make_file(json.dumps(data, ensure_ascii=False).encode(), "test.json")
    result = parse_uploaded_file(fs)
    parsed = json.loads(result)
    assert parsed["interview"] == data["interview"]


def test_parse_json_invalid_falls_back_to_text():
    fs = _make_file(b"not valid json {", "test.json")
    result = parse_uploaded_file(fs)
    assert "not valid json" in result


# ── Index page ────────────────────────────────────────────────────────────


def test_index_returns_200(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "AI UX" in resp.data.decode("utf-8")


# ── /generate endpoint ────────────────────────────────────────────────────


def test_generate_no_file(client):
    resp = client.post("/generate")
    assert resp.status_code == 400
    assert "파일" in resp.get_json()["error"]


def test_generate_empty_filename(client):
    data = {"file": (io.BytesIO(b"content"), "")}
    resp = client.post("/generate", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400


def test_generate_unsupported_extension(client):
    data = {"file": (io.BytesIO(b"content"), "report.pdf")}
    resp = client.post("/generate", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400
    assert "지원하지 않는" in resp.get_json()["error"]


def test_generate_empty_file(client):
    data = {"file": (io.BytesIO(b"   \n  "), "empty.txt")}
    resp = client.post("/generate", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400
    assert "비어 있" in resp.get_json()["error"]


def test_generate_success(client):
    mock_content = "## 요약\n테스트 보고서"
    mock_choice = MagicMock()
    mock_choice.message.content = mock_content
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_openai = MagicMock()
    mock_openai.chat.completions.create.return_value = mock_response

    with patch("app._get_openai_client", return_value=mock_openai):
        data = {"file": (io.BytesIO(b"User interview data here"), "interview.txt")}
        resp = client.post("/generate", data=data, content_type="multipart/form-data")

    assert resp.status_code == 200
    body = resp.get_json()
    assert "report_html" in body
    assert "report_md" in body
    assert mock_content == body["report_md"]


def test_generate_openai_error(client):
    with patch("app._get_openai_client", side_effect=Exception("API error")):
        data = {"file": (io.BytesIO(b"Some interview data"), "data.txt")}
        resp = client.post("/generate", data=data, content_type="multipart/form-data")

    assert resp.status_code == 500
    assert "오류" in resp.get_json()["error"]
