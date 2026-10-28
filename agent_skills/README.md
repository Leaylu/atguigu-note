# 尚硅谷 企业级 Agent 应用与 Skills 开发实战

> 从 WorkBuddy、Codex 上手到企业项目落地：搞懂 Agent 与 Skills 的运行机制，把工作经验做成可复用的 Skill
>
> Codex 提供 OpenAI 与 DeepSeek 两条模型路线 | 技术篇 13 章 + 项目实战篇 7 章

## 在线视频（推荐）

🎬 [尚硅谷 · 最新 Skills 开发教程，Agent Skill 实战（WorkBuddy + Codex + DeepSeek Harness）](https://www.bilibili.com/video/BV14rxM6qEnL)

---

## 仓库结构

```text
agent_skills/
├── README.md                    # 本说明（含分 P 在线目录）
├── index.md                     # 站点入口
├── 课件/
│   ├── 00-课程大纲.md
│   ├── 技术篇/                   # 第 1 – 13 章
│   │   ├── 01-Vibe-Coding与Agent的工作方式.md
│   │   ├── ...
│   │   ├── 13-DeepSeek-Harness介绍与上手.md
│   │   ├── README.md             # 技术篇目录
│   │   ├── 案例与资料索引.md
│   │   └── 资料/                 # 各章输入数据与结果核对
│   └── 实战篇/                   # 第 0 – 7 章
│       ├── 00-依赖安装与项目启动.md
│       ├── ...
│       ├── 07-完成端到端业务任务.md
│       ├── README.md             # 实战篇目录
│       ├── 大纲.md
│       └── 资料/                 # 业务需求、验收场景、版本说明
└── 代码/
    └── ecommerce-agent/          # 电商订单异常排查助手（FastAPI + MySQL + LangGraph + MCP）
```

---

## 学习路线 & 资料对照

| 章节                                        | 课件                                                                   | 视频分 P    |
| ------------------------------------------- | ---------------------------------------------------------------------- | ----------- |
| 课程简介与大纲                              | [课程大纲](./课件/00-课程大纲.md)                                      | P1 – P2     |
| 技术篇 · 第 01 章 Vibe Coding 与 Agent 工作方式 | [课件](./课件/技术篇/01-Vibe-Coding与Agent的工作方式.md)          | P3 – P6     |
| 技术篇 · 第 02 章 WorkBuddy 上手与任务管理  | [课件](./课件/技术篇/02-WorkBuddy上手与任务管理.md)                    | P7 – P8     |
| 技术篇 · 第 03 章 WorkBuddy 办公工作流实战  | [课件](./课件/技术篇/03-WorkBuddy办公工作流实战.md)                    | P9          |
| 技术篇 · 第 04 章 Codex 上手与双模型接入    | [课件](./课件/技术篇/04-Codex上手、双模型接入与第一个应用.md)          | P10 – P11   |
| 技术篇 · 第 05 章 Codex 调试、迭代与交付    | [课件](./课件/技术篇/05-Codex调试、迭代与交付.md)                      | P12         |
| 技术篇 · 第 06 章 MCP 服务器介绍与接入      | [课件](./课件/技术篇/06-MCP服务器介绍与接入.md)                        | P13 – P14   |
| 技术篇 · 第 07 章 Skills 含义与运行机制     | [课件](./课件/技术篇/07-Skills的含义、作用与运行机制.md)               | P15 – P17   |
| 技术篇 · 第 08 章 查找、安装与使用现有 Skills | [课件](./课件/技术篇/08-查找、安装与使用现有Skills.md)               | P18         |
| 技术篇 · 第 09 章 从工作经验中设计 Skill    | [课件](./课件/技术篇/09-从工作经验中设计Skill.md)                      | P19         |
| 技术篇 · 第 10 章 手工制作第一个 Skill      | [课件](./课件/技术篇/10-手工制作第一个Skill.md)                        | P20         |
| 技术篇 · 第 11 章 Agent 辅助制作与改进      | [课件](./课件/技术篇/11-用Agent辅助制作与改进Skills.md)                | P21         |
| 技术篇 · 第 12 章 带资料、模板与脚本的 Skills | [课件](./课件/技术篇/12-制作带资料、模板与脚本的Skills.md)           | P22         |
| 技术篇 · 第 13 章 DeepSeek Harness          | [课件](./课件/技术篇/13-DeepSeek-Harness介绍与上手.md)                 | P23 – P24   |
| 实战篇 · 前置准备 依赖安装与项目启动        | [课件](./课件/实战篇/00-依赖安装与项目启动.md)                         | P25         |
| 实战篇 · 第 01 章 项目背景与架构            | [课件](./课件/实战篇/01-项目背景与架构.md)                             | P26         |
| 实战篇 · 第 02 章 认识已有电商系统          | [课件](./课件/实战篇/02-认识已有电商系统.md)                           | P27         |
| 实战篇 · 第 03 章 接入已有 Python 程序      | [课件](./课件/实战篇/03-接入已有Python程序.md)                         | P28         |
| 实战篇 · 第 04 章 接入 FastAPI 与 MySQL     | [课件](./课件/实战篇/04-接入FastAPI与MySQL.md)                         | P29         |
| 实战篇 · 第 05 章 制作企业业务 Skills       | [课件](./课件/实战篇/05-制作企业业务Skills.md)                         | P30         |
| 实战篇 · 第 06 章 接入 LangGraph 工作流     | [课件](./课件/实战篇/06-接入LangGraph工作流.md)                        | P31         |
| 实战篇 · 第 07 章 完成端到端业务任务        | [课件](./课件/实战篇/07-完成端到端业务任务.md)                         | P32         |

---

## 完整视频目录（点击即可跳转对应分 P）

> 链接格式：`https://www.bilibili.com/video/BV14rxM6qEnL?p=N`，打开后直接定位到第 N 集。

| P   | 标题                                         | 时长  | 在线观看                                                   |
| --- | -------------------------------------------- | ----- | ---------------------------------------------------------- |
| 1   | 01_企业级Agent与Skills实战_教程简介           | 06:39 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=1)  |
| 2   | 02_企业级Agent与Skills实战_内容大纲           | 07:25 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=2)  |
| 3   | 03_vibe coding和Agent的企业应用逻辑           | 15:29 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=3)  |
| 4   | 04_Agent与skills概念补全                      | 11:44 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=4)  |
| 5   | 05_Agent与提示词工程                          | 07:03 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=5)  |
| 6   | 06_Agent的实际使用案例                        | 09:27 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=6)  |
| 7   | 07_WorkBuddy的工作方式演示                    | 10:18 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=7)  |
| 8   | 08_WorkBuddy的完整使用展示                    | 32:15 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=8)  |
| 9   | 09_WorkBuddy的实战工作流演示                  | 15:14 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=9)  |
| 10  | 10_Codex两种使用路线演示                      | 12:20 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=10) |
| 11  | 11_Codex简单案例展示                          | 07:43 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=11) |
| 12  | 12_Codex调试和交付                            | 09:26 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=12) |
| 13  | 13_MCP服务介绍                                | 08:23 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=13) |
| 14  | 14_MCP实际使用演示                            | 11:25 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=14) |
| 15  | 15_Skills介绍                                 | 12:37 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=15) |
| 16  | 16_skills补充说明                             | 11:25 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=16) |
| 17  | 17_skills使用逻辑                             | 05:12 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=17) |
| 18  | 18_查找安装使用现有的skills                   | 11:28 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=18) |
| 19  | 19_从工作经验中设计skills                     | 10:23 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=19) |
| 20  | 20_手工制作skills                             | 06:48 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=20) |
| 21  | 21_agent辅助创建skills                        | 09:02 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=21) |
| 22  | 22_创建带有模板脚本和规则的skills             | 13:58 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=22) |
| 23  | 23_deepseekHarness基础使用演示                | 13:11 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=23) |
| 24  | 24_deepseekHarness简单案例演示                | 11:05 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=24) |
| 25  | 25_实战_项目准备                              | 16:49 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=25) |
| 26  | 26_实战_项目架构介绍                          | 08:07 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=26) |
| 27  | 27_实战_现有的电商系统介绍                    | 06:42 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=27) |
| 28  | 28_实战_Agent使用MCP接入python程序            | 17:06 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=28) |
| 29  | 29_实战_Agent接入FastAPI和MySQL               | 08:17 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=29) |
| 30  | 30_实战_设计企业应用的SKILLS                  | 06:51 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=30) |
| 31  | 31_实战_设计langgraph完成记录管理             | 09:19 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=31) |
| 32  | 32_实战_完成最终的端到端流程                  | 05:04 | [▶ 观看](https://www.bilibili.com/video/BV14rxM6qEnL?p=32) |

---

## 使用建议

1. **看视频**：按上表分 P 跳转，边看边在本地跟着操作。
2. **看课件**：技术篇先跑 Word / Excel / Python 小案例，再到 Skills 的制作与复用；实战篇先完成 `00-依赖安装与项目启动`。
3. **练代码**：`代码/ecommerce-agent/` 是实战篇的配套工程，启动说明见[工程 README](./代码/ecommerce-agent/README.md)。

---

## 版权说明

课程版权归 [尚硅谷](http://www.atguigu.com/) 所有。本仓库整理课件、资料与代码目录，仅供学习交流使用。
