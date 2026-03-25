"""搜索栏组件"""

from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtCore import pyqtSignal, QTimer


class SearchBar(QLineEdit):
    """带防抖的搜索输入框"""

    search_triggered = pyqtSignal(str)

    def __init__(self, placeholder: str = "搜索...", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setClearButtonEnabled(True)
        self.setMinimumHeight(32)

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(300)
        self._debounce.timeout.connect(lambda: self.search_triggered.emit(self.text().strip()))

        self.textChanged.connect(lambda _: self._debounce.start())
