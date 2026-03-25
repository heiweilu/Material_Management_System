"""应用初始化与全局配置"""

import logging

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

from src.config import ROOT_DIR, load_config
from src.db.database import init_database


def _init_logging(data_dir):
    """初始化日志系统"""
    log_dir = data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "app.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def create_app(argv: list) -> QApplication:
    """创建并初始化应用"""
    app = QApplication(argv)
    app.setApplicationName("物料管理系统")
    app.setApplicationVersion("0.1.0")

    font = QFont("Microsoft YaHei UI", 10)
    app.setFont(font)

    # 加载配置
    config = load_config()

    # 确保 data 目录存在
    data_dir = ROOT_DIR / "data"
    data_dir.mkdir(exist_ok=True)
    (data_dir / "backups").mkdir(exist_ok=True)
    (data_dir / "logs").mkdir(exist_ok=True)

    _init_logging(data_dir)
    logger = logging.getLogger(__name__)
    logger.info("物料管理系统启动中...")

    # 初始化数据库
    db_path = ROOT_DIR / config.get("database", {}).get("path", "data/mms.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    init_database(str(db_path))

    # 创建主窗口（延迟导入，避免循环引用）
    from src.ui.main_window import MainWindow

    window = MainWindow(config)
    window.show()
    window.raise_()
    window.activateWindow()

    # 保持窗口引用
    app._main_window = window  # type: ignore[attr-defined]
    logger.info("应用启动完成")
    return app
