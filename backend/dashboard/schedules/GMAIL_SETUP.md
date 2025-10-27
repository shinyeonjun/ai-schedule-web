# Gmail API 설정 가이드

## 1. Google Cloud Console 설정

### 1.1 프로젝트 생성
1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. 프로젝트 이름: `MUFI Gmail Integration`

### 1.2 Gmail API 활성화
1. API 및 서비스 → 라이브러리
2. "Gmail API" 검색 후 활성화
3. `gmail.googleapis.com` API 활성화

### 1.3 OAuth 2.0 클라이언트 ID 생성
1. API 및 서비스 → 사용자 인증 정보
2. "사용자 인증 정보 만들기" → "OAuth 2.0 클라이언트 ID"
3. 애플리케이션 유형: **웹 애플리케이션**
4. 승인된 리디렉션 URI 추가:
   - `http://localhost:8000/api/schedules/gmail/callback`
   - `http://127.0.0.1:8000/api/schedules/gmail/callback`

### 1.4 인증 정보 다운로드
1. 생성된 OAuth 2.0 클라이언트 ID 클릭
2. "JSON 다운로드" 클릭
3. 다운로드된 파일을 `backend/dashboard/schedules/gmail_credentials.json`로 저장

## 2. 환경 변수 설정

### 2.1 .env 파일에 추가
```env
GMAIL_CLIENT_ID=your_client_id_here
GMAIL_CLIENT_SECRET=your_client_secret_here
GMAIL_REDIRECT_URI=http://localhost:8000/api/schedules/gmail/callback
```

## 3. 필요한 Python 패키지 설치

```bash
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```

## 4. 파일 구조

```
backend/dashboard/schedules/
├── gmail_service.py          # Gmail API 서비스
├── gmail_credentials.json    # OAuth 2.0 인증 정보 (다운로드 필요)
├── gmail_token.pickle        # 인증 토큰 (자동 생성)
└── GMAIL_SETUP.md           # 이 설정 가이드
```

## 5. 보안 주의사항

### 5.1 인증 파일 보안
- `gmail_credentials.json` 파일을 Git에 커밋하지 마세요
- `.gitignore`에 다음 항목 추가:
  ```
  backend/dashboard/schedules/gmail_credentials.json
  backend/dashboard/schedules/gmail_token.pickle
  ```

### 5.2 API 할당량
- Gmail API는 일일 할당량이 있습니다
- 무료 계정: 1,000,000,000 쿼리/일
- 사용량 모니터링 권장

## 6. 테스트

### 6.1 인증 테스트
```bash
# 서버 실행 후
curl http://localhost:8000/api/schedules/gmail-auth-status
```

### 6.2 전송 테스트
1. 분석 결과에서 일정 선택
2. "메일 보내기" 버튼 클릭
3. 수신자 이메일 입력
4. 전송 확인

## 7. 문제 해결

### 7.1 인증 오류
- `gmail_credentials.json` 파일이 올바른 위치에 있는지 확인
- OAuth 2.0 클라이언트 ID가 올바른지 확인
- 리디렉션 URI가 정확한지 확인

### 7.2 전송 실패
- Gmail API 할당량 확인
- 네트워크 연결 상태 확인
- 수신자 이메일 형식 확인

## 8. 프로덕션 배포 시 주의사항

### 8.1 도메인 변경
- 프로덕션 도메인으로 리디렉션 URI 변경
- Google Cloud Console에서 승인된 도메인 추가

### 8.2 보안 강화
- 환경 변수로 민감한 정보 관리
- HTTPS 사용 필수
- 토큰 암호화 저장 고려
