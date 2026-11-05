<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import ArEvaluation from '~/components/ArEvaluation.vue'
import PredictForm from '~/components/PredictForm.vue'
import { useSidebarStore } from '~/stores/sidebar'
import request from '~/utils/request'

// Initialize router for navigation
const router = useRouter()

// UI state management
const loading = ref(false)
const showAr = ref(false)
const error = ref('')
const showConfirmDialog = ref(false)
const existingHash = ref('')
const formDataCache = ref<FormData | null>(null)

useSidebarStore().chatSessions.forEach((chat) => {
  chat.selected = false
})

// Empty initial form data
const formData = {
  task_type: '',
  data_type: '',
  industry_type: '',
}

// Handle form submission
async function handleFormSubmit(data: FormData) {
  error.value = ''
  formDataCache.value = data // Cache the form data for later use
  await generatePrediction(data)
}

// Generate prediction by calling the predict API
async function generatePrediction(data: FormData, force = false) {
  loading.value = true
  try {
    if (force)
      data.set('force', '1')
    else
      data.delete('force')

    const response = await request.post('/predict', data, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

    if (response.data.status === 'success') {
      // Redirect to result page with the returned hash
      router.push(`/result/${response.data.hash}`)
    }
    else if (response.data.status === 'exists') {
      existingHash.value = response.data.hash
      showConfirmDialog.value = true
    }
    else {
      error.value = response.data.message || '预测失败，请稍后重试'
    }
  }
  catch (err: any) {
    console.error('Prediction error:', err)
    error.value = err.response?.data?.message || err.message || '预测失败，请稍后重试'
  }
  finally {
    loading.value = false
  }
}

// Dialog action handlers
function handleRegenerate() {
  showConfirmDialog.value = false
  if (formDataCache.value) {
    generatePrediction(formDataCache.value, true)
  }
}

function handleRedirect() {
  showConfirmDialog.value = false
  if (existingHash.value) {
    router.push(`/result/${existingHash.value}`)
  }
}

function handleCancel() {
  showConfirmDialog.value = false
  // Just close the dialog
}
</script>

<template>
  <div class="mx-auto px-4 py-6 max-w-7xl w-full">
    <n-card title="新建预测" :bordered="false" class="mb-6">
      <template #header-extra>
        <n-button size="small" secondary @click="showAr = true">
          模型AR值
        </n-button>
      </template>
      <p class="text-gray-700 mb-4 dark:text-gray-300">
        填写预测参数并上传数据文件，系统将自动分析并生成结果。
      </p>

      <!-- Loading state -->
      <n-spin :show="loading">
        <!-- Error message -->
        <n-alert v-if="error" type="error" class="mb-4" closable>
          {{ error }}
        </n-alert>

        <!-- Predict form -->
        <PredictForm
          :data="formData"
          @submit-success="handleFormSubmit"
        />
      </n-spin>
    </n-card>

    <n-modal v-model:show="showAr" preset="card" title="模型AR值" style="width: 1100px; max-width: 95vw" :content-style="{ maxHeight: '80vh', overflowY: 'auto' }">
      <ArEvaluation v-if="showAr" />
    </n-modal>

    <!-- Confirmation dialog when result already exists -->
    <n-modal
      v-model:show="showConfirmDialog"
      preset="dialog"
      title="结果已存在"
      positive-text="重新生成"
      negative-text="取消"
    >
      <template #default>
        <p>检测到相同参数的预测结果已存在，您是否要：</p>
      </template>

      <template #action>
        <div class="flex gap-2 justify-end">
          <n-button @click="handleCancel">
            取消
          </n-button>
          <n-button type="info" @click="handleRedirect">
            跳转到已有结果
          </n-button>
          <n-button type="primary" @click="handleRegenerate">
            重新生成
          </n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<style>

</style>
