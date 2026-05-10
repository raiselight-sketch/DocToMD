import subprocess
import tempfile
import os
from pathlib import Path
from markitdown import MarkItDown
from .base_handler import BaseHandler, ConversionResult

class PagesHandler(BaseHandler):
    """
    Apple Pages 전용 핸들러 (macOS 전용).
    
    동작 방식:
    1. AppleScript를 사용하여 Pages 파일을 .docx로 내보냄.
    2. 생성된 .docx 파일을 MarkItDown을 사용하여 Markdown으로 변환.
    """

    def __init__(self):
        self._md = MarkItDown()
        self.supported_extensions = {".pages"}

    def can_handle(self, file_extension: str) -> bool:
        return file_extension.lower() in self.supported_extensions

    def convert(self, input_path: Path, output_dir: Path) -> ConversionResult:
        output_path = output_dir / f"{input_path.stem}.md"
        warnings: list[str] = []

        # macOS 및 Pages 앱 설치 여부 확인
        if os.name != "posix" or subprocess.run(["uname"], capture_output=True, text=True).stdout.strip() != "Darwin":
            return ConversionResult(
                input_path=input_path,
                success=False,
                error_message="Pages 변환은 macOS 환경에서만 지원됩니다."
            )

        # Pages 앱 설치 여부 확인
        if subprocess.run(["mdfind", "kMDItemCFBundleIdentifier == 'com.apple.iWork.Pages'"], capture_output=True).returncode != 0:
            return ConversionResult(
                input_path=input_path,
                success=False,
                error_message="Apple Pages 앱이 설치되어 있지 않습니다."
            )

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_docx = Path(tmp_dir) / f"{input_path.stem}.docx"
            
            # ── Step 1: AppleScript를 이용해 docx로 변환 ──
            applescript = f'''
            set inputPath to "{input_path.absolute()}"
            set outputPath to "{tmp_docx.absolute()}"
            
            tell application "Pages"
                activate
                try
                    set myDoc to open (POSIX file inputPath as alias)
                    delay 1
                    export myDoc to (POSIX file outputPath) as Microsoft Word
                    close myDoc saving no
                on error errMsg number errNum
                    error "Pages 에러: " & errMsg & " (" & errNum & ")"
                end try
            end tell
            '''
            
            try:
                process = subprocess.run(
                    ["osascript", "-e", applescript],
                    capture_output=True,
                    text=True,
                    timeout=90
                )
                
                if process.returncode != 0:
                    error_msg = process.stderr.strip()
                    if "에러" in error_msg or "error" in error_msg.lower():
                        return ConversionResult(
                            input_path=input_path,
                            success=False,
                            error_message=f"AppleScript 실행 실패: {error_msg}",
                            warnings=warnings
                        )
                    warnings.append(f"AppleScript 경고: {error_msg}")
                
                if not tmp_docx.exists():
                    return ConversionResult(
                        input_path=input_path,
                        success=False,
                        error_message="docx 파일이 생성되지 않았습니다.",
                        warnings=warnings
                    )

                # ── Step 2: markitdown 으로 Markdown 변환 ──
                result = self._md.convert(str(tmp_docx))
                md_text = result.text_content
                
                # ── Step 3: 후처리 (Cleanup) ──
                cleaned_md = self._cleanup_markdown(md_text)
                
                output_path.write_text(cleaned_md, encoding="utf-8")

                return ConversionResult(
                    input_path=input_path,
                    output_path=output_path,
                    success=True,
                    warnings=warnings
                )

            except subprocess.TimeoutExpired:
                return ConversionResult(
                    input_path=input_path,
                    success=False,
                    error_message="AppleScript 실행 시간 초과 (90초).",
                    warnings=warnings
                )
            except Exception as e:
                return ConversionResult(
                    input_path=input_path,
                    success=False,
                    error_message=f"변환 중 알 수 없는 오류 발생: {str(e)}",
                    warnings=warnings
                )

    def _cleanup_markdown(self, text: str) -> str:
        """
        변환된 Markdown의 노이즈를 제거하고 가독성을 개선합니다.
        """
        import re
        lines = text.splitlines()
        cleaned_lines = []
        
        # 1. 상단/하단 반복 노이즈 패턴 정의 (예: Pages에서 발생하는 메타데이터)
        noise_patterns = [
            r"^Page \d+ of \d+$",
            r"^제목 없음$",
            r"^게시판 이름:.*",
            r"^작성일:.*",
        ]
        
        for line in lines:
            # 노이즈 라인 스킵
            if any(re.match(p, line.strip()) for p in noise_patterns):
                continue
            cleaned_lines.append(line)
        
        text = "\n".join(cleaned_lines)
        
        # 2. 깨진 줄바꿈 복구 (한국어 특화)
        # 문장이 마침표(.), 물음표(?), 느낌표(!), 따옴표("') 등으로 끝나지 않았는데 
        # 다음 줄에 바로 텍스트가 이어지는 경우 하나로 합침
        text = re.sub(r'([가-힣,])\n([가-힣])', r'\1 \2', text)
        
        # 3. 불필요한 연속 공백 및 빈 줄 정리
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()

