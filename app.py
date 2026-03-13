import os
import json
import csv
import io

import bleach
import markdown
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from openai import OpenAI
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

ALLOWED_EXTENSIONS = {"txt", "csv", "json"}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

def _get_openai_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY 환경 변수가 설정되지 않았습니다. "
            ".env 파일을 확인해 주세요."
        )
    return OpenAI(api_key=api_key)


def allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def parse_uploaded_file(file_storage) -> str:
    """Read and normalise uploaded file content into plain text.

    Args:
        file_storage: A Werkzeug ``FileStorage`` object obtained from
            ``request.files``.  The file is read once and not rewound.

    Returns:
        The file content as a Unicode string.  CSV rows are joined with
        commas; JSON data is pretty-printed; plain-text files are returned
        as-is.  Falls back to latin-1 decoding when UTF-8 fails.
    """
    filename = secure_filename(file_storage.filename)
    ext = filename.rsplit(".", 1)[1].lower()
    raw_bytes = file_storage.read()

    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = raw_bytes.decode("latin-1")

    if ext == "json":
        try:
            data = json.loads(text)
            text = json.dumps(data, ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            pass  # treat as plain text if JSON is invalid
    elif ext == "csv":
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        lines = []
        for row in rows:
            lines.append(", ".join(row))
        text = "\n".join(lines)

    return text


def generate_report(raw_text: str) -> str:
    """Call OpenAI to analyse the data and return a Markdown report.

    Args:
        raw_text: Plain-text user data (interview transcripts, reviews, etc.)
            to be analysed.  Only the first 12 000 characters are sent to
            the model to stay within token limits.

    Returns:
        A Markdown-formatted UX research report string.

    Raises:
        RuntimeError: If ``OPENAI_API_KEY`` is not set in the environment.
        openai.OpenAIError: On API-level failures (rate limits, timeouts, etc.).
    """
    system_prompt = (
        "당신은 UX 리서치 전문가입니다. "
        "사용자가 제공한 인터뷰 또는 리뷰 데이터를 분석하여 "
        "구조화된 UX 리서치 보고서를 한국어로 작성하세요.\n\n"
        "보고서는 반드시 다음 섹션을 포함해야 합니다:\n"
        "1. **요약 (Executive Summary)** – 데이터 개요 및 주요 발견 사항을 2–3문장으로 요약합니다.\n"
        "2. **핵심 인사이트 (Key Insights)** – 데이터에서 도출된 3–5개의 핵심 인사이트를 작성합니다.\n"
        "3. **사용자 페인 포인트 (User Pain Points)** – 사용자가 경험한 주요 불편함이나 문제점을 나열합니다.\n"
        "4. **사용자 니즈 (User Needs)** – 사용자가 원하거나 필요로 하는 것들을 정리합니다.\n"
        "5. **기회 영역 (Opportunity Areas)** – 개선하거나 새롭게 만들 수 있는 기회 영역을 제안합니다.\n"
        "6. **권장 사항 (Recommendations)** – 우선순위에 따른 실행 가능한 권장 사항을 제시합니다.\n\n"
        "보고서는 Markdown 형식으로 작성하세요."
    )

    user_message = (
        f"다음은 분석할 데이터입니다:\n\n{raw_text[:12000]}"
    )

    response = _get_openai_client().chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.4,
    )

    return response.choices[0].message.content


def markdown_to_safe_html(md_text: str) -> str:
    """Convert Markdown to HTML and sanitise it against XSS.

    Args:
        md_text: A Markdown-formatted string, typically the AI-generated report.

    Returns:
        A sanitised HTML string that is safe to inject into the DOM via
        ``innerHTML``.  Only a whitelist of tags and attributes is allowed.
    """
    html = markdown.markdown(md_text, extensions=["extra", "nl2br"])
    allowed_tags = list(bleach.sanitizer.ALLOWED_TAGS) + [
        "h1", "h2", "h3", "h4", "h5", "h6",
        "p", "br", "ul", "ol", "li",
        "strong", "em", "blockquote", "code", "pre", "hr",
        "table", "thead", "tbody", "tr", "th", "td",
    ]
    allowed_attributes = {**bleach.sanitizer.ALLOWED_ATTRIBUTES}
    safe_html = bleach.clean(html, tags=allowed_tags, attributes=allowed_attributes)
    return safe_html


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    if "file" not in request.files:
        return jsonify({"error": "파일이 첨부되지 않았습니다."}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "파일을 선택해 주세요."}), 400

    if not allowed_file(file.filename):
        return jsonify(
            {"error": "지원하지 않는 파일 형식입니다. TXT, CSV, JSON 파일만 업로드할 수 있습니다."}
        ), 400

    try:
        raw_text = parse_uploaded_file(file)
    except Exception:
        return jsonify({"error": "파일을 읽는 중 오류가 발생했습니다."}), 400

    if not raw_text.strip():
        return jsonify({"error": "파일이 비어 있습니다."}), 400

    try:
        report_md = generate_report(raw_text)
    except Exception as exc:
        return jsonify({"error": f"AI 분석 중 오류가 발생했습니다: {exc}"}), 500

    report_html = markdown_to_safe_html(report_md)
    return jsonify({"report_html": report_html, "report_md": report_md})


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug)
