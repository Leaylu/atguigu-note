"""本地 Streamable HTTP MCP 入口；复用现有六项工具，不加载 .env。"""
import argparse
import os
import secrets
import uvicorn
from starlette.responses import JSONResponse
from app.mcp_server import mcp


class AgentTokenMiddleware:
    """仅接受本地教学 Agent 令牌；不提供 OAuth 登录。"""

    def __init__(self, app, token: str):
        self.app = app
        self.token = token.encode("utf-8")

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            authorization = dict(scope["headers"]).get(b"authorization", b"")
            scheme, _, token = authorization.partition(b" ")
            if scheme.lower() != b"bearer" or not secrets.compare_digest(token, self.token):
                response = JSONResponse(
                    {"detail": "缺少有效 MCP Agent 令牌"},
                    status_code=401,
                    headers={"WWW-Authenticate": "Bearer"},
                )
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)


def create_http_app():
    token = os.getenv("AGENT_TOKEN", "")
    if not token or token.startswith("replace-"):
        raise RuntimeError("请在启动 MCP HTTP 服务的终端设置非占位 AGENT_TOKEN")
    mcp.settings.stateless_http = True
    mcp.settings.json_response = True
    app = mcp.streamable_http_app()
    app.add_middleware(AgentTokenMiddleware, token=token)
    return app


def main():
    parser = argparse.ArgumentParser(description="启动本机 MCP Streamable HTTP 服务")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("端口必须在 1—65535 范围内")
    uvicorn.run(create_http_app(), host="127.0.0.1", port=args.port, workers=1)


if __name__ == "__main__":
    main()
