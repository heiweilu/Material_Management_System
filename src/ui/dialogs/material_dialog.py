"""物料新增/编辑弹窗"""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QSpinBox, QComboBox, QTextEdit,
    QPushButton, QLabel, QMessageBox, QFileDialog,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl

from src.core import category_service, material_service


class MaterialDialog(QDialog):
    """新增或编辑物料的表单弹窗"""

    def __init__(self, parent=None, material_data: dict | None = None):
        super().__init__(parent)
        self._is_edit = material_data is not None
        self._data = material_data or {}
        self.result_data: dict | None = None

        self.setWindowTitle("编辑物料" if self._is_edit else "新增物料")
        self.setMinimumWidth(540)
        self.setModal(True)

        self._setup_ui()
        if self._is_edit:
            self._populate_fields()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # 物料名称
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("如: 贴片电阻 100Ω")
        form.addRow("物料名称 *", self._name_edit)

        # 型号
        self._model_edit = QLineEdit()
        form.addRow("型号", self._model_edit)

        # 封装
        self._package_edit = QLineEdit()
        self._package_edit.setPlaceholderText("如: 0805, SOP-8, DIP-8")
        form.addRow("封装", self._package_edit)

        # 规格
        self._spec_edit = QLineEdit()
        self._spec_edit.setPlaceholderText("如: 100Ω ±1%, 10μF/16V")
        form.addRow("规格", self._spec_edit)

        # 库存 + 单位（同一行）
        stock_row = QHBoxLayout()
        self._stock_spin = QSpinBox()
        self._stock_spin.setRange(0, 999999)
        self._stock_spin.setValue(0)
        stock_row.addWidget(self._stock_spin)

        self._unit_combo = QComboBox()
        self._unit_combo.setEditable(True)
        self._unit_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._unit_combo.addItems(["个", "只", "粒", "块", "片", "米", "卷", "包", "盘", "套", "条", "根"])
        self._unit_combo.setCurrentText("个")
        self._unit_combo.setMinimumWidth(80)
        stock_row.addWidget(self._unit_combo)
        form.addRow("库存 / 单位 *", stock_row)

        # 预警阈值
        self._threshold_spin = QSpinBox()
        self._threshold_spin.setRange(0, 999999)
        self._threshold_spin.setValue(10)
        form.addRow("预警阈值", self._threshold_spin)

        # 供应商（可编辑下拉框，支持历史匹配）
        self._supplier_combo = QComboBox()
        self._supplier_combo.setEditable(True)
        self._supplier_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._supplier_combo.setPlaceholderText("输入或选择供应商")
        self._supplier_combo.addItems(material_service.get_distinct_suppliers())
        self._supplier_combo.setCurrentText("")
        form.addRow("供应商", self._supplier_combo)

        # 分类
        self._category_combo = QComboBox()
        self._category_combo.addItem("-- 无分类 --", None)
        for cat in category_service.get_all_categories():
            prefix = "  " * cat.level
            self._category_combo.addItem(f"{prefix}{cat.name}", cat.id)
        form.addRow("所属分类", self._category_combo)

        # 存放位置
        self._location_edit = QLineEdit()
        self._location_edit.setPlaceholderText("如: 抽屉A-3, 柜子B-2")
        form.addRow("存放位置", self._location_edit)

        # 数据手册（支持本地路径或网页链接）
        ds_row = QHBoxLayout()
        self._datasheet_edit = QLineEdit()
        self._datasheet_edit.setPlaceholderText("本地路径或网页链接 (如: https://...)")
        ds_row.addWidget(self._datasheet_edit)
        ds_browse = QPushButton("浏览")
        ds_browse.setFixedWidth(70)
        ds_browse.clicked.connect(self._browse_datasheet)
        ds_row.addWidget(ds_browse)
        ds_open = QPushButton("打开")
        ds_open.setFixedWidth(55)
        ds_open.clicked.connect(self._open_datasheet)
        ds_row.addWidget(ds_open)
        form.addRow("数据手册", ds_row)

        # 物料图片
        img_row = QHBoxLayout()
        self._image_edit = QLineEdit()
        self._image_edit.setPlaceholderText("图片文件路径 (png/jpg/...)")
        img_row.addWidget(self._image_edit)
        img_browse = QPushButton("浏览")
        img_browse.setFixedWidth(70)
        img_browse.clicked.connect(self._browse_image)
        img_row.addWidget(img_browse)
        form.addRow("物料图片", img_row)

        # 备注
        self._remarks_edit = QTextEdit()
        self._remarks_edit.setMaximumHeight(80)
        form.addRow("备注", self._remarks_edit)

        layout.addLayout(form)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setProperty("secondary", True)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _populate_fields(self):
        """编辑模式下填充已有数据"""
        d = self._data
        self._name_edit.setText(d.get("material_name", ""))
        self._model_edit.setText(d.get("model", ""))
        self._package_edit.setText(d.get("package_type", ""))
        self._spec_edit.setText(d.get("specification", ""))
        self._unit_combo.setCurrentText(d.get("unit", "个"))
        self._stock_spin.setValue(d.get("current_stock", 0))
        self._threshold_spin.setValue(d.get("warning_threshold", 10))
        self._location_edit.setText(d.get("storage_location", ""))
        self._supplier_combo.setCurrentText(d.get("supplier", ""))
        self._datasheet_edit.setText(d.get("datasheet_path", ""))
        self._image_edit.setText(d.get("image_path", ""))
        self._remarks_edit.setPlainText(d.get("remarks", ""))

        # 分类
        cat_id = d.get("category_id")
        if cat_id is not None:
            idx = self._category_combo.findData(cat_id)
            if idx >= 0:
                self._category_combo.setCurrentIndex(idx)



    def _browse_datasheet(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择数据手册", "",
            "文档文件 (*.pdf *.doc *.docx *.xls *.xlsx *.html *.txt);;所有文件 (*)",
        )
        if path:
            self._datasheet_edit.setText(path)

    def _open_datasheet(self):
        val = self._datasheet_edit.text().strip()
        if not val:
            return
        if val.startswith(("http://", "https://")):
            QDesktopServices.openUrl(QUrl(val))
        elif os.path.exists(val):
            QDesktopServices.openUrl(QUrl.fromLocalFile(val))

    def _browse_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择物料图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;所有文件 (*)",
        )
        if path:
            self._image_edit.setText(path)

    def _on_save(self):
        name = self._name_edit.text().strip()
        unit = self._unit_combo.currentText().strip()

        if not name:
            QMessageBox.warning(self, "提示", "物料名称不能为空")
            self._name_edit.setFocus()
            return
        if not unit:
            QMessageBox.warning(self, "提示", "计量单位不能为空")
            self._unit_combo.setFocus()
            return

        self.result_data = {
            "material_name": name,
            "model": self._model_edit.text().strip(),
            "package_type": self._package_edit.text().strip(),
            "specification": self._spec_edit.text().strip(),
            "unit": unit,
            "warning_threshold": self._threshold_spin.value(),
            "category_id": self._category_combo.currentData(),
            "supplier": self._supplier_combo.currentText().strip(),
            "storage_location": self._location_edit.text().strip(),
            "datasheet_path": self._datasheet_edit.text().strip(),
            "image_path": self._image_edit.text().strip(),
            "remarks": self._remarks_edit.toPlainText().strip(),
        }
        self.result_data["current_stock"] = self._stock_spin.value()
        self.accept()
