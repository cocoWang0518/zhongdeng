import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '~/utils/request'

export interface ChatSession {
  id: string
  title: string
  date: string
  selected: boolean
  type?: string // Add optional type property for special sessions
}

export const useSidebarStore = defineStore('sidebar', () => {
  // State
  const router = useRouter()
  const isCollapsed = ref(false)
  const chatSessions = ref<ChatSession[]>([])
  request.get('/results').then(({ data }) => {
    data.results.forEach(async (result: any) => {
      const { data: res } = await request.get(`/results/${result.hash}/config.json`)
      chatSessions.value.push({
        id: result.hash,
        title: res.original_filename,
        date: new Date(res.processing_time).toLocaleString(),
        selected: false,
      })
    })
  })
  // Actions
  function toggleCollapsed() {
    isCollapsed.value = !isCollapsed.value
  }

  function createNewChat() {
    const newChat: ChatSession = {
      id: Date.now().toString(),
      title: '新对话',
      date: new Date().toISOString().split('T')[0],
      selected: true,
    }

    // Deselect all other chats
    chatSessions.value.forEach((chat) => {
      chat.selected = false
    })

    // Add new chat to the beginning of the array
    chatSessions.value.unshift(newChat)
  }

  function selectChat(id: string) {
    // Find the selected chat
    const selectedChat = chatSessions.value.find(chat => chat.id === id)

    if (selectedChat) {
      // Mark this chat as selected and others as not selected
      chatSessions.value.forEach((chat) => {
        chat.selected = chat.id === id
      })
      router.push(`/result/${id}`)
    }
  }

  return {
    // State
    isCollapsed,
    chatSessions,

    // Actions
    toggleCollapsed,
    createNewChat,
    selectChat,
  }
})
