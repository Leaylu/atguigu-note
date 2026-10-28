"""仅用临时SQLite验证课程重置，不连接用户数据库。"""
import json
import socket
from pathlib import Path

import pytest
from sqlalchemy import select, func
from app import reset_demo as reset
from app.db import make_engine, orders, tickets, workflows
from app.seed import seed


@pytest.fixture
def sample(tmp_path, monkeypatch):
    monkeypatch.setattr(reset, "check_services", lambda *args: None)
    (tmp_path / "data").mkdir()
    url = "sqlite:///" + (tmp_path / "data/business.sqlite").as_posix()
    engine = make_engine(url)
    seed(engine)
    with engine.begin() as conn:
        conn.execute(workflows.insert().values(id="W1", request_id="demo", store="A", params={}))
        conn.execute(tickets.insert().values(id="TK-A1001", order_id="A1001", workflow_id="W1", status="open"))
    engine.dispose()
    for name in ("checkpoints.sqlite", "checkpoints.sqlite-wal", "checkpoints.sqlite-shm"):
        (tmp_path / "data" / name).write_bytes(b"checkpoint-fixture")
    (tmp_path / ".env").write_text("keep-local-config", encoding="utf-8")
    (tmp_path / "outputs").mkdir()
    (tmp_path / "outputs/report.md").write_text("keep-report", encoding="utf-8")
    return tmp_path, url


def counts(url):
    engine = make_engine(url)
    try:
        with engine.connect() as conn:
            return {t.name: conn.scalar(select(func.count()).select_from(t)) for t in reset.TABLES}
    finally:
        engine.dispose()


def test_reset_backup_and_preservation(sample):
    root, url = sample
    backup = reset.reset_demo(root, url, "data/checkpoints.sqlite", yes=True)
    assert all(value == 0 for value in counts(url).values())
    saved = json.loads((backup / "business-data.json").read_text(encoding="utf-8"))
    assert len(saved["orders"]) == 7 and len(saved["tickets"]) == 1
    assert (backup / "checkpoints.sqlite-wal").read_bytes() == b"checkpoint-fixture"
    assert not (root / "data/checkpoints.sqlite").exists()
    assert not (root / "data/checkpoints.sqlite-wal").exists()
    assert not (root / "data/checkpoints.sqlite-shm").exists()
    assert (root / ".env").read_text() == "keep-local-config"
    assert (root / "outputs/report.md").read_text() == "keep-report"


def test_reset_and_seed(sample):
    root, url = sample
    reset.reset_demo(root, url, "data/checkpoints.sqlite", yes=True, reseed=True)
    assert counts(url) == {"tickets": 0, "workflows": 0, "fulfillment": 2, "inventory": 3, "orders": 7}


def test_cancel_keeps_data(sample, monkeypatch):
    root, url = sample
    monkeypatch.setattr("builtins.input", lambda _: "cancel")
    assert reset.reset_demo(root, url, "data/checkpoints.sqlite") is None
    assert counts(url)["orders"] == 7
    assert (root / "data/checkpoints.sqlite").exists()
    assert not (root / "data/reset-backups").exists()


@pytest.mark.parametrize("url,checkpoint", [
    ("mysql+pymysql://course:dummy@remote.example:3307/ecommerce", "data/c.sqlite"),
    ("mysql+pymysql://course:dummy@127.0.0.1:3307/other", "data/c.sqlite"),
    ("mysql+pymysql://root:dummy@127.0.0.1:3307/ecommerce", "data/c.sqlite"),
    ("sqlite:///outside.sqlite", "data/c.sqlite"),
    ("sqlite:///:memory:", "data/c.sqlite"),
    ("sqlite:///data/business.sqlite", "../outside.sqlite"),
    ("sqlite:///data/business.sqlite", "data/business.sqlite"),
])
def test_refuses_wrong_targets(tmp_path, url, checkpoint):
    with pytest.raises(ValueError):
        reset.validate_target(tmp_path.resolve(), url, checkpoint)


def test_running_service_blocks_reset():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen()
        port = sock.getsockname()[1]
        with pytest.raises(ValueError, match="端口仍在运行"):
            reset.check_services(port, port)


def test_backup_failure_keeps_business_data(sample, monkeypatch):
    root, url = sample
    def fail(*args, **kwargs):
        raise OSError("simulated checkpoint backup failure")
    monkeypatch.setattr(reset.shutil, "copy2", fail)
    with pytest.raises(OSError):
        reset.reset_demo(root, url, "data/checkpoints.sqlite", yes=True)
    assert counts(url)["orders"] == 7 and counts(url)["tickets"] == 1


def test_mysql_target_matches_course(tmp_path):
    url, label, _ = reset.validate_target(tmp_path.resolve(),
        "mysql+pymysql://course:dummy@127.0.0.1:3307/ecommerce", "data/checkpoints.sqlite")
    assert url.database == "ecommerce" and "dummy" not in label
