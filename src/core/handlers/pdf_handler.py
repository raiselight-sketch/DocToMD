"""
PDF 전용 핸들러.

동작 방식:
1. PDF에서 텍스트가 거의 추출되지 않으면 → 스캔본으로 판단
2. ocrmypdf (한국어+영어) 로 텍스트 레이어를 입혀 새 PDF 생성
3. 텍스트 PDF를 markitdown 으로 Markdown 변환
"""

import subprocess
import tempfile
from pathlib import Path

from markitdown import MarkItDown

from .base_handler import BaseHandler, ConversionResult

# 텍스트가 이 글자 수 미만이면 스캔본으로 간주
SCAN_THRESHOLD = 100


def _extract_text_length(pdf_path: Path) -> int:
    """pikepdf 없이 pdfminer 또는 pypdfium2로 텍스트 길이 추정."""
    try:
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(str(pdf_path))
        total = ""
        for i in range(min(len(doc), 3)):   # 앞 3페이지만 샘플
            page = doc[i]
            textpage = page.get_textpage()
            total += textpage.get_text_range()
        return len(total.strip())
    except Exception:
        return 9999   # 오류 시 텍스트 있다고 가정 → OCR 건너뜀


def _run_ocr(input_pdf: Path, output_pdf: Path, language: str = "kor+eng") -> tuple[bool, str]:
    """
    ocrmypdf 를 실행하여 OCR 텍스트 레이어를 추가한 PDF 생성.

    Returns:
        (success: bool, message: str)
    """
    cmd = [
        "ocrmypdf",
        "--language", language,
        "--output-type", "pdf",
        "--skip-text",          # 이미 텍스트가 있는 페이지는 건너뜀
        "--optimize", "0",      # 이미지 재압축 안 함 (속도 우선)
        "--jobs", "2",
        str(input_pdf),
        str(output_pdf),
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,        # 최대 5분
        )
        if result.returncode == 0:
            return True, "OCR 성공"
        # exit code 6 = 이미 텍스트 있음 → 정상 처리
        if result.returncode == 6:
            return True, "이미 텍스트 레이어 존재 (OCR 불필요)"
        return False, result.stderr.strip() or result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, "OCR 시간 초과 (5분)"
    except FileNotFoundError:
        return False, "ocrmypdf 명령을 찾을 수 없습니다. (설치 확인 필요)"


class PdfHandler(BaseHandler):
    """스캔 PDF 자동 감지 + OCR 전처리 후 Markdown 변환."""

    def __init__(self):
        self._md = MarkItDown()
        self.supported_extensions = {".pdf"}

    def can_handle(self, file_extension: str) -> bool:
        return file_extension.lower() in self.supported_extensions

    def convert(self, input_path: Path, output_dir: Path) -> ConversionResult:
        output_path = output_dir / f"{input_path.stem}.md"
        warnings: list[str] = []

        # ── Step 1: 텍스트 추출량 확인 ───────────────────────────
        text_len = _extract_text_length(input_path)
        is_scan = text_len < SCAN_THRESHOLD

        source_pdf = input_path   # 실제로 변환에 사용할 PDF

        # ── Step 2: 스캔본이면 OCR 전처리 ────────────────────────
        if is_scan:
            warnings.append(
                f"스캔 PDF 감지 (추출 텍스트 {text_len}자 미만) → "
                "ocrmypdf 한국어 OCR 전처리 중…"
            )
            with tempfile.TemporaryDirectory() as tmp:
                ocr_pdf = Path(tmp) / f"{input_path.stem}_ocr.pdf"
                ok, msg = _run_ocr(input_path, ocr_pdf)

                if ok and ocr_pdf.exists():
                    warnings.append(f"OCR 완료: {msg}")
                    # OCR 결과를 임시경로에서 출력 폴더 옆으로 복사해야
                    # markitdown이 접근 가능하게 함 (TemporaryDirectory 블록 내)
                    ocr_copy = output_dir / f"{input_path.stem}_ocr_temp.pdf"
                    import shutil
                    shutil.copy2(ocr_pdf, ocr_copy)
                    source_pdf = ocr_copy
                else:
                    warnings.append(f"OCR 실패: {msg} → 원본 PDF로 계속 진행")

        # ── Step 3: markitdown 으로 Markdown 변환 ────────────────
        try:
            result = self._md.convert(str(source_pdf))
            md_text = result.text_content

            output_path.write_text(md_text, encoding="utf-8")

            # 임시 OCR PDF 파일 정리
            if source_pdf != input_path and source_pdf.exists():
                source_pdf.unlink(missing_ok=True)

            return ConversionResult(
                input_path=input_path,
                output_path=output_path,
                success=True,
                warnings=warnings,
            )

        except Exception as e:
            # 임시 파일 정리
            if source_pdf != input_path and source_pdf.exists():
                source_pdf.unlink(missing_ok=True)

            return ConversionResult(
                input_path=input_path,
                success=False,
                error_message=str(e),
                warnings=warnings,
            )
