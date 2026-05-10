# 작업 계획: Pages 변환 안정화 및 누락된 파일 복구

현재 `src/core/converter.py`에서 여러 핸들러를 임포트하고 있으나, 실제 `src/core/handlers/` 디렉토리에는 `pdf_handler.py`만 존재하고 나머지는 누락된 상태입니다. 특히 사용자가 지적한 `Pages` 변환 기능이 정상 동작하려면 `PagesHandler` 및 기반 클래스인 `BaseHandler`의 복구가 시급합니다.

## 1. 현재 상태 진단
- [x] `src/core/handlers/` 내 누락된 파일 목록 확정 (`base_handler.py`, `pages_handler.py`, `markitdown_handler.py`, `hwp_handler.py`, `text_handler.py`)
- [x] `converter.py`의 임포트 구조와 실제 파일 정합성 확인
- [x] `pages` 변환 방식 검토 (Mac 환경이므로 AppleScript + MarkItDown 조합 확정)

## 2. 핵심 로직 복구
- [x] `base_handler.py`: 모든 핸들러의 인터페이스 정의 및 복구 완료
- [x] `pages_handler.py`: Apple Pages 변환 로직 초기 구현 완료
- [x] `markitdown_handler.py`: Microsoft MarkItDown 기반 범용 핸들러 복구 완료
- [x] `hwp_handler.py` & `text_handler.py`: 기타 포맷 지원 핸들러 복구 완료
- [x] `src/main.py` 및 패키지 구조(`__init__.py`) 복구 완료

## 3. Pages 변환 세부 구현 및 안정화
- [ ] AppleScript 로직 강화 (파일 열림 상태, 권한 문제 대응)
- [ ] 변환 대기 시간 및 예외 처리 로직 추가
- [ ] Pages 앱 상태 체크 로직 구현


## 4. 테스트 및 검증
- [ ] 더미 `.pages` 파일 또는 테스트 파일을 통한 변환 테스트 실행
- [ ] GUI(`main_window.py`)와의 연동 확인

## 5. 최종 점검
- [ ] 전체 변환 프로세스 안정성 확인
- [ ] 사용자 요청 사항 반영 여부 체크
