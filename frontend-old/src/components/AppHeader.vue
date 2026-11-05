<script setup lang="ts">
const router = useRouter()
const route = useRoute()

const navItems = [
  {
    label: '信用评级',
    path: '/',
    icon: 'i-carbon-analytics',
    active: (path: string) => path === '/' || path === '/new' || path === '/query' || path.startsWith('/result/'),
  },
  {
    label: '指标查看',
    path: '/indicators',
    icon: 'i-carbon-table-split',
    active: (path: string) => path === '/indicators',
  },
  {
    label: '资产查看',
    path: '/assets',
    icon: 'i-carbon-data-table',
    active: (path: string) => path === '/assets',
  },
  {
    label: '数据库初始化',
    path: '/init/db',
    icon: 'i-carbon-data-base',
    active: (path: string) => path === '/init/db',
  },
]

function navigateTo(path: string) {
  router.push(path)
}
</script>

<template>
  <header class="px-5 border-b border-gray-200 bg-white flex shrink-0 h-15 items-center justify-between dark:border-gray-700 dark:bg-dark-900">
    <div class="flex gap-3 min-w-0 items-center">
      <div class="text-white rounded bg-blue-600 flex shrink-0 h-8 w-8 items-center justify-center">
        <div class="i-carbon-chart-relationship" />
      </div>
      <div class="text-base text-gray-900 font-semibold min-w-0 dark:text-gray-100">
        业务示范系统
      </div>
    </div>

    <nav class="flex shrink-0 gap-1 items-center">
      <n-button
        v-for="item in navItems"
        :key="item.path"
        :type="item.active(route.path) ? 'primary' : 'default'"
        :secondary="item.active(route.path)"
        :quaternary="!item.active(route.path)"
        size="medium"
        @click="navigateTo(item.path)"
      >
        <template #icon>
          <div :class="item.icon" />
        </template>
        {{ item.label }}
      </n-button>
    </nav>
  </header>
</template>
