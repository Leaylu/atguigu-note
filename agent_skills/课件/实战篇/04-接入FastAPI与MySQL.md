# 第四章：接入 FastAPI 与 MySQL

## 4.1 从文件校验走向实时业务查询

上一章调用的是本地 Python 能力。本章连接已有电商系统，查询服务端保存的订单、库存和履约信息。

调用链为：

```text
Codex → MCP 工具 → FastAPI 业务接口 → MySQL
```

业务接口已经承担身份验证、店铺范围和筛选规则。MCP 复用这些接口，使自然语言入口与其他业务调用方遵守同一套规则。

本章涉及两个工具：

| MCP 工具 | 对应接口 | 用途 |
| --- | --- | --- |
| `ecommerce_list_orders` | `GET /orders` | 分页查询超时未发货订单 |
| `ecommerce_order_evidence` | `GET /orders/{order_id}/evidence` | 获取某笔订单的库存、履约及分析结果 |

适配代码见 [app/mcp_server.py](../../代码/ecommerce-agent/app/mcp_server.py)。

## 4.2 先直接调用业务接口

保持第二章启动的 API 服务运行。以下命令在已设置 `AGENT_TOKEN` 的 PowerShell 中执行：

```powershell
$headers = @{ Authorization = "Bearer $env:AGENT_TOKEN" }
$queryUrl = "http://127.0.0.1:8000/orders?paid_on=2026-10-10&as_of=2026-10-11T12%3A00%3A00%2B08%3A00&offset=0&limit=20"
Invoke-RestMethod -Uri $queryUrl -Headers $headers | ConvertTo-Json -Depth 10
```

查询字符串中的 `%2B` 是加号的 URL 编码，用于保留时间中的 `+08:00`。MCP 适配层使用 HTTP 客户端的参数功能编码请求，无需模型手工拼接 URL。

预期结果包含 A1001、A1002、A1003。它们属于店铺 A，在目标日期付款，且截至指定时间已超过 24 小时仍处于 `paid` 状态。

这里的接口已经筛选超时订单。不要把返回总数理解为“店铺当日全部订单数”。

## 4.3 认识查询参数

| 参数 | 示例 | 含义 |
| --- | --- | --- |
| `paid_on` | `2026-10-10` | 业务时区下的付款日期 |
| `as_of` | `2026-10-11T12:00:00+08:00` | 计算是否超时的时刻 |
| `offset` | `0` | 跳过多少条符合条件的记录 |
| `limit` | `20` | 当前页最多返回多少条记录 |

这些参数不包含可以自由填写的店铺编号。店铺范围由服务端根据 Agent 凭据确定，避免模型修改参数就扩大查询范围。

分页意味着一次返回不一定包含全部数据。假设 `limit=2`，本项目第一批返回两条，还需要继续获取剩余记录。

报告只能在读取完整结果后声明“共发现三笔订单”。如果请求中断，只能说明已经取得的部分，并标明尚未完成。

## 4.4 在 Codex 中调用查询工具

输入：

> 请使用 ecommerce_list_orders 查询 2026-10-10 付款、截至 2026-10-11T12:00:00+08:00 超过 24 小时仍未发货的订单。每页读取 2 条，获取全部结果后列出订单编号，不要创建工单。

第一次调用参数为：

```json
{
  "paid_on": "2026-10-10",
  "as_of": "2026-10-11T12:00:00+08:00",
  "offset": 0,
  "limit": 2
}
```

首批返回 `total=3`、`next_offset=2`，`items` 中为 A1001、A1002。下一页把 `offset` 调整为 `2`，得到 A1003，此时 `next_offset=null`。完整读取后，共得到三个订单编号。

决定继续翻页的依据是接口返回的 `next_offset` 与已获取数量，而不是让模型猜测“应该没有更多了”。`limit` 允许 1 到 100，`offset` 必须为非负整数。

## 4.5 关联库存和履约证据

