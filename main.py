"""物料管理系统 - 入口文件"""

import sys
import traceback

from PyQt6.QtWidgets import QApplication, QMessageBox

from src.app import create_app
from src.config import ROOT_DIR


def main():
    try:
        app = create_app(sys.argv)
        sys.exit(app.exec())
    except Exception as exc:
        log_dir = ROOT_DIR / "data" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        error_file = log_dir / "startup_error.log"
        error_file.write_text(traceback.format_exc(), encoding="utf-8")
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(
            None,
            "启动失败",
            f"程序启动失败：{exc}\n\n详细错误已写入：{error_file}",
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
