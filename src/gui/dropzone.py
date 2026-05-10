import re
import customtkinter as ctk
from pathlib import Path
from typing import Callable, Optional

class DropzoneFrame(ctk.CTkFrame):
    """파일 및 폴더 드래그앤드롭을 위한 위젯."""

    def __init__(self, master, on_drop_callback: Optional[Callable] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_drop_callback = on_drop_callback

        # 중앙 안내 텍스트
        self._label = ctk.CTkLabel(
            self,
            text="⬇   파일 또는 폴더를 여기로 드래그하세요\n(.docx  .pdf  .pptx  .xlsx  .hwp  .txt  .png …)",
            font=ctk.CTkFont(size=14),
            text_color=("gray50", "gray65"),
            justify="center"
        )
        self._label.pack(expand=True)

        # tkinterdnd2 드롭 이벤트 등록 (루트 윈도우가 TkinterDnD.Tk여야 동작)
        try:
            self.drop_target_register("*")          # 모든 파일 타입 허용
            self.dnd_bind("<<Drop>>", self._on_drop)
            self.dnd_bind("<<DragEnter>>", self._on_drag_enter)
            self.dnd_bind("<<DragLeave>>", self._on_drag_leave)
        except Exception:
            # DnD 등록에 실패해도 나머지 UI는 작동
            pass

    # ── 드래그 이벤트 ──────────────────────────────────────────────

    def _on_drag_enter(self, event):
        self.configure(border_color="#4a9eff")

    def _on_drag_leave(self, event):
        self.configure(border_color=("gray60", "#4a9eff"))

    def _on_drop(self, event):
        self.configure(border_color=("gray60", "#4a9eff"))
        paths = self._parse_drop_data(event.data)
        if self.on_drop_callback and paths:
            self.on_drop_callback(paths)

    @staticmethod
    def _parse_drop_data(data: str) -> list[Path]:
        """
        tkinterdnd2 드롭 데이터를 Path 리스트로 변환.
        Mac: 공백 포함 경로를 {} 또는 공백 구분으로 전달할 수 있음.
        """
        paths = []
        # {} 로 감싸인 경로 먼저 추출 (공백 포함 경로)
        braced = re.findall(r'\{([^}]+)\}', data)
        remaining = re.sub(r'\{[^}]+\}', '', data).strip()

        for p in braced:
            paths.append(Path(p))

        # 나머지는 공백으로 구분 (Mac에서 쐐기문자 없이 오는 경우)
        if remaining:
            for token in remaining.split():
                candidate = Path(token)
                if candidate.exists():
                    paths.append(candidate)

        return paths
