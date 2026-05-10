# DocToMD Converter

모든 문서(.docx, .pdf, .pptx, .xlsx, .hwp 등)를 Markdown으로 일괄 변환하는 Mac/Windows 데스크톱 앱.

## 실행
```bash
# 방법 1: venv 활성화 후 실행
source .venv/bin/activate
python src/main.py

# 방법 2: 직접 실행
~/doctomd/.venv/bin/python ~/doctomd/src/main.py
```

## 설치 경로
`~/doctomd` (로컬) — Google Drive에 두면 심볼릭 링크가 깨져 venv/PyInstaller 빌드가 동작하지 않음.

## 진행 상황
- [x] Phase 1 환경 설정
- [x] Phase 2 변환 코어
- [x] Phase 3 GUI
- [x] Phase 4 배치 처리
- [x] Phase 5 패키징
- [x] Phase 6 테스트 & 배포
