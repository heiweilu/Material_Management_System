"""出库服务层"""

from datetime import datetime

from src.db.database import get_session
from src.db.models import OutboundOrder, OutboundDetail, Material, OperationLog


def get_all_orders() -> list[OutboundOrder]:
    with get_session() as s:
        return s.query(OutboundOrder).order_by(OutboundOrder.created_at.desc()).all()


def get_order_by_id(order_id: int) -> OutboundOrder | None:
    with get_session() as s:
        return s.get(OutboundOrder, order_id)


def create_order(header: dict, details: list[dict]) -> OutboundOrder:
    """创建出库单 + 明细，同时扣减库存

    header: {outbound_no, outbound_date, recipient, remarks}
    details: [{material_id, quantity, remarks}, ...]
    """
    with get_session() as s:
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


def delete_order(order_id: int):
    """删除出库单并回退库存"""
    with get_session() as s:
        order = s.get(OutboundOrder, order_id)
        if not order:
            raise ValueError("出库单不存在")
        for detail in order.details:
            mat = s.get(Material, detail.material_id)
            if mat:
                mat.current_stock += detail.quantity
        s.add(OperationLog(
            operation_type="delete",
            target_type="outbound_order",
            target_id=order.id,
            description=f"删除出库单 {order.outbound_no}",
        ))
        s.delete(order)
        s.commit()


def generate_outbound_no() -> str:
    """生成出库单号: OUT-yyyyMMdd-xxxx"""
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"OUT-{today}-"
    with get_session() as s:
        last = (
            s.query(OutboundOrder)
            .filter(OutboundOrder.outbound_no.like(f"{prefix}%"))
            .order_by(OutboundOrder.outbound_no.desc())
            .first()
        )
    if last:
        seq = int(last.outbound_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"
