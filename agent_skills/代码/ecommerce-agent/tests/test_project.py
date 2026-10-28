import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func, update
from app.api import create_app
from app.checker import check_orders
from app.db import make_engine, tickets, orders, workflows
from app.seed import seed
from app import mcp_server

PARAMS = {"paid_on": "2026-10-10", "as_of": "2026-10-11T12:00:00+08:00"}
AGENT = {"Authorization": "Bearer agent-test"}
APPROVER = {"Authorization": "Bearer approver-test"}


@pytest.fixture
def system(tmp_path):
    url = "sqlite:///" + (tmp_path / "business.sqlite").as_posix()
    engine = make_engine(url)
    seed(engine)
    checkpoint = str(tmp_path / "checkpoints.sqlite")
    def factory():
        return create_app(url, checkpoint, "agent-test", "approver-test")
    with TestClient(factory()) as client:
        yield client, engine, factory
    engine.dispose()


def start(client, request_id="test-1", **overrides):
    result = client.post("/workflows", headers=AGENT, json={**PARAMS, "request_id": request_id, **overrides})
    assert result.status_code == 200, result.text
    return result.json()


def count_tickets(engine):
    with engine.connect() as conn:
        return conn.scalar(select(func.count()).select_from(tickets))


def test_checker_and_cli():
    result = check_orders(json.loads(Path("samples/orders.json").read_text()))
    assert result["valid"] and result["record_count"] == 3
    result = check_orders(json.loads(Path("samples/invalid-orders.json").read_text()))
    assert not result["valid"] and result["error_count"] == 4
    for path, expected in [("samples/orders.json", 0), ("samples/invalid-orders.json", 1), ("missing.json", 2)]:
        process = subprocess.run([sys.executable, "-m", "app.checker", path], capture_output=True)
        assert process.returncode == expected


def test_checker_rejects_boolean_quantity():
    record = {"id": "X", "status": "paid", "quantity": True, "paid_at": PARAMS["as_of"]}
    assert check_orders([record])["error_count"] == 1


def test_query_paging_empty_and_permissions(system):
    client, _, _ = system
    first = client.get("/orders", headers=AGENT, params={**PARAMS, "limit": 2}).json()
    assert first["total"] == 3 and first["next_offset"] == 2
    assert [row["id"] for row in first["items"]] == ["A1001", "A1002"]
    last = client.get("/orders", headers=AGENT, params={**PARAMS, "offset": 2, "limit": 2}).json()
    assert last["items"][0]["id"] == "A1003" and last["next_offset"] is None
    empty = client.get("/orders", headers=AGENT, params={**PARAMS, "paid_on": "2026-10-09"}).json()
    assert empty["total"] == 0 and empty["items"] == []
    assert client.get("/orders", params=PARAMS).status_code == 401
    assert client.get("/orders", params=PARAMS, headers=APPROVER).status_code == 403
    assert client.get("/orders/B1001/evidence", headers=AGENT).status_code == 404


@pytest.mark.parametrize("change", [{"limit": 101}, {"offset": -1}, {"as_of": "2026-10-11T12:00:00"}, {"paid_on": "bad"}])
def test_invalid_query(system, change):
    assert system[0].get("/orders", params={**PARAMS, **change}, headers=AGENT).status_code == 422


def test_strict_24_hours(system):
    response = system[0].get("/orders", headers=AGENT, params={**PARAMS, "as_of": "2026-10-11T08:00:00+08:00"})
    assert response.json()["total"] == 0
    response = system[0].get("/orders", headers=AGENT, params={**PARAMS, "as_of": "2026-10-11T08:00:01+08:00"})
    assert response.json()["total"] == 1


def test_over_limit_never_creates_partial_tickets(system):
    client, engine, _ = system
    with engine.begin() as conn:
        template = dict(conn.execute(select(orders).where(orders.c.id == "A1003")).mappings().one())
        conn.execute(orders.insert(), [{**template, "id": f"EXTRA-{i:03d}"} for i in range(100)])
    response = client.post("/workflows", headers=AGENT, json={**PARAMS, "request_id": "over-limit"})
    assert response.status_code == 409
    assert count_tickets(engine) == 0
    with engine.connect() as conn:
        wid = conn.scalar(select(workflows.c.id).where(workflows.c.request_id == "over-limit"))
    assert client.get(f"/workflows/{wid}", headers=AGENT).json()["status"] == "failed"


def test_evidence(system):
    client = system[0]
    a = client.get("/orders/A1001/evidence", headers=AGENT).json()
    b = client.get("/orders/A1002/evidence", headers=AGENT).json()
    c = client.get("/orders/A1003/evidence", headers=AGENT).json()
    assert a["inventory"]["available"] == 0
    assert b["fulfillment"]["event"] == "warehouse_hold"
    assert c["fulfillment"] is None and "待确认" in c["analysis"]["possible_reason"]


