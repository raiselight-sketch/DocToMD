import os
import subprocess
import tempfile
from pathlib import Path
from .base_handler import BaseHandler, ConversionResult
from markitdown import MarkItDown

def _find_apple_pages_app() -> Path | None:
    """정식 Apple Pages 앱의 경로를 찾아 반환합니다."""
    candidates = {
        Path("/Applications/Pages.app"),
        Path("/System/Applications/Pages.app")
    }
    
    # mdfind를 통해 추가 후보 수집
    try:
        res = subprocess.run(
            ['mdfind', "kMDItemCFBundleIdentifier == 'com.apple.Pages'"],
            capture_output=True, text=True, timeout=5
        )
        for line in res.stdout.splitlines():
            if line.strip():
                candidates.add(Path(line.strip()))
    except Exception:
        pass

    for path in candidates:
        if not path.exists():
            continue
            
        try:
            res = subprocess.run(
                ['codesign', '-dv', '--verbose=2', str(path)],
                capture_output=True, text=True, timeout=5
            )
            output = res.stdout + res.stderr
            
            # Apple 정식 서명 확인 (Team ID K36BKF7T3D 또는 Software Signing 권한 확인)
            has_authority = any(auth in output for auth in [
                "Authority=Software Signing",
                "TeamIdentifier=K36BKF7T3D"
            ])
            # 번들 ID 확인
            has_identifier = any(ident in output for ident in [
                "Identifier=com.apple.iWork.Pages",
                "Identifier=com.apple.Pages"
            ])
            
            if has_authority and has_identifier:
                return path
        except Exception:
            continue
            
    return None

class PagesHandler(BaseHandler):
    """AppleScript를 사용하여 Pages 문서를 Word로 변환 후, MarkItDown으로 Markdown 변환하는 핸들러."""

    def __init__(self):
        self.md = MarkItDown()
        self.supported_extensions = {'.pages'}

    def can_handle(self, file_extension: str) -> bool:
        return file_extension.lower() in self.supported_extensions

    def convert(self, input_path: Path, output_dir: Path) -> ConversionResult:
        # 정식 Pages 앱 확인
        pages_path = _find_apple_pages_app()
        if not pages_path:
            return ConversionResult(
                input_path=input_path,
                success=False,
                error_message="Apple Pages가 설치되어 있지 않거나 다른 앱이 'com.apple.Pages' 번들 ID를 점유하고 있습니다. Mac App Store에서 정식 Pages를 설치하세요."
            )

        try:
            # 1. 임시 디렉토리에 Word(.docx) 파일로 수출
            with tempfile.TemporaryDirectory() as tmpdir:
                docx_path = Path(tmpdir) / f"{input_path.stem}.docx"
                
                # 경로 문자열 탈출 처리 (따옴표 등)
                input_posix = str(input_path.absolute()).replace('"', '\\"')
                docx_posix = str(docx_path.absolute()).replace('"', '\\"')
                pages_posix = str(pages_path.absolute()).replace('"', '\\"')
                
                # AppleScript 실행 (절대 경로 사용)
                applescript = f'''
                set inputPath to POSIX file "{input_posix}"
                set outputPath to POSIX file "{docx_posix}"
                tell application "{pages_posix}"
                    activate
                    try
                        set theDoc to open inputPath
                        export theDoc to outputPath as Microsoft Word
                        close theDoc saving no
                    on error errMsg
                        return "ERROR: " & errMsg
                    end try
                end tell
                return "SUCCESS"
                '''
                
                result = subprocess.run(['osascript', '-e', applescript], capture_output=True, text=True)
                
                if "ERROR:" in result.stdout or result.returncode != 0:
                    error_msg = result.stdout.strip() if "ERROR:" in result.stdout else result.stderr
                    return ConversionResult(
                        input_path=input_path,
                        success=False,
                        error_message=f"Pages Export Failed: {error_msg}"
                    )

                # 2. MarkItDown을 사용하여 Word를 Markdown으로 변환
                if not docx_path.exists():
                    return ConversionResult(
                        input_path=input_path,
                        success=False,
                        error_message="변환된 Word 파일을 찾을 수 없습니다."
                    )
                
                md_result = self.md.convert(str(docx_path))
                output_path = output_dir / f"{input_path.stem}.md"
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(md_result.text_content)
                
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
