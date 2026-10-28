"""真实 Streamable HTTP 握手、身份校验和业务流程。"""
import asyncio
from contextlib import contextmanager
import os
import socket
import subprocess
import sys
import time

import httpx
import pytest
from fastapi.testclient import TestClient
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from app.db import make_engine
from app.seed import seed
from app.mcp_http import create_http_app


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@contextmanager
def running(args, env, ready):
    process = subprocess.Popen(
        [sys.executable, "-m", *args], env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    try:
        for _ in range(150):
            if process.poll() is not None:
                raise RuntimeError("临时服务启动失败")
            try:
                if ready():
                    break
            except httpx.RequestError:
                pass
            time.sleep(0.1)
        else:
            raise RuntimeError("临时服务启动超时")
        yield
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_http_requires_token(monkeypatch):
    monkeypatch.delenv("AGENT_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="AGENT_TOKEN"):
        create_http_app()
    monkeypatch.setenv("AGENT_TOKEN", "replace-placeholder")
    with pytest.raises(RuntimeError, match="AGENT_TOKEN"):
        create_http_app()


async def call_sequence(base, api):
    headers = {"Authorization": "Bearer http-agent"}
    async with (httpx.AsyncClient(headers=headers, trust_env=False) as transport,
                streamable_http_client(base + "/mcp", http_client=transport) as (read, write, _)):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert len(tools.tools) == 6
            assert not any("decision" in tool.name or "approve" in tool.name for tool in tools.tools)
            sample = {"id": "DEMO001", "status": "paid",
                      "paid_at": "2026-10-10T08:00:00+08:00", "quantity": 2}
            result = await session.call_tool("ecommerce_check_orders", {"records": [sample]})
            assert not result.isError and result.structuredContent["valid"]
            invalid = await session.call_tool("ecommerce_check_orders", {"records": [{**sample, "quantity": 0}]})
            assert not invalid.isError and invalid.structuredContent["error_count"] == 1
            params = {"paid_on": "2026-10-10", "as_of": "2026-10-11T12:00:00+08:00"}
            first = await session.call_tool("ecommerce_list_orders", {**params, "limit": 2})
            assert first.structuredContent["total"] == 3
            assert first.structuredContent["next_offset"] == 2
            last = await session.call_tool("ecommerce_list_orders", {**params, "offset": 2, "limit": 2})
            assert last.structuredContent["items"][0]["id"] == "A1003"
            assert last.structuredContent["next_offset"] is None
            bad_params = await session.call_tool("ecommerce_list_orders", {**params, "limit": 101})
            assert bad_params.isError
            evidence = await session.call_tool("ecommerce_order_evidence", {"order_id": "A1002"})
            assert evidence.structuredContent["fulfillment"]["event"] == "warehouse_hold"
            denied = await session.call_tool("ecommerce_order_evidence", {"order_id": "B1001"})
            assert denied.isError
            start_args = {**params, "request_id": "http-demo"}
            start = await session.call_tool("ecommerce_start_workflow", start_args)
            wid = start.structuredContent["workflow_id"]
            assert start.structuredContent["status"] == "awaiting_approval"
            repeated = await session.call_tool("ecommerce_start_workflow", start_args)
            assert repeated.structuredContent["workflow_id"] == wid
            blocked = await session.call_tool("ecommerce_resume_workflow", {"workflow_id": wid})
            assert blocked.isError
            async with httpx.AsyncClient(trust_env=False) as client:
                no = await client.post(api + f"/workflows/{wid}/decision",
                    headers=headers, json={"decision": "approve"})
                assert no.status_code == 403
                yes = await client.post(api + f"/workflows/{wid}/decision",
                    headers={"Authorization": "Bearer http-approver"}, json={"decision": "approve"})
                assert yes.status_code == 200
            completed = await session.call_tool("ecommerce_resume_workflow", {"workflow_id": wid})
            assert completed.structuredContent["status"] == "completed"
            assert len(completed.structuredContent["tickets"]) == 3
            repeated = await session.call_tool("ecommerce_resume_workflow", {"workflow_id": wid})
            assert repeated.structuredContent == completed.structuredContent
    # Reconnect with a fresh HTTP/MCP client; business state is independent.
    async with (httpx.AsyncClient(headers=headers, trust_env=False) as transport,
                streamable_http_client(base + "/mcp", http_client=transport) as (read, write, _)):
        async with ClientSession(read, write) as session:
            await session.initialize()
            status = await session.call_tool("ecommerce_workflow_status", {"workflow_id": wid})
            assert status.structuredContent["status"] == "completed"


def test_real_streamable_http(tmp_path):
    database = "sqlite:///" + (tmp_path / "business.sqlite").as_posix()
    engine = make_engine(database)
    seed(engine)
    engine.dispose()
    api_port, mcp_port = free_port(), free_port()
    api, base = f"http://127.0.0.1:{api_port}", f"http://127.0.0.1:{mcp_port}"
    env = {**os.environ, "DATABASE_URL": database,
           "CHECKPOINT_PATH": str(tmp_path / "checkpoints.sqlite"),
           "AGENT_TOKEN": "http-agent", "APPROVER_TOKEN": "http-approver"}
    child = {k: v for k, v in env.items()
             if k not in ("APPROVER_TOKEN", "DATABASE_URL", "CHECKPOINT_PATH")}
    child["API_BASE_URL"] = api
    def api_ready():
        return httpx.get(api + "/health", timeout=1, trust_env=False).status_code == 200
    def mcp_ready():
        return httpx.get(base + "/mcp", timeout=1, trust_env=False).status_code == 401
    with running(["uvicorn", "app.api:app", "--host", "127.0.0.1",
                  "--port", str(api_port), "--workers", "1"], env, api_ready):
        with running(["app.mcp_http", "--port", str(mcp_port)], child, mcp_ready):
            for token in (None, "wrong-token", "http-approver"):
                headers = {} if token is None else {"Authorization": "Bearer " + token}
                assert httpx.post(base + "/mcp", headers=headers, timeout=3,
                                  trust_env=False).status_code == 401
            asyncio.run(call_sequence(base, api))
