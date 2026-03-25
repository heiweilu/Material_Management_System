"""分类管理页面 — 树形结构 + 右键菜单 CRUD"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTreeWidget, QTreeWidgetItem, QInputDialog, QMessageBox, QMenu, QLabel,
)
from PyQt6.QtCore import Qt

from src.core import category_service
from src.ui.widgets.toast import Toast


class CategoryPage(QWidget):
    """物料管理 - 分类管理"""

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)

        # 工具栏
        toolbar = QHBoxLayout()
        title = QLabel("📂 分类管理")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        toolbar.addWidget(title)
        toolbar.addStretch()

        btn_add = QPushButton("＋ 新增根分类")
        btn_add.setObjectName("primaryButton")
        btn_add.clicked.connect(self._on_add_root)
        toolbar.addWidget(btn_add)

        btn_refresh = QPushButton("刷新")
        btn_refresh.clicked.connect(self.refresh)
        toolbar.addWidget(btn_refresh)

        root.addLayout(toolbar)

        # 分类树
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["分类名称", "层级", "ID"])
        self._tree.setColumnWidth(0, 300)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._show_context_menu)
        root.addWidget(self._tree)

        # 底部提示
        self._hint = QLabel("右键点击分类可进行 新增子分类 / 重命名 / 删除 操作")
        self._hint.setStyleSheet("color: #94A3B8; font-size: 12px;")
        root.addWidget(self._hint)

    def refresh(self):
        self._tree.clear()
        roots = category_service.get_root_categories()
        for cat in roots:
            item = self._make_item(cat)
            self._tree.addTopLevelItem(item)
            self._load_children(item, cat.id)
        self._tree.expandAll()

    def _make_item(self, cat) -> QTreeWidgetItem:
        item = QTreeWidgetItem([cat.name, str(cat.level), str(cat.id)])
        item.setData(0, Qt.ItemDataRole.UserRole, cat.id)
        return item

    def _load_children(self, parent_item: QTreeWidgetItem, parent_id: int):
        children = category_service.get_children(parent_id)
        for child in children:
            child_item = self._make_item(child)
            parent_item.addChild(child_item)
            self._load_children(child_item, child.id)

    # ── 右键菜单 ─────────────────────────────
    def _show_context_menu(self, pos):
        item = self._tree.itemAt(pos)
        menu = QMenu(self)

        if item:
            cat_id = item.data(0, Qt.ItemDataRole.UserRole)
            act_add_child = menu.addAction("➕ 新增子分类")
            act_rename = menu.addAction("✏️ 重命名")
            act_delete = menu.addAction("🗑️ 删除")

            action = menu.exec(self._tree.viewport().mapToGlobal(pos))
            if action == act_add_child:
                self._on_add_child(cat_id)
            elif action == act_rename:
                self._on_rename(cat_id, item.text(0))
            elif action == act_delete:
                self._on_delete(cat_id, item.text(0))
        else:
            act_add_root = menu.addAction("➕ 新增根分类")
            action = menu.exec(self._tree.viewport().mapToGlobal(pos))
            if action == act_add_root:
                self._on_add_root()

    # ── 操作 ─────────────────────────────────
    def _on_add_root(self):
        name, ok = QInputDialog.getText(self, "新增根分类", "分类名称:")
        if ok and name.strip():
            try:
                category_service.create_category(name.strip())
                Toast.show(self, "分类已创建", "success")
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "创建失败", str(e))

    def _on_add_child(self, parent_id: int):
        name, ok = QInputDialog.getText(self, "新增子分类", "子分类名称:")
        if ok and name.strip():
            try:
                category_service.create_category(name.strip(), parent_id)
                Toast.show(self, "子分类已创建", "success")
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "创建失败", str(e))

    def _on_rename(self, cat_id: int, old_name: str):
        name, ok = QInputDialog.getText(self, "重命名分类", "新名称:", text=old_name)
        if ok and name.strip() and name.strip() != old_name:
            try:
                category_service.update_category(cat_id, name.strip())
                Toast.show(self, "分类已重命名", "success")
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "重命名失败", str(e))

    def _on_delete(self, cat_id: int, name: str):
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除分类 [{name}] 及其所有子分类吗？\n该操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                category_service.delete_category(cat_id)
                Toast.show(self, "分类已删除", "success")
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "删除失败", str(e))
