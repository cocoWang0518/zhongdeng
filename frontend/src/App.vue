<script setup lang="ts">
import { darkTheme } from 'naive-ui'
import AppHeader from '~/components/AppHeader.vue'
import ChatSidebar from '~/components/ChatSidebar.vue'
import { useSidebarStore } from '~/stores/sidebar'

const store = useSidebarStore()
const route = useRoute()

const showCreditSidebar = computed(() => {
  const path = route.path
  return path === '/' || path === '/new' || path === '/query' || path.startsWith('/result/')
})
</script>

<template>
  <n-config-provider :theme="isDark ? darkTheme : null">
    <div class="text-gray-700 font-sans flex flex-col h-screen dark:text-gray-200">
      <AppHeader />
      <n-layout
        v-if="showCreditSidebar"
        has-sider
        class="flex-1 min-h-0"
      >
        <ChatSidebar
          :chat-sessions="store.chatSessions"
          @select-chat="store.selectChat"
        />
        <n-layout-content class="p-0 overflow-auto">
          <RouterView />
        </n-layout-content>
      </n-layout>
      <main v-else class="flex-1 min-h-0 overflow-auto">
        <RouterView />
      </main>
    </div>
    <n-global-style />
  </n-config-provider>
</template>
