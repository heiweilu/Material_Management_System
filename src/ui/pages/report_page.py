"""报表统计页面"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class ReportPage(QWidget):
    """库存中心 - 报表统计"""

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        layout = QVBoxLayout(self)
        label = QLabel("📈 报表统计")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 24px; color: #64748B;")
        layout.addWidget(label)
