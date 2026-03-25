"""出库管理页面 — 新建出库单 + 历史记录"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QFormLayout, QLineEdit, QComboBox,
    QSpinBox, QDateEdit, QMessageBox, QGroupBox,
)
from PyQt6.QtCore import Qt, QDate

from src.core import outbound_service, material_service
from src.ui.widgets.toast import Toast


class OutboundPage(QWidget):
    """出库管理"""

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self._order_items: list[dict] = []
        self._orders: list = []

        self._setup_ui()
        self._refresh_history()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)

        self._tabs = QTabWidget()
        self._tabs.addWidget(self._build_new_order_tab())
        self._tabs.addWidget(self._build_history_tab())
        self._tabs.currentChanged.connect(lambda idx: self._refresh_history() if idx == 1 else None)
        root.addWidget(self._tabs)

    # ── Tab 1: 新建出库单 ──────────────────────
    def _build_new_order_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        header_group = QGroupBox("出库单信息")
        header_form = QFormLayout()

        self._no_edit = QLineEdit()
        self._no_edit.setReadOnly(True)
        self._no_edit.setText(outbound_service.generate_outbound_no())
        header_form.addRow("出库单号", self._no_edit)

        self._date_edit = QDateEdit(QDate.currentDate())
        self._date_edit.setCalendarPopup(True)
        header_form.addRow("出库日期", self._date_edit)

        self._recipient_edit = QLineEdit()
        self._recipient_edit.setPlaceholderText("领用人 / 项目名称")
        header_form.addRow("领用方", self._recipient_edit)

        self._header_remarks = QLineEdit()
        header_form.addRow("备注", self._header_remarks)

        header_group.setLayout(header_form)
        layout.addWidget(header_group)

        # 添加明细行
        add_row = QHBoxLayout()
        self._mat_combo = QComboBox()
        self._mat_combo.setMinimumWidth(200)
        for mat in material_service.get_all_materials():
            self._mat_combo.addItem(
                f"[{mat.material_code}] {mat.material_name} (库存:{mat.current_stock})",
                mat.id,
            )
        add_row.addWidget(QLabel("物料:"))
        add_row.addWidget(self._mat_combo, 2)

        self._qty_spin = QSpinBox()
        self._qty_spin.setRange(1, 999999)
        self._qty_spin.setValue(1)
        add_row.addWidget(QLabel("数量:"))
        add_row.addWidget(self._qty_spin)

        btn_add_row = QPushButton("添加")
        btn_add_row.clicked.connect(self._add_detail_row)
        add_row.addWidget(btn_add_row)

        layout.addLayout(add_row)

        self._detail_table = QTableWidget()
        self._detail_table.setColumnCount(4)
        self._detail_table.setHorizontalHeaderLabels(["物料ID", "物料", "数量", "操作"])
        self._detail_table.horizontalHeader().setStretchLastSection(True)
        self._detail_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self._detail_table)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_submit = QPushButton("✅ 提交出库单")
        btn_submit.setObjectName("primaryButton")
        btn_submit.clicked.connect(self._submit_order)
        btn_row.addWidget(btn_submit)
        layout.addLayout(btn_row)

        return page

    def _add_detail_row(self):
        mat_id = self._mat_combo.currentData()
        if mat_id is None:
            return
        self._order_items.append({
            "material_id": mat_id,
            "material_text": self._mat_combo.currentText(),
            "quantity": self._qty_spin.value(),
        })
        self._refresh_detail_table()

    def _refresh_detail_table(self):
        self._detail_table.setRowCount(len(self._order_items))
        for row, d in enumerate(self._order_items):
            self._detail_table.setItem(row, 0, QTableWidgetItem(str(d["material_id"])))
            self._detail_table.setItem(row, 1, QTableWidgetItem(d["material_text"]))
            self._detail_table.setItem(row, 2, QTableWidgetItem(str(d["quantity"])))
            btn_remove = QPushButton("移除")
            btn_remove.clicked.connect(lambda checked, r=row: self._remove_detail_row(r))
            self._detail_table.setCellWidget(row, 3, btn_remove)

    def _remove_detail_row(self, row: int):
        if 0 <= row < len(self._order_items):
            self._order_items.pop(row)
            self._refresh_detail_table()

    def _submit_order(self):
        if not self._order_items:
            Toast.show(self, "请至少添加一条明细", "warning")
            return
        header = {
            "outbound_no": self._no_edit.text(),
            "outbound_date": self._date_edit.date().toString("yyyy-MM-dd"),
            "recipient": self._recipient_edit.text().strip(),
            "remarks": self._header_remarks.text().strip(),
        }
        details = [
            {"material_id": d["material_id"], "quantity": d["quantity"]}
            for d in self._order_items
        ]
        try:
            outbound_service.create_order(header, details)
            Toast.show(self, "出库单已提交", "success")
            self._order_items.clear()
            self._refresh_detail_table()
            self._no_edit.setText(outbound_service.generate_outbound_no())
        except Exception as e:
            QMessageBox.warning(self, "提交失败", str(e))

    # ── Tab 2: 历史记录 ────────────────────────
    def _build_history_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        top = QHBoxLayout()
        top.addStretch()
        btn_refresh = QPushButton("刷新")
        btn_refresh.clicked.connect(self._refresh_history)
        top.addWidget(btn_refresh)
        btn_del = QPushButton("删除选中单据")
        btn_del.setProperty("danger", True)
        btn_del.clicked.connect(self._delete_history_order)
        top.addWidget(btn_del)
        layout.addLayout(top)

        self._history_table = QTableWidget()
        self._history_table.setColumnCount(5)
        self._history_table.setHorizontalHeaderLabels(["出库单号", "领用方", "出库日期", "备注", "创建时间"])
        self._history_table.horizontalHeader().setStretchLastSection(True)
        self._history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._history_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._history_table.setAlternatingRowColors(True)
        layout.addWidget(self._history_table)

        self._history_status = QLabel()
        layout.addWidget(self._history_status)
        return page

    def _refresh_history(self):
        self._orders = outbound_service.get_all_orders()
        self._history_table.setRowCount(len(self._orders))
        for row, o in enumerate(self._orders):
            self._history_table.setItem(row, 0, QTableWidgetItem(o.outbound_no))
            self._history_table.setItem(row, 1, QTableWidgetItem(o.recipient or ""))
            self._history_table.setItem(row, 2, QTableWidgetItem(str(o.outbound_date or "")))
            self._history_table.setItem(row, 3, QTableWidgetItem(o.remarks or ""))
            self._history_table.setItem(row, 4, QTableWidgetItem(str(o.created_at or "")))
        self._history_status.setText(f"共 {len(self._orders)} 条出库单")

    def _delete_history_order(self):
        row = self._history_table.currentRow()
        if row < 0 or row >= len(self._orders):
            Toast.show(self, "请先选择一条记录", "warning")
            return
        o = self._orders[row]
        reply = QMessageBox.question(
            self, "确认删除",
            f"删除出库单 [{o.outbound_no}] 将回退库存，确定吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                outbound_service.delete_order(o.id)
                Toast.show(self, "出库单已删除", "success")
                self._refresh_history()
            except Exception as e:
                QMessageBox.warning(self, "删除失败", str(e))
