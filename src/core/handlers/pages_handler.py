import os
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path
from .base_handler import BaseHandler, ConversionResult
from markitdown import MarkItDown


def _find_apple_pages_app() -> Path | None:
    """정식 Apple Pages 앱의 경로를 찾아 반환합니다."""
    candidates = {
        Path("/Applications/Pages.app"),
        Path("/System/Applications/Pages.app")
    }
    try:
        res = subprocess.run(
            ['mdfind', "kMDItemCFBundleIdentifier == 'com.apple.Pages'"],
            capture_output=True, text=True, timeout=5
        )
        for line in res.stdout.splitlines():
            if line.strip():
                candidates.add(Path(line.strip()))
    except Exception:
        pass

    for path in candidates:
        if not path.exists():
            continue
        try:
            res = subprocess.run(
                ['codesign', '-dv', '--verbose=2', str(path)],
                capture_output=True, text=True, timeout=5
            )
            output = res.stdout + res.stderr
            has_authority = any(auth in output for auth in [
                "Authority=Software Signing",
                "TeamIdentifier=K36BKF7T3D"
            ])
            has_identifier = any(ident in output for ident in [
                "Identifier=com.apple.iWork.Pages",
                "Identifier=com.apple.Pages"
            ])
            if has_authority and has_identifier:
                return path
        except Exception:
            continue
    return None


def _decompress_iwa(data: bytes) -> bytes:
    """iWork .iwa 파일의 Snappy framing format을 해제합니다."""
    try:
        import snappy
    except ImportError:
        return data  # snappy 미설치 시 원본 반환

    result = bytearray()
    pos = 0
    while pos + 4 <= len(data):
        chunk_type = data[pos]
        chunk_len = data[pos + 1] | (data[pos + 2] << 8) | (data[pos + 3] << 16)
        pos += 4
        if chunk_len == 0 or pos + chunk_len > len(data):
            break
        chunk_data = data[pos:pos + chunk_len]
        pos += chunk_len

        if chunk_type == 0x00:
            try:
                result.extend(snappy.decompress(chunk_data))
            except Exception:
                result.extend(chunk_data)
        elif chunk_type == 0x01:
            result.extend(chunk_data)
        # 0xff (stream identifier) 등은 무시

    return bytes(result) if result else data


def _extract_text_from_pages_zip(pages_path: Path) -> str | None:
    """Pages ZIP 아카이브에서 직접 텍스트를 추출합니다 (Pages 앱 불필요)."""
    try:
        if not zipfile.is_zipfile(str(pages_path)):
            return None

        with zipfile.ZipFile(str(pages_path), 'r') as zf:
            names = zf.namelist()
            # 실제 콘텐츠가 있는 .iwa 파일만 선택 (Stylesheet, Metadata 등 제외)
            iwa_files = sorted([
                n for n in names if n.endswith('.iwa')
                and 'Stylesheet' not in n
                and 'Metadata' not in n
                and 'ViewState' not in n
                and 'AnnotationAuthor' not in n
                and 'CalculationEngine' not in n
            ])
            all_text_parts = []

            for iwa_name in iwa_files:
                raw = zf.read(iwa_name)
                # Snappy framing format 해제 시도
                data = _decompress_iwa(raw)

                # UTF-8 한글(3바이트) + ASCII + 줄바꿈이 8바이트 이상 연속된 패턴
                pattern = re.compile(
                    b'(?:'
                    b'[\xea-\xed][\x80-\xbf][\x80-\xbf]'
                    b'|[\xc2-\xdf][\x80-\xbf]'
                    b'|[\x20-\x7e]'
                    b'|[\x0a\x0d]'
                    b'){8,}'
                )
                matches = pattern.findall(data)
                for m in matches:
                    try:
                        text = m.decode('utf-8').strip()
                        korean_count = len(re.findall(r'[\uAC00-\uD7A3]', text))
                        if korean_count < 3:
                            continue
                        # iWork 내부 메타데이터 필터링
                        iwork_keywords = [
                            'paragraphStyle', 'headerRow', 'footerRow',
                            'tableCell', 'tocentry', 'referenceLine',
                            'valueaxis', 'stickyComment', 'liststyle',
                            'HelveticaNeue', 'AppleSDGothicNeo',
                            'Document.iwa', 'Stylesheet', 'ViewState',
                            'AnnotationAuthor', 'CalculationEngine',
                        ]
                        if any(kw in text for kw in iwork_keywords):
                            continue
                        # 후행 '*' 등 잔여물 제거
                        text = text.rstrip('*').strip()
                        if text and len(text) >= 6:
                            all_text_parts.append(text)
                    except UnicodeDecodeError:
                        continue

            if all_text_parts:
                seen = set()
                unique_parts = []
                for part in all_text_parts:
                    if part not in seen:
                        seen.add(part)
                        unique_parts.append(part)
                return '\n\n'.join(unique_parts)

    except Exception:
        pass
    return None


