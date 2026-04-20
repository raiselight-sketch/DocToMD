from pathlib import Path
from markitdown import MarkItDown
from .base_handler import BaseHandler, ConversionResult

class MarkItDownHandler(BaseHandler):
    """markitdown 패키지를 사용하여 다양한 문서를 변환하는 핸들러."""
    
    def __init__(self):
        # markitdown 인스턴스 생성
        # 추후 LLM 옵션 등을 추가할 수 있음
        self.md = MarkItDown()
        self.supported_extensions = {
            '.docx', '.doc',
            '.pdf',
            '.pptx', '.ppt',
            '.xlsx', '.xls', '.csv',
            '.html', '.htm',
            '.png', '.jpg', '.jpeg'
        }

    def can_handle(self, file_extension: str) -> bool:
        return file_extension.lower() in self.supported_extensions

    def convert(self, input_path: Path, output_dir: Path) -> ConversionResult:
        try:
            # 출력 파일 경로 설정 (.md)
            output_path = output_dir / f"{input_path.stem}.md"
            
            # markitdown 변환 실행
            result = self.md.convert(str(input_path))
            
            # 결과 텍스트 저장
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result.text_content)
            
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
