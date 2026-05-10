from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

@dataclass
class ConversionResult:
    input_path: Path
    success: bool
    output_path: Optional[Path] = None
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

class BaseHandler:
    """모든 문서 핸들러의 기본 추상 클래스."""

    def can_handle(self, file_extension: str) -> bool:
        """해당 핸들러가 처리할 수 있는 확장자인지 확인."""
        raise NotImplementedError

    def convert(self, input_path: Path, output_dir: Path) -> ConversionResult:
        """문서를 변환하고 결과를 반환."""
        raise NotImplementedError
