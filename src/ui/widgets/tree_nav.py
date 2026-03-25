"""树形导航组件 — 左侧侧边栏"""

from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

# 导航节点定义: (显示文本, page_key 或 None 表示纯分组, 子节点列表)
NAV_TREE = [
    ("📋 物料管理", None, [
        ("物料列表", "material"),
        ("分类管理", "category"),
    ]),
    ("📥 入库管理", "inbound", []),
    ("📤 出库管理", "outbound", []),
    ("📊 库存中心", None, [
        ("库存总览", "inventory"),
        ("报表统计", "report"),
    ]),
    ("🏢 供应商管理", "supplier", []),
    ("🔄 数据管理", None, [
        ("导入导出", "import_export"),
        ("备份恢复", "backup"),
    ]),
    ("⚙️ 系统设置", "settings", []),
]

PAGE_KEY_ROLE = Qt.ItemDataRole.UserRole


class TreeNav(QTreeWidget):
    """树形侧边栏导航"""

    page_selected = pyqtSignal(str)  # 发射 page_key

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setIndentation(20)
        self.setAnimated(True)
        self.setFont(QFont("Microsoft YaHei UI", 11))
        self.setMinimumWidth(200)
        self.setMaximumWidth(260)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._build_tree()
        self.itemClicked.connect(self._on_item_clicked)

        # 默认展开所有分组
        self.expandAll()

    def _build_tree(self):
        """根据 NAV_TREE 构建树形节点"""
        for text, page_key, children in NAV_TREE:
            item = QTreeWidgetItem([text])
            item.setData(0, PAGE_KEY_ROLE, page_key)
            # 分组节点设为不可选中（除非自身有 page_key）
            if page_key is None:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.addTopLevelItem(item)
            for child_text, child_key in children:
                child = QTreeWidgetItem([child_text])
                child.setData(0, PAGE_KEY_ROLE, child_key)
                item.addChild(child)

    def _on_item_clicked(self, item: QTreeWidgetItem, _column: int):
        page_key = item.data(0, PAGE_KEY_ROLE)
        if page_key:
            self.page_selected.emit(page_key)

    def select_page(self, page_key: str):
        """编程方式选中指定页面节点"""
        for i in range(self.topLevelItemCount()):
            top = self.topLevelItem(i)
            if top and top.data(0, PAGE_KEY_ROLE) == page_key:
                self.setCurrentItem(top)
                return
            if top:
                for j in range(top.childCount()):
                    child = top.child(j)
                    if child and child.data(0, PAGE_KEY_ROLE) == page_key:
                        self.setCurrentItem(child)
                        return
