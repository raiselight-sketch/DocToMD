import time
import datetime
import concurrent.futures
from pathlib import Path
from typing import Callable, Optional
from dataclasses import dataclass, field
from .converter import DocumentConverter, ConversionResult

@dataclass
class BatchReport:
    """배치 처리 결과를 담는 리포트 클래스."""
    total_files: int
    success_count: int
    fail_count: int
    duration_seconds: float
    detailed_results: list[ConversionResult] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

class BatchProcessor:
    """여러 파일을 병렬로 처리하는 프로세서."""

    def __init__(self, converter: DocumentConverter, max_workers: int = 4):
        self.converter = converter
        self.max_workers = max_workers
        self.executor: Optional[concurrent.futures.ThreadPoolExecutor] = None
        self._is_cancelled = False

    def process(
        self, 
        files: list[Path], 
        output_dir: Path, 
        on_progress: Optional[Callable[[int, int, Path, str, Optional[str]], None]] = None,
        on_done: Optional[Callable[[BatchReport], None]] = None
    ) -> None:
        """파일 리스트를 받아 병렬로 변환 작업을 수행합니다."""
        self._is_cancelled = False
        start_time = time.time()
        total = len(files)
        detailed_results = []
        success_count = 0
        fail_count = 0

        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)
        
        try:
            # 병렬 작업 제출
            future_to_file = {
                self.executor.submit(self.converter.convert, f, output_dir): f 
                for f in files
            }

            for i, future in enumerate(concurrent.futures.as_completed(future_to_file), 1):
                if self._is_cancelled:
                    break
                
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    detailed_results.append(result)
                    
                    if result.success:
                        success_count += 1
                        status = "SUCCESS"
                    else:
                        fail_count += 1
                        status = "FAILED"
                    
                    if on_progress:
                        on_progress(i, total, file_path, status, result.error_message)
                
                except Exception as e:
                    fail_count += 1
                    if on_progress:
                        on_progress(i, total, file_path, "FAILED", str(e))

            # 요약 리포트 생성
            report = BatchReport(
                total_files=total,
                success_count=success_count,
                fail_count=fail_count,
                duration_seconds=time.time() - start_time,
                detailed_results=detailed_results
            )
            
            self._save_report(report, output_dir)
            
            if on_done:
                on_done(report)

        finally:
            self.shutdown()

    def cancel(self):
        """진행 중인 모든 작업을 취소합니다."""
        self._is_cancelled = True
        self.shutdown()

    def shutdown(self):
        """스레드 풀 종료."""
        if self.executor:
            self.executor.shutdown(wait=False, cancel_futures=True)
            self.executor = None

    def _save_report(self, report: BatchReport, output_dir: Path):
        """변환 작업 요약을 .md 파일로 저장."""
        report_filename = f"conversion_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_path = output_dir / report_filename
        
        content = [
            f"# DocToMD 변환 작업 보고서",
            f"- **일시**: {report.timestamp}",
            f"- **총 파일**: {report.total_files}개",
            f"- **성공**: {report.success_count}개",
            f"- **실패**: {report.fail_count}개",
            f"- **소요 시간**: {report.duration_seconds:.2f}초",
            "\n## 상세 결과\n",
            "| 상태 | 파일명 | 메시지 |",
            "| :--- | :--- | :--- |"
        ]

        for res in report.detailed_results:
            status_icon = "✅" if res.success else "❌"
            error_msg = res.error_message if res.error_message else "-"
            content.append(f"| {status_icon} | {res.input_path.name} | {error_msg} |")

        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write("\n".join(content))
        except Exception as e:
            print(f"리포트 저장 실패: {e}")
