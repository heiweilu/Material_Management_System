"""供应商 CRUD 服务"""

import logging
from datetime import datetime, timezone

from sqlalchemy import or_

from src.db.database import get_session
from src.db.models import Supplier, Material, OperationLog

logger = logging.getLogger(__name__)


def get_all_suppliers(active_only: bool = False) -> list[Supplier]:
    session = get_session()
    try:
        q = session.query(Supplier)
        if active_only:
            q = q.filter(Supplier.status == "active")
        results = q.order_by(Supplier.supplier_name).all()
        session.expunge_all()
        return results
    finally:
        session.close()


def search_suppliers(keyword: str) -> list[Supplier]:
    session = get_session()
    try:
        like = f"%{keyword}%"
        results = session.query(Supplier).filter(
            or_(
                Supplier.supplier_name.ilike(like),
                Supplier.contact_person.ilike(like),
                Supplier.phone.ilike(like),
            )
        ).order_by(Supplier.supplier_name).all()
        session.expunge_all()
        return results
    finally:
        session.close()


def get_supplier_by_id(supplier_id: int) -> Supplier | None:
    session = get_session()
    try:
        return session.query(Supplier).get(supplier_id)
    finally:
        session.close()


def create_supplier(data: dict) -> Supplier:
    session = get_session()
    try:
        s = Supplier(**data)
        session.add(s)
        session.flush()
        session.add(OperationLog(
            operation_type="create", target_type="supplier",
            target_id=s.id, description=f"新增供应商: {s.supplier_name}",
        ))
        session.commit()
        session.refresh(s)
        logger.info("新增供应商: %s", s.supplier_name)
        return s
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def update_supplier(supplier_id: int, data: dict) -> Supplier | None:
    session = get_session()
    try:
        s = session.query(Supplier).get(supplier_id)
        if s is None:
            return None
        for key, val in data.items():
            if hasattr(s, key):
                setattr(s, key, val)
        s.updated_at = datetime.now(timezone.utc)
        session.add(OperationLog(
            operation_type="update", target_type="supplier",
            target_id=s.id, description=f"编辑供应商: {s.supplier_name}",
        ))
        session.commit()
        session.refresh(s)
        logger.info("更新供应商: %s", s.supplier_name)
        return s
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def delete_supplier(supplier_id: int) -> bool:
    session = get_session()
    try:
        s = session.query(Supplier).get(supplier_id)
        if s is None:
            return False
        desc = f"删除供应商: {s.supplier_name}"
        session.delete(s)
        session.add(OperationLog(
            operation_type="delete", target_type="supplier",
            target_id=supplier_id, description=desc,
        ))
        session.commit()
        logger.info(desc)
        return True
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_supplier_materials(supplier_id: int) -> list[Material]:
    """获取供应商关联的物料"""
    session = get_session()
    try:
        return session.query(Material).filter(
            Material.default_supplier_id == supplier_id
        ).order_by(Material.material_code).all()
    finally:
        session.close()
