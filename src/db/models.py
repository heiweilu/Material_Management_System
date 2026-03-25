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


# ── 2. 供应商 ────────────────────────────────────────────────


class Supplier(Base):
    """供应商信息"""
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    supplier_name = Column(String(200), unique=True, nullable=False)
    contact_person = Column(String(100), default="")
    phone = Column(String(50), default="")
    email = Column(String(200), default="")
    address = Column(Text, default="")
    website = Column(String(500), default="")
    status = Column(String(20), nullable=False, default="active")   # active / inactive
    remarks = Column(Text, default="")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    materials = relationship("Material", back_populates="default_supplier")
    inbound_orders = relationship("InboundOrder", back_populates="supplier")

    def __repr__(self):
        return f"<Supplier(id={self.id}, name='{self.supplier_name}')>"


# ── 3. 物料主表 ──────────────────────────────────────────────


class Material(Base):
    """物料（电子元器件）"""
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    material_code = Column(String(100), unique=True, nullable=False)
    material_name = Column(String(200), nullable=False)
    model = Column(String(200), default="")              # 型号
    package_type = Column(String(100), default="")       # 封装 (0805, SOP-8 …)
    specification = Column(String(200), default="")      # 规格 (100Ω, 10μF …)
    unit = Column(String(20), nullable=False, default="个")
    current_stock = Column(Integer, nullable=False, default=0)
    warning_threshold = Column(Integer, nullable=False, default=10)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    default_supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    storage_location = Column(String(200), default="")   # 存放位置（抽屉A-3）
    datasheet_path = Column(String(500), default="")     # 数据手册本地路径
    remarks = Column(Text, default="")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    category = relationship("Category", back_populates="materials")
    default_supplier = relationship("Supplier", back_populates="materials")
    inbound_details = relationship("InboundDetail", back_populates="material")
    outbound_details = relationship("OutboundDetail", back_populates="material")

    def __repr__(self):
        return f"<Material(id={self.id}, code='{self.material_code}', name='{self.material_name}')>"


# ── 4. 入库单 ────────────────────────────────────────────────


class InboundOrder(Base):
    """入库单表头"""
    __tablename__ = "inbound_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    inbound_no = Column(String(50), unique=True, nullable=False)    # IN-YYYYMMDD-NNN
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    inbound_date = Column(DateTime, nullable=False, default=_utcnow)
    remarks = Column(Text, default="")
    created_at = Column(DateTime, default=_utcnow)

    supplier = relationship("Supplier", back_populates="inbound_orders")
    details = relationship("InboundDetail", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<InboundOrder(id={self.id}, no='{self.inbound_no}')>"


class InboundDetail(Base):
    """入库单明细"""
    __tablename__ = "inbound_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    inbound_id = Column(Integer, ForeignKey("inbound_orders.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=True)
    remarks = Column(Text, default="")

    order = relationship("InboundOrder", back_populates="details")
    material = relationship("Material", back_populates="inbound_details")


# ── 5. 出库单 ────────────────────────────────────────────────


class OutboundOrder(Base):
    """出库单表头"""
    __tablename__ = "outbound_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    outbound_no = Column(String(50), unique=True, nullable=False)   # OUT-YYYYMMDD-NNN
    outbound_date = Column(DateTime, nullable=False, default=_utcnow)
    recipient = Column(String(200), default="")    # 领用人/用途
    remarks = Column(Text, default="")
    created_at = Column(DateTime, default=_utcnow)

    details = relationship("OutboundDetail", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<OutboundOrder(id={self.id}, no='{self.outbound_no}')>"


class OutboundDetail(Base):
    """出库单明细"""
    __tablename__ = "outbound_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    outbound_id = Column(Integer, ForeignKey("outbound_orders.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    remarks = Column(Text, default="")

    order = relationship("OutboundOrder", back_populates="details")
    material = relationship("Material", back_populates="outbound_details")


# ── 6. 操作日志 ──────────────────────────────────────────────


class OperationLog(Base):
    """系统操作日志"""
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    operation_type = Column(String(30), nullable=False)   # create/update/delete/inbound/outbound/import/export/backup
    target_type = Column(String(30), default="")          # material/supplier/inbound/outbound
    target_id = Column(Integer, nullable=True)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=_utcnow)

    def __repr__(self):
        return f"<OperationLog(id={self.id}, type='{self.operation_type}')>"
