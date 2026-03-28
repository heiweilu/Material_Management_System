"""物料列表页面 — 表格 + 搜索 + CRUD"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QLabel,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from src.core import material_service, category_service
from src.ui.widgets.search_bar import SearchBar
from src.ui.widgets.toast import Toast
from src.ui.dialogs.material_dialog import MaterialDialog


class MaterialPage(QWidget):
    """物料管理 - 物料列表"""

    _COLUMNS = [
        ("物料名称", "material_name"),
        ("型号", "model"),
        ("封装", "package_type"),
        ("规格", "specification"),
        ("单位", "unit"),
        ("当前库存", "current_stock"),
        ("预警阈值", "warning_threshold"),
        ("分类", "_category_name"),
        ("存放位置", "storage_location"),
    ]

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self._materials: list = []

        self._setup_ui()
        self.refresh()

    # ── 构建 UI ─────────────────────────────
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)

        # 顶栏: 搜索 + 分类筛选 + 按钮
        top = QHBoxLayout()

        self._search = SearchBar(placeholder="搜索物料名称/型号/规格…")
        self._search.search_triggered.connect(self._on_search)
        top.addWidget(self._search, 3)

        self._cat_filter = QComboBox()
        self._cat_filter.setMinimumWidth(160)
        self._cat_filter.currentIndexChanged.connect(lambda _: self.refresh())
        top.addWidget(self._cat_filter, 1)

        top.addStretch()

        btn_add = QPushButton("＋ 新增物料")
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

        # 表格
        self._table = QTableWidget()
        self._table.setColumnCount(len(self._COLUMNS))
        self._table.setHorizontalHeaderLabels([c[0] for c in self._COLUMNS])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(True)
        self._table.doubleClicked.connect(self._on_edit)
        root.addWidget(self._table)

        # 底栏: 统计
        self._status_label = QLabel()
        root.addWidget(self._status_label)

    # ── 数据刷新 ─────────────────────────────
    def refresh(self):
        """重新加载分类下拉和物料列表"""
        self._reload_category_filter()
        cat_id = self._cat_filter.currentData()
        keyword = self._search.text().strip()
        if keyword:
            self._materials = material_service.search_materials(keyword, cat_id)
        else:
            self._materials = material_service.get_all_materials(cat_id)
        self._fill_table()

    def _reload_category_filter(self):
        """刷新分类下拉（保持当前选择）"""
        prev = self._cat_filter.currentData()
        self._cat_filter.blockSignals(True)
        self._cat_filter.clear()
        self._cat_filter.addItem("全部分类", None)
        for cat in category_service.get_all_categories():
            prefix = "  " * cat.level
            self._cat_filter.addItem(f"{prefix}{cat.name}", cat.id)
        if prev is not None:
            idx = self._cat_filter.findData(prev)
            if idx >= 0:
                self._cat_filter.setCurrentIndex(idx)
        self._cat_filter.blockSignals(False)

    def _fill_table(self):
        self._table.setRowCount(len(self._materials))
        low_color = QColor("#FEF2F2")
        low_fg = QColor("#DC2626")

        for row, m in enumerate(self._materials):
            is_low = (m.current_stock <= m.warning_threshold)
            cat_name = m.category.name if m.category else ""

            for col, (_, attr) in enumerate(self._COLUMNS):
                if attr == "_category_name":
                    val = cat_name
                else:
                    val = getattr(m, attr, "")
                item = QTableWidgetItem(str(val) if val is not None else "")
                if is_low:
                    item.setBackground(low_color)
                    item.setForeground(low_fg)
                self._table.setItem(row, col, item)

        low_count = sum(1 for m in self._materials if m.current_stock <= m.warning_threshold)
        self._status_label.setText(
            f"共 {len(self._materials)} 条记录"
            + (f"  ⚠ {low_count} 种低库存" if low_count else "")
        )

    # ── 事件处理 ─────────────────────────────
    def _on_search(self, keyword: str):
        self.refresh()

    def _on_add(self):
        dlg = MaterialDialog(self)
        if dlg.exec() == MaterialDialog.DialogCode.Accepted and dlg.result_data:
            try:
                material_service.create_material(dlg.result_data)
                Toast.show(self, "物料已新增", "success")
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "新增失败", str(e))

    def _on_edit(self):
        row = self._table.currentRow()
        if row < 0 or row >= len(self._materials):
            Toast.show(self, "请先选择一条记录", "warning")
            return
        m = self._materials[row]
        data = {
            "material_name": m.material_name,
            "model": m.model,
            "package_type": m.package_type,
            "specification": m.specification,
            "unit": m.unit,
            "current_stock": m.current_stock,
            "warning_threshold": m.warning_threshold,
            "category_id": m.category_id,
            "storage_location": m.storage_location,
            "datasheet_path": m.datasheet_path,
            "image_path": getattr(m, "image_path", ""),
            "remarks": m.remarks,
        }
        dlg = MaterialDialog(self, material_data=data)
        if dlg.exec() == MaterialDialog.DialogCode.Accepted and dlg.result_data:
            try:
                material_service.update_material(m.id, dlg.result_data)
                Toast.show(self, "物料已更新", "success")
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "更新失败", str(e))

    def _on_delete(self):
        row = self._table.currentRow()
        if row < 0 or row >= len(self._materials):
            Toast.show(self, "请先选择一条记录", "warning")
            return
        m = self._materials[row]
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除物料 [{m.material_name}] 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                material_service.delete_material(m.id)
                Toast.show(self, "物料已删除", "success")
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "删除失败", str(e))
