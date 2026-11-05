<script setup lang="ts">
import type { ChatSession } from '~/stores/sidebar'
import { useDark, useToggle } from '@vueuse/core'
import { useSidebarStore } from '~/stores/sidebar'

// Props
defineProps<{
  chatSessions: ChatSession[]
}>()

// Emits
const emit = defineEmits(['selectChat', 'createChat'])

const store = useSidebarStore()
const showCreateModal = ref(false)
const router = useRouter()

// Theme toggle setup
const isDark = useDark()
const toggleDark = useToggle(isDark)

// Handle select chat
function handleSelectChat(id: string) {
  emit('selectChat', id)
}

// Handle create new chat
function handleCreateChat() {
  showCreateModal.value = true
}

// Handle create type selection
function handleCreateType(type: 'predict' | 'query') {
  showCreateModal.value = false
  if (type === 'predict') {
    router.push('/new')
  }
  else {
    router.push('/query')
  }
}

// Calculate time ago display
function getTimeAgo(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))

  if (diffDays === 0)
    return '今天'
  if (diffDays === 1)
    return '昨天'
  if (diffDays < 7)
    return `${diffDays}天前`
  return dateStr
}
</script>

<template>
  <n-layout-sider
    bordered
    collapse-mode="width"
    :collapsed-width="64"
    :width="260"
    show-trigger
    :collapsed="store.isCollapsed"
    content-style="display: flex; flex-direction: column; height: 100%;"
    class="bg-gray-50 dark:bg-dark-900"
    @update:collapsed="store.toggleCollapsed"
  >
    <!-- Header with new chat button -->
    <div class="p-4 border-b border-gray-200 dark:border-gray-700">
      <n-button type="primary" block @click="handleCreateChat">
        <template #icon>
          <div class="i-carbon-add" />
        </template>
        <span v-if="!store.isCollapsed">新建</span>
      </n-button>
    </div>

    <!-- Chat history list (scrollable) -->
    <div class="p-2 flex-1 overflow-hidden">
      <n-scrollbar class="h-full">
        <n-list class="bg-gray-50 dark:bg-dark-900">
          <n-list-item
            v-for="chat in chatSessions"
            :key="chat.id"
            class="mb-1 rounded-lg cursor-pointer transition-colors"
            :class="[
              chat.selected ? 'bg-gray-200/50 dark:bg-gray-700/50' : 'hover:bg-gray-100 dark:hover:bg-gray-800/50',
              store.isCollapsed ? 'px-0 py-3 flex justify-center' : 'px-3 py-2.5',
            ]"
            @click="handleSelectChat(chat.id)"
          >
            <div :class="[store.isCollapsed ? 'justify-center' : 'flex items-center']">
              <div class="i-carbon-chat-bot text-gray-600 dark:text-gray-300" :class="[store.isCollapsed ? 'mx-auto' : 'mr-2']" />
              <div v-if="!store.isCollapsed" class="flex-1 min-w-0">
                <div class="text-sm text-gray-800 font-medium truncate dark:text-gray-200">
                  {{ chat.title }}
                </div>
                <div class="text-xs text-gray-500 dark:text-gray-400">
                  {{ getTimeAgo(chat.date) }}
                </div>
              </div>
            </div>
          </n-list-item>
        </n-list>
      </n-scrollbar>
    </div>

    <!-- Footer with theme toggle -->
    <div class="p-4 border-t border-gray-200 dark:border-gray-700">
      <n-button
        quaternary
        block
        class="flex items-center justify-center"
        :class="store.isCollapsed ? 'p-0' : 'gap-2'"
        @click="toggleDark()"
      >
        <template #icon>
          <div v-if="isDark" class="i-carbon-moon text-yellow-400" />
          <div v-else class="i-carbon-sun text-orange-400" />
        </template>
        <span v-if="!store.isCollapsed" class="text-gray-800 dark:text-gray-200">
          {{ isDark ? '切换到亮色模式' : '切换到暗色模式' }}
        </span>
      </n-button>
    </div>
  </n-layout-sider>

  <!-- Create Modal -->
  <n-modal v-model:show="showCreateModal">
    <n-card
      style="width: 600px"
      title="选择新建类型"
      :bordered="false"
      size="huge"
      role="dialog"
      aria-modal="true"
    >
      <div class="flex gap-4 justify-center">
        <n-button
          size="large"
          class="py-4 flex-1"
          type="primary"
          @click="handleCreateType('query')"
        >
          <template #icon>
            <div class="i-carbon-search" />
          </template>
          新建查询
        </n-button>
        <n-button
          size="large"
          class="py-4 flex-1"
          @click="handleCreateType('predict')"
        >
          <template #icon>
            <div class="i-carbon-chemistry" />
          </template>
          新建预测
        </n-button>
      </div>
    </n-card>
  </n-modal>
</template>
