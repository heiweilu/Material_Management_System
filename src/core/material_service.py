"""物料 CRUD + 搜索服务"""

import logging
from datetime import datetime, timezone

from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from sqlalchemy import distinct

from src.db.database import get_session
from src.db.models import Material, OperationLog

logger = logging.getLogger(__name__)


def get_all_materials(category_id: int | None = None) -> list[Material]:
    """获取所有物料，可按分类筛选"""
    session = get_session()
    try:
        q = session.query(Material).options(
            joinedload(Material.category),
        )
        if category_id is not None:
            q = q.filter(Material.category_id == category_id)
        results = q.order_by(Material.material_name).all()
        session.expunge_all()
        return results
    finally:
        session.close()


def search_materials(keyword: str, category_id: int | None = None) -> list[Material]:
    """按名称/型号/规格模糊搜索"""
    session = get_session()
    try:
        like = f"%{keyword}%"
        q = session.query(Material).options(
            joinedload(Material.category),
        ).filter(
            or_(
                Material.material_name.ilike(like),
                Material.model.ilike(like),
                Material.specification.ilike(like),
            )
        )
        if category_id is not None:
            q = q.filter(Material.category_id == category_id)
        results = q.order_by(Material.material_name).all()
        session.expunge_all()
        return results
    finally:
        session.close()


def get_material_by_id(material_id: int) -> Material | None:
    session = get_session()
    try:
        return session.query(Material).get(material_id)
    finally:
        session.close()


def create_material(data: dict) -> Material:
    """新增物料"""
    session = get_session()
    try:
        m = Material(**data)
        session.add(m)
        session.flush()
        _log(session, "create", "material", m.id,
             f"新增物料: {m.material_name}")
        session.commit()
        session.refresh(m)
        logger.info("新增物料: %s", m.material_name)
        return m
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def update_material(material_id: int, data: dict) -> Material | None:
    """更新物料"""
    session = get_session()
    try:
        m = session.query(Material).get(material_id)
        if m is None:
            return None
        for key, val in data.items():
            if hasattr(m, key):
                setattr(m, key, val)
        m.updated_at = datetime.now(timezone.utc)
        _log(session, "update", "material", m.id,
             f"编辑物料: {m.material_name}")
        session.commit()
        session.refresh(m)
        logger.info("更新物料: %s", m.material_name)
        return m
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def delete_material(material_id: int) -> bool:
    """删除物料"""
    session = get_session()
    try:
        m = session.query(Material).get(material_id)
        if m is None:
            return False
        desc = f"删除物料: {m.material_name}"
        session.delete(m)
        _log(session, "delete", "material", material_id, desc)
        session.commit()
        logger.info(desc)
        return True
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_low_stock_materials() -> list[Material]:
    """获取低库存预警物料"""
    session = get_session()
    try:
        results = session.query(Material).options(
            joinedload(Material.category),
        ).filter(
            Material.current_stock <= Material.warning_threshold
        ).order_by(Material.current_stock).all()
        session.expunge_all()
        return results
    finally:
        session.close()


def get_distinct_suppliers() -> list[str]:
    """获取所有已使用的供应商名称（去重），用于可编辑下拉框补全"""
    session = get_session()
    try:
        rows = session.query(distinct(Material.supplier)).filter(
            Material.supplier != "", Material.supplier.isnot(None)
        ).order_by(Material.supplier).all()
        return [r[0] for r in rows]
    finally:
        session.close()


def _log(session, op_type: str, target_type: str, target_id: int, desc: str):
    session.add(OperationLog(
        operation_type=op_type,
        target_type=target_type,
        target_id=target_id,
        description=desc,
    ))
