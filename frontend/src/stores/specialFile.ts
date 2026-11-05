import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSpecialFileStore = defineStore('specialFile', () => {
  // State
  const csvFileContent = ref<string>('')
  const isSpecialFile = ref(false)
  const fileName = ref('')

  // Actions
  function setSpecialFile(content: string, name: string) {
    csvFileContent.value = content
    fileName.value = name
    isSpecialFile.value = true
  }

  function clearSpecialFile() {
    csvFileContent.value = ''
    fileName.value = ''
    isSpecialFile.value = false
  }

  return {
    csvFileContent,
    isSpecialFile,
    fileName,
    setSpecialFile,
    clearSpecialFile,
  }
})
