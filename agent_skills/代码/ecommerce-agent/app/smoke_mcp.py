"""独立 MCP 客户端，启动真实 stdio 子进程；可选调用运行中的 API。"""
import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def run(with_api):
    env = {key: value for key, value in os.environ.items() if key != "APPROVER_TOKEN"}
    params = StdioServerParameters(command=sys.executable, args=["-m", "app.mcp_server"], env=env,
                                   cwd=str(Path(__file__).resolve().parents[1]))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listing = await session.list_tools()
            assert len(listing.tools) == 6
            records = json.loads(Path("samples/orders.json").read_text())
            result = await session.call_tool("ecommerce_check_orders", {"records": records})
            assert not result.isError and result.structuredContent["valid"]
            invalid = await session.call_tool("ecommerce_list_orders", {
                "paid_on": "2026-10-10", "as_of": "2026-10-11T12:00:00+08:00", "limit": 101})
            assert invalid.isError
            if with_api:
                result = await session.call_tool("ecommerce_list_orders", {
                    "paid_on": "2026-10-10", "as_of": "2026-10-11T12:00:00+08:00", "limit": 2})
                assert not result.isError, result
                assert result.structuredContent["total"] == 3
                assert result.structuredContent["next_offset"] == 2
                denied = await session.call_tool("ecommerce_order_evidence", {"order_id": "B1001"})
                assert denied.isError
            print("MCP stdio 验证通过：6 项工具、结构化结果、参数拒绝" + ("、API 查询和越权拒绝" if with_api else ""))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-api", action="store_true")
    asyncio.run(run(parser.parse_args().with_api))
