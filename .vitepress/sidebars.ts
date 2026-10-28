import type { DefaultTheme } from 'vitepress'

export const langchainSidebar: DefaultTheme.SidebarItem[] = [
  {
    text: 'LangChain 课件',
    items: [
      { text: '01 · LangChain 概述', link: '/langchain/课件/01-LangChain概述' },
      { text: '02 · 模型的创建与调用', link: '/langchain/课件/02-模型的创建与调用' },
      { text: '03 · LangSmith 的使用', link: '/langchain/课件/03-LangSmith的使用' },
      { text: '04 · Message 与提示词模板', link: '/langchain/课件/04-Message与提示词模板' },
      { text: '05 · Tools', link: '/langchain/课件/05-Tools' },
      { text: '06 · 结构化输出', link: '/langchain/课件/06-结构化输出' },
      { text: '07 · 智能体', link: '/langchain/课件/07-智能体' },
      { text: '08 · 中间件', link: '/langchain/课件/08-中间件' },
      { text: '09 · 上下文与记忆', link: '/langchain/课件/09-上下文与记忆' },
      { text: '10 · RAG', link: '/langchain/课件/10-RAG' },
      { text: '11 · MCP 与 Skills', link: '/langchain/课件/11-MCP与Skills' },
    ],
  },
  {
    text: '相关链接',
    items: [
      { text: 'Notebook 在线阅读', link: '/langchain/notebooks' },
      { text: '视频分 P 目录', link: '/langchain/README' },
      { text: 'B 站在线观看', link: 'https://www.bilibili.com/video/BV1rv7A6oEeP' },
    ],
  },
]

export const langgraphSidebar: DefaultTheme.SidebarItem[] = [
  {
    text: 'LangGraph 课件',
    items: [
      { text: '00 · 环境配置', link: '/langgraph/课件/00-环境配置' },
      { text: '01 · LangGraph 基础入门', link: '/langgraph/课件/01-LangGraph基础入门' },
      { text: '02 · 控制流与节点执行', link: '/langgraph/课件/02-LangGraph控制流与节点执行' },
      { text: '03 · 持久化与记忆管理', link: '/langgraph/课件/03-LangGraph持久化与记忆管理' },
      { text: '04 · 中断与工具与部署', link: '/langgraph/课件/04-LangGraph中断与工具与部署' },
      { text: '05 · 高级特性', link: '/langgraph/课件/05-LangGraph高级特性' },
    ],
  },
  {
    text: '相关链接',
    items: [
      { text: 'Notebook 在线阅读', link: '/langgraph/notebooks' },
      { text: '视频分 P 目录', link: '/langgraph/README' },
      { text: 'B 站在线观看', link: 'https://www.bilibili.com/video/BV1z3NY66EY1' },
    ],
  },
]

export const vibeSidebar: DefaultTheme.SidebarItem[] = [
  {
    text: 'AI Coding 课件',
    items: [
      { text: '00 · 课程介绍与环境准备', link: '/vibe_coding/课件/00-课程介绍与环境准备' },
      { text: '01 · AI 编程基础理论', link: '/vibe_coding/课件/01-AI编程基础理论' },
      { text: '02 · AI 编程工具生态', link: '/vibe_coding/课件/02-AI编程工具生态' },
      { text: '03 · Claude Code 深度使用', link: '/vibe_coding/课件/03-ClaudeCode深度使用与进阶技巧' },
      { text: '04 · AI 技能系统（Skills）', link: '/vibe_coding/课件/04-AI技能系统Skills' },
      { text: '05 · 完整项目案例实操', link: '/vibe_coding/课件/05-完整项目案例实操' },
      { text: '06 · 项目实战（独立完成）', link: '/vibe_coding/课件/06-项目实战独立完成' },
      { text: '07 · Codex Desktop', link: '/vibe_coding/课件/07-CodexDesktop' },
      { text: '08 · 附录', link: '/vibe_coding/课件/08-附录' },
    ],
  },
  {
    text: '相关链接',
    items: [
      { text: '视频分 P 目录', link: '/vibe_coding/README' },
      { text: 'B 站在线观看', link: 'https://www.bilibili.com/video/BV1RPET6tEp2' },
    ],
  },
]

