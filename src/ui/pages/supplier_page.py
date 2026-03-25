"""供应商管理页面 — 表格 + 搜索 + CRUD"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QLabel,
)
from PyQt6.QtCore import Qt

from src.core import supplier_service
from src.ui.widgets.search_bar import SearchBar
from src.ui.widgets.toast import Toast
from src.ui.dialogs.supplier_dialog import SupplierDialog


class SupplierPage(QWidget):
    """供应商管理"""

    _COLUMNS = [
        ("供应商名称", "supplier_name"),
        ("联系人", "contact_person"),
        ("电话", "phone"),
        ("邮箱", "email"),
        ("地址", "address"),
        ("网站", "website"),
        ("状态", "status"),
    ]

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self._suppliers: list = []
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)

        top = QHBoxLayout()
        self._search = SearchBar(placeholder="搜索供应商名称/联系人/电话…")
        self._search.search_triggered.connect(self._on_search)
        top.addWidget(self._search, 3)
        top.addStretch()

        btn_add = QPushButton("＋ 新增供应商")
        btn_add.setObjectName("primaryButton")
        btn_add.clicked.connect(self._on_add)
        top.addWidget(btn_add)

        btn_edit = QPushButton("编辑")
        btn_edit.clicked.connect(self._on_edit)
        top.addWidget(btn_edit)

        btn_del = QPushButton("删除")
        btn_del.setProperty("danger", True)
        btn_del.clicked.connect(self._on_delete)
        top.addWidget(btn_del)

        root.addLayout(top)

        self._table = QTableWidget()
        self._table.setColumnCount(len(self._COLUMNS))
        self._table.setHorizontalHeaderLabels([c[0] for c in self._COLUMNS])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.doubleClicked.connect(self._on_edit)
        root.addWidget(self._table)

        self._status_label = QLabel()
        root.addWidget(self._status_label)

    def refresh(self):
        keyword = self._search.text().strip()
        if keyword:
            self._suppliers = supplier_service.search_suppliers(keyword)
        else:
            self._suppliers = supplier_service.get_all_suppliers()
        self._fill_table()

    def _fill_table(self):
        self._table.setRowCount(len(self._suppliers))
        for row, s in enumerate(self._suppliers):
            for col, (_, attr) in enumerate(self._COLUMNS):
                val = getattr(s, attr, "")
                self._table.setItem(row, col, QTableWidgetItem(str(val) if val else ""))
        self._status_label.setText(f"共 {len(self._suppliers)} 个供应商")

    def _on_search(self, _keyword: str):
        self.refresh()

    def _on_add(self):
        dlg = SupplierDialog(self)
        if dlg.exec() == SupplierDialog.DialogCode.Accepted and dlg.result_data:
            try:
                supplier_service.create_supplier(dlg.result_data)
                Toast.show(self, "供应商已新增", "success")
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "新增失败", str(e))

    def _on_edit(self):
        row = self._table.currentRow()
        if row < 0 or row >= len(self._suppliers):
            Toast.show(self, "请先选择一条记录", "warning")
            return
        s = self._suppliers[row]
        data = {
            "supplier_name": s.supplier_name,
            "contact_person": s.contact_person,
            "phone": s.phone,
            "email": s.email,
            "address": s.address,
            "website": s.website,
            "status": s.status,
            "remarks": s.remarks,
        }
        dlg = SupplierDialog(self, supplier_data=data)
        if dlg.exec() == SupplierDialog.DialogCode.Accepted and dlg.result_data:
            try:
                supplier_service.update_supplier(s.id, dlg.result_data)
                Toast.show(self, "供应商已更新", "success")
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "更新失败", str(e))

    def _on_delete(self):
        row = self._table.currentRow()
        if row < 0 or row >= len(self._suppliers):
            Toast.show(self, "请先选择一条记录", "warning")
            return
        s = self._suppliers[row]
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除供应商 [{s.supplier_name}] 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                supplier_service.delete_supplier(s.id)
                Toast.show(self, "供应商已删除", "success")
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "删除失败", str(e))
