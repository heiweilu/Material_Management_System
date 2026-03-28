"""入库服务层"""

from datetime import datetime

from sqlalchemy.orm import joinedload

from src.db.database import get_session
from src.db.models import InboundOrder, InboundDetail, Material, OperationLog


def get_all_orders() -> list[InboundOrder]:
    session = get_session()
    try:
        results = session.query(InboundOrder).options(
            joinedload(InboundOrder.supplier),
        ).order_by(InboundOrder.created_at.desc()).all()
        session.expunge_all()
        return results
    finally:
        session.close()


def get_order_by_id(order_id: int) -> InboundOrder | None:
    session = get_session()
    try:
        return session.get(InboundOrder, order_id)
    finally:
        session.close()


def create_order(header: dict, details: list[dict]) -> InboundOrder:
    """创建入库单 + 明细，同时更新库存

    header: {inbound_no, supplier_id, inbound_date, remarks}
    details: [{material_id, quantity, unit_price, remarks}, ...]
    """
    session = get_session()
    try:
        s = session
        order = InboundOrder(
            inbound_no=header["inbound_no"],
            supplier_id=header.get("supplier_id"),
            inbound_date=header.get("inbound_date", datetime.now().strftime("%Y-%m-%d")),
            remarks=header.get("remarks", ""),
        )
        s.add(order)
        s.flush()

        for d in details:
            detail = InboundDetail(
                inbound_id=order.id,
                material_id=d["material_id"],
                quantity=d["quantity"],
                unit_price=d.get("unit_price", 0),
                remarks=d.get("remarks", ""),
            )
            s.add(detail)
            # 更新库存
            mat = s.get(Material, d["material_id"])
            if mat:
                mat.current_stock += d["quantity"]

        s.add(OperationLog(
            operation_type="create",
            target_type="inbound_order",
            target_id=order.id,
            description=f"创建入库单 {order.inbound_no}，共 {len(details)} 条明细",
        ))
        s.commit()
        s.refresh(order)
        return order
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def delete_order(order_id: int):
    """删除入库单并回退库存"""
    session = get_session()
    try:
        order = session.get(InboundOrder, order_id)
        if not order:
            raise ValueError("入库单不存在")
        for detail in order.details:
            mat = session.get(Material, detail.material_id)
            if mat:
                mat.current_stock = max(0, mat.current_stock - detail.quantity)
        session.add(OperationLog(
            operation_type="delete",
            target_type="inbound_order",
            target_id=order.id,
            description=f"删除入库单 {order.inbound_no}",
        ))
        session.delete(order)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def generate_inbound_no() -> str:
    """生成入库单号: IN-yyyyMMdd-xxxx"""
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"IN-{today}-"
    session = get_session()
    try:
        last = (
            session.query(InboundOrder)
            .filter(InboundOrder.inbound_no.like(f"{prefix}%"))
            .order_by(InboundOrder.inbound_no.desc())
            .first()
        )
    finally:
        session.close()
    if last:
        seq = int(last.inbound_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"