export const agentSkillsSidebar: DefaultTheme.SidebarItem[] = [
  {
    text: '课程概览',
    items: [
      { text: '课程大纲', link: '/agent_skills/课件/00-课程大纲' },
      { text: '视频分 P 目录', link: '/agent_skills/README' },
    ],
  },
  {
    text: '技术篇',
    items: [
      { text: '技术篇目录', link: '/agent_skills/课件/技术篇/README' },
      { text: '01 · Vibe Coding 与 Agent 的工作方式', link: '/agent_skills/课件/技术篇/01-Vibe-Coding与Agent的工作方式' },
      { text: '02 · WorkBuddy 上手与任务管理', link: '/agent_skills/课件/技术篇/02-WorkBuddy上手与任务管理' },
      { text: '03 · WorkBuddy 办公工作流实战', link: '/agent_skills/课件/技术篇/03-WorkBuddy办公工作流实战' },
      { text: '04 · Codex 上手与双模型接入', link: '/agent_skills/课件/技术篇/04-Codex上手、双模型接入与第一个应用' },
      { text: '05 · Codex 调试、迭代与交付', link: '/agent_skills/课件/技术篇/05-Codex调试、迭代与交付' },
      { text: '06 · MCP 服务器介绍与接入', link: '/agent_skills/课件/技术篇/06-MCP服务器介绍与接入' },
      { text: '07 · Skills 的含义与运行机制', link: '/agent_skills/课件/技术篇/07-Skills的含义、作用与运行机制' },
      { text: '08 · 查找、安装与使用现有 Skills', link: '/agent_skills/课件/技术篇/08-查找、安装与使用现有Skills' },
      { text: '09 · 从工作经验中设计 Skill', link: '/agent_skills/课件/技术篇/09-从工作经验中设计Skill' },
      { text: '10 · 手工制作第一个 Skill', link: '/agent_skills/课件/技术篇/10-手工制作第一个Skill' },
      { text: '11 · 用 Agent 辅助制作与改进', link: '/agent_skills/课件/技术篇/11-用Agent辅助制作与改进Skills' },
      { text: '12 · 带资料、模板与脚本的 Skills', link: '/agent_skills/课件/技术篇/12-制作带资料、模板与脚本的Skills' },
      { text: '13 · DeepSeek Harness 上手', link: '/agent_skills/课件/技术篇/13-DeepSeek-Harness介绍与上手' },
      { text: '附 · 案例与资料索引', link: '/agent_skills/课件/技术篇/案例与资料索引' },
    ],
  },
  {
    text: '项目实战篇',
    items: [
      { text: '实战篇目录', link: '/agent_skills/课件/实战篇/README' },
      { text: '项目实战篇大纲', link: '/agent_skills/课件/实战篇/大纲' },
      { text: '00 · 依赖安装与项目启动', link: '/agent_skills/课件/实战篇/00-依赖安装与项目启动' },
      { text: '01 · 项目背景与架构', link: '/agent_skills/课件/实战篇/01-项目背景与架构' },
      { text: '02 · 认识已有电商系统', link: '/agent_skills/课件/实战篇/02-认识已有电商系统' },
      { text: '03 · 接入已有 Python 程序', link: '/agent_skills/课件/实战篇/03-接入已有Python程序' },
      { text: '04 · 接入 FastAPI 与 MySQL', link: '/agent_skills/课件/实战篇/04-接入FastAPI与MySQL' },
      { text: '05 · 制作企业业务 Skills', link: '/agent_skills/课件/实战篇/05-制作企业业务Skills' },
      { text: '06 · 接入 LangGraph 工作流', link: '/agent_skills/课件/实战篇/06-接入LangGraph工作流' },
      { text: '07 · 完成端到端业务任务', link: '/agent_skills/课件/实战篇/07-完成端到端业务任务' },
    ],
  },
  {
    text: '相关链接',
    items: [
      { text: 'B 站在线观看', link: 'https://www.bilibili.com/video/BV14rxM6qEnL' },
    ],
  },
]

export const pythonSidebar: DefaultTheme.SidebarItem[] = [
  {
    text: 'Python 课件',
    items: [
      { text: '01 · 必备基础知识', link: '/python/课件/01-必备基础知识' },
      { text: '02 · 初识 Python', link: '/python/课件/02-初识Python' },
      { text: '03 · Python 核心基础', link: '/python/课件/03-Python核心基础' },
      { text: '04 · 流程控制语句', link: '/python/课件/04-流程控制语句' },
      { text: '05 · 函数入门', link: '/python/课件/05-函数入门' },
      { text: '06 · 数据容器', link: '/python/课件/06-数据容器' },
      { text: '07 · 面向对象', link: '/python/课件/07-面向对象' },
      { text: '08 · 函数进阶', link: '/python/课件/08-函数进阶' },
      { text: '09 · 错误与异常', link: '/python/课件/09-错误与异常' },
      { text: '10 · 模块与包', link: '/python/课件/10-模块与包' },
      { text: '11 · 迭代器 vs 生成器', link: '/python/课件/11-迭代器vs生成器' },
      { text: '12 · 文件操作', link: '/python/课件/12-文件操作' },
      { text: '13 · 进程与线程', link: '/python/课件/13-进程与线程' },
      { text: '14 · 协程', link: '/python/课件/14-协程' },
    ],
  },
  {
    text: '相关链接',
    items: [
      { text: '视频分 P 目录', link: '/python/README' },
      { text: 'B 站在线观看', link: 'https://www.bilibili.com/video/BV1tDsgzxECr' },
    ],
  },
]
