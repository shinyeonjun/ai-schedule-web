# MUFI 변경 로그

모든 주요 변경 사항이 이 파일에 기록됩니다.

## [1.0.0] - 2025-01-04

### 추가된 기능
- **통화 분석 시스템**: 파일 업로드(TXT, DOCX, PDF) 및 직접 텍스트 입력을 통한 AI 기반 통화 분석
- **실시간 DB 저장**: Supabase PostgreSQL 연동으로 분석 결과 자동 저장
- **컬럼별 수정 기능**: 요약, 상세 설명, 장소, 시작일시, 종료일시 개별 수정 가능
- **액션 아이템 관리**: 체크박스를 통한 완료 상태 관리 및 DB 연동
- **이메일 발송**: 분석된 일정을 여러 명에게 ICS 파일 첨부하여 발송
- **일정 공유**: 사용자 간 분석 결과 공유 기능
- **연락처 관리**: 자주 사용하는 연락처 저장 및 관리

### 기술적 구현
- **백엔드**: FastAPI 기반 REST API
- **프론트엔드**: 바닐라 JavaScript + HTML/CSS
- **데이터베이스**: Supabase PostgreSQL
- **AI**: OpenAI GPT 연동
- **파일 처리**: Python-docx, PyPDF2, aiofiles
- **인증**: Supabase Auth (향후 구현 예정)

### API 엔드포인트
- `POST /api/analyze/file` - 파일 분석 및 DB 저장
- `POST /api/analyze/text` - 텍스트 분석 및 DB 저장
- `GET /api/results` - 분석 결과 목록 조회
- `GET /api/results/{id}` - 특정 분석 결과 조회
- `PATCH /api/results/{id}` - 분석 결과 필드 업데이트
- `PATCH /api/results/{id}/actions/{index}` - 액션 아이템 상태 업데이트
- `DELETE /api/results/{id}` - 분석 결과 삭제

### 데이터베이스 스키마
- `analysis_results` - 메인 분석 결과
- `analysis_schedules` - 일정 정보
- `analysis_participants` - 참석자 정보
- `analysis_actions` - 액션 아이템

### UI/UX 특징
- **3개 메인 탭**: 통화 분석, 메일 보내기, 일정 공유
- **실시간 피드백**: 분석 중, 완료, 오류 상태 표시
- **드래그 앤 드롭**: 파일 업로드 및 텍스트 붙여넣기 지원
- **반응형 디자인**: 모바일 및 데스크톱 지원
- **다크/라이트 테마**: 깔끔한 현대적 디자인

### 보안 및 성능
- **파일 크기 제한**: 10MB 이하
- **텍스트 길이 제한**: 10,000자 이하
- **파일 형식 검증**: TXT, DOCX, PDF만 허용
- **에러 처리**: 포괄적인 예외 처리 및 사용자 친화적 오류 메시지 