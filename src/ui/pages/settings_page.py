"""系统设置页面 — 主题切换 + 默认参数 + 日志级别"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QFormLayout, QComboBox, QSpinBox, QLineEdit,
    QMessageBox,
)
from PyQt6.QtCore import Qt

from src.config import save_config
from src.ui.widgets.toast import Toast


class SettingsPage(QWidget):
    """系统设置"""

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)

        title = QLabel("⚙️ 系统设置")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        root.addWidget(title)

        # 外观
        theme_group = QGroupBox("外观")
        theme_form = QFormLayout()

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["light", "dark"])
        current_theme = self.config.get("theme", "light")
        idx = self._theme_combo.findText(current_theme)
        if idx >= 0:
            self._theme_combo.setCurrentIndex(idx)
        theme_form.addRow("主题", self._theme_combo)
        theme_group.setLayout(theme_form)
        root.addWidget(theme_group)

        # 默认参数
        defaults_group = QGroupBox("默认参数")
        defaults_form = QFormLayout()

        defaults = self.config.get("defaults", {})
        self._threshold_spin = QSpinBox()
        self._threshold_spin.setRange(0, 999999)
        self._threshold_spin.setValue(defaults.get("warning_threshold", 10))
        defaults_form.addRow("预警阈值", self._threshold_spin)

        self._unit_edit = QLineEdit(defaults.get("unit", "个"))
        defaults_form.addRow("默认单位", self._unit_edit)

        defaults_group.setLayout(defaults_form)
        root.addWidget(defaults_group)

        # 备份设置
        backup_group = QGroupBox("备份设置")
        backup_form = QFormLayout()

        backup = self.config.get("backup", {})
        self._max_backups_spin = QSpinBox()
        self._max_backups_spin.setRange(1, 100)
        self._max_backups_spin.setValue(backup.get("max_backups", 20))
        backup_form.addRow("最大备份数", self._max_backups_spin)

        backup_group.setLayout(backup_form)
        root.addWidget(backup_group)

        # 日志级别
        log_group = QGroupBox("日志")
        log_form = QFormLayout()
        self._log_combo = QComboBox()
        self._log_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        current_log = self.config.get("log_level", "INFO").upper()
        idx = self._log_combo.findText(current_log)
        if idx >= 0:
            self._log_combo.setCurrentIndex(idx)
        log_form.addRow("日志级别", self._log_combo)
        log_group.setLayout(log_form)
        root.addWidget(log_group)

        # 保存按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_save = QPushButton("💾 保存设置")
        btn_save.setObjectName("primaryButton")
        btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(btn_save)
        root.addLayout(btn_row)

        root.addStretch()

    def _on_save(self):
        new_theme = self._theme_combo.currentText()
        self.config["theme"] = new_theme
        self.config.setdefault("defaults", {})["warning_threshold"] = self._threshold_spin.value()
        self.config.setdefault("defaults", {})["unit"] = self._unit_edit.text().strip() or "个"
        self.config.setdefault("backup", {})["max_backups"] = self._max_backups_spin.value()
        self.config["log_level"] = self._log_combo.currentText()

        try:
            save_config(self.config)
            # 通知主窗口切换主题
            main_win = self.window()
            if hasattr(main_win, "switch_theme"):
                main_win.switch_theme(new_theme)
            Toast.show(self, "设置已保存", "success")
        except Exception as e:
            QMessageBox.warning(self, "保存失败", str(e))
