"""清空课程业务数据和工作流检查点；只用于本机演示环境。"""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import socket
from uuid import uuid4

from dotenv import load_dotenv
from sqlalchemy import inspect, select, func
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from app.db import make_engine, tickets, workflows, fulfillment, inventory, orders

TABLES = (tickets, workflows, fulfillment, inventory, orders)


def project_file(root: Path, value: str) -> Path:
    raw = Path(value)
    path = raw if raw.is_absolute() else root / raw
    target = path.resolve()
    data = (root / "data").resolve()
    if not data.is_relative_to(root) or not target.is_relative_to(data) or target == data or path.is_symlink():
        raise ValueError("数据库和检查点文件必须位于本工程data目录内，且不能是符号链接")
    return target


def validate_target(root, database_url, checkpoint_path):
    url = make_url(database_url)
    if url.get_backend_name() == "mysql":
        if (url.drivername != "mysql+pymysql" or
                url.host not in ("127.0.0.1", "localhost") or
                url.database != "ecommerce" or url.username != "course"):
            raise ValueError("仅允许本机course账号连接的ecommerce课程MySQL数据库")
        label = f"MySQL {url.host}:{url.port or 3306}/{url.database}"
        business_path = None
    elif url.get_backend_name() == "sqlite":
        if not url.database or url.database == ":memory:":
            raise ValueError("SQLite必须使用本工程data目录内的文件")
        business_path = project_file(root, url.database)
        url = url.set(database=str(business_path))
        label = f"SQLite {business_path}"
    else:
        raise ValueError("仅支持课程MySQL或SQLite配置")
    checkpoint = project_file(root, checkpoint_path)
    files = [checkpoint, Path(str(checkpoint) + "-wal"), Path(str(checkpoint) + "-shm")]
    for path in files:
        if path.is_symlink() or not path.resolve().is_relative_to((root / "data").resolve()):
            raise ValueError("检查点文件路径不在课程data目录内")
        if path.exists() and not path.is_file():
            raise ValueError("检查点目标必须是文件")
    if business_path is not None and business_path in files:
        raise ValueError("业务数据库文件不能与检查点文件相同")
    return url, label, files


def check_services(api_port, mcp_port):
    for port in {api_port, mcp_port}:
        if not 1 <= port <= 65535:
            raise ValueError("检查端口必须在1—65535范围内")
        with socket.socket() as sock:
            sock.settimeout(0.3)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                raise ValueError(f"本机{port}端口仍在运行，请先停止API/MCP服务再清空")


def reset_demo(root, database_url, checkpoint_path, *, yes=False, reseed=False,
               api_port=8000, mcp_port=8001):
    root = Path(root).resolve()
    url, label, checkpoint_files = validate_target(root, database_url, checkpoint_path)
    check_services(api_port, mcp_port)
    # 只允许删除配置指向的检查点文件，不递归删除整个data目录。
    (root / "data").mkdir(exist_ok=True)
    engine = make_engine(url.render_as_string(hide_password=False))
    try:
        present = set(inspect(engine).get_table_names())
        tables = [table for table in TABLES if table.name in present]
        with engine.connect() as conn:
            counts = {t.name: conn.scalar(select(func.count()).select_from(t)) for t in tables}
        print("清空目标：", label)
        print("现有记录：", json.dumps(counts, ensure_ascii=False))
        print("检查点：", checkpoint_files[0])
        print("将清空订单、库存、履约、工作流与工单；保留.env、outputs和表结构。")
        if not yes and input("输入 DELETE 确认；其他输入取消：").strip() != "DELETE":
            print("已取消，数据未删除。")
            return None
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid4().hex[:8]
        backup = root / "data" / "reset-backups" / stamp
        backup.mkdir(parents=True, exist_ok=False)
        # 先备份，备份失败时不执行DELETE。
        for path in checkpoint_files:
            if path.exists():
                shutil.copy2(path, backup / path.name)
        with engine.begin() as conn:
            snapshot = {t.name: [dict(row) for row in conn.execute(select(t)).mappings()]
                        for t in tables}
            with (backup / "business-data.json").open("x", encoding="utf-8") as stream:
                json.dump(snapshot, stream, ensure_ascii=False, indent=2, default=str)
                stream.write("\n")
            for table in tables:
                conn.execute(table.delete())
        print("业务表已清空，备份：", backup)
        try:
            for path in checkpoint_files:
                path.unlink(missing_ok=True)
        except OSError as exc:
            raise RuntimeError("业务表已清空，但检查点清理失败；请停止占用进程后重试，备份已保留") from exc
        if reseed:
            from app.seed import seed
            seed(engine)
            print("教学数据已重建：7个订单、3条库存、2条履约记录。")
        else:
            print("清空完成。重新演示前执行：uv run --frozen python -m app.seed")
        return backup
    finally:
        engine.dispose()


def main(argv=None):
    parser = argparse.ArgumentParser(description="清空本机课程演示数据，保留.env和输出报告")
    parser.add_argument("--yes", action="store_true", help="跳过DELETE输入确认")
    parser.add_argument("--seed", action="store_true", help="清空后立即重新生成教学数据")
    parser.add_argument("--api-port", type=int, default=8000, help="检查API是否停止")
    parser.add_argument("--mcp-port", type=int, default=8001, help="检查MCP是否停止")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    load_dotenv(root / ".env")
    url = os.getenv("DATABASE_URL")
    if not url:
        print("缺少DATABASE_URL，请先配置工程.env。")
        return 2
    try:
        reset_demo(root, url, os.getenv("CHECKPOINT_PATH", "data/checkpoints.sqlite"),
                   yes=args.yes, reseed=args.seed, api_port=args.api_port,
                   mcp_port=args.mcp_port)
        return 0
    except (ValueError, RuntimeError, OSError, SQLAlchemyError, EOFError) as exc:
        if isinstance(exc, SQLAlchemyError):
            print("数据库操作失败；请检查连接、权限和表结构。若已开始重置，请核对终端记录和备份。")
        else:
            print("处理停止：", str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
