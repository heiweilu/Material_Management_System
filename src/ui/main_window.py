"""主窗口 — 树形侧边栏导航 + QStackedWidget 内容区"""

import logging

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QLabel, QStatusBar,
)
from PyQt6.QtCore import Qt

from src.config import ROOT_DIR, save_config
from src.ui.widgets.tree_nav import TreeNav

# 页面延迟导入映射
from src.ui.pages.material_page import MaterialPage
from src.ui.pages.category_page import CategoryPage
from src.ui.pages.inventory_page import InventoryPage
from src.ui.pages.import_export_page import ImportExportPage
from src.ui.pages.backup_page import BackupPage
from src.ui.pages.settings_page import SettingsPage

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """物料管理系统主窗口"""

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self._page_map: dict[str, int] = {}

        self.setWindowTitle("物料管理系统 v0.1.0")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)

        self._setup_ui()
        self._apply_theme(config.get("theme", "light"))

        # 默认选中物料列表
        self._nav_tree.select_page("material")
        self._switch_page("material")

    # ── UI 构建 ──────────────────────────────────────────────

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ─ 左侧：侧边栏 ─
        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        sidebar.setObjectName("sidebar")
        sidebar.setAutoFillBackground(True)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Logo / 标题
        title_label = QLabel("物料管理系统")
        title_label.setObjectName("app_title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(title_label)

        # 树形导航
        self._nav_tree = TreeNav()
        self._nav_tree.setObjectName("nav_tree")
        self._nav_tree.page_selected.connect(self._switch_page)
        sidebar_layout.addWidget(self._nav_tree, 1)

        # 版本号
        ver_label = QLabel("v0.1.0")
        ver_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver_label.setStyleSheet("color: #94A3B8; font-size: 11px; padding: 8px;")
        sidebar_layout.addWidget(ver_label)

        main_layout.addWidget(sidebar)

        # ─ 右侧：内容区 ─
        self._stack = QStackedWidget()
        main_layout.addWidget(self._stack, 1)

        # 注册所有页面
        self._register_pages()

        # ─ 状态栏 ─
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("就绪")

    def _register_pages(self):
        """创建并注册所有页面到 QStackedWidget"""
        pages = [
            ("material", MaterialPage(self.config)),
            ("category", CategoryPage(self.config)),
            ("inventory", InventoryPage(self.config)),
            ("import_export", ImportExportPage(self.config)),
            ("backup", BackupPage(self.config)),
            ("settings", SettingsPage(self.config)),
        ]
        for key, page in pages:
            idx = self._stack.addWidget(page)
            self._page_map[key] = idx

    # ── 页面切换 ─────────────────────────────────────────────

    def _switch_page(self, page_key: str):
        idx = self._page_map.get(page_key)
        if idx is not None:
            self._stack.setCurrentIndex(idx)
            page_name = self._stack.currentWidget().__class__.__name__
            self._status_bar.showMessage(f"当前页面: {page_name}")
            logger.debug("切换到页面: %s (index=%d)", page_key, idx)

    # ── 主题 ─────────────────────────────────────────────────

    # 主题名 → QSS 文件映射
    _THEME_FILES = {
        "frosted_light": "style.qss",
        "frosted_dark": "dark.qss",
        "felt": "felt.qss",
        "marble": "marble.qss",
        # 兼容旧配置
        "light": "style.qss",
        "dark": "dark.qss",
    }

    def _apply_theme(self, theme_name: str):
        """加载并应用 QSS 主题"""
        qss_name = self._THEME_FILES.get(theme_name, "style.qss")
        theme_file = ROOT_DIR / "src" / "ui" / "theme" / qss_name
        if theme_file.exists():
            qss = theme_file.read_text(encoding="utf-8")
            self.setStyleSheet(qss)
            logger.info("已应用主题: %s", theme_name)
        else:
            logger.warning("主题文件不存在: %s", theme_file)

    def switch_theme(self, theme_name: str):
        """外部调用切换主题并保存到配置"""
        self._apply_theme(theme_name)
        self.config["theme"] = theme_name
        save_config(self.config)