def test_approval_gate_idempotency_and_decision_immutability(system):
    client, engine, _ = system
    first = start(client)
    wid = first["workflow_id"]
    assert first["status"] == "awaiting_approval" and len(first["report"]) == 3
    assert count_tickets(engine) == 0
    assert start(client)["workflow_id"] == wid
    assert client.post(f"/workflows/{wid}/resume", headers=AGENT).status_code == 409
    assert client.post(f"/workflows/{wid}/decision", headers=AGENT, json={"decision": "approve"}).status_code == 403
    assert client.post(f"/workflows/{wid}/decision", headers=APPROVER, json={"decision": "approve"}).status_code == 200
    assert count_tickets(engine) == 0
    result = client.post(f"/workflows/{wid}/resume", headers=AGENT).json()
    assert result["status"] == "completed" and len(result["tickets"]) == 3
    assert all(row["outcome"] == "created" for row in result["tickets"])
    assert client.post(f"/workflows/{wid}/resume", headers=AGENT).json() == result
    assert count_tickets(engine) == 3
    assert client.post(f"/workflows/{wid}/decision", headers=APPROVER, json={"decision": "reject"}).status_code == 409
    conflict = client.post("/workflows", headers=AGENT, json={**PARAMS, "request_id": "test-1", "paid_on": "2026-10-09"})
    assert conflict.status_code == 409
    next_wid = start(client, "test-2")["workflow_id"]
    client.post(f"/workflows/{next_wid}/decision", headers=APPROVER, json={"decision": "approve"})
    repeated = client.post(f"/workflows/{next_wid}/resume", headers=AGENT).json()
    assert all(row["outcome"] == "existing" for row in repeated["tickets"])
    assert count_tickets(engine) == 3


def test_reject_and_empty(system):
    client, engine, _ = system
    wid = start(client)["workflow_id"]
    client.post(f"/workflows/{wid}/decision", headers=APPROVER, json={"decision": "reject"})
    assert client.post(f"/workflows/{wid}/resume", headers=AGENT).json()["status"] == "rejected"
    assert count_tickets(engine) == 0
    assert start(client, "empty", paid_on="2026-10-09")["status"] == "no_action"


def test_recheck_before_writing(system):
    client, engine, _ = system
    wid = start(client)["workflow_id"]
    client.post(f"/workflows/{wid}/decision", headers=APPROVER, json={"decision": "approve"})
    with engine.begin() as conn:
        conn.execute(update(orders).where(orders.c.id == "A1001").values(status="shipped"))
    result = client.post(f"/workflows/{wid}/resume", headers=AGENT).json()
    assert result["tickets"][0] == {"order_id": "A1001", "outcome": "skipped_changed"}
    assert count_tickets(engine) == 2


def test_persistent_restart(system):
    client, engine, factory = system
    wid = start(client)["workflow_id"]
    # 新应用/新 saver 重读相同文件，原应用不再执行工作流。
    with TestClient(factory()) as restarted:
        result = restarted.get(f"/workflows/{wid}", headers=AGENT).json()
        assert result["status"] == "awaiting_approval"
        restarted.post(f"/workflows/{wid}/decision", headers=APPROVER, json={"decision": "approve"})
        assert restarted.post(f"/workflows/{wid}/resume", headers=AGENT).json()["status"] == "completed"
    assert count_tickets(engine) == 3


def test_reseed_does_not_overwrite(system):
    with pytest.raises(ValueError, match="已有数据"):
        seed(system[1])


@pytest.mark.parametrize("failure,expected", [(httpx.ReadTimeout("timeout"), "超时"), (httpx.ConnectError("offline"), "无法连接")])
def test_mcp_network_errors(monkeypatch, failure, expected):
    monkeypatch.setenv("AGENT_TOKEN", "agent-test")
    async def fail(self, *args, **kwargs):
        raise failure
    monkeypatch.setattr(httpx.AsyncClient, "request", fail)
    with pytest.raises(RuntimeError, match=expected):
        asyncio.run(mcp_server.request("GET", "/orders"))


def test_frontend_assets_and_api_auth(system):
    client = system[0]
    page = client.get("/")
    assert page.status_code == 200 and "text/html" in page.headers["content-type"]
    for filename in ("app.js", "style.css"):
        assert client.get(f"/ui/{filename}").status_code == 200
    assert client.get("/orders", params=PARAMS).status_code == 401
    assert client.get("/ui/../.env").status_code == 404
