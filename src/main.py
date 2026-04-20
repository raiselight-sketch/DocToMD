"""DocToMD Converter 진입점."""

import sys
from pathlib import Path

# src 디렉토리를 경로에 추가
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

def main() -> None:
    from gui.main_window import MainWindow
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
