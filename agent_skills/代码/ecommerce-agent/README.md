# 电商订单异常排查与处理助手

通过 Codex、Skills 和 MCP 复用 Python 校验程序、FastAPI 业务接口、MySQL 数据和 LangGraph 工作流。

首次使用先阅读[依赖安装与后端项目启动](../../课件/实战篇/00-依赖安装与项目启动.md)，完成工具安装、配置、数据库初始化和接口验证。

## 环境与目录

使用 Python 3.12、uv、Docker Desktop（MySQL 路线）。所有命令在本目录执行，Windows 示例使用 PowerShell。

| 文件 | 用途 |
| --- | --- |
| app/checker.py | 独立订单校验程序及 CLI |
| app/db.py、app/seed.py | 业务表和固定样本 |
| app/business.py | 超时筛选、分页、证据分析 |
| app/api.py | 身份权限与业务 HTTP 接口 |
| app/mcp_server.py | 六项MCP工具、业务API适配与错误映射 |
| app/mcp_http.py | 本机Streamable HTTP入口与连接令牌校验 |
| app/workflow.py | 持久化工作流、人工审批、创建工单 |
| app/approve.py | 人工审批命令行入口 |
| app/smoke_mcp.py | 真实 stdio 工具验证 |
| .agents/skills/ecommerce-order-investigation | 订单异常排查技能 |
| tests | 数据、权限、幂等、重启和协议验证 |

锁定依赖在 [uv.lock](uv.lock)：FastAPI 0.143.0、SQLAlchemy 2.0.54、PyMySQL 1.2.3、MCP Python SDK 1.30.0、LangGraph 1.2.14、SQLite checkpointer 3.1.1。MCP 使用官方 SDK 1.x 的 FastMCP API；不要把独立 `fastmcp` 包或 SDK 2.x 示例直接混入。

```powershell
python --version
uv --version
uv sync --frozen
```

`uv sync --frozen` 安装锁定依赖并创建 `.venv`。IDE 的 Python 解释器选择 `.venv/Scripts/python.exe`。

## 启动业务系统

### MySQL 路线

启动 Docker Desktop 后执行：

```powershell
docker compose up -d --wait
Copy-Item .env.example .env
```

编辑 `.env`，将两个 `replace-...` 值改成不同的本地演示令牌。数据库连接默认指向映射端口 3307；容器内部端口为 3306。Compose 中账号仅用于课程数据库。

```powershell
uv run --frozen python -m app.seed
uv run --frozen python -m uvicorn app.api:app --host 127.0.0.1 --port 8000 --workers 1
```

初始化建立业务表并插入 7 个订单、3 条库存和 2 条履约摘要。重复运行会拒绝覆盖已有订单；这是保护原数据的行为。浏览器打开 `http://127.0.0.1:8000/docs` 查看接口，`/health` 仅表示应用启动，不代表数据库查询一定成功。

### SQLite 本地路线

没有 MySQL 时可以先用同一套应用观察调用过程。在 `.env` 中把 `DATABASE_URL` 改为：

```dotenv
DATABASE_URL=sqlite:///data/business.sqlite
```

再执行相同的初始化与 API 启动命令。此路线用于本地调试；SQLite 检查不能替代 MySQL 驱动、事务、锁和部署验证。切换数据库时也要给 `CHECKPOINT_PATH` 换一个新文件名，避免旧工作流检查点关联新业务库。

## 简洁前端工作台

启动API后访问 http://127.0.0.1:8000/ 。页面由FastAPI直接提供，不需要Node.js或前端构建。

1. 输入.env中的AGENT_TOKEN，在“异常订单”查询固定日期，翻页并查看库存、履约证据。
2. 在“处理工作流”启动排查，保存工作流编号。请求编号用于幂等重试，新任务使用新编号。
3. 人工审批页使用单独的APPROVER_TOKEN，读取报告，批准或拒绝，并输入完整工作流编号确认。
4. 回到工作流页查询状态，再按审批结果继续；在“工单记录”刷新查看结果。

令牌只保留在当前页面内存，不写入浏览器存储；刷新页面需重新输入。审批令牌提交成功后清空。
页面不自动读取.env，不内置任何令牌。已有工作流可粘贴编号重新查询。
同机审批页面用于课程演示角色差异，企业部署需独立身份与审批入口。
核心文件为app/static/index.html、style.css、app.js；接口文档仍位于/docs。

## 先调用已有能力

另开 PowerShell，进入本目录：

```powershell
uv run --frozen python -m app.checker samples/orders.json
$env:AGENT_TOKEN = '填写与API端一致的Agent令牌'
$env:API_BASE_URL = 'http://127.0.0.1:8000'
$headers = @{ Authorization = "Bearer $env:AGENT_TOKEN" }
$query = 'paid_on=2026-10-10&as_of=2026-10-11T12%3A00%3A00%2B08%3A00&limit=2'
Invoke-RestMethod "$env:API_BASE_URL/orders?$query" -Headers $headers
```

校验输出 `valid=true`、`record_count=3`。查询输出 `total=3`，首批为 A1001、A1002，`next_offset=2`；继续读取第二页得到 A1003。

## Codex 接入：Streamable HTTP

保留前端/API进程，在新的工程终端单独启动MCP：

~~~powershell
$env:AGENT_TOKEN = '填写与API端一致的Agent令牌'
$env:API_BASE_URL = 'http://127.0.0.1:8000'
uv run --frozen python -m app.mcp_http
~~~

