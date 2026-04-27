from pathlib import Path
from .handlers.base_handler import BaseHandler, ConversionResult
from .handlers.markitdown_handler import MarkItDownHandler
from .handlers.hwp_handler import HwpHandler
from .handlers.text_handler import TextHandler
from .handlers.pages_handler import PagesHandler
from .gemma_handler import gemma_2b, gemma_4b

class DocumentConverter:
    """확장자에 따라 적절한 핸들러를 호출하여 문서를 변환하는 메인 변환기."""

    def __init__(self):
        # 핸들러 우선순위에 따라 등록 (MarkItDown이 포괄적이므로 나중에 등록하거나
        # 특정 포맷을 명시적으로 처리하는 핸들러를 먼저 체크)
        self.handlers: list[BaseHandler] = [
            HwpHandler(),
            TextHandler(),
            PagesHandler(),  # Pages 핸들러 추가
            MarkItDownHandler()  # 가장 범용적인 핸들러를 마지막에 배치
        ]

    def convert(self, input_path: str | Path, output_dir: str | Path, use_ai: bool = False, ai_model: str = "2b") -> ConversionResult:
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
                result = handler.convert(path, out_dir)
                if result.success and use_ai and result.output_path:
                    # AI 처리 적용
                    self._apply_ai_processing(result.output_path, ai_model)
                return result
        
        return ConversionResult(
            input_path=path,
            success=False,
            error_message=f"지원하지 않는 파일 형식입니다: {suffix}"
        )

    def _apply_ai_processing(self, output_path: Path, ai_model: str):
        """AI 모델을 사용하여 출력 파일을 후처리합니다."""
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # AI 모델 선택
            if ai_model == "4b":
                processed = gemma_4b.process_text(content)
            else:
                processed = gemma_2b.process_text(content)
            
            # 처리된 내용으로 파일 덮어쓰기
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(processed)
                
        except Exception as e:
            print(f"AI 처리 실패: {e}")
