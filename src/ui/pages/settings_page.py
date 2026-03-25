"""系统设置页面"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class SettingsPage(QWidget):
    """系统设置"""

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        layout = QVBoxLayout(self)
        label = QLabel("⚙️ 系统设置")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 24px; color: #64748B;")
        layout.addWidget(label)
