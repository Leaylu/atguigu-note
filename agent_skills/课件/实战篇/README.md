# 项目实战篇

以“电商订单异常排查与处理助手”为场景，学习通过 MCP 与 Skills 将已有 Python、FastAPI、MySQL 和 LangGraph 系统接入 Codex。

[项目背景、架构与七章大纲](大纲.md) · [配套工程与启动说明](../../代码/ecommerce-agent/README.md)

## 学习顺序

开始项目操作前，先完成[前置准备：依赖安装与后端项目启动](00-依赖安装与项目启动.md)，确认后端及固定数据可以独立查询。

1. [第一章：项目背景与架构](01-项目背景与架构.md)
2. [第二章：认识已有电商系统](02-认识已有电商系统.md)
3. [第三章：接入已有 Python 程序](03-接入已有Python程序.md)
4. [第四章：接入 FastAPI 与 MySQL](04-接入FastAPI与MySQL.md)
5. [第五章：制作企业业务 Skills](05-制作企业业务Skills.md)
6. [第六章：接入 LangGraph 工作流](06-接入LangGraph工作流.md)
7. [第七章：完成端到端业务任务](07-完成端到端业务任务.md)

第00篇完成环境准备与启动，第二章通过前端认识订单、证据、业务表和接口，第三、四章接入程序和数据，第五章制作业务 Skill，第六章接入持久化流程，第七章串联完整任务并整理结果报告。每章给出调用方式、预期结果和对应源码。

## 前端工作台

启动后访问 http://127.0.0.1:8000/，查看异常订单、库存与履约证据、工作流和工单；人工审批使用单独令牌。页面与API同源，不需要前端构建。操作见[工程说明](../../代码/ecommerce-agent/README.md)。

## 配套资料

- [业务需求与数据口径](资料/业务需求与数据口径.md)
- [验收场景与预期结果](资料/验收场景与预期结果.md)
- [官方资料与版本说明](资料/官方资料与版本说明.md)
- [订单异常排查 Skill](../../代码/ecommerce-agent/.agents/skills/ecommerce-order-investigation/SKILL.md)
- [Codex MCP 配置示例](../../代码/ecommerce-agent/examples/codex-mcp.toml)
- [只读工具评测样例](../../代码/ecommerce-agent/examples/evaluation.xml)

主案例使用固定日期和虚构订单，数据库支持 MySQL 路线与本地 SQLite 路线。业务结果可以继续交给 WorkBuddy 整理为 Word 与 Excel。真实公司接入时，以既有业务接口替换示例接口，并保留服务端权限和审批边界。

[技术篇目录](../技术篇/README.md) · [课程总纲](../00-课程大纲.md)