class PagesHandler(BaseHandler):
    """Pages 문서를 Markdown으로 변환하는 핸들러.
    1순위: 정식 Apple Pages AppleScript 변환
    2순위: ZIP 아카이브에서 직접 텍스트 추출 (Pages 미설치 시)"""

    def __init__(self):
        self.md = MarkItDown()
        self.supported_extensions = {'.pages'}

    def can_handle(self, file_extension: str) -> bool:
        return file_extension.lower() in self.supported_extensions

    def convert(self, input_path: Path, output_dir: Path) -> ConversionResult:
        # 1순위: 정식 Pages 앱을 통한 AppleScript 변환
        pages_path = _find_apple_pages_app()
        if pages_path:
            result = self._convert_via_applescript(input_path, output_dir, pages_path)
            if result.success:
                return result

        # 2순위: ZIP 아카이브에서 직접 텍스트 추출 (snappy + protobuf)
        return self._convert_via_zip_extraction(input_path, output_dir)

    def _convert_via_applescript(self, input_path: Path, output_dir: Path, pages_path: Path) -> ConversionResult:
        """정식 Pages 앱의 AppleScript를 사용하여 변환합니다."""
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                docx_path = Path(tmpdir) / f"{input_path.stem}.docx"
                input_posix = str(input_path.absolute()).replace('"', '\\"')
                docx_posix = str(docx_path.absolute()).replace('"', '\\"')
                # 서드파티 앱 충돌 방지를 위해 절대 경로로 지정
                pages_posix = str(pages_path.absolute()).replace('"', '\\"')

                applescript = f'''
                set inputPath to POSIX file "{input_posix}"
                set outputPath to POSIX file "{docx_posix}"
                tell application "{pages_posix}"
                    activate
                    try
                        set theDoc to open inputPath
                        export theDoc to outputPath as Microsoft Word
                        close theDoc saving no
                    on error errMsg
                        return "ERROR: " & errMsg
                    end try
                end tell
                return "SUCCESS"
                '''

                result = subprocess.run(['osascript', '-e', applescript], capture_output=True, text=True)
                if "ERROR:" in result.stdout or result.returncode != 0:
                    error_msg = result.stdout.strip() if "ERROR:" in result.stdout else result.stderr
                    return ConversionResult(
                        input_path=input_path, success=False,
                        error_message=f"Pages Export Failed: {error_msg}"
                    )

                if not docx_path.exists():
                    return ConversionResult(
                        input_path=input_path, success=False,
                        error_message="변환된 Word 파일을 찾을 수 없습니다."
                    )

                md_result = self.md.convert(str(docx_path))
                output_path = output_dir / f"{input_path.stem}.md"
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(md_result.text_content)

                return ConversionResult(
                    input_path=input_path, output_path=output_path, success=True
                )
        except Exception as e:
            return ConversionResult(
                input_path=input_path, success=False, error_message=str(e)
            )

    def _convert_via_zip_extraction(self, input_path: Path, output_dir: Path) -> ConversionResult:
        """Pages ZIP 아카이브에서 직접 텍스트를 추출하여 Markdown으로 변환합니다."""
        try:
            extracted_text = _extract_text_from_pages_zip(input_path)

            if extracted_text and len(extracted_text.strip()) > 10:
                output_path = output_dir / f"{input_path.stem}.md"
                title = input_path.stem
                md_content = f"# {title}\n\n{extracted_text}\n"
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(md_content)
                return ConversionResult(
                    input_path=input_path, output_path=output_path, success=True
                )

            return ConversionResult(
                input_path=input_path, success=False,
                error_message="Pages 파일에서 텍스트를 추출할 수 없습니다. 정식 Apple Pages를 설치하면 더 정확한 변환이 가능합니다."
            )
        except Exception as e:
            return ConversionResult(
                input_path=input_path, success=False,
                error_message=f"Pages ZIP 추출 실패: {str(e)}"
            )