直接查询 A1001 的证据：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/orders/A1001/evidence" -Headers $headers | ConvertTo-Json -Depth 10
```

对应 MCP 调用参数为：

```json
{"order_id": "A1001"}
```

在 Codex 中可以继续输入：

> 对刚才查到的每笔订单调用 ecommerce_order_evidence，列出付款时间、商品数量、库存和履约记录。请把已知事实与可能原因分开，不要将没有履约记录直接判定为仓库故障。

预期能形成以下分析：

| 订单 | 查询事实 | 可给出的排查方向 |
| --- | --- | --- |
| A1001 | 数量 2，当前库存 0 | 核实可用库存、补货及占用情况 |
| A1002 | 当前库存 20，履约记录含 `warehouse_hold` | 核实仓库拦截原因与解除条件 |
| A1003 | 当前库存 20，没有履约记录 | 核实履约任务是否创建、同步是否异常 |

这些方向用于指导后续处理。当前库存快照不能替代付款时库存历史，也不能单独证明最终根因。

## 4.6 通过接口访问 MySQL 的价值

业务数据库保存的是事实，接口定义的是允许使用这些事实的方式。服务端负责使用确定的字段和筛选逻辑访问数据库，MCP 无需暴露任意 SQL 执行能力。

这样能够集中处理三类问题：

- 业务口径：付款日期、超时时限、订单状态在服务端统一计算。
- 权限范围：所有订单读取都必须符合当前凭据的店铺权限。
- 输出稳定：模型接收到约定字段，不依赖数据库内部表结构。

具体查询代码见 [app/business.py](../../代码/ecommerce-agent/app/business.py)，表结构见 [app/db.py](../../代码/ecommerce-agent/app/db.py)，认证与接口见 [app/api.py](../../代码/ecommerce-agent/app/api.py)。数据库内部结构发生变化时，可以先调整业务层。只要工具契约保持兼容，Skill 的排查步骤通常无需一起重写。

## 4.7 区分空结果与调用失败

| 情况 | 含义 | 报告中的表达 |
| --- | --- | --- |
| 成功返回空列表 | 本次条件下没有匹配订单 | “未发现符合本次筛选条件的订单” |
| 请求参数不合法 | 日期、时区或分页参数不符合接口要求 | 指出参数问题并修正 |
| 凭据缺失或错误 | 调用方身份未通过验证 | 说明认证失败 |
| 查询店铺 B 的 B1001 | HTTP 404，订单不存在或不在当前店铺权限内 | 说明无法访问，不泄露其他店铺数据 |
| 网络超时或服务未启动 | 本次查询没有获得有效业务结果 | 说明查询失败，不能宣称无异常 |

MCP 适配层把接口失败作为工具错误返回，不会把它改成正常的空列表。这样 Codex 才能分清“查过但没有”与“根本没查到”。

到这里，Codex 已能读取业务事实。下一章把查询顺序、证据要求和报告格式写入 Skill，让相同任务可以重复执行。

## 4.8 业务接口与数据访问实现

business.py 使用固定查询表达式和绑定参数。predicate 集中时间、状态和店铺条件；evidence 将库存与履约事实和可能原因分开。api.py 用 Depends 注入身份，再调用业务层。API 生命周期管理检查点连接，第六章会解释工作流细节。

<details>
<summary>app/business.py 完整代码</summary>

```python
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
```

</details>

<details>
<summary>app/api.py 完整代码</summary>

```python
"""FastAPI 是业务授权边界；仅示例身份，实际企业需替换为统一身份系统。"""
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, ConfigDict, field_validator
from langgraph.checkpoint.sqlite import SqliteSaver
from sqlalchemy import select
from app import business
from app.db import make_engine, tickets, orders
from app.workflow import WorkflowService, Conflict


class StartInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    paid_on: str
    as_of: str
    request_id: str = Field(min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")

    @field_validator("as_of")
    @classmethod
    def timezone_required(cls, value):
        from datetime import datetime
        if datetime.fromisoformat(value).utcoffset() is None:
            raise ValueError("as_of 必须带时区")
        return value


class DecisionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["approve", "reject"]


def create_app(database_url=None, checkpoint_path=None, agent_token=None, approver_token=None):
    @asynccontextmanager
    async def lifespan(app):
        load_dotenv()
        agent = agent_token or os.environ.get("AGENT_TOKEN")
        approver = approver_token or os.environ.get("APPROVER_TOKEN")
        if not agent or not approver or agent == approver or agent.startswith("replace-") or approver.startswith("replace-"):
            raise RuntimeError("请分别设置两个不同的非占位令牌")
        app.state.agent_token, app.state.approver_token = agent, approver
        path = Path(checkpoint_path or os.getenv("CHECKPOINT_PATH", "data/checkpoints.sqlite"))
        path.parent.mkdir(parents=True, exist_ok=True)
        engine = make_engine(database_url or os.environ["DATABASE_URL"])
        app.state.engine = engine
        try:
            with SqliteSaver.from_conn_string(str(path)) as saver:
                app.state.workflows = WorkflowService(engine, saver)
                yield
        finally:
            engine.dispose()

    app = FastAPI(title="电商订单异常排查 API", lifespan=lifespan)
    static_dir = Path(__file__).resolve().parent / "static"
    app.mount("/ui", StaticFiles(directory=static_dir), name="ui")

    @app.get("/", include_in_schema=False)
    def dashboard():
        return FileResponse(static_dir / "index.html")

    bearer = HTTPBearer(auto_error=False)

    def identity(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
        import secrets
        if credentials and secrets.compare_digest(credentials.credentials, app.state.agent_token):
            return "agent"
        if credentials and secrets.compare_digest(credentials.credentials, app.state.approver_token):
            return "approver"
        raise HTTPException(401, "缺少有效身份凭据")

    def agent(role=Depends(identity)):
        if role != "agent":
            raise HTTPException(403, "此入口需要 Agent 身份")
        return "A"

    @app.exception_handler(Conflict)
    async def conflict_handler(request, error):
        return JSONResponse(status_code=409, content={"detail": str(error)})

    @app.exception_handler(LookupError)
    async def missing_handler(request, error):
        return JSONResponse(status_code=404, content={"detail": str(error)})

    @app.exception_handler(ValueError)
    async def value_handler(request, error):
        return JSONResponse(status_code=422, content={"detail": str(error)})

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/orders")
    def get_orders(paid_on: str, as_of: str, offset: int = Query(0, ge=0),
                   limit: int = Query(20, ge=1, le=100), store=Depends(agent)):
        return business.list_orders(app.state.engine, store, paid_on, as_of, offset, limit)

    @app.get("/orders/{order_id}/evidence")
    def get_evidence(order_id: str, store=Depends(agent)):
        return business.evidence(app.state.engine, store, order_id)

    @app.post("/workflows")
    def start(body: StartInput, store=Depends(agent)):
        return app.state.workflows.start(store, **body.model_dump())

    @app.get("/workflows/{workflow_id}")
    def status(workflow_id: str, role=Depends(identity)):
        return app.state.workflows.status(workflow_id, "A")

    @app.post("/workflows/{workflow_id}/decision")
    def decide(workflow_id: str, body: DecisionInput, role=Depends(identity)):
        if role != "approver":
            raise HTTPException(403, "Agent 身份无审批权限")
        return app.state.workflows.decide(workflow_id, "A", body.decision)

    @app.post("/workflows/{workflow_id}/resume")
    def resume(workflow_id: str, store=Depends(agent)):
        return app.state.workflows.resume(workflow_id, store)

    @app.get("/tickets")
    def get_tickets(offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), store=Depends(agent)):
        with app.state.engine.connect() as conn:
            rows = conn.execute(select(tickets).join(orders, tickets.c.order_id == orders.c.id)
                .where(orders.c.store == store).order_by(tickets.c.id).offset(offset).limit(limit)).mappings().all()
        return {"items": [dict(row) for row in rows], "offset": offset, "limit": limit}

    return app


app = create_app()
```

</details>

[返回项目篇目录](README.md)


## 前端静态资源

API在根地址提供操作页面，/ui提供样式和脚本。运行前确认app/static包含[index.html](../../代码/ecommerce-agent/app/static/index.html)、[style.css](../../代码/ecommerce-agent/app/static/style.css)与[app.js](../../代码/ecommerce-agent/app/static/app.js)。直接使用完整配套工程即可，不需要npm构建。前端通过现有接口查询与提交操作，服务端继续校验Agent和审批身份。
