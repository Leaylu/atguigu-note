# 第 13 章：DeepSeek Harness 介绍与上手

DeepSeek Harness 既是可以直接处理任务的 Agent 软件，也是允许开发者组合、扩展运行能力的开源项目。本章从使用者的角度开始，再理解它如何组织模型、工具、Skills 和插件。

案例是“生成电商服务巡检日报”：读取本地巡检快照，运行计算脚本，加载技能，生成报告，并查看任务实际执行过程。全部材料独立提供，无需启动企业业务系统。

## 13.1 Harness 到底是什么

### 模型负责推理，运行环境负责执行

模型可以提出“读取文件、运行脚本、生成报告”的操作，但实际打开哪个目录、怎样启动进程、如何收回结果、什么时候暂停等待权限，都需要运行环境协调。

这里的 Harness 可以理解为围绕模型构建的 Agent 运行框架：

~~~text
用户提出任务
    ↓
Harness 组织上下文、技能说明和可用工具
    ↓
模型判断下一步操作
    ↓
Harness 调用工具并记录结果
    ↓
模型根据结果继续判断
    ↓
完成文件与答复，或等待输入
~~~

假设用户说“生成巡检日报”：模型决定需要哪些数据；文件工具读取快照；Python 程序计算数量；模型组织报告；文件工具保存 Markdown。这些动作形成循环，并不是模型一次回答就完成全部工作。

### DeepSeek Harness 是具体产品

