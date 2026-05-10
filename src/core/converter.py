import sys
import asyncio
from pathlib import Path
from .handlers.base_handler import BaseHandler, ConversionResult
from .handlers.pdf_handler import PdfHandler       # PDF (OCR 자동 전처리)
from .handlers.pages_handler import PagesHandler   # Apple Pages
from .handlers.markitdown_handler import MarkItDownHandler
from .handlers.hwp_handler import HwpHandler
from .handlers.text_handler import TextHandler
from .post_processor import AIPostProcessor
from .config_manager import ConfigManager

class DocumentConverter:
    """확장자에 따라 적절한 핸들러를 호출하여 문서를 변환하는 메인 변환기."""

    def __init__(self):
        self.config = ConfigManager()
        # 핸들러 우선순위에 따라 등록
        self.handlers: list[BaseHandler] = [
            PdfHandler(),       # .pdf  (스캔본 자동 OCR 포함)
            PagesHandler(),     # .pages (Apple Pages → docx → md)
            HwpHandler(),       # .hwp / .hwpx
            TextHandler(),      # .txt / .rtf
            MarkItDownHandler() # 나머지 모든 포맷 (docx, pptx, xlsx …)
        ]
        self.post_processor = AIPostProcessor(
            provider=self.config.get("ai_provider"),
            model=self.config.get("ai_model"),
            api_key=self.config.get("gemini_api_key"),
            base_url=self.config.get("ollama_base_url")
        )

    def convert(self, input_path: str | Path, output_dir: str | Path, use_ai: bool = False) -> ConversionResult:
        """파일 경로와 출력 디렉토리를 받아 변환을 수행합니다."""
        path = Path(input_path)
        out_dir = Path(output_dir)
        
        # 출력 디렉토리가 없으면 생성
        out_dir.mkdir(parents=True, exist_ok=True)
        
        if not path.exists():
            return ConversionResult(
                input_path=path,
                success=False,
                error_message=f"파일을 찾을 수 없습니다: {path}"
            )

        suffix = path.suffix.lower()
        
        # 적절한 핸들러 찾기
        result = None
        for handler in self.handlers:
            if handler.can_handle(suffix):
                result = handler.convert(path, out_dir)
                break
        
        if not result:
            return ConversionResult(
                input_path=path,
                success=False,
                error_message=f"지원하지 않는 파일 형식입니다: {suffix}"
            )

        # AI 후처리 (성공한 경우에만 수행)
        if result.success and use_ai and result.output_path:
            try:
                original_text = result.output_path.read_text(encoding="utf-8")
                # 비동기 처리를 동기식으로 호출
                processed_text = asyncio.run(self.post_processor.process(original_text))
                result.output_path.write_text(processed_text, encoding="utf-8")
            except Exception as e:
                if result.warnings is None: result.warnings = []
                result.warnings.append(f"AI 후처리 중 오류 발생: {str(e)}")
        
        return result
