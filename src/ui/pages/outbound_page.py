"""出库管理页面"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class OutboundPage(QWidget):
    """出库管理"""

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        layout = QVBoxLayout(self)
        label = QLabel("📤 出库管理")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 24px; color: #64748B;")
        layout.addWidget(label)