端点为 http://127.0.0.1:8001/mcp，仅监听本机。MCP不加载.env或审批令牌。
将[HTTP配置示例](examples/codex-mcp.toml)合并到Codex配置；同名节只留一份，
移除旧stdio节的command、args、cwd、env_vars，保留已有模型设置。

另开终端，在工程目录启动Codex：

~~~powershell
$env:AGENT_TOKEN = '填写与MCP服务端一致的Agent令牌'
codex mcp list
codex
~~~

Codex从AGENT_TOKEN读取Bearer令牌；API_BASE_URL只需在MCP服务终端设置。
通过/mcp确认连接及六项工具。IDE/桌面进程也需获得令牌环境变量后重启。
完整步骤见[第三章](../../课件/实战篇/03-接入已有Python程序.md)。

独立stdio测试入口仍为python -m app.mcp_server，备用配置为
[examples/codex-mcp-stdio.toml](examples/codex-mcp-stdio.toml)，无需同时配置两种连接。

发送：

```text
使用 ecommerce-order-investigation。
检查店铺 A 在 2026-10-10 支付的订单，以 2026-10-11T12:00:00+08:00
为判断基准，找出付款超过 24 小时仍未发货的订单。
查询完整分页并关联库存与履约证据，先输出报告，不创建工单。
```

OpenAI 与 DeepSeek 两条模型路线沿用技术篇配置；业务 API 不接收模型密钥。切换模型后分别检查 Skill 触发、工具参数、分页和审批行为，不能只检查文字是否流畅。

## 人工审批与恢复

需要工单时，让 Codex 调用 `ecommerce_start_workflow`，传入同一日期、基准时间和唯一 `request_id`，例如 `order-demo-001`。返回 `workflow_id` 后状态应为 `awaiting_approval`，工单为空。

审批人使用独立终端，进入本目录并运行以下命令，把示例编号替换成返回的编号：

```powershell
uv run --frozen python -m app.approve WORKFLOW_ID --decision approve
```

按提示隐藏输入审批令牌，阅读打印的报告，再输入工作流编号确认。拒绝时使用 `--decision reject`。工具不会代替人输入确认，也不会立即创建工单。

回到 Codex 说明该工作流已审批，让它先查询状态，再调用 `ecommerce_resume_workflow`。批准后首次结果应为 `completed`，创建 `TK-A1001`、`TK-A1002`、`TK-A1003`。拒绝后为 `rejected`，不创建工单。

本地 `.env` 便于学习角色划分，但同一操作系统账号可读取的文件不构成安全隔离。企业部署时，API 的数据库和审批凭据放在远端服务环境；审批人通过独立身份入口操作，Codex 的文件权限和凭据范围不能覆盖审批服务。

## 验证

```powershell
uv run --frozen pytest -q
uv run --frozen python -m app.smoke_mcp
uv run --frozen python -m app.smoke_mcp --with-api
```

前两条不需要先启动正式业务 API。测试使用临时 SQLite 数据；真实进程测试会启动并停止一个临时端口上的 API。第三条需要已初始化的 API 和 Agent 环境变量，检查 API 查询及越权拒绝。

新增HTTP传输测试可单独运行：

~~~powershell
uv run --frozen python -m pytest tests/test_mcp_http.py -q
~~~

测试自行启动临时API/MCP服务并使用隔离SQLite，无需手动启动8000或8001端口，不调用真实模型。

## 状态与运行边界

- 业务数据由 MySQL 保存，课程工作流检查点由 `CHECKPOINT_PATH` 指定的 SQLite 文件保存。重启须保留两者，并继续使用原 workflow_id。
- 使用单 API 进程 `--workers 1`。进程内锁不能替代多实例分布式锁。
- 示例是店铺 A 单 Agent 身份；没有企业 SSO、逐员工身份、多租户、审批有效期或完整审计平台。
- 查询的订单状态和库存均为读取时数据；固定 as_of 仅用于判断超时，不提供任意历史时点的数据回放。
- workflow_id 绑定报告和审批；request_id 防止重复启动；订单唯一工单约束防止重复创建。跨库事务不是原子事务，恢复时通过已有工单复用避免重复写入。
- 教学工作流同步执行，最多 100 单。实际批量任务应采用后台任务、状态轮询和受控分批。
- `completed` 表示已完成工单处理流程，不能理解为订单已经发货。

[项目学习目录](../../课件/实战篇/README.md)

## 重新录制：一键清空或重建演示数据

先在API和MCP终端按Ctrl+C停止服务。在工程根目录执行：

~~~powershell
uv run --frozen python -m app.reset_demo --yes
~~~

也可双击工程中的reset-demo.cmd，查看目标与记录数量，输入DELETE确认清空。

脚本清空tickets、workflows、fulfillment、inventory、orders，保留表结构；
同时删除CHECKPOINT_PATH指向的检查点及其-wal、-shm文件。
.env、虚拟环境、outputs报告与MySQL容器保留。
删除前会在data/reset-backups中备份业务JSON和已有检查点文件。

清空后重新初始化：

~~~powershell
uv run --frozen python -m app.seed
~~~

若希望清空后直接恢复到7单初始样例，一条命令即可：

~~~powershell
uv run --frozen python -m app.reset_demo --yes --seed
~~~

仅支持本机course账号的ecommerce MySQL库，或本工程data内的SQLite文件。
脚本检查8000和8001端口；若服务使用其他端口，传入--api-port和--mcp-port指定实际端口。
.env加载保留已有环境变量优先级，运行前应核对终端打印的实际数据库目标。
备份JSON保留用于核对，未提供自动恢复功能。重置后旧workflow_id及工单失效，
outputs中的旧报告仅为历史记录；重新启动API/MCP后可从头演示。
