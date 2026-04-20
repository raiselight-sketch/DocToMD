import subprocess
from pathlib import Path
from .base_handler import BaseHandler, ConversionResult

class HwpHandler(BaseHandler):
    """pyhwp의 hwp5txt를 사용하여 HWP 파일을 처리하는 핸들러."""

    def __init__(self):
        self.supported_extensions = {'.hwp', '.hwpx'}

    def can_handle(self, file_extension: str) -> bool:
        return file_extension.lower() in self.supported_extensions

    def convert(self, input_path: Path, output_dir: Path) -> ConversionResult:
        try:
            output_path = output_dir / f"{input_path.stem}.md"
            
            # hwp5txt 명령 실행
            # .venv 로 인해 PATH에 hwp5txt가 있을 것으로 가정
            # subprocess.run을 사용하여 변환 수행
            result = subprocess.run(
                ["hwp5txt", "--output", str(output_path), str(input_path)],
                capture_output=True,
                text=True,
                check=True
            )
            
            # 변환 후 성공 여부 확인
            if output_path.exists():
                return ConversionResult(
                    input_path=input_path,
                    output_path=output_path,
                    success=True
                )
            else:
                return ConversionResult(
                    input_path=input_path,
                    success=False,
                    error_message=f"변환 결과 파일이 생성되지 않았습니다: {result.stderr}"
                )

        except subprocess.CalledProcessError as e:
            return ConversionResult(
                input_path=input_path,
                success=False,
                error_message=f"hwp5txt 실행 오류: {e.stderr}"
            )
        except Exception as e:
            return ConversionResult(
                input_path=input_path,
                success=False,
                error_message=str(e)
            )
