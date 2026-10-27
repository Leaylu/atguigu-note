import { defineConfig } from 'vitepress'
import type { HeadConfig } from 'vitepress'
import { langchainSidebar, langgraphSidebar, vibeSidebar, pythonSidebar } from './sidebars'

const site = 'https://xbsheng.github.io'
const homeUrl = site + '/atguigu-note/'

function jsonLd(schema: object): HeadConfig {
  return ['script', { type: 'application/ld+json' }, JSON.stringify(schema)]
}

function breadcrumb(pageUrl: string, crumbs: { name: string; url?: string }[]): HeadConfig {
  return jsonLd({
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: crumbs.map((c, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: c.name,
      ...(c.url ? { item: c.url } : {}),
    })),
  })
}

export default defineConfig({
  title: 'AI 课程笔记',
  description: 'Python / LangChain / LangGraph / AI Coding 课程配套课件与代码整理',
  lang: 'zh-CN',

  head: [
    ['link', { rel: 'icon', href: '/atguigu-note/favicon.ico' }],
    jsonLd({
      '@context': 'https://schema.org',
      '@type': 'WebSite',
      name: 'AI 课程笔记',
      url: homeUrl,
      inLanguage: 'zh-CN',
      description: 'Python / LangChain / LangGraph / AI Coding 课程配套课件与代码整理',
    }),
    [
      'script',
      {},
      `var _hmt = _hmt || [];
(function() {
  var hm = document.createElement("script");
  hm.src = "https://hm.baidu.com/hm.js?7a1e6eb3ba3fbae26e9f64cd365ee357";
  var s = document.getElementsByTagName("script")[0];
  s.parentNode.insertBefore(hm, s);
})();`,
    ],
  ],

  // GitHub Pages 项目站：https://xbsheng.github.io/atguigu-note/
  base: '/atguigu-note/',

  transformHead(ctx) {
    const isHome = ctx.pageData.relativePath === 'index.md'
    const rel = ctx.pageData.relativePath.replace(/\.md$/, '')
    const pageUrl = isHome ? homeUrl : site + '/atguigu-note/' + rel
    const head: HeadConfig[] = [['link', { rel: 'canonical', href: pageUrl }]]

    const course = rel.split('/')[0]
    const labels: Record<string, string> = {
      python: 'Python',
      langchain: 'LangChain',
      langgraph: 'LangGraph',
      vibe_coding: 'AI Coding',
    }
    if (labels[course]) {
      head.push(
        breadcrumb(pageUrl, [
          { name: 'AI 课程笔记', url: homeUrl },
          { name: labels[course], url: homeUrl + course + '/' },
          { name: ctx.pageData.title },
        ]),
      )
    }
    return head
  },

  // 直接复用仓库根目录下的现有课件
  srcDir: '.',
  srcExclude: ['**/代码/**', '**/code/**', '**/.venv/**', '**/node_modules/**', '**/langgraph-runtime-viz/**'],

  // 死链检查保持开启，仅忽略两类“刻意排除”导致的预期失效链接：
  // 1. 指向 代码/ 目录的链接：源码目录在站点构建中被 srcExclude 排除，
  //    这些链接用于 GitHub 仓库内导航（README 分章表格中的代码列）
  // 2. langgraph-runtime-viz：独立 HTML 应用，未纳入站点构建
  ignoreDeadLinks: [/代码|%E4%BB%A3%E7%A0%81/, /langgraph-runtime-viz/],

  cleanUrls: true,

  themeConfig: {
    siteTitle: 'AI 课程笔记',

    logo: '/atguigu-logo.png',

    nav: [
      { text: '首页', link: '/' },
      {
        text: 'Python',
        items: [
          { text: '课件目录', link: '/python/课件/01-必备基础知识' },
          { text: '视频分 P', link: '/python/README' },
          { text: 'B 站视频', link: 'https://www.bilibili.com/video/BV1tDsgzxECr' },
        ],
      },
      {
        text: 'LangChain',
        items: [
          { text: '课件目录', link: '/langchain/课件/01-LangChain概述' },
          { text: 'Notebook', link: '/langchain/notebooks' },
          { text: '视频分 P', link: '/langchain/README' },
          { text: 'B 站视频', link: 'https://www.bilibili.com/video/BV1rv7A6oEeP' },
        ],
      },
      {
        text: 'LangGraph',
        items: [
          { text: '课件目录', link: '/langgraph/课件/00-环境配置' },
          { text: 'Notebook', link: '/langgraph/notebooks' },
          { text: '视频分 P', link: '/langgraph/README' },
          { text: 'B 站视频', link: 'https://www.bilibili.com/video/BV1z3NY66EY1' },
        ],
      },
      {
        text: 'AI Coding',
        items: [
          { text: '课件目录', link: '/vibe_coding/课件/00-课程介绍与环境准备' },
          { text: '视频分 P', link: '/vibe_coding/README' },
          { text: 'B 站视频', link: 'https://www.bilibili.com/video/BV1RPET6tEp2' },
        ],
      },
      { text: 'CMU Agents', link: 'https://xbsheng.github.io/cmu-agents/' },
      { text: '速通 Python', link: 'https://pybridge.quarkcode.cn' },
      // { text: '微信交流群', link: '/wechat' },
    ],

    sidebar: {
      '/python/': pythonSidebar,
      '/langchain/': langchainSidebar,
      '/langgraph/': langgraphSidebar,
      '/vibe_coding/': vibeSidebar,
    },

    socialLinks: [{ icon: 'github', link: 'https://github.com/xbsheng/atguigu-note' }],

    search: {
      provider: 'local',
      options: {
        translations: {
          button: {
            buttonText: '搜索课件',
            buttonAriaLabel: '搜索课件',
          },
          modal: {
            noResultsText: '没有找到相关结果',
            resetButtonTitle: '清除查询',
            footer: {
              selectText: '选择',
              navigateText: '切换',
              closeText: '关闭',
            },
          },
        },
      },
    },

    outline: {
      label: '本页目录',
      level: [2, 3],
    },

    docFooter: {
      prev: '上一篇',
      next: '下一篇',
    },

    lastUpdated: {
      text: '最后更新',
    },

    returnToTopLabel: '回到顶部',
    sidebarMenuLabel: '菜单',
    darkModeSwitchLabel: '主题',
    lightModeSwitchTitle: '切换到浅色模式',
    darkModeSwitchTitle: '切换到深色模式',

    footer: {
      message: '本站仅供学习交流',
      copyright: 'Copyright © 笔记整理',
    },
  },

  markdown: {
    // 课件中大量出现 <class '...'>、<YOUR_API_KEY>、<h1> 等文本，
    // 关闭原始 HTML 解析，避免被 Vue 当成未闭合标签导致构建失败
    html: false,
    lineNumbers: true,
    image: {
      lazyLoading: true,
    },
  },

  vite: {
    define: {
      __COMMIT_SHA__: JSON.stringify((process.env.GITHUB_SHA || 'dev').slice(0, 7)),
    },
    server: {
      fs: {
        allow: ['.'],
      },
    },
  },
})
