from pathlib import Path
from markitdown import MarkItDown
from .base_handler import BaseHandler, ConversionResult

class MarkItDownHandler(BaseHandler):
    """
    Microsoft MarkItDown을 사용하는 범용 핸들러.
    docx, pptx, xlsx, html 등 다양한 포맷을 지원합니다.
    """

    def __init__(self):
        self._md = MarkItDown()
        # MarkItDown이 지원하는 일반적인 확장자들
        self.supported_extensions = {
            ".docx", ".pptx", ".xlsx", ".html", ".htm", ".csv", ".json", ".xml"
        }

    def can_handle(self, file_extension: str) -> bool:
        # MarkItDown은 매우 다양한 형식을 지원하므로, 
        # 다른 전용 핸들러(PDF, Pages 등)가 처리하지 못하는 경우를 위해 넓게 설정할 수도 있습니다.
        return file_extension.lower() in self.supported_extensions or True

    def convert(self, input_path: Path, output_dir: Path) -> ConversionResult:
        output_path = output_dir / f"{input_path.stem}.md"
        
        try:
            result = self._md.convert(str(input_path))
            md_text = result.text_content
            output_path.write_text(md_text, encoding="utf-8")

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
