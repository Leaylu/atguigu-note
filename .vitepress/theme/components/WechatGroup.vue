<script setup lang="ts">
/**
 * 微信群二维码：不在仓库里存图片，运行时从 Gist 取邀请链接文本，前端渲染二维码。
 *
 * Gist 文件（纯文本，# 开头为注释）：
 *   第 1 行：微信群邀请链接（微信里打开群二维码 → 右上角「…」→ 复制链接）
 *   第 2 行：过期时间 ISO 8601，如 2026-10-29T00:00+08:00
 *           （缺省时按 Gist 的 updated_at + GRACE_DAYS 估算，需额外请求一次 GitHub API）
 *
 * 换码流程：手机改 Gist 两行文本 → 提交。站点无需重新构建，CDN 最多 5 分钟生效。
 *
 * 由 Layout.vue 按 frontmatter 的 qr: true 注入到 /wechat 页（站点关闭了 markdown 原始 HTML）。
 */
import { computed, onMounted, ref } from 'vue'
import cfg from '../../wechat-qr.json'

const GIST_RAW = cfg.gistUrl
const FALLBACK = cfg.fallback

/** 没有过期时间行时的估算缓冲：微信二维码 7 天有效，留 1 天余量 */
const GRACE_DAYS = 6
const TIMEOUT_MS = 4000

type State = 'loading' | 'ready' | 'expired' | 'error'

const state = ref<State>('loading')
const qr = ref('') // dataURL：必须用 <img>，内联 SVG 在微信里无法长按保存/转发
const expiresAt = ref<Date | null>(null)
const estimated = ref(false)

const expiryText = computed(() => {
  const d = expiresAt.value
  if (!d) return '有效期未知'
  const md = `${d.getMonth() + 1} 月 ${d.getDate()} 日`
  return (estimated.value ? '约至 ' : '有效期至 ') + md
})

/** AbortSignal.timeout 在旧版微信内核里可能没有 */
function timeoutSignal() {
  if (typeof AbortSignal !== 'undefined' && 'timeout' in AbortSignal) {
    return AbortSignal.timeout(TIMEOUT_MS)
  }
  const ctrl = new AbortController()
  setTimeout(() => ctrl.abort(), TIMEOUT_MS)
  return ctrl.signal
}

function parseGist(text: string) {
  const lines = text
    .split('\n')
    .map(l => l.trim())
    .filter(l => l && !l.startsWith('#'))
  const link = lines[0] ?? ''
  if (!/^https?:\/\//i.test(link)) throw new Error('Gist 第一行不是 http 链接')
  const d = lines[1] ? new Date(lines[1].replace(' ', 'T')) : null
  return { link, date: d && !isNaN(d.getTime()) ? d : null }
}

/** 从 raw 地址里取出 gist id，读它的 updated_at（限流 60 次/IP/小时，失败不阻塞） */
async function gistUpdatedAt(url: string): Promise<Date | null> {
  const id = url.match(/gist\.githubusercontent\.com\/[^/]+\/([0-9a-f]+)/i)?.[1]
  if (!id) return null
  try {
    const res = await fetch(`https://api.github.com/gists/${id}`, { signal: timeoutSignal() })
    if (!res.ok) return null
    const d = new Date((await res.json()).updated_at)
    return isNaN(d.getTime()) ? null : d
  } catch {
    return null
  }
}

async function load() {
  state.value = 'loading'
  estimated.value = false
  try {
    if (!GIST_RAW || GIST_RAW.includes('REPLACE')) throw new Error('wechat-qr.json 里还没填 gistUrl')
    const res = await fetch(`${GIST_RAW}?t=${Date.now()}`, {
      cache: 'no-store', // 打掉 Gist CDN 的 max-age=300
      signal: timeoutSignal(),
    })
    if (!res.ok) throw new Error(`Gist ${res.status}`)
    const { link, date } = parseGist(await res.text())

    if (!date) {
      const updated = await gistUpdatedAt(GIST_RAW)
      if (updated) {
        expiresAt.value = new Date(updated.getTime() + GRACE_DAYS * 864e5)
        estimated.value = true
      }
    } else {
      expiresAt.value = date
    }

    if (expiresAt.value && Date.now() > expiresAt.value.getTime()) {
      state.value = 'expired'
      return
    }

    // 二维码固定纯黑白 + 白底：跟随深色模式反色会有大量机型扫不出
    const QRCode = (await import('qrcode')).default
    qr.value = await QRCode.toDataURL(link, {
      width: 280,
      margin: 2,
      errorCorrectionLevel: 'M',
      color: { dark: '#000000ff', light: '#ffffffff' },
    })
    state.value = 'ready'
  } catch (e) {
    console.warn('[wechat] 群二维码加载失败：', e)
    state.value = 'error'
  }
}

onMounted(load)
</script>

<template>
  <div class="wechat-group">
    <div v-if="state === 'loading'" class="wq-hint">二维码加载中…</div>

    <template v-else-if="state === 'ready'">
      <img class="wq-qr" :src="qr" alt="微信群二维码" width="280" height="280" />
      <p class="wq-meta">{{ expiryText }}</p>
      <p class="wq-hint">扫码进群</p>
    </template>

    <div v-else class="wq-hint">
      <p>{{ FALLBACK }}</p>
      <button class="wq-retry" type="button" @click="load">刷新重试</button>
    </div>
  </div>
</template>

<style scoped>
.wechat-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  margin: 24px 0;
}

.wq-qr {
  width: 280px;
  max-width: 100%;
  height: auto;
  padding: 8px;
  background: #fff; /* 深色模式下也保持白底，保证可扫 */
  border-radius: 8px;
  box-shadow: 0 0 0 1px var(--vp-c-divider);
}

.wq-meta {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  color: var(--vp-c-text-1);
}

.wq-hint {
  margin: 0;
  font-size: 13px;
  text-align: center;
  color: var(--vp-c-text-2);
}

.wq-retry {
  margin-top: 8px;
  padding: 6px 16px;
  font-size: 13px;
  color: var(--vp-c-brand-1);
  border: 1px solid var(--vp-c-brand-1);
  border-radius: 16px;
  background: transparent;
  cursor: pointer;
}
</style>
