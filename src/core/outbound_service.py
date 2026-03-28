"""出库服务层"""

from datetime import datetime

from src.db.database import get_session
from src.db.models import OutboundOrder, OutboundDetail, Material, OperationLog


def get_all_orders() -> list[OutboundOrder]:
    session = get_session()
    try:
        results = session.query(OutboundOrder).order_by(OutboundOrder.created_at.desc()).all()
        session.expunge_all()
        return results
    finally:
        session.close()


def get_order_by_id(order_id: int) -> OutboundOrder | None:
    session = get_session()
    try:
        return session.get(OutboundOrder, order_id)
    finally:
        session.close()


def create_order(header: dict, details: list[dict]) -> OutboundOrder:
    """创建出库单 + 明细，同时扣减库存

    header: {outbound_no, outbound_date, recipient, remarks}
    details: [{material_id, quantity, remarks}, ...]
    """
    session = get_session()
    try:
        s = session
        # 先检查库存是否充足
        for d in details:
            mat = s.get(Material, d["material_id"])
            if not mat:
                raise ValueError(f"物料ID {d['material_id']} 不存在")
            if mat.current_stock < d["quantity"]:
                raise ValueError(
                    f"物料 [{mat.material_code}] {mat.material_name} "
                    f"库存不足: 当前 {mat.current_stock}, 需要 {d['quantity']}"
                )

        order = OutboundOrder(
            outbound_no=header["outbound_no"],
            outbound_date=header.get("outbound_date", datetime.now().strftime("%Y-%m-%d")),
            recipient=header.get("recipient", ""),
            remarks=header.get("remarks", ""),
        )
        s.add(order)
        s.flush()

        for d in details:
            detail = OutboundDetail(
                outbound_id=order.id,
                material_id=d["material_id"],
                quantity=d["quantity"],
                remarks=d.get("remarks", ""),
            )
            s.add(detail)
            mat = s.get(Material, d["material_id"])
            if mat:
                mat.current_stock -= d["quantity"]

        s.add(OperationLog(
            operation_type="create",
            target_type="outbound_order",
            target_id=order.id,
            description=f"创建出库单 {order.outbound_no}，共 {len(details)} 条明细",
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
    """删除出库单并回退库存"""
    session = get_session()
    try:
        order = session.get(OutboundOrder, order_id)
        if not order:
            raise ValueError("出库单不存在")
        for detail in order.details:
            mat = session.get(Material, detail.material_id)
            if mat:
                mat.current_stock += detail.quantity
        session.add(OperationLog(
            operation_type="delete",
            target_type="outbound_order",
            target_id=order.id,
            description=f"删除出库单 {order.outbound_no}",
        ))
        session.delete(order)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def generate_outbound_no() -> str:
    """生成出库单号: OUT-yyyyMMdd-xxxx"""
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"OUT-{today}-"
    session = get_session()
    try:
        last = (
            session.query(OutboundOrder)
            .filter(OutboundOrder.outbound_no.like(f"{prefix}%"))
            .order_by(OutboundOrder.outbound_no.desc())
            .first()
        )
    finally:
        session.close()
    if last:
        seq = int(last.outbound_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"
