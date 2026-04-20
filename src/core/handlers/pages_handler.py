import subprocess
import tempfile
from pathlib import Path
from .base_handler import BaseHandler, ConversionResult

class PagesHandler(BaseHandler):
    """Apple Pages 파일을 AppleScript를 통해 docx로 변환 후 MarkItDown으로 처리하는 핸들러 (Mac 전용)."""

    def __init__(self):
        self.supported_extensions = {'.pages'}

    def can_handle(self, file_extension: str) -> bool:
        return file_extension.lower() in self.supported_extensions

    def convert(self, input_path: Path, output_dir: Path) -> ConversionResult:
        try:
            # 임시 폴더에 .docx로 먼저 내보내기
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_docx = Path(tmp_dir) / f"{input_path.stem}.docx"

                # AppleScript로 Pages → docx 내보내기
                script = f'''
                    tell application "Pages"
                        set theDoc to open POSIX file "{input_path}"
                        export theDoc to POSIX file "{tmp_docx}" as Microsoft Word
                        close theDoc saving no
                    end tell
                '''
                result = subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True, text=True, timeout=60
                )

                if result.returncode != 0:
                    return ConversionResult(
                        input_path=input_path,
                        success=False,
                        error_message=f"Pages 내보내기 실패: {result.stderr.strip()}"
                    )

                if not tmp_docx.exists():
                    return ConversionResult(
                        input_path=input_path,
                        success=False,
                        error_message="Pages에서 docx 파일이 생성되지 않았습니다."
                    )

                # 내보낸 docx를 MarkItDown으로 변환
                from markitdown import MarkItDown
                md = MarkItDown()
                md_result = md.convert(str(tmp_docx))

                output_path = output_dir / f"{input_path.stem}.md"
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(md_result.text_content)

                return ConversionResult(
                    input_path=input_path,
                    output_path=output_path,
                    success=True,
                    warnings=["Pages → docx → Markdown 순서로 변환되었습니다."]
                )

        except subprocess.TimeoutExpired:
            return ConversionResult(
                input_path=input_path,
                success=False,
                error_message="Pages 변환 시간 초과 (60초). Pages 앱이 설치되어 있는지 확인해 주세요."
            )
        except Exception as e:
            return ConversionResult(
                input_path=input_path,
                success=False,
                error_message=str(e)
            )
