from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from codedir.ui.main_window import show_main_window
from codedir.ui.styles import get_stylesheet


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(get_stylesheet("dark"))

    app.window = show_main_window(app)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
