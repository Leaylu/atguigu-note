"""真实 HTTP + MCP stdio + API 进程重启。仅使用临时课程数据库。"""
import asyncio
from contextlib import contextmanager
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from app.db import make_engine
from app.seed import seed


@contextmanager
def running_api(env, port):
    process = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.api:app", "--host", "127.0.0.1",
        "--port", str(port), "--workers", "1"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    try:
        for _ in range(100):
            if process.poll() is not None:
                raise RuntimeError("临时 API 进程启动失败")
            try:
                if httpx.get(f"http://127.0.0.1:{port}/health", timeout=1, trust_env=False).status_code == 200:
                    break
            except httpx.RequestError:
                pass
            time.sleep(0.1)
        else:
            raise RuntimeError("临时 API 启动超时")
        yield
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


async def via_mcp(env, name, arguments):
    child_env = {k: v for k, v in env.items() if k not in ("APPROVER_TOKEN", "DATABASE_URL", "CHECKPOINT_PATH")}
    params = StdioServerParameters(command=sys.executable, args=["-m", "app.mcp_server"], env=child_env,
                                   cwd=str(Path.cwd()))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.call_tool(name, arguments)


def test_http_mcp_and_process_restart(tmp_path):
    url = "sqlite:///" + (tmp_path / "business.sqlite").as_posix()
    engine = make_engine(url)
    seed(engine)
    engine.dispose()
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    env = {**os.environ, "DATABASE_URL": url, "CHECKPOINT_PATH": str(tmp_path / "checkpoints.sqlite"),
           "AGENT_TOKEN": "network-agent-test", "APPROVER_TOKEN": "network-approver-test", "API_BASE_URL": base}
    params = {"paid_on": "2026-10-10", "as_of": "2026-10-11T12:00:00+08:00", "request_id": "network-demo"}
    with running_api(env, port):
        start = asyncio.run(via_mcp(env, "ecommerce_start_workflow", params))
        assert not start.isError
        wid = start.structuredContent["workflow_id"]
        assert start.structuredContent["status"] == "awaiting_approval"
        result = asyncio.run(via_mcp(env, "ecommerce_resume_workflow", {"workflow_id": wid}))
        assert result.isError
    with running_api(env, port):
        status = asyncio.run(via_mcp(env, "ecommerce_workflow_status", {"workflow_id": wid}))
        assert status.structuredContent["status"] == "awaiting_approval"
        response = httpx.post(f"{base}/workflows/{wid}/decision", headers={"Authorization": "Bearer network-approver-test"},
                              json={"decision": "approve"}, timeout=10, trust_env=False)
        assert response.status_code == 200
        result = asyncio.run(via_mcp(env, "ecommerce_resume_workflow", {"workflow_id": wid}))
        assert not result.isError
        assert result.structuredContent["status"] == "completed"
        assert len(result.structuredContent["tickets"]) == 3
        repeated = asyncio.run(via_mcp(env, "ecommerce_resume_workflow", {"workflow_id": wid}))
        assert repeated.structuredContent == result.structuredContent
