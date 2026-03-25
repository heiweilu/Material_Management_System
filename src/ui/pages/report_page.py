"""报表统计页面 — 分类库存分布饼图 + 出入库趋势折线图"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSplitter,
)
from PyQt6.QtCore import Qt

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib

from src.db.database import get_session
from src.db.models import Material, Category, InboundOrder, InboundDetail, OutboundOrder, OutboundDetail

# 中文字体
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei UI", "SimHei", "sans-serif"]
matplotlib.rcParams["axes.unicode_minus"] = False


class ReportPage(QWidget):
    """库存中心 - 报表统计"""

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
        title = QLabel("📈 报表统计")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        toolbar.addWidget(title)
        toolbar.addStretch()

        self._period_combo = QComboBox()
        self._period_combo.addItems(["最近7天", "最近30天", "最近90天", "全部"])
        self._period_combo.currentIndexChanged.connect(lambda _: self.refresh())
        toolbar.addWidget(QLabel("时间范围:"))
        toolbar.addWidget(self._period_combo)

        btn_refresh = QPushButton("刷新")
        btn_refresh.clicked.connect(self.refresh)
        toolbar.addWidget(btn_refresh)
        root.addLayout(toolbar)

        # 图表区 — 上下分栏
        splitter = QSplitter(Qt.Orientation.Vertical)

        # 上半：分类库存饼图
        self._fig_pie = Figure(figsize=(6, 3), dpi=100)
        self._fig_pie.set_facecolor("none")
        self._canvas_pie = FigureCanvas(self._fig_pie)
        splitter.addWidget(self._canvas_pie)

        # 下半：出入库趋势折线图
        self._fig_line = Figure(figsize=(6, 3), dpi=100)
        self._fig_line.set_facecolor("none")
        self._canvas_line = FigureCanvas(self._fig_line)
        splitter.addWidget(self._canvas_line)

        root.addWidget(splitter)

    def refresh(self):
        self._draw_pie()
        self._draw_line()

    # ── 分类库存饼图 ─────────────────────────
    def _draw_pie(self):
        self._fig_pie.clear()
        ax = self._fig_pie.add_subplot(111)

        with get_session() as s:
            cats = s.query(Category).filter(Category.parent_id.is_(None)).all()
            data = {}
            for cat in cats:
                # 统计该分类及其子分类下所有物料库存
                mat_ids = self._collect_material_ids(s, cat.id)
                total = sum(
                    m.current_stock
                    for m in s.query(Material).filter(Material.id.in_(mat_ids)).all()
                ) if mat_ids else 0
                if total > 0:
                    data[cat.name] = total

            # 未分类
            uncategorized = sum(
                m.current_stock
                for m in s.query(Material).filter(Material.category_id.is_(None)).all()
            )
            if uncategorized > 0:
                data["未分类"] = uncategorized

        if data:
            ax.pie(
                data.values(), labels=data.keys(), autopct="%1.1f%%",
                startangle=90, textprops={"fontsize": 9},
            )
            ax.set_title("分类库存分布", fontsize=12)
        else:
            ax.text(0.5, 0.5, "暂无库存数据", ha="center", va="center", fontsize=14, color="#94A3B8")
            ax.set_axis_off()

        self._canvas_pie.draw()

    def _collect_material_ids(self, session, category_id: int) -> list[int]:
        """递归收集分类及子分类下的物料 ID"""
        ids = [m.id for m in session.query(Material.id).filter(Material.category_id == category_id).all()]
        children = session.query(Category).filter(Category.parent_id == category_id).all()
        for child in children:
            ids.extend(self._collect_material_ids(session, child.id))
        return ids

    # ── 出入库趋势折线图 ─────────────────────
    def _draw_line(self):
        from datetime import datetime, timedelta

        self._fig_line.clear()
        ax = self._fig_line.add_subplot(111)

        period_map = {"最近7天": 7, "最近30天": 30, "最近90天": 90, "全部": 3650}
        days = period_map.get(self._period_combo.currentText(), 30)
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        with get_session() as s:
            # 入库按日期汇总
            inbound_orders = (
                s.query(InboundOrder)
                .filter(InboundOrder.inbound_date >= start_date)
                .all()
            )
            inbound_by_date: dict[str, int] = {}
            for o in inbound_orders:
                d = str(o.inbound_date) if o.inbound_date else ""
                qty = sum(det.quantity for det in o.details)
                inbound_by_date[d] = inbound_by_date.get(d, 0) + qty

            # 出库按日期汇总
            outbound_orders = (
                s.query(OutboundOrder)
                .filter(OutboundOrder.outbound_date >= start_date)
                .all()
            )
            outbound_by_date: dict[str, int] = {}
            for o in outbound_orders:
                d = str(o.outbound_date) if o.outbound_date else ""
                qty = sum(det.quantity for det in o.details)
                outbound_by_date[d] = outbound_by_date.get(d, 0) + qty

        all_dates = sorted(set(list(inbound_by_date.keys()) + list(outbound_by_date.keys())))

        if all_dates:
            in_vals = [inbound_by_date.get(d, 0) for d in all_dates]
            out_vals = [outbound_by_date.get(d, 0) for d in all_dates]
            # 简化日期标签: 只取月-日
            labels = [d[5:] if len(d) >= 10 else d for d in all_dates]

            ax.plot(labels, in_vals, marker="o", label="入库数量", color="#10B981")
            ax.plot(labels, out_vals, marker="s", label="出库数量", color="#EF4444")
            ax.legend(fontsize=9)
            ax.set_title("出入库趋势", fontsize=12)
            ax.tick_params(axis="x", rotation=45, labelsize=8)
            self._fig_line.tight_layout()
        else:
            ax.text(0.5, 0.5, "暂无出入库记录", ha="center", va="center", fontsize=14, color="#94A3B8")
            ax.set_axis_off()

        self._canvas_line.draw()
