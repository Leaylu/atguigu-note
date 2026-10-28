"""LangGraph 状态管理；单 API 进程内以锁串行处理课程工作流。"""
from datetime import datetime, timezone
from threading import RLock
from typing import TypedDict
from uuid import uuid4
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from sqlalchemy import select, update
from app import business
from app.db import workflows, tickets, orders


class Conflict(ValueError):
    pass


class State(TypedDict, total=False):
    workflow_id: str
    store: str
    paid_on: str
    as_of: str
    status: str
    report: list[dict]
    tickets: list[dict]


class WorkflowService:
    def __init__(self, engine, checkpointer):
        self.engine = engine
        self.lock = RLock()
        builder = StateGraph(State)
        builder.add_node("investigate", self.investigate)
        builder.add_node("review", self.review)
        builder.add_edge(START, "investigate")
        builder.add_conditional_edges("investigate", lambda state: "review" if state["report"] else END)
        builder.add_edge("review", END)
        self.graph = builder.compile(checkpointer=checkpointer)

    @staticmethod
    def config(workflow_id):
        return {"configurable": {"thread_id": workflow_id}}

    def record(self, workflow_id, store):
        with self.engine.connect() as conn:
            row = conn.execute(select(workflows).where(workflows.c.id == workflow_id,
                                workflows.c.store == store)).mappings().first()
        if row is None:
            raise LookupError("工作流不存在或无权访问")
        return dict(row)

    def investigate(self, state: State):
        page = business.list_orders(self.engine, state["store"], state["paid_on"], state["as_of"], 0, 100)
        if page["next_offset"] is not None:
            raise Conflict("单次工作流最多处理 100 单，请缩小服务端查询范围后再启动；本次未创建工单")
        report = [business.evidence(self.engine, state["store"], row["id"]) for row in page["items"]]
        return {"report": report, "tickets": [], "status": "awaiting_approval" if report else "no_action"}

    def review(self, state: State):
        interrupt({"workflow_id": state["workflow_id"], "order_ids": [r["order"]["id"] for r in state["report"]],
                   "message": "请由审批人通过独立入口核对清单并决定；MCP 恢复工具不具备审批权限"})
        record = self.record(state["workflow_id"], state["store"])
        if record["decision"] not in ("approve", "reject"):
            raise Conflict("尚无人工审批记录")
        if record["decision"] == "reject":
            return {"status": "rejected", "tickets": []}
        results = []
        with self.engine.begin() as conn:
            for item in state["report"]:
                order_id = item["order"]["id"]
                current = conn.execute(select(orders).where(orders.c.id == order_id,
                    business.predicate(state["store"], state["paid_on"], state["as_of"]))
                    .with_for_update()).mappings().first()
                if not current:
                    results.append({"order_id": order_id, "outcome": "skipped_changed"})
                    continue
                existing = conn.execute(select(tickets).where(tickets.c.order_id == order_id)).mappings().first()
                if existing:
                    results.append({**dict(existing), "outcome": "existing"})
                    continue
                ticket = {"id": f"TK-{order_id}", "order_id": order_id,
                          "workflow_id": state["workflow_id"], "status": "open"}
                conn.execute(tickets.insert().values(**ticket))
                results.append({**ticket, "outcome": "created"})
        return {"status": "completed", "tickets": results}

    def status(self, workflow_id, store):
        with self.lock:
            record = self.record(workflow_id, store)
            snapshot = self.graph.get_state(self.config(workflow_id))
            result = dict(snapshot.values)
            if not result:
                result = {"workflow_id": workflow_id, "status": "not_started", "report": [], "tickets": []}
            if any(task.error for task in snapshot.tasks):
                result["status"] = "failed"
            result["decision"] = record["decision"]
            result["decided_at"] = (record["decided_at"].replace(tzinfo=timezone.utc).isoformat()
                                    if record["decided_at"] else None)
            return result

    def start(self, store, paid_on, as_of, request_id):
        business.scope(paid_on, as_of)
        params = {"paid_on": paid_on, "as_of": as_of}
        with self.lock:
            with self.engine.begin() as conn:
                old = conn.execute(select(workflows).where(workflows.c.request_id == request_id)).mappings().first()
                if old and (old["store"] != store or old["params"] != params):
                    raise Conflict("request_id 已用于不同参数，请使用新的请求编号")
                workflow_id = old["id"] if old else str(uuid4())
                if not old:
                    conn.execute(workflows.insert().values(id=workflow_id, request_id=request_id, store=store, params=params))
            config = self.config(workflow_id)
            snapshot = self.graph.get_state(config)
            if not snapshot.values:
                self.graph.invoke({"workflow_id": workflow_id, "store": store, **params}, config)
            return self.status(workflow_id, store)

    def decide(self, workflow_id, store, decision):
        with self.lock:
            record = self.record(workflow_id, store)
            if record["decision"]:
                if record["decision"] != decision:
                    raise Conflict("审批记录已提交，不能改写")
                return self.status(workflow_id, store)
            if self.status(workflow_id, store)["status"] != "awaiting_approval":
                raise Conflict("仅等待审批的工作流允许提交决策")
            with self.engine.begin() as conn:
                conn.execute(update(workflows).where(workflows.c.id == workflow_id).values(
                    decision=decision, decided_at=datetime.now(timezone.utc).replace(tzinfo=None)))
            return self.status(workflow_id, store)

    def resume(self, workflow_id, store):
        with self.lock:
            record = self.record(workflow_id, store)
            config = self.config(workflow_id)
            snapshot = self.graph.get_state(config)
            if not snapshot.next:
                return self.status(workflow_id, store)
            if not record["decision"]:
                raise Conflict("尚未获得人工审批；请审批人通过独立审批入口提交决定")
            self.graph.invoke(Command(resume=True), config)
            return self.status(workflow_id, store)
