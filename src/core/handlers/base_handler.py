from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

@dataclass
class ConversionResult:
    """문서 변환 결과를 담는 데이터 클래스."""
    input_path: Path
    output_path: Optional[Path] = None
    success: bool = False
    error_message: Optional[str] = None
    warnings: Optional[list[str]] = None

class BaseHandler(ABC):
    """모든 문서 변환 핸들러의 추상 베이스 클래스."""
    
    @abstractmethod
    def can_handle(self, file_extension: str) -> bool:
        """해당 확장자를 처리할 수 있는지 여부를 반환합니다."""
        pass

    @abstractmethod
    def convert(self, input_path: Path, output_dir: Path) -> ConversionResult:
        """문서를 변환하고 결과를 반환합니다."""
        pass
