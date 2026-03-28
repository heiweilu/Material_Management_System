"""库存总览页面 — 统计卡片 + 低库存预警表"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QPushButton,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from src.core import material_service
from src.db.database import get_session
from src.db.models import Material


class _StatCard(QFrame):
    """单个统计卡片"""

    def __init__(self, title: str, value: str, color: str = "#3B82F6"):
        super().__init__()
        self.setObjectName("statCard")
        self.setStyleSheet(f"""
            #statCard {{
                background: white;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                padding: 16px;
                border-left: 4px solid {color};
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 12px; color: #64748B;")
        layout.addWidget(lbl_title)

        self._lbl_value = QLabel(value)
        self._lbl_value.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {color};")
        layout.addWidget(self._lbl_value)

    def set_value(self, value: str):
        self._lbl_value.setText(value)


class InventoryPage(QWidget):
    """库存中心 - 库存总览"""

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)

        # 标题栏
        top = QHBoxLayout()
        title = QLabel("库存总览")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        top.addWidget(title)
        top.addStretch()
        btn_refresh = QPushButton("刷新")
        btn_refresh.clicked.connect(self.refresh)
        top.addWidget(btn_refresh)
        root.addLayout(top)

        # 统计卡片
        cards = QHBoxLayout()
        self._card_total = _StatCard("物料种类", "0", "#3B82F6")
        self._card_stock = _StatCard("库存总量", "0", "#10B981")
        self._card_low = _StatCard("低库存预警", "0", "#EF4444")
        self._card_zero = _StatCard("零库存", "0", "#F59E0B")
        cards.addWidget(self._card_total)
        cards.addWidget(self._card_stock)
        cards.addWidget(self._card_low)
        cards.addWidget(self._card_zero)
        root.addLayout(cards)

        # 低库存预警表
        warn_label = QLabel("低库存物料清单")
        warn_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 12px;")
        root.addWidget(warn_label)

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "物料名称", "型号", "封装", "当前库存", "预警阈值", "存放位置",
        ])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        root.addWidget(self._table)

    def refresh(self):
        with get_session() as s:
            all_mats = s.query(Material).all()
            total_kinds = len(all_mats)
            total_stock = sum(m.current_stock for m in all_mats)
            low_mats = [m for m in all_mats if m.current_stock <= m.warning_threshold and m.current_stock > 0]
            zero_mats = [m for m in all_mats if m.current_stock == 0]

        self._card_total.set_value(str(total_kinds))
        self._card_stock.set_value(str(total_stock))
        self._card_low.set_value(str(len(low_mats)))
        self._card_zero.set_value(str(len(zero_mats)))

        # 表格: 合并低库存 + 零库存
        warn_list = material_service.get_low_stock_materials()
        self._table.setRowCount(len(warn_list))
        low_bg = QColor("#FEF2F2")
        low_fg = QColor("#DC2626")

        for row, m in enumerate(warn_list):
            vals = [m.material_name, m.model, m.package_type,
                    str(m.current_stock), str(m.warning_threshold), m.storage_location]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(str(val) if val else "")
                item.setBackground(low_bg)
                item.setForeground(low_fg)
                self._table.setItem(row, col, item)
