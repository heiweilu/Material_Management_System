"""备份恢复页面"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class BackupPage(QWidget):
    """数据管理 - 备份恢复"""

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        layout = QVBoxLayout(self)
        label = QLabel("💾 备份恢复")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 24px; color: #64748B;")
        layout.addWidget(label)
