# AI UX 리서치 보고서 생성기

UX 리서치 데이터를 분석하고 보고서를 작성하는 데 시간이 너무 오래 걸린다.

이 프로젝트는 인터뷰 데이터나 리뷰 데이터를 업로드하면 **AI가 자동으로 핵심 인사이트를 도출하고 구조화된 UX 리서치 보고서를 작성**해 주는 웹 애플리케이션입니다.

---

## 주요 기능

- 📁 **파일 업로드**: TXT, CSV, JSON 형식의 인터뷰 / 리뷰 데이터 지원 (최대 5 MB)
- 🤖 **AI 분석**: OpenAI GPT-4o-mini가 데이터를 분석하여 6가지 섹션으로 구성된 보고서 자동 생성
  - 요약 (Executive Summary)
  - 핵심 인사이트 (Key Insights)
  - 사용자 페인 포인트 (User Pain Points)
  - 사용자 니즈 (User Needs)
  - 기회 영역 (Opportunity Areas)
  - 권장 사항 (Recommendations)
- 📋 **보고서 내보내기**: Markdown 복사 / 다운로드 지원

---

## 시작하기

### 1. 저장소 클론

```bash
git clone https://github.com/Lingee050143/AI-UX-Research-Report-Generator.git
cd AI-UX-Research-Report-Generator
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 OpenAI API 키를 입력하세요:

```
OPENAI_API_KEY=your_openai_api_key_here
FLASK_SECRET_KEY=change-this-to-a-random-secret-key
```

### 4. 서버 실행

```bash
python app.py
```

브라우저에서 `http://localhost:5000` 으로 접속하세요.

---

## 테스트 실행

```bash
pip install pytest
python -m pytest tests/ -v
```

---

## 프로젝트 구조

```
├── app.py               # Flask 백엔드 (파일 파싱, AI 분석, 보고서 생성)
├── requirements.txt     # Python 의존성
├── .env.example         # 환경 변수 템플릿
├── templates/
│   └── index.html       # 메인 UI 페이지
├── static/
│   ├── css/style.css    # 스타일시트
│   └── js/main.js       # 프론트엔드 로직
└── tests/
    └── test_app.py      # 단위 테스트
```

