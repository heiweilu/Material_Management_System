"""Toast 轻量通知组件"""

from PyQt6.QtWidgets import QLabel, QWidget, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont


class Toast(QLabel):
    """自动消失的消息提示"""

    STYLE_MAP = {
        "info": "background-color: #3B82F6; color: white;",
        "success": "background-color: #10B981; color: white;",
        "warning": "background-color: #F59E0B; color: white;",
        "error": "background-color: #EF4444; color: white;",
    }

    def __init__(self, parent: QWidget, message: str, toast_type: str = "info",
                 duration: int = 2500):
        super().__init__(message, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFont(QFont("Microsoft YaHei UI", 11))
        base_style = self.STYLE_MAP.get(toast_type, self.STYLE_MAP["info"])
        self.setStyleSheet(
            f"{base_style} border-radius: 8px; padding: 12px 24px;"
        )
        self.setFixedHeight(44)
        self.adjustSize()
        self.setMinimumWidth(200)

        px = (parent.width() - self.width()) // 2
        self.move(px, 40)
        super().show()
        self.raise_()

        self._opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity)
        QTimer.singleShot(duration, self._fade_out)

    @staticmethod
    def show(parent: QWidget, message: str, toast_type: str = "info",
             duration: int = 2500) -> "Toast":
        """工厂方法：在 parent 上显示一条 Toast"""
        return Toast(parent, message, toast_type, duration)

        self._opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity)
        QTimer.singleShot(duration, self._fade_out)

    def _fade_out(self):
        self._anim = QPropertyAnimation(self._opacity, b"opacity")
        self._anim.setDuration(400)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.finished.connect(self.deleteLater)
        self._anim.start()
