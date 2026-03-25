"""供应商新增/编辑弹窗"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QTextEdit, QPushButton, QMessageBox,
)
from PyQt6.QtCore import Qt


class SupplierDialog(QDialog):
    """新增或编辑供应商的表单弹窗"""

    def __init__(self, parent=None, supplier_data: dict | None = None):
        super().__init__(parent)
        self._is_edit = supplier_data is not None
        self._data = supplier_data or {}
        self.result_data: dict | None = None

        self.setWindowTitle("编辑供应商" if self._is_edit else "新增供应商")
        self.setMinimumWidth(460)
        self.setModal(True)

        self._setup_ui()
        if self._is_edit:
            self._populate_fields()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("供应商全称")
        form.addRow("供应商名称 *", self._name_edit)

        self._contact_edit = QLineEdit()
        form.addRow("联系人", self._contact_edit)

        self._phone_edit = QLineEdit()
        form.addRow("电话", self._phone_edit)

        self._email_edit = QLineEdit()
        form.addRow("邮箱", self._email_edit)

        self._address_edit = QLineEdit()
        form.addRow("地址", self._address_edit)

        self._website_edit = QLineEdit()
        self._website_edit.setPlaceholderText("如: https://www.example.com")
        form.addRow("网站", self._website_edit)

        self._status_combo = QComboBox()
        self._status_combo.addItems(["active", "inactive"])
        form.addRow("状态", self._status_combo)

        self._remarks_edit = QTextEdit()
        self._remarks_edit.setMaximumHeight(80)
        form.addRow("备注", self._remarks_edit)

        layout.addLayout(form)

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
        d = self._data
        self._name_edit.setText(d.get("supplier_name", ""))
        self._contact_edit.setText(d.get("contact_person", ""))
        self._phone_edit.setText(d.get("phone", ""))
        self._email_edit.setText(d.get("email", ""))
        self._address_edit.setText(d.get("address", ""))
        self._website_edit.setText(d.get("website", ""))
        idx = self._status_combo.findText(d.get("status", "active"))
        if idx >= 0:
            self._status_combo.setCurrentIndex(idx)
        self._remarks_edit.setPlainText(d.get("remarks", ""))

    def _on_save(self):
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "供应商名称不能为空")
            self._name_edit.setFocus()
            return
        self.result_data = {
            "supplier_name": name,
            "contact_person": self._contact_edit.text().strip(),
            "phone": self._phone_edit.text().strip(),
            "email": self._email_edit.text().strip(),
            "address": self._address_edit.text().strip(),
            "website": self._website_edit.text().strip(),
            "status": self._status_combo.currentText(),
            "remarks": self._remarks_edit.toPlainText().strip(),
        }
        self.accept()
