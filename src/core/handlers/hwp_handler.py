import subprocess
from pathlib import Path
from .base_handler import BaseHandler, ConversionResult

class HwpHandler(BaseHandler):
    """
    한글(HWP/HWPX) 문서 핸들러.
    hwp5txt (pyhwp) 또는 hwpx의 경우 내부 xml 추출 방식을 사용할 수 있습니다.
    """

    def __init__(self):
        self.supported_extensions = {".hwp", ".hwpx"}

    def can_handle(self, file_extension: str) -> bool:
        return file_extension.lower() in self.supported_extensions

    def convert(self, input_path: Path, output_dir: Path) -> ConversionResult:
        output_path = output_dir / f"{input_path.stem}.md"
        suffix = input_path.suffix.lower()

        try:
            if suffix == ".hwp":
                # pyhwp의 hwp5txt 명령 사용 시도
                result = subprocess.run(
                    ["hwp5txt", str(input_path)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8"
                )
                if result.returncode == 0:
                    md_text = self._cleanup_markdown(result.stdout)
                    output_path.write_text(md_text, encoding="utf-8")
                    return ConversionResult(input_path=input_path, output_path=output_path, success=True)
                else:
                    return ConversionResult(
                        input_path=input_path,
                        success=False,
                        error_message=f"hwp5txt 변환 실패: {result.stderr}"
                    )
            elif suffix == ".hwpx":
                # HWPX 지원 추가
                success, content_or_error = self._convert_hwpx(input_path)
                if success:
                    md_text = self._cleanup_markdown(content_or_error)
                    output_path.write_text(md_text, encoding="utf-8")
                    return ConversionResult(input_path=input_path, output_path=output_path, success=True)
                else:
                    return ConversionResult(
                        input_path=input_path,
                        success=False,
                        error_message=f"HWPX 변환 실패: {content_or_error}"
                    )
            
        except FileNotFoundError:
            return ConversionResult(
                input_path=input_path,
                success=False,
                error_message="hwp5txt (pyhwp)가 설치되어 있지 않습니다."
            )
        except Exception as e:
            return ConversionResult(
                input_path=input_path,
                success=False,
                error_message=str(e)
            )

        return ConversionResult(input_path=input_path, success=False, error_message="처리할 수 없는 형식입니다.")

    def _convert_hwpx(self, input_path: Path) -> tuple[bool, str]:
        """HWPX 파일(ZIP)에서 단락 구조를 유지하며 텍스트를 추출합니다."""
        import zipfile
        import xml.etree.ElementTree as ET
        
        try:
            all_sections_text = []
            with zipfile.ZipFile(input_path, 'r') as z:
                # HWPX의 실제 텍스트는 Contents/section0.xml, section1.xml 등에 저장됨
                section_files = [f for f in z.namelist() if f.startswith('Contents/section') and f.endswith('.xml')]
                section_files.sort()
                
                if not section_files:
                    return False, "HWPX 내부 텍스트 파일을 찾을 수 없습니다."
                
                # 네임스페이스 정의 (HWPX 표준)
                ns = {'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph'}
                
                for section in section_files:
                    with z.open(section) as f:
                        tree = ET.parse(f)
                        root = tree.getroot()
                        
                        section_texts = []
                        # 모든 단락(<hp:p>) 태그 찾기
                        for p in root.findall('.//hp:p', ns):
                            paragraph_text = []
                            # 단락 내의 모든 텍스트(<hp:t>) 추출
                            for t in p.findall('.//hp:t', ns):
                                if t.text:
                                    paragraph_text.append(t.text)
                            
                            if paragraph_text:
                                section_texts.append("".join(paragraph_text))
                            else:
                                # 빈 단락은 빈 줄로 처리
                                section_texts.append("")
                        
                        all_sections_text.append("\n".join(section_texts))
            
            return True, "\n\n".join(all_sections_text)
        except Exception as e:
            return False, f"HWPX 파싱 중 오류: {str(e)}"

    def _cleanup_markdown(self, text: str) -> str:
        """한글 문서 특유의 깨진 줄바꿈 등을 보정합니다."""
        import re
        # 한국어 줄바꿈 복구 (조사나 어미 뒤의 줄바꿈 합치기)
        text = re.sub(r'([가-힣,])\n([가-힣])', r'\1 \2', text)
        # 연속된 빈 줄 정리
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
