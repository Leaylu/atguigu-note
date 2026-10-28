"""仅初始化课程数据库；已有订单时拒绝覆盖。"""
import os
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import select, func
from app.db import make_engine, metadata, orders, inventory, fulfillment


def seed(engine):
    metadata.create_all(engine)
    with engine.begin() as conn:
        if conn.scalar(select(func.count()).select_from(orders)):
            raise ValueError("订单表已有数据，初始化已停止；原数据保持不变")
        rows = [
            ("A1001", "A", "SKU-1", 2, "paid", "08:00:00"),
            ("A1002", "A", "SKU-2", 1, "paid", "09:00:00"),
            ("A1003", "A", "SKU-2", 1, "paid", "10:00:00"),
            ("A1004", "A", "SKU-2", 1, "paid", "18:00:00"),
            ("A1005", "A", "SKU-2", 1, "shipped", "08:00:00"),
            ("A1006", "A", "SKU-1", 1, "cancelled", "08:00:00"),
            ("B1001", "B", "SKU-1", 1, "paid", "08:00:00"),
        ]
        conn.execute(orders.insert(), [dict(id=i, store=s, sku=k, quantity=q, status=t,
            paid_at=datetime.fromisoformat("2026-10-10T" + h + "+08:00")
            .astimezone(timezone.utc).replace(tzinfo=None)) for i, s, k, q, t, h in rows])
        conn.execute(inventory.insert(), [
            dict(store="A", sku="SKU-1", available=0),
            dict(store="A", sku="SKU-2", available=20),
            dict(store="B", sku="SKU-1", available=10)])
        conn.execute(fulfillment.insert(), [
            dict(order_id="A1002", event="warehouse_hold", note="地址核验未通过，仓库暂缓出库"),
            dict(order_id="A1005", event="shipped", note="已出库")])


if __name__ == "__main__":
    load_dotenv()
    Path("data").mkdir(exist_ok=True)
    engine = make_engine(os.environ["DATABASE_URL"])
    seed(engine)
    engine.dispose()
    print("初始化完成：7 个订单、3 条库存、2 条履约记录")
