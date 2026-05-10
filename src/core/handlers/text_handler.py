from pathlib import Path
from .base_handler import BaseHandler, ConversionResult

class TextHandler(BaseHandler):
    """
    일반 텍스트(.txt) 및 서식 있는 텍스트(.rtf) 핸들러.
    """

    def __init__(self):
        self.supported_extensions = {".txt", ".rtf"}

    def can_handle(self, file_extension: str) -> bool:
        return file_extension.lower() in self.supported_extensions

    def convert(self, input_path: Path, output_dir: Path) -> ConversionResult:
        output_path = output_dir / f"{input_path.stem}.md"
        
        try:
            # 텍스트 파일 읽기 (인코딩 시도)
            for encoding in ['utf-8', 'cp949', 'euc-kr']:
                try:
                    text = input_path.read_text(encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                return ConversionResult(
                    input_path=input_path,
                    success=False,
                    error_message="지원하지 않는 파일 인코딩입니다."
                )

            output_path.write_text(text, encoding="utf-8")

            return ConversionResult(
                input_path=input_path,
                output_path=output_path,
                success=True
            )
        except Exception as e:
            return ConversionResult(
                input_path=input_path,
                success=False,
                error_message=str(e)
            )
