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
