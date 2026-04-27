import os
import sys
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
import tkinterdnd2
from src import __version__

SUPPORTED_EXTENSIONS = {
    ".docx", ".doc", ".pdf", ".pptx", ".ppt",
    ".xlsx", ".xls", ".csv", ".html", ".htm",
    ".hwp", ".hwpx", ".png", ".jpg", ".jpeg",
    ".txt", ".rtf", ".pages"
}

# ── 팔레트 ──────────────────────────────────────────────────────
BG           = "#0f1117"   # 최외곽 배경
CARD         = "#16181f"   # 카드 배경
CARD2        = "#1c1f2a"   # 보조 카드
ACCENT       = "#4f8ef7"   # 메인 액센트 (블루)
ACCENT_DARK  = "#2563eb"
SUCCESS      = "#22c55e"
DANGER       = "#ef4444"
TEXT_PRI     = "#f1f5f9"   # 주요 텍스트
TEXT_SEC     = "#64748b"   # 보조 텍스트
BORDER       = "#2a2d3a"   # 테두리


class MainWindow(tkinterdnd2.TkinterDnD.Tk):
    """DocToMD Converter — 프리미엄 UI"""

    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        src_dir = Path(__file__).parent.parent
        if str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))

        from core import DocumentConverter
        self.converter = DocumentConverter()

        self.title(f"DocToMD v{__version__}")
        self.geometry("800x680")
        self.minsize(680, 560)
        self.configure(bg=BG)

        # 상태
        self.files_to_convert: list[Path] = []
        self.file_widgets: dict = {}
        self.source_folder: Path | None = None
        self.output_directory = Path(os.path.expanduser("~/Desktop/DocToMD_Result"))
        self.keep_structure   = ctk.BooleanVar(value=True)
        self.save_same_as_source = ctk.BooleanVar(value=True)  # 원본 위치 저장 기능 추가
        self.appearance_mode  = "dark"
        self.is_processing    = False
        self.use_ai = ctk.BooleanVar(value=False)
        self.ai_model = ctk.StringVar(value="2b")

        self._build_ui()

    # ──────────────────────────────────────────────────────────────
    # UI 빌드
    # ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # ── 헤더 ────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color=CARD, corner_radius=0, height=64)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        hdr.columnconfigure(1, weight=1)

        # 로고 + 타이틀
        logo_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=24, pady=12, sticky="w")

        ctk.CTkLabel(
            logo_frame, text="⬡", font=ctk.CTkFont(size=26),
            text_color=ACCENT
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            logo_frame, text="DocToMD",
            font=ctk.CTkFont(size=22, weight="bold"), text_color=TEXT_PRI
        ).pack(side="left")

        ctk.CTkLabel(
            logo_frame, text="  Converter",
            font=ctk.CTkFont(size=13), text_color=TEXT_SEC
        ).pack(side="left", pady=(4, 0))

        # 우측 버튼
        right = ctk.CTkFrame(hdr, fg_color="transparent")
        right.grid(row=0, column=2, padx=20, pady=12, sticky="e")

        self._theme_btn = ctk.CTkButton(
            right, text="🌙", width=36, height=36,
            fg_color=CARD2, hover_color=BORDER,
            corner_radius=10, command=self._toggle_theme
        )
        self._theme_btn.pack(side="left")

        self._chat_btn = ctk.CTkButton(
            right, text="💬 채팅", width=60, height=36,
            fg_color=CARD2, hover_color=BORDER,
            corner_radius=10, command=self._open_chat
        )
        self._chat_btn.pack(side="left", padx=(8, 0))

        # ── 액션 버튼 행 ────────────────────────────────────────
        action_bar = ctk.CTkFrame(self, fg_color=BG)
        action_bar.grid(row=1, column=0, sticky="ew", padx=20, pady=(16, 0))
        action_bar.columnconfigure(99, weight=1)  # 오른쪽 여백용

        self._btn("➕  파일 추가", action_bar, self._add_files_dialog,
                  CARD2, BORDER).pack(side="left", padx=(0, 8))
        self._btn("📂  폴더 전체", action_bar, self._add_folder_dialog,
                  ACCENT_DARK, "#1d4ed8").pack(side="left", padx=(0, 8))
        self._btn("✕  전체 삭제", action_bar, self._clear_all,
                  "#1c1f2a", "#7f1d1d", text_color=DANGER).pack(side="left")

        self.count_lbl = ctk.CTkLabel(
            action_bar, text="대기 파일 없음",
            font=ctk.CTkFont(size=12), text_color=TEXT_SEC
        )
        self.count_lbl.pack(side="right")

        # ── 드롭존 ──────────────────────────────────────────────
        from gui.dropzone import DropzoneFrame
        self.dropzone = DropzoneFrame(
            self, on_drop_callback=self._on_dropped,
            height=110, corner_radius=16,
            border_width=2, border_color=BORDER,
            fg_color=CARD
        )
        self.dropzone.grid(row=2, column=0, sticky="ew", padx=20, pady=(12, 0))

        # ── 파일 리스트 카드 ─────────────────────────────────────
        list_card = ctk.CTkFrame(self, fg_color=CARD, corner_radius=14)
        list_card.grid(row=3, column=0, sticky="nsew", padx=20, pady=12)
        self.rowconfigure(3, weight=1)
        list_card.columnconfigure(0, weight=1)
        list_card.rowconfigure(1, weight=1)

        # 카드 헤더
        list_hdr = ctk.CTkFrame(list_card, fg_color="transparent", height=38)
        list_hdr.grid(row=0, column=0, sticky="ew", padx=16, pady=(10, 0))
        list_hdr.grid_propagate(False)
        list_hdr.columnconfigure(1, weight=1)

        ctk.CTkLabel(
            list_hdr, text="변환 목록",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_PRI
        ).grid(row=0, column=0, sticky="w")

        # AI 옵션
        ai_frame = ctk.CTkFrame(list_hdr, fg_color="transparent")
        ai_frame.grid(row=0, column=1, padx=(20, 0))

        self.ai_chk = ctk.CTkCheckBox(
            ai_frame, text="AI 개선",
            variable=self.use_ai,
            font=ctk.CTkFont(size=12), text_color=TEXT_SEC,
            border_color=BORDER, fg_color=ACCENT, checkmark_color=TEXT_PRI
        )
        self.ai_chk.pack(side="left", padx=(0, 8))

        self.ai_model_combo = ctk.CTkComboBox(
            ai_frame, values=["2b", "7b"], variable=self.ai_model,
            width=60, height=24, font=ctk.CTkFont(size=11),
            fg_color=CARD2, button_color=BORDER, button_hover_color=ACCENT,
            dropdown_fg_color=CARD, dropdown_text_color=TEXT_PRI,
            state="disabled"  # 기본적으로 비활성화
        )
        self.ai_model_combo.pack(side="left")

        # 체크박스 상태에 따라 콤보박스 활성화
        self.use_ai.trace_add("write", self._toggle_ai_model)

        self.keep_chk = ctk.CTkCheckBox(
            list_hdr, text="구조 유지",
            variable=self.keep_structure,
            font=ctk.CTkFont(size=12), text_color=TEXT_SEC,
            border_color=BORDER, fg_color=ACCENT, checkmark_color=TEXT_PRI
        )
        self.keep_chk.grid(row=0, column=2, sticky="e", padx=(10, 0))

        self.same_folder_chk = ctk.CTkCheckBox(
            list_hdr, text="원본 위치에 저장",
            variable=self.save_same_as_source,
            font=ctk.CTkFont(size=12), text_color=TEXT_SEC,
            border_color=BORDER, fg_color=ACCENT, checkmark_color=TEXT_PRI
        )
        self.same_folder_chk.grid(row=0, column=3, sticky="e")

        # 구분선
        ctk.CTkFrame(list_card, height=1, fg_color=BORDER).grid(
            row=1, column=0, sticky="ew", padx=16, pady=(8, 0)
        )

        # 스크롤 리스트
        self.file_list = ctk.CTkScrollableFrame(
            list_card, fg_color="transparent",
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=ACCENT
        )
        self.file_list.grid(row=2, column=0, sticky="nsew", padx=8, pady=8)
        list_card.rowconfigure(2, weight=1)

        # ── 하단 푸터 ────────────────────────────────────────────
        footer = ctk.CTkFrame(self, fg_color=CARD, corner_radius=0, height=62)
        footer.grid(row=4, column=0, sticky="ew")
        footer.grid_propagate(False)
        footer.columnconfigure(1, weight=1)

        path_box = ctk.CTkFrame(footer, fg_color=CARD2, corner_radius=8)
        path_box.grid(row=0, column=0, padx=16, pady=12, sticky="w")

        ctk.CTkLabel(
            path_box, text="📁", font=ctk.CTkFont(size=13)
        ).pack(side="left", padx=(10, 4), pady=6)

        self.path_lbl = ctk.CTkLabel(
            path_box,
            text=self._short_path(self.output_directory),
            font=ctk.CTkFont(size=11), text_color=TEXT_SEC,
            width=260, anchor="w"
        )
        self.path_lbl.pack(side="left", pady=6)

        ctk.CTkButton(
            path_box, text="변경", width=48, height=24,
            fg_color=BORDER, hover_color=ACCENT,
            corner_radius=6, font=ctk.CTkFont(size=11),
            command=self._select_output
        ).pack(side="left", padx=(6, 8), pady=6)

        # 진행 표시 바 (평소엔 숨김)
        self.progress = ctk.CTkProgressBar(footer, width=0, mode="indeterminate",
                                            progress_color=ACCENT, fg_color=CARD2)

        self.start_btn = ctk.CTkButton(
            footer, text="변환 시작  ▶",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=150, height=38,
            fg_color=ACCENT, hover_color=ACCENT_DARK,
            corner_radius=10, command=self._start
        )
        self.start_btn.grid(row=0, column=2, padx=16, pady=12)

    # ──────────────────────────────────────────────────────────────
    # 헬퍼
    # ──────────────────────────────────────────────────────────────
    @staticmethod
    def _btn(text, parent, cmd, bg, hover, text_color=TEXT_PRI):
        return ctk.CTkButton(
            parent, text=text, height=34,
            font=ctk.CTkFont(size=12),
            fg_color=bg, hover_color=hover,
            text_color=text_color,
            corner_radius=8, command=cmd
        )

    @staticmethod
    def _short_path(p: Path, max_len: int = 45) -> str:
        s = str(p)
        return "…" + s[-(max_len - 1):] if len(s) > max_len else s

    def _update_count(self):
        n = len(self.files_to_convert)
        self.count_lbl.configure(
            text=f"{n}개 파일 대기 중" if n else "대기 파일 없음",
            text_color=ACCENT if n else TEXT_SEC
        )

    # ──────────────────────────────────────────────────────────────
    # 파일/폴더 수집
    # ──────────────────────────────────────────────────────────────
    def _collect(self, folder: Path):
        added = 0
        for child in sorted(folder.rglob("*")):
            if child.is_file() and child.suffix.lower() in SUPPORTED_EXTENSIONS:
                if child not in self.files_to_convert:
                    self.files_to_convert.append(child)
                    self._append_row(child)
                    added += 1
        return added

    def _add_files_dialog(self):
        if self.is_processing: return
        paths = filedialog.askopenfilenames(
            title="변환할 파일 선택",
            filetypes=[("지원 파일", " ".join(f"*{e}" for e in SUPPORTED_EXTENSIONS)),
                       ("모든 파일", "*.*")]
        )
        if paths:
            self._on_dropped([Path(p) for p in paths])

    def _add_folder_dialog(self):
        if self.is_processing: return
        folder = filedialog.askdirectory(title="변환할 폴더 선택")
        if not folder: return
        fp = Path(folder)
        if self.source_folder is None:
            self.source_folder = fp
        n = self._collect(fp)
        self._update_count()
        messagebox.showinfo("폴더 추가", f"'{fp.name}' 에서 {n}개 파일 추가됨")

    def _on_dropped(self, paths: list[Path]):
        if self.is_processing: return
        for p in paths:
            if p.is_file() and p not in self.files_to_convert:
                self.files_to_convert.append(p)
                self._append_row(p)
            elif p.is_dir():
                if self.source_folder is None:
                    self.source_folder = p
                self._collect(p)
        self._update_count()

    def _clear_all(self):
        if self.is_processing: return
        self.files_to_convert.clear()
        self.file_widgets.clear()
        self.source_folder = None
        for w in self.file_list.winfo_children():
            w.destroy()
        self._update_count()

    # ──────────────────────────────────────────────────────────────
    # 파일 행 렌더링
    # ──────────────────────────────────────────────────────────────
    EXT_ICON = {
        ".pdf": "🔴", ".docx": "🔵", ".doc": "🔵",
        ".pptx": "🟠", ".ppt": "🟠", ".xlsx": "🟢", ".xls": "🟢",
        ".hwp": "🟣", ".hwpx": "🟣", ".pages": "🍎",
        ".png": "🖼", ".jpg": "🖼", ".jpeg": "🖼",
        ".txt": "📝", ".csv": "📊", ".html": "🌐", ".htm": "🌐",
    }

    def _append_row(self, path: Path):
        icon = self.EXT_ICON.get(path.suffix.lower(), "📄")

        row = ctk.CTkFrame(self.file_list, fg_color=CARD2, corner_radius=8, height=40)
        row.pack(fill="x", pady=2, padx=4)
        row.pack_propagate(False)
        row.columnconfigure(1, weight=1)

        ctk.CTkLabel(row, text=icon, width=28,
                     font=ctk.CTkFont(size=14)).grid(row=0, column=0, padx=(10, 4))

        name_lbl = ctk.CTkLabel(
            row, text=path.name, anchor="w",
            font=ctk.CTkFont(size=12), text_color=TEXT_PRI
        )
        name_lbl.grid(row=0, column=1, sticky="ew", padx=4)

        status_lbl = ctk.CTkLabel(
            row, text="대기", font=ctk.CTkFont(size=11),
            text_color=TEXT_SEC, width=52
        )
        status_lbl.grid(row=0, column=2, padx=6)

        del_btn = ctk.CTkButton(
            row, text="✕", width=26, height=26,
            fg_color="transparent", text_color=TEXT_SEC,
            hover_color=BORDER, corner_radius=6,
            command=lambda p=path, r=row: self._remove(p, r)
        )
        del_btn.grid(row=0, column=3, padx=(0, 8))

        self.file_widgets[path] = (row, name_lbl, status_lbl, del_btn)

    def _remove(self, path: Path, row):
        if self.is_processing: return
        self.files_to_convert.remove(path) if path in self.files_to_convert else None
        self.file_widgets.pop(path, None)
        row.destroy()
        self._update_count()

    # ──────────────────────────────────────────────────────────────
    # 설정
    # ──────────────────────────────────────────────────────────────
    def _select_output(self):
        d = filedialog.askdirectory(initialdir=str(self.output_directory.parent))
        if d:
            self.output_directory = Path(d)
            self.path_lbl.configure(text=self._short_path(self.output_directory))

    def _toggle_theme(self):
        self.appearance_mode = "light" if self.appearance_mode == "dark" else "dark"
        ctk.set_appearance_mode(self.appearance_mode)
        self._theme_btn.configure(text="🌙" if self.appearance_mode == "dark" else "☀️")

    def _toggle_ai_model(self, *args):
        if self.use_ai.get():
            self.ai_model_combo.configure(state="normal")
        else:
            self.ai_model_combo.configure(state="disabled")

    def _open_chat(self):
        """Gemma 채팅 창을 엽니다."""
        ChatWindow(self)

    # ──────────────────────────────────────────────────────────────
    # 변환 실행
    # ──────────────────────────────────────────────────────────────
    def _start(self):
        if not self.files_to_convert:
            messagebox.showwarning("경고", "변환할 파일을 먼저 추가해 주세요.")
            return
        self.is_processing = True
        self.start_btn.configure(state="disabled", text="변환 중…", fg_color=TEXT_SEC)
        self.progress.grid(row=0, column=1, padx=8, sticky="ew")
        self.progress.start()
        threading.Thread(target=self._worker, daemon=True).start()

    def _get_outdir(self, p: Path) -> Path:
        # 원본 위치 저장 옵션이 켜져 있으면 파일이 있는 폴더 반환
        if self.save_same_as_source.get():
            return p.parent
            
        if self.keep_structure.get() and self.source_folder:
            try:
                rel = p.parent.relative_to(self.source_folder)
                out = self.output_directory / rel
                out.mkdir(parents=True, exist_ok=True)
                return out
            except ValueError:
                pass
        return self.output_directory

    def _worker(self):
        self.output_directory.mkdir(parents=True, exist_ok=True)
        files = list(self.files_to_convert)
        ok = fail = 0
        for f in files:
            outdir = self._get_outdir(f)
            result = self.converter.convert(f, outdir, self.use_ai.get(), self.ai_model.get())
            status = "SUCCESS" if result.success else "FAILED"
            if result.success:
                ok += 1
            else:
                fail += 1
            self.after(0, self._set_status, f, status)
        self.after(0, self._done, ok, fail)

    def _set_status(self, path: Path, status: str):
        if path in self.file_widgets:
            _, _, slbl, dbtn = self.file_widgets[path]
            dbtn.configure(state="disabled")
            if status == "SUCCESS":
                slbl.configure(text="✅ 완료", text_color=SUCCESS)
            else:
                slbl.configure(text="❌ 실패", text_color=DANGER)

    def _done(self, ok: int, fail: int):
        self.is_processing = False
        self.progress.stop()
        self.progress.grid_remove()
        self.start_btn.configure(state="normal", text="변환 시작  ▶", fg_color=ACCENT)

        save_msg = "원본 파일 위치" if self.save_same_as_source.get() else str(self.output_directory)
        
        messagebox.showinfo(
            "완료",
            f"변환 완료!\n\n✅ 성공  {ok}개\n❌ 실패  {fail}개\n\n저장 위치:\n{save_msg}"
        )


