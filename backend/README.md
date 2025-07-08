# MUFI 백엔드 API

통화 내용을 AI로 분석하여 자동으로 일정을 생성하고 관리하는 백엔드 시스템입니다.

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 가상환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
OPENAI_API_KEY=your_openai_api_key_here
ENVIRONMENT=development
```

### 3. 서버 실행

```bash
# 방법 1: 시작 스크립트 사용
python start_server.py

# 방법 2: 직접 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 접속

- **프론트엔드**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **OpenAPI**: http://localhost:8000/redoc

## 📁 프로젝트 구조

```
backend/
├── main.py                 # FastAPI 메인 애플리케이션
├── config.py              # 설정 관리
├── start_server.py        # 서버 시작 스크립트
├── requirements.txt       # Python 의존성
├── models/               # Pydantic 모델
│   ├── __init__.py
│   └── analysis.py       # 분석 관련 모델
├── routers/              # API 라우터
│   ├── __init__.py
│   └── analysis.py       # 통화 분석 API
├── services/             # 비즈니스 로직
│   ├── __init__.py
│   ├── gpt_service.py    # GPT API 서비스
│   └── file_service.py   # 파일 처리 서비스
└── uploads/              # 업로드된 파일 저장소
```

## 🔧 API 엔드포인트

### 통화 분석

- `POST /api/analyze/text` - 텍스트 내용 분석
- `POST /api/analyze/file` - 파일 업로드 및 분석
- `POST /api/upload` - 파일 업로드만
- `POST /api/analyze/uploaded-file` - 업로드된 파일 분석

### ICS 생성

- `POST /api/generate-ics` - 분석 결과를 ICS 포맷으로 변환
- `POST /api/download-ics` - ICS 파일 다운로드

### 유틸리티

- `GET /api/health` - 서비스 상태 확인
- `POST /api/cleanup` - 오래된 파일 정리

## 🎯 주요 기능

### 1. 통화 내용 분석
- GPT-4를 사용한 고품질 분석
- 5개 필드 추출: 요약, 설명, 장소, 시작일시, 종료일시
- 다양한 날짜 형식 자동 인식 및 변환

### 2. 파일 지원
- `.txt` - 텍스트 파일
- `.docx` - Microsoft Word 문서 (python-docx 필요)
- `.pdf` - PDF 문서 (PyPDF2 필요)

### 3. ICS 생성
- 표준 iCalendar 형식 지원
- 다운로드 가능한 .ics 파일 생성
- 고유 UID 및 타임스탬프

### 4. 보안 및 안정성
- 파일 크기 및 형식 검증
- 자동 파일 정리
- CORS 설정
- 에러 핸들링

## 🔒 보안 설정

### 환경 변수
- `OPENAI_API_KEY`: OpenAI API 키 (필수)
- `ENVIRONMENT`: 실행 환경 (development/production)

### 파일 업로드 제한
- 최대 파일 크기: 10MB
- 허용 형식: .txt, .docx, .pdf
- 자동 파일 정리: 1일 후 삭제

## 🛠 개발 가이드

### 코드 구조
- **모듈화**: 각 기능별로 분리된 서비스
- **타입 힌트**: Pydantic 모델 사용
- **에러 처리**: 포괄적인 예외 처리
- **문서화**: 자동 API 문서 생성

### 확장 방법
1. 새 라우터 추가: `routers/` 폴더에 추가
2. 새 서비스 추가: `services/` 폴더에 추가
3. 새 모델 추가: `models/` 폴더에 추가
4. `main.py`에서 라우터 등록

## 📝 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 