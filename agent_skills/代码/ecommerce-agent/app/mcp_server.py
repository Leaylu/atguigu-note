"""stdio 与 HTTP 共用的 MCP 工具定义。只读取 Agent 凭据，不加载 .env。"""
import os
from typing import Annotated, Any
from urllib.parse import quote
import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from app.checker import check_orders

mcp = FastMCP("ecommerce_mcp")
READ = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True}
WRITE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True}
ShortText = Annotated[str, Field(min_length=1, max_length=80)]


async def request(method: str, path: str, **kwargs) -> dict[str, Any]:
    token = os.getenv("AGENT_TOKEN")
    if not token:
        raise RuntimeError("缺少 AGENT_TOKEN，请在 MCP 服务进程环境中配置 Agent 令牌")
    url = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=10, trust_env=False) as client:
            response = await client.request(method, url + path,
                headers={"Authorization": f"Bearer {token}"}, **kwargs)
        if response.is_error:
            # 不回传代理页、内部堆栈或凭据；只转发本服务的业务 detail。
            detail = "服务调用失败，请检查 API 日志"
            if response.status_code < 500:
                try:
                    detail = response.json().get("detail", detail)
                except ValueError:
                    pass
            raise RuntimeError(f"业务 API HTTP {response.status_code}: {detail}")
        return response.json()
    except httpx.TimeoutException as error:
        raise RuntimeError("业务 API 超时；写操作请使用同一 request_id 查询或重试，不能断言未执行") from error
    except httpx.RequestError as error:
        raise RuntimeError("无法连接业务 API，请检查 API_BASE_URL 与服务状态") from error


@mcp.tool(annotations={**READ, "openWorldHint": False})
def ecommerce_check_orders(records: Annotated[list[dict], Field(max_length=1000)]) -> dict[str, Any]:
    """校验最多1000条订单基础字段；返回 valid、record_count、error_count、issues。数据错误不等于执行失败。"""
    return check_orders(records)


@mcp.tool(annotations=READ)
async def ecommerce_list_orders(paid_on: ShortText, as_of: ShortText,
    offset: Annotated[int, Field(ge=0)] = 0,
    limit: Annotated[int, Field(ge=1, le=100)] = 20) -> dict[str, Any]:
    """分页查询授权店铺已付款且超过24小时未发货的订单。paid_on按上海日期，as_of须带时区；返回total/items/next_offset，须读取全部页。"""
    return await request("GET", "/orders", params=dict(paid_on=paid_on, as_of=as_of, offset=offset, limit=limit))


@mcp.tool(annotations=READ)
async def ecommerce_order_evidence(order_id: ShortText) -> dict[str, Any]:
    """获取授权订单的order、inventory、fulfillment、analysis。库存为当前快照，possible_reason不等于已证实历史根因。"""
    return await request("GET", f"/orders/{quote(order_id, safe='')}/evidence")


@mcp.tool(annotations=WRITE)
async def ecommerce_start_workflow(paid_on: ShortText, as_of: ShortText, request_id: ShortText) -> dict[str, Any]:
    """启动订单异常排查并暂停待审批，返回workflow_id/status/report/tickets；request_id重试须保持不变。最多100单。不会自动批准。"""
    return await request("POST", "/workflows", json=dict(paid_on=paid_on, as_of=as_of, request_id=request_id))


@mcp.tool(annotations=READ)
async def ecommerce_workflow_status(workflow_id: ShortText) -> dict[str, Any]:
    """查询持久化工作流状态、报告、审批决策与工单结果，不推进执行。"""
    return await request("GET", f"/workflows/{quote(workflow_id, safe='')}")


@mcp.tool(annotations=WRITE)
async def ecommerce_resume_workflow(workflow_id: ShortText) -> dict[str, Any]:
    """仅按服务端已有人工审批记录恢复工作流；无审批返回409。批准后创建工单，拒绝后结束；重复恢复不重复建单。"""
    return await request("POST", f"/workflows/{quote(workflow_id, safe='')}/resume")


if __name__ == "__main__":
    mcp.run(transport="stdio")
