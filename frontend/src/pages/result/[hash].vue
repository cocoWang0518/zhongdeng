<script setup lang="ts">
import { useRouteParams } from '@vueuse/router'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import PredictForm from '~/components/PredictForm.vue'
import ResultDisplay from '~/components/ResultDisplay.vue'
import { useSidebarStore } from '~/stores/sidebar'
import request from '~/utils/request'

const hash = useRouteParams<string>('hash')
const router = useRouter()
const sidebarStore = useSidebarStore()

const baseUrl = computed(() => `/results/${hash.value}`)

// Result URLs
const tableResult = computed(() => `${baseUrl.value}/biaoge.csv`)
const downloadResult = computed(() => import.meta.env.DEV ? `/api${baseUrl.value}/biaoge.csv` : `${baseUrl.value}/biaoge.csv`)
const riskTextUrl = computed(() => `${baseUrl.value}/risk_metrics.json`)

const riskText = ref({})
const configData = ref(
  {
    task_type: '',
    data_type: '',
    industry_type: '',
    dataset_filename: '',
    test_info: {},
  },
)

// const { state: riskText } = useAsyncState(
//   () => request.get(riskTextUrl.value).then(res => res.data),
//   {},
// )

// const { state: configData } = useAsyncState(
//   () => request.get(`${baseUrl.value}/config.json`).then(res => res.data),
//   {
//     task_type: '',
//     data_type: '',
//     industry_type: '',
//   },
// )

// Fetch initial data
const tableData = ref('') // Changed to string for CSV data
const datasetFilename = computed(() => configData.value.dataset_filename || 'dataset.csv')
const resolvedDatasetUrl = computed(() => {
  const path = `${baseUrl.value}/${datasetFilename.value}`
  return import.meta.env.DEV ? `/api${path}` : path
})

// Load data from API
function loadData() {
  const waitList = [
    request.get(tableResult.value, {
      responseType: 'text',
    }).then(({ data }) => {
      tableData.value = data
    }),
    request.get(riskTextUrl.value).then(({ data }) => {
      riskText.value = data
    }),
    request.get(`${baseUrl.value}/config.json`).then(({ data }) => {
      configData.value = data
    }),
  ]
  return Promise.allSettled(waitList)
}

watch(hash, () => {
  loadData()
  setTimeout(() => {
    sidebarStore.chatSessions.forEach((chat) => {
      if (chat.id === hash.value) {
        chat.selected = true
      }
    })
  }, 500)
}, { immediate: true })

// Loading state and error handling
const loading = ref(false)
const error = ref('')

async function handleFormSubmit(formData: FormData) {
  loading.value = true
  error.value = ''

  try {
    const response = await request.post('/predict', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

    if (['success', 'exists'].includes(response.data.status)) {
      if (response.data.hash === hash.value)
        await loadData()
      else
        await router.push(`/result/${response.data.hash}`)
    }
    else {
      error.value = response.data.message || '预测失败，请稍后重试'
    }
  }
  catch (err: any) {
    console.error('Prediction error:', err)
    error.value = err.response?.data?.message || err.message || '提交失败，请稍后重试'
  }
  finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="mx-auto px-4 py-6 max-w-7xl w-full">
    <n-card title="预测分析" class="mb-6" :bordered="false">
      <p class="text-gray-700 mb-4 dark:text-gray-300">
        在下方表单中填写预测参数，上传数据文件后点击提交进行预测分析。
      </p>

      <!-- Loading state -->
      <n-spin :show="loading">
        <!-- Error message -->
        <n-alert v-if="error" type="error" class="mb-4" closable>
          {{ error }}
        </n-alert>

        <!-- Predict form for non-special hash -->
        <PredictForm
          :data="configData"
          @submit-success="handleFormSubmit"
        />

        <!-- Standard results display for non-special hash -->
        <ResultDisplay
          :download-result="downloadResult"
          :table-data="tableData"
          :dataset-url="resolvedDatasetUrl"
          :risk-text="riskText"
          :test-info="configData.test_info"
        />
      </n-spin>
    </n-card>
  </div>
</template>

<style>

</style>
