"""业务表。时间统一以 UTC 无时区 datetime 存储。"""
from sqlalchemy import (MetaData, Table, Column, String, Integer, DateTime,
                        JSON, ForeignKey, create_engine)

metadata = MetaData()
orders = Table("orders", metadata,
    Column("id", String(32), primary_key=True),
    Column("store", String(16), nullable=False),
    Column("sku", String(32), nullable=False),
    Column("quantity", Integer, nullable=False),
    Column("status", String(16), nullable=False),
    Column("paid_at", DateTime, nullable=False))
inventory = Table("inventory", metadata,
    Column("store", String(16), primary_key=True),
    Column("sku", String(32), primary_key=True),
    Column("available", Integer, nullable=False))
fulfillment = Table("fulfillment", metadata,
    Column("order_id", String(32), ForeignKey("orders.id"), primary_key=True),
    Column("event", String(32), nullable=False),
    Column("note", String(200), nullable=False))
workflows = Table("workflows", metadata,
    Column("id", String(36), primary_key=True),
    Column("request_id", String(64), unique=True, nullable=False),
    Column("store", String(16), nullable=False),
    Column("params", JSON, nullable=False),
    Column("decision", String(16)),
    Column("decided_at", DateTime))
tickets = Table("tickets", metadata,
    Column("id", String(40), primary_key=True),
    Column("order_id", String(32), ForeignKey("orders.id"), unique=True, nullable=False),
    Column("workflow_id", String(36), ForeignKey("workflows.id"), nullable=False),
    Column("status", String(16), nullable=False))


def make_engine(url: str):
    kwargs = {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {}
    return create_engine(url, pool_pre_ping=True, **kwargs)
