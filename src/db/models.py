"""SQLAlchemy ORM 模型定义 — 物料管理系统"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, ForeignKey
)
from sqlalchemy.orm import DeclarativeBase, relationship


def _utcnow():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


# ── 1. 物料分类（树形结构） ───────────────────────────────────


class Category(Base):
    """物料分类（支持多级树形）"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    level = Column(Integer, nullable=False, default=0)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent", cascade="all, delete-orphan")
    materials = relationship("Material", back_populates="category")

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"


# ── 2. 物料主表 ──────────────────────────────────────────────


class Material(Base):
    """物料（电子元器件）"""
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    material_name = Column(String(200), nullable=False)
    model = Column(String(200), default="")              # 型号
    package_type = Column(String(100), default="")       # 封装 (0805, SOP-8 …)
    specification = Column(String(200), default="")      # 规格 (100Ω, 10μF …)
    unit = Column(String(20), nullable=False, default="个")
    current_stock = Column(Integer, nullable=False, default=0)
    warning_threshold = Column(Integer, nullable=False, default=10)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    storage_location = Column(String(200), default="")   # 存放位置（抽屉A-3）
    datasheet_path = Column(String(500), default="")     # 数据手册路径或URL
    image_path = Column(String(500), default="")         # 物料图片路径
    remarks = Column(Text, default="")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    category = relationship("Category", back_populates="materials")

    def __repr__(self):
        return f"<Material(id={self.id}, name='{self.material_name}')>"


# ── 3. 操作日志 ──────────────────────────────────────────────


class OperationLog(Base):
    """系统操作日志"""
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    operation_type = Column(String(30), nullable=False)   # create/update/delete/import/export/backup
    target_type = Column(String(30), default="")          # material/supplier/inbound/outbound
    target_id = Column(Integer, nullable=True)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=_utcnow)

    def __repr__(self):
        return f"<OperationLog(id={self.id}, type='{self.operation_type}')>"
