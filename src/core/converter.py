from pathlib import Path
from .handlers.base_handler import BaseHandler, ConversionResult
from .handlers.markitdown_handler import MarkItDownHandler
from .handlers.hwp_handler import HwpHandler
from .handlers.text_handler import TextHandler

class DocumentConverter:
    """확장자에 따라 적절한 핸들러를 호출하여 문서를 변환하는 메인 변환기."""

    def __init__(self):
        # 핸들러 우선순위에 따라 등록 (MarkItDown이 포괄적이므로 나중에 등록하거나
        # 특정 포맷을 명시적으로 처리하는 핸들러를 먼저 체크)
        self.handlers: list[BaseHandler] = [
            HwpHandler(),
            TextHandler(),
            MarkItDownHandler()  # 가장 범용적인 핸들러를 마지막에 배치
        ]

    def convert(self, input_path: str | Path, output_dir: str | Path) -> ConversionResult:
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
        for handler in self.handlers:
            if handler.can_handle(suffix):
                return handler.convert(path, out_dir)
        
        return ConversionResult(
            input_path=path,
            success=False,
            error_message=f"지원하지 않는 파일 형식입니다: {suffix}"
        )
