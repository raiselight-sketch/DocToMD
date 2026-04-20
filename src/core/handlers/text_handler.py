import shutil
from pathlib import Path
from .base_handler import BaseHandler, ConversionResult

class TextHandler(BaseHandler):
    """일반 텍스트(.txt) 및 지원 가능한 텍스트 포맷을 처리하는 핸들러."""

    def __init__(self):
        self.supported_extensions = {'.txt', '.rtf'}

    def can_handle(self, file_extension: str) -> bool:
        return file_extension.lower() in self.supported_extensions

    def convert(self, input_path: Path, output_dir: Path) -> ConversionResult:
        try:
            output_path = output_dir / f"{input_path.stem}.md"
            
            # .txt는 단순히 확장자만 바꿔서 복사하거나 내용을 읽어서 저장
            # 인코딩 문제가 있을 수 있으므로 UTF-8로 읽어서 저장하는 것이 안전함
            try:
                # UTF-8 시도
                with open(input_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                # euc-kr(cp949) 시도
                with open(input_path, "r", encoding="cp949") as f:
                    content = f.read()
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)

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
