"""备份恢复页面 — SQLite 数据库文件备份与恢复"""

import shutil
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QListWidget, QMessageBox, QFileDialog,
)
from PyQt6.QtCore import Qt

from src.config import ROOT_DIR, load_config
from src.ui.widgets.toast import Toast


class BackupPage(QWidget):
    """数据管理 - 备份恢复"""

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self._backup_dir = ROOT_DIR / config.get("backup", {}).get("backup_dir", "data/backups")
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        self._setup_ui()
        self._refresh_list()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)

        title = QLabel("备份恢复")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        root.addWidget(title)

        # 操作区
        action_group = QGroupBox("操作")
        action_layout = QHBoxLayout()

        btn_backup = QPushButton("📦 立即备份")
        btn_backup.setObjectName("primaryButton")
        btn_backup.clicked.connect(self._do_backup)
        action_layout.addWidget(btn_backup)

        btn_restore = QPushButton("♻️ 恢复选中备份")
        btn_restore.clicked.connect(self._do_restore)
        action_layout.addWidget(btn_restore)

        btn_delete = QPushButton("🗑️ 删除选中")
        btn_delete.setProperty("danger", True)
        btn_delete.clicked.connect(self._do_delete)
        action_layout.addWidget(btn_delete)

        btn_export = QPushButton("📁 导出备份到…")
        btn_export.clicked.connect(self._export_backup)
        action_layout.addWidget(btn_export)

        action_layout.addStretch()
        action_group.setLayout(action_layout)
        root.addWidget(action_group)

        # 备份列表
        list_group = QGroupBox("备份记录")
        list_layout = QVBoxLayout()
        self._list = QListWidget()
        list_layout.addWidget(self._list)
        self._info_label = QLabel()
        self._info_label.setStyleSheet("color: #64748B; font-size: 12px;")
        list_layout.addWidget(self._info_label)
        list_group.setLayout(list_layout)
        root.addWidget(list_group)

    def _db_path(self) -> Path:
        return ROOT_DIR / self.config.get("database", {}).get("path", "data/mms.db")

    def _refresh_list(self):
        self._list.clear()
        backups = sorted(self._backup_dir.glob("mms_backup_*.db"), reverse=True)
        max_backups = self.config.get("backup", {}).get("max_backups", 20)
        for f in backups:
            size_kb = f.stat().st_size / 1024
            self._list.addItem(f"{f.name}  ({size_kb:.1f} KB)")
        self._info_label.setText(
            f"备份目录: {self._backup_dir}  |  共 {len(backups)} 个备份  |  上限 {max_backups} 个"
        )

    def _do_backup(self):
        db = self._db_path()
        if not db.exists():
            Toast.show(self, "数据库文件不存在", "error")
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = self._backup_dir / f"mms_backup_{ts}.db"
        try:
            shutil.copy2(db, dest)
            self._cleanup_old_backups()
            Toast.show(self, f"备份成功: {dest.name}", "success")
            self._refresh_list()
        except Exception as e:
            QMessageBox.warning(self, "备份失败", str(e))

    def _cleanup_old_backups(self):
        max_backups = self.config.get("backup", {}).get("max_backups", 20)
        backups = sorted(self._backup_dir.glob("mms_backup_*.db"), reverse=True)
        for old in backups[max_backups:]:
            old.unlink(missing_ok=True)

    def _do_restore(self):
        item = self._list.currentItem()
        if not item:
            Toast.show(self, "请先选择一个备份", "warning")
            return
        name = item.text().split("  ")[0]
        backup_file = self._backup_dir / name
        if not backup_file.exists():
            Toast.show(self, "备份文件不存在", "error")
            return

        reply = QMessageBox.question(
            self, "确认恢复",
            f"恢复备份 [{name}] 将覆盖当前数据库，确定吗？\n建议先手动备份当前数据。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            db = self._db_path()
            try:
                shutil.copy2(backup_file, db)
                Toast.show(self, "恢复成功，请重启应用使更改生效", "success")
            except Exception as e:
                QMessageBox.warning(self, "恢复失败", str(e))

    def _do_delete(self):
        item = self._list.currentItem()
        if not item:
            Toast.show(self, "请先选择一个备份", "warning")
            return
        name = item.text().split("  ")[0]
        backup_file = self._backup_dir / name
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除备份 [{name}] 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            backup_file.unlink(missing_ok=True)
            Toast.show(self, "备份已删除", "success")
            self._refresh_list()

    def _export_backup(self):
        item = self._list.currentItem()
        if not item:
            Toast.show(self, "请先选择一个备份", "warning")
            return
        name = item.text().split("  ")[0]
        backup_file = self._backup_dir / name
        dest, _ = QFileDialog.getSaveFileName(self, "导出备份", name, "Database Files (*.db)")
        if dest:
            try:
                shutil.copy2(backup_file, dest)
                Toast.show(self, "备份已导出", "success")
            except Exception as e:
                QMessageBox.warning(self, "导出失败", str(e))
