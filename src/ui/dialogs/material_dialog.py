"""物料新增/编辑弹窗"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QSpinBox, QComboBox, QTextEdit,
    QPushButton, QLabel, QMessageBox,
)
from PyQt6.QtCore import Qt

from src.core import category_service, supplier_service


class MaterialDialog(QDialog):
    """新增或编辑物料的表单弹窗"""

    def __init__(self, parent=None, material_data: dict | None = None):
        super().__init__(parent)
        self._is_edit = material_data is not None
        self._data = material_data or {}
        self.result_data: dict | None = None

        self.setWindowTitle("编辑物料" if self._is_edit else "新增物料")
        self.setMinimumWidth(500)
        self.setModal(True)

        self._setup_ui()
        if self._is_edit:
            self._populate_fields()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # 物料编码
        self._code_edit = QLineEdit()
        self._code_edit.setPlaceholderText("如: R-0805-100R")
        form.addRow("物料编码 *", self._code_edit)

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

        # 单位
        self._unit_edit = QLineEdit("个")
        form.addRow("计量单位 *", self._unit_edit)

        # 预警阈值
        self._threshold_spin = QSpinBox()
        self._threshold_spin.setRange(0, 999999)
        self._threshold_spin.setValue(10)
        form.addRow("预警阈值", self._threshold_spin)

        # 分类
        self._category_combo = QComboBox()
        self._category_combo.addItem("-- 无分类 --", None)
        for cat in category_service.get_all_categories():
            prefix = "  " * cat.level
            self._category_combo.addItem(f"{prefix}{cat.name}", cat.id)
        form.addRow("所属分类", self._category_combo)

        # 供应商
        self._supplier_combo = QComboBox()
        self._supplier_combo.addItem("-- 无供应商 --", None)
        for sup in supplier_service.get_all_suppliers():
            self._supplier_combo.addItem(sup.supplier_name, sup.id)
        form.addRow("默认供应商", self._supplier_combo)

        # 存放位置
        self._location_edit = QLineEdit()
        self._location_edit.setPlaceholderText("如: 抽屉A-3, 柜子B-2")
        form.addRow("存放位置", self._location_edit)

        # 数据手册路径
        self._datasheet_edit = QLineEdit()
        self._datasheet_edit.setPlaceholderText("本地文件路径 (可选)")
        form.addRow("数据手册", self._datasheet_edit)

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
        self._code_edit.setText(d.get("material_code", ""))
        self._name_edit.setText(d.get("material_name", ""))
        self._model_edit.setText(d.get("model", ""))
        self._package_edit.setText(d.get("package_type", ""))
        self._spec_edit.setText(d.get("specification", ""))
        self._unit_edit.setText(d.get("unit", "个"))
        self._threshold_spin.setValue(d.get("warning_threshold", 10))
        self._location_edit.setText(d.get("storage_location", ""))
        self._datasheet_edit.setText(d.get("datasheet_path", ""))
        self._remarks_edit.setPlainText(d.get("remarks", ""))

        # 分类
        cat_id = d.get("category_id")
        if cat_id is not None:
            idx = self._category_combo.findData(cat_id)
            if idx >= 0:
                self._category_combo.setCurrentIndex(idx)

        # 供应商
        sup_id = d.get("default_supplier_id")
        if sup_id is not None:
            idx = self._supplier_combo.findData(sup_id)
            if idx >= 0:
                self._supplier_combo.setCurrentIndex(idx)

    def _on_save(self):
        code = self._code_edit.text().strip()
        name = self._name_edit.text().strip()
        unit = self._unit_edit.text().strip()

        if not code:
            QMessageBox.warning(self, "提示", "物料编码不能为空")
            self._code_edit.setFocus()
            return
        if not name:
            QMessageBox.warning(self, "提示", "物料名称不能为空")
            self._name_edit.setFocus()
            return
        if not unit:
            QMessageBox.warning(self, "提示", "计量单位不能为空")
            self._unit_edit.setFocus()
            return

        self.result_data = {
            "material_code": code,
            "material_name": name,
            "model": self._model_edit.text().strip(),
            "package_type": self._package_edit.text().strip(),
            "specification": self._spec_edit.text().strip(),
            "unit": unit,
            "warning_threshold": self._threshold_spin.value(),
            "category_id": self._category_combo.currentData(),
            "default_supplier_id": self._supplier_combo.currentData(),
            "storage_location": self._location_edit.text().strip(),
            "datasheet_path": self._datasheet_edit.text().strip(),
            "remarks": self._remarks_edit.toPlainText().strip(),
        }
        self.accept()