DeepSeek 官方项目命令名为 dsh，采用基于 Cordis 的插件架构，仍处于预览阶段。它可以直接使用，也可以用于开发扩展。[官方仓库](https://github.com/deepseek-ai/deepseek-harness)

| 概念 | 在本例中做什么 |
| --- | --- |
| 模型 | 理解日报需求，选择操作，解释输出 |
| Harness | 组织会话、工具执行和过程记录 |
| 工具 | 读取文件、执行命令、写入成果 |
| Skill | 规定巡检分类和报告流程 |
| 插件 | 为运行环境提供或扩展能力 |
| MCP | 将外部服务提供的工具接入运行环境 |

“DeepSeek 模型”和“DeepSeek Harness”不是同一个配置项。模型更换后，工作区、脚本和输入并不会因此自动改变。

### 与 Codex 接入 DeepSeek 的关系

第四章在 Codex 中配置 DeepSeek，是让 Codex 调用该模型服务。本章改用 DeepSeek Harness 组织任务；即使模型提供方相同，界面、工具与运行记录也会不同。

例如，两边调用同一脚本都得到8条巡检记录，只能证明这次脚本计算一致，不能据此判定两种产品在所有任务中的表现相同。

## 13.2 选择入口：桌面端、Web 与源码

### 路线一：桌面端

打开[官方下载页](https://www.deepseek.com/harness/)，选择与电脑匹配的安装包。官方提供 Windows 64位和 macOS Apple 芯片下载入口。本章以 Windows 为例。

安装后打开应用，再完成模型配置和工作区选择。桌面版有自己的运行时；不需要为了打开桌面应用，先执行 Web 启动命令。

桌面版关闭主窗口可能只是隐藏到托盘，任务仍可继续；需要结束应用时，使用退出入口。是否仍在后台运行应以应用状态为准。[桌面说明](https://github.com/deepseek-ai/deepseek-harness/blob/master/apps/desktop/README.md)

### 路线二：通过 Node.js 启动 Web

先检查环境：

~~~powershell
node --version
npm --version
~~~

当前官方CLI包要求 Node.js >=24.9.0，安装时应核对所选发布版本的要求；源码主分支与已发布安装包可能不同。[CLI环境要求](https://github.com/deepseek-ai/deepseek-harness/blob/master/apps/cli/package.json)

将本章“演示项目”复制到独立位置，在该目录打开 PowerShell：

~~~powershell
npx @deepseek-ai/dsh web
~~~

首次执行可能需要下载软件，终端默认打印 http://127.0.0.1:3080。以实际输出地址为准，保留启动进程所在终端。只启动服务、不自动打开浏览器时使用：

~~~powershell
npx @deepseek-ai/dsh web --no-open
~~~

npx 下载和启动的是 Harness；随后调用模型是另一环节。能打开本地网页，尚不能说明 API Key 有效。启动方式见[官方说明](https://github.com/deepseek-ai/deepseek-harness)。

PowerShell 如果因脚本执行策略拒绝 npm.ps1 或 npx.ps1，可以在已安装 Node 的前提下使用 npm.cmd、npx.cmd 对应命令，不必为此调整整台电脑的执行策略。

### 路线三：运行源码

希望研究框架或开发插件时，可以按官方流程运行源码：

~~~powershell
git clone https://github.com/deepseek-ai/deepseek-harness.git
cd deepseek-harness
pnpm install
pnpm run build
pnpm dsh web
~~~

需要先按仓库要求准备 Node 和 pnpm。源码目录用于开发框架，本章业务演示目录用于存放巡检输入，不要混为一个工作区。

三条路线选择一条即可完成本章案例。初次使用优先桌面端；需要观察启动日志时可选 Web。

## 13.3 配置模型，确认一次真实调用

### 配置 DeepSeek

在设置的模型区域找到 DeepSeek，填写开放平台 API Key 并保存。模型列表中选择本账号可用的模型；具体名称以当前服务返回与客户端显示为准。配置细节见[模型指南](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/providers.md)。

本章使用 API Key 路线。网页聊天账号与 API 调用凭据的用途不同，不把聊天密码填入密钥框，也不把真实密钥写进课程项目。

保存设置后，创建会话并提出一个简单问题；再执行读取本地文件的请求，逐层确认：

| 检查 | 能说明什么 |
| --- | --- |
| 模型可以回答 | 当前模型请求能成功 |
| 实际读取工作区文件 | 文件工具及目录选择可用 |
| 实际运行Python | 本地程序执行环境可用 |
| 结果文件真实存在 | 文件写入已完成 |

### 企业网关怎样配置

使用公司统一网关时，官方提供自定义模型API入口，需要明确 Provider ID、Base URL、协议、凭据和模型ID。支持的协议包括 OpenAI Chat Completions、OpenAI Responses、Anthropic Messages；应选择网关真实实现的协议。[自定义提供方配置](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/providers.md)

这些字段的含义是：
- Provider ID：客户端内部区分服务的标识。
- Base URL：请求送往哪里。
- 协议：双方使用哪种请求和响应结构。
- 模型ID：请求哪个模型。
- 凭据：服务怎样识别调用者。

模型名字相同，不代表不同协议可以互换。企业网关返回401时先检查认证，返回找不到接口时先检查地址与协议，不要盲目修改业务脚本。

## 13.4 工作区、会话与执行权限

### 工作区决定文件范围

将[本章演示项目](资料/第13章/演示项目/任务说明.md)所在的整个目录复制出来，在 Harness 中选择这个目录为工作区。Web 首次启动后仍需点击“选择工作区”添加并选中目录。[Web指南](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/index.zh.md)

本例结构如下：

~~~text
演示项目/
├── 任务说明.md
├── 输入资料/
│   ├── 巡检快照.json
│   └── 异常输入.json
└── .dsh/
    └── skills/
        └── service-check-report/
            ├── SKILL.md
            ├── references/巡检口径.md
            ├── assets/巡检日报模板.md
            └── scripts/summarize_checks.py
~~~

复制时包含隐藏目录 .dsh。目录树没有展示输出，因为输出会在任务执行时创建。

### 会话保留任务上下文

同一会话中继续说“增加核查顺序”，可以承接刚生成的日报。新会话应明确输入与输出，不能假设模型知道上一个会话里选了哪份文件。

工作区相同不意味着每个会话都有相同历史；会话相同也不意味着此前文件仍未被外部修改，涉及具体数字时仍需读取实际结果。

### 权限影响可执行操作

本例需要读取输入、运行本地脚本和在工作区写新文件。只读权限下可能无法创建结果目录；出现审批时，查看实际命令、目标路径和用途，再决定是否允许。

工作区写入许可也不代表已经授权真实采购、接口重放或对外通知。本例的任务范围始终是离线快照分析。

## 13.5 理解插件、Profile 和 Agent 模式

### “一切皆插件”不是“所有文件都是技能”

DeepSeek Harness 用 Cordis 组织插件。模型适配、工具、会话记录和Agent循环等都可以作为可组合部分；Profile 保存一组运行配置，Bundle 打包一组插件配置与代码。[架构说明](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md)

可以用本例区分：
- 巡检技能告诉 Agent 如何生成日报。
- Python 脚本执行固定分类。
- MCP插件可连接公司巡检服务。
- 界面插件可增加日报预览入口。
- Profile 决定当前应用装配哪些能力。

前两项属于业务方法与计算，后几项涉及运行环境。新增一种日报格式，通常不需要先开发 Harness 插件。

### Profile 与 Agent模式

官方CLI提供 web、headless、sdk、sdk-minimal、acp 等入口，分别面向界面、一次性任务或程序连接。Profile是应用启动时的能力组合；Agent preset 则定义会话中Agent使用的插件组合，两者不是同一个层级。[CLI说明](https://github.com/deepseek-ai/deepseek-harness/blob/master/apps/cli/README.md)

本章先选标准模式完成业务任务。创造模式用于扩展运行环境及插件；官方提供相关插件开发技能。[模式定义](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/preset/agent-preset/README.md)

PTC可以用程序组织工具调用；相关工作流能力还可组织分步或并行执行。这不同于“运行一个独立Python脚本”：后者只是一次工具执行，不足以说明使用了PTC。[PTC工作流说明](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/workflow/workflow-ptc/README.md)

不要为了一个小型巡检日报同时开启所有模式。先让输入、计算和输出完整闭合，再判断是否需要更复杂的编排。

### 插件页面看什么

插件管理页面用于查看、启用或安装能力。应区分“包已安装”“配置已启用”和“运行时成功加载”。插件修改可能影响同一Profile的多个会话，不只是当前对话。[插件管理说明](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/boot/plugin-manager/README.md)

遇到功能缺失时，先看相关插件是否可用、是否报加载错误。安装第三方插件会引入可执行代码，不应只根据插件名称判断它的能力和范围。

## 13.6 第一段演示：读文件并调用现成脚本

### 先确认工作区

~~~text
请读取任务说明.md，说明这次需要分析什么数据、生成什么成果。
检查本机可用的Python 3命令。
先不要修改文件，也不要访问真实业务接口。
~~~

界面中的回复应对应“电商服务巡检”，而不是其他目录的项目。Node用于Web入口；Python用于案例脚本，职责不同。

### 看懂8条快照

输入包含记录ID、服务名称、接口路径、HTTP状态码和耗时。它是离线教学快照，接口路径只是文本，不需要发送HTTP请求。

本例分类顺序：

| 条件 | 分类 |
| --- | --- |
| 状态码不是2xx | 失败 |
| 状态码为2xx且耗时>=1000ms | 慢响应 |
| 状态码为2xx且耗时<1000ms | 正常 |

三类互斥：503且2200ms只算失败；200且1000ms算慢响应。阈值是案例约定，不是所有企业统一标准。

### 让 Harness 执行程序

~~~text
请运行 .dsh/skills/service-check-report/scripts/summarize_checks.py，
输入为 输入资料/巡检快照.json，输出到新的“脚本演示-01”。
读取实际JSON结果，解释正常、慢响应和失败各有多少。
保留源文件，不推测异常根因。
~~~

实际命令应等价于：

~~~powershell
py .dsh/skills/service-check-report/scripts/summarize_checks.py --input "输入资料/巡检快照.json" --output-dir "脚本演示-01"
~~~

预期生成 巡检汇总.json：总数8、正常4、慢响应2、失败2。异常为库存与搜索慢响应、支付与物流失败。

这段演示明确指定程序，重点验证工具执行，还未证明技能已被加载。

## 13.7 第二段演示：让 Harness 加载 Skill

### 技能放在哪里

官方本地技能提供方支持项目下 .dsh/skills 和 .agents/skills 等目录。同层本地来源冲突时，项目 .dsh 的优先级高于项目 .agents。目录技能采用“技能名/SKILL.md”，不会无限递归搜索任意深度的文件。[Skills机制](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/skills.md)

本章包已放在 .dsh/skills/service-check-report。项目根定位会考虑最近的.git祖先；为避免教学目录嵌套在其他仓库下导致根目录变化，复制到独立目录并选择它作为工作区。

### 显式使用

新建会话，使用界面提供的技能选择入口，或清楚写出技能名称：

~~~text
请使用 service-check-report 技能处理 输入资料/巡检快照.json，
输出到新的“技能演示-01”，生成计算JSON和Markdown日报。
确认加载技能，再按技能中的脚本和模板完成。
~~~

应能观察到技能加载、读规则、执行脚本、读取计算结果、按模板写日报的过程。官方模型侧技能工具为 skill，可按名称加载正文；资源按需要读取。[技能加载过程](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/skills.md)

如果只看到普通文件读取，并未发生技能加载，应描述为“按文件说明执行”，不把它说成原生技能发现成功。

### 再用自然需求调用

在另一个新会话中输入：

~~~text
请把 输入资料/巡检快照.json 整理成电商服务巡检日报，
包含异常明细和建议核查方向，保存到新的“日报-02”目录。
保留源文件，不提交工单。
~~~

这次不写技能名称，可以观察描述能否帮助模型选择它。未触发时，先检查技能是否可见、工作区是否正确、名称和描述是否符合格式，再考虑修改描述。

最终目录应同时包含 巡检汇总.json 和 巡检日报.md。数字来自脚本，说明来自Agent对规则和结果的理解。

## 13.8 从运行过程定位问题

把任务过程分成四层：

| 层面 | 具体核对 |
| --- | --- |
| 模型请求 | 选中的提供方和模型是否可用 |
| 工具调用 | 参数、路径、命令和退出状态是否正确 |
| 数据计算 | 8条是否被正确分成4、2、2 |
| 报告交付 | 是否有实际文件、异常明细和依据 |

官方提供运行轨迹视图，便于查看调用与结果。[运行轨迹介绍](https://www.deepseek.com/harness/)

### 失败记录不等于脚本失败

本例有2条业务失败记录，但JSON结构有效、汇总成功，因此脚本退出0。异常输入.json 包含负耗时，违反输入契约，脚本才退出2。不要把业务状态和程序退出码混在一起。

### 结果更新要有依据

在同一会话继续：

~~~text
根据刚才实际生成的JSON，在日报增加“优先核查顺序”。
先列失败，再列慢响应；只写核查建议，不假定故障已修复。
保持数字不变，不访问真实业务接口。
~~~

核对报告是否列出支付、物流、库存和搜索的观测事实。比如503只能说明该条检查返回该状态，不能直接写“支付渠道故障已经确认”。

最后打开实际文件。聊天里出现报告文本，不一定表示文件已保存。

## 13.9 MCP：把本地快照换成业务工具

本例的输入来自JSON。如果企业已经有巡检API，可由MCP服务器暴露“查询巡检结果”等工具，再让Harness调用。

~~~text
Harness → MCP客户端插件 → 企业MCP服务器 → 巡检API
        ← 工具结果       ← 业务数据
~~~

Harness支持stdio与Streamable HTTP连接；需要显式配置服务器，不会自动接入公司的系统。[MCP说明](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/mcp.md)

例如已有本地测试MCP服务运行在127.0.0.1:8001/mcp，可准备如下覆盖文件。这里是连接配置示例，本章没有启动该服务：

~~~yaml
- insert:
    - id: mcp-ecommerce-checks
      name: '@deepseek-ai/dsh-mcp-client'
      config:
        serverName: ecommerce-checks
        transport: streamable-http
        url: http://127.0.0.1:8001/mcp
~~~

将其保存为 mcp-checks.cordis.yml 后，Web方式可使用：

~~~powershell
npx @deepseek-ai/dsh web --patch "./mcp-checks.cordis.yml"
~~~

insert表示新增插件配置，serverName用于区分工具来源，url必须是实际MCP端点，普通REST地址不能直接替代。覆盖文件的用法见[官方接入指南](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/mcp-memory.md)，字段见[MCP客户端](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/mcp/mcp-client/README.md)。

配置保存不等于连接成功。检查服务器工具是否出现、实际调用是否返回，以及认证是否满足企业服务要求。不要将覆盖文件整段替换已有配置，以免丢失其他设置。

技能仍可以负责“怎样解释巡检结果”，MCP负责“怎样获取结果”；两者可以配合。

## 13.10 常见问题与处理顺序

| 现象 | 优先检查 |
| --- | --- |
| 桌面应用打开但任务不执行 | 模型配置、账号可用条件、会话错误 |
| npx启动失败 | Node版本、包下载错误、命令名 |
| 本地网页打不开 | 启动进程、实际地址、端口冲突 |
| 输入框不可用 | 是否已选中工作区 |
| 能对话但找不到文件 | 工作区路径和文件名 |
| 找不到Python | 当前进程可用的解释器与PATH |
| 技能不出现 | .dsh目录是否复制、实际项目根、SKILL.md结构 |
| 结果目录已经存在 | 使用新的输出目录 |
| 只有JSON，没有日报 | 是否完成模板填充和文件写入 |
| MCP工具缺失 | 服务是否启动、连接配置和加载日志 |
| 模型请求成功但工具失败 | 参数、权限和本地环境，不只检查模型 |
| 改了设置仍像旧行为 | 是否用了旧会话或另一Profile，查看实际选择 |

处理时提供完整操作、错误和路径；只说“用不了”无法区分安装、认证、文件访问和脚本执行问题。

本章完成了从软件启动到技能调用的完整链路。进入[项目实战篇](../../课件/实战篇/大纲.md)后，将以Codex为统一入口，把Python、FastAPI、MySQL与LangGraph接入企业Agent工作流。

---

[技术篇目录](README.md) · [上一章](12-制作带资料、模板与脚本的Skills.md)
