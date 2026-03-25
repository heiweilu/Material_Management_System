"""物料列表页面"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class MaterialPage(QWidget):
    """物料管理 - 物料列表"""

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        layout = QVBoxLayout(self)
        label = QLabel("📋 物料列表")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 24px; color: #64748B;")
        layout.addWidget(label)
