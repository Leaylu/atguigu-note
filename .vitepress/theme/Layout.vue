<script setup lang="ts">
import DefaultTheme from 'vitepress/theme'
import { useRouter, useData } from 'vitepress'
import { NProgress } from 'nprogress-v2'
import 'nprogress-v2/dist/index.css'
import './style.css'
import Giscus from './components/Giscus.vue'
import WechatGroup from './components/WechatGroup.vue'

NProgress.configure({ showSpinner: false })
import { inBrowser } from 'vitepress'

declare global {
  interface Window {
    _hmt?: string[][]
  }
}

// 构建期由 vite define 注入，本地构建显示 dev
declare const __COMMIT_SHA__: string
console.log('[atguigu-note] commit:', __COMMIT_SHA__)

const router = useRouter()
// SSR 下 window 不存在，只在浏览器端注册
if (inBrowser) {
  router.onBeforeRouteChange = to => {
    NProgress.start()
    window._hmt?.push(['_trackPageview', to])
  }

  router.onAfterRouteChange = () => {
    NProgress.done()
  }
}

const { Layout } = DefaultTheme

// 站点关闭了 markdown 原始 HTML（见 config.mts），组件只能从主题注入；
// wechat.md 用 frontmatter 的 qr: true 声明自己是二维码页
const { frontmatter } = useData()
</script>

<template>
  <Layout>
    <template #doc-after>
      <WechatGroup v-if="frontmatter.qr" />
      <Giscus />
    </template>
  </Layout>
</template>