class ChatWindow(ctk.CTkToplevel):
    """Gemma 채팅 창."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Gemma 채팅")
        self.geometry("600x700")
        self.configure(bg=BG)

        from core.gemma_handler import gemma_chat
        self.chat_handler = gemma_chat

        self._build_chat_ui()

    def _build_chat_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # 채팅 히스토리
        self.chat_frame = ctk.CTkScrollableFrame(
            self, fg_color=CARD, corner_radius=14,
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=ACCENT
        )
        self.chat_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 10))

        # 입력 프레임
        input_frame = ctk.CTkFrame(self, fg_color=CARD, corner_radius=14, height=80)
        input_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        input_frame.grid_propagate(False)
        input_frame.columnconfigure(0, weight=1)

        self.input_entry = ctk.CTkEntry(
            input_frame, placeholder_text="메시지를 입력하세요...",
            font=ctk.CTkFont(size=14), fg_color=CARD2,
            border_color=BORDER
        )
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=16, pady=16)
        self.input_entry.bind("<Return>", self._send_message)

        send_btn = ctk.CTkButton(
            input_frame, text="전송", width=80, height=32,
            fg_color=ACCENT, hover_color=ACCENT_DARK,
            command=self._send_message
        )
        send_btn.grid(row=0, column=1, padx=(8, 16), pady=16)

        # 초기 메시지
        self._add_message("Assistant", "안녕하세요! Gemma와 대화할 수 있습니다. 무엇을 도와드릴까요?")

    def _send_message(self, event=None):
        user_text = self.input_entry.get().strip()
        if not user_text:
            return

        self._add_message("You", user_text)
        self.input_entry.delete(0, "end")

        # 응답 생성 (비동기로)
        threading.Thread(target=self._generate_response, args=(user_text,), daemon=True).start()

    def _generate_response(self, user_text):
        response = self.chat_handler.chat(user_text)
        self.after(0, self._add_message, "Assistant", response)

    def _add_message(self, sender, text):
        msg_frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        msg_frame.pack(fill="x", pady=8, padx=8)

        sender_label = ctk.CTkLabel(
            msg_frame, text=f"{sender}:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=ACCENT if sender == "Assistant" else TEXT_PRI
        )
        sender_label.pack(anchor="w")

        text_label = ctk.CTkLabel(
            msg_frame, text=text,
            font=ctk.CTkFont(size=13), text_color=TEXT_PRI,
            wraplength=500, justify="left"
        )
        text_label.pack(anchor="w", pady=(4, 0))
₩