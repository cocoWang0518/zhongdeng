<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import SpecialResult from '~/components/SpecialResult.vue'
import { useSpecialFileStore } from '~/stores/specialFile'

const store = useSpecialFileStore()
const router = useRouter()
const csvContent = ref('')
const fileName = ref('')

onMounted(() => {
  // Check if we have the special file data in sessionStorage and store
  if (!store.isSpecialFile) {
    // If no special file, redirect back to home
    router.push('/')
    return
  }

  // Get the file data from store
  csvContent.value = store.csvFileContent
  fileName.value = store.fileName
})

// Create a new File-like object for the SpecialResult component
const csvFile = computed(() => {
  if (!csvContent.value)
    return null

  // Create a Blob from the CSV content
  const blob = new Blob([csvContent.value], { type: 'text/csv' })

  // Create a File object from the Blob
  return new File([blob], fileName.value || 'special-data.csv', { type: 'text/csv' })
})
</script>

<template>
  <div class="special-page mx-auto px-4 py-6 max-w-7xl w-full">
    <n-card title="预测分析" :bordered="false">
      <template #header-extra>
        <div class="flex gap-2 items-center">
          <n-tag v-if="fileName" type="info">
            {{ fileName }}
          </n-tag>
        </div>
      </template>

      <SpecialResult
        v-if="csvFile"
        :csv-file="csvFile"
      />

      <n-empty v-else description="无法获取特殊数据文件，请重新上传" />
    </n-card>
  </div>
</template>

<style scoped>
.special-page {
  min-height: 80vh;
}
</style>
