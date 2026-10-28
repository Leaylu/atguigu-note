"""确定性的查询与证据分析，供 API 和工作流共同复用。"""
from datetime import date, datetime, timedelta, timezone
from sqlalchemy import select, and_, func
from app.db import orders, inventory, fulfillment

SHANGHAI = timezone(timedelta(hours=8))


def scope(paid_on: str, as_of: str):
    day = date.fromisoformat(paid_on)
    instant = datetime.fromisoformat(as_of)
    if instant.utcoffset() is None:
        raise ValueError("as_of 必须带时区")
    start = datetime.combine(day, datetime.min.time(), SHANGHAI)
    if instant < start:
        raise ValueError("as_of 不能早于所查支付日期起点")
    utc = lambda value: value.astimezone(timezone.utc).replace(tzinfo=None)
    return utc(start), utc(start + timedelta(days=1)), utc(instant - timedelta(hours=24))


def predicate(store, paid_on, as_of):
    start, end, deadline = scope(paid_on, as_of)
    return and_(orders.c.store == store, orders.c.status == "paid",
                orders.c.paid_at >= start, orders.c.paid_at < end,
                orders.c.paid_at < deadline)


def serialize_order(row):
    value = dict(row)
    value["paid_at"] = value["paid_at"].replace(tzinfo=timezone.utc).astimezone(SHANGHAI).isoformat()
    return value


def list_orders(engine, store, paid_on, as_of, offset=0, limit=20):
    condition = predicate(store, paid_on, as_of)
    with engine.connect() as conn:
        total = conn.scalar(select(func.count()).select_from(orders).where(condition))
        rows = conn.execute(select(orders).where(condition).order_by(orders.c.id)
                            .offset(offset).limit(limit)).mappings().all()
    next_offset = offset + len(rows) if offset + len(rows) < total else None
    return {"store": store, "paid_on": paid_on, "as_of": as_of,
            "total": total, "items": [serialize_order(row) for row in rows],
            "next_offset": next_offset}


def evidence(engine, store, order_id):
    with engine.connect() as conn:
        order = conn.execute(select(orders).where(orders.c.id == order_id,
                              orders.c.store == store)).mappings().first()
        if not order:
            raise LookupError("订单不存在或不在当前店铺权限内")
        stock = conn.execute(select(inventory).where(inventory.c.store == store,
                              inventory.c.sku == order["sku"])).mappings().first()
        event = conn.execute(select(fulfillment).where(fulfillment.c.order_id == order_id)).mappings().first()
    if stock is None:
        reason, suggestion = "库存记录缺失，原因待确认", "联系库存系统负责人补齐证据"
    elif stock["available"] < order["quantity"]:
        reason, suggestion = "当前可用库存不足，可能影响发货", "核实库存分配及补货计划"
    elif event and event["event"] == "warehouse_hold":
        reason, suggestion = "存在仓库拦截记录", "联系履约人员核验拦截原因"
    else:
        reason, suggestion = "现有证据不足，原因待确认", "检查履约同步和仓库处理状态"
    return {"order": serialize_order(order), "inventory": dict(stock) if stock else None,
            "fulfillment": dict(event) if event else None,
            "analysis": {"possible_reason": reason, "suggestion": suggestion}}
