<script setup lang="ts">
import { marked } from 'marked'
import { NButton, NSpin } from 'naive-ui'
import request from '~/utils/request'

interface IdentifierData {
  债券代码: string
  债券名称: string
  时间: string
  [key: string]: string | number
}

type HistoryRecord = Record<string, string | number>

interface ModelResult {
  模型名称: string
  模型评级: string
  importance?: Array<{ Feature: string, Importance: number }>
}

interface QueryResultData {
  bond_type: string
  detected_type?: string
  model_metrics?: ModelMetric[]
  identifier_data: IdentifierData
  df_results: ModelResult[]
  df_history: HistoryRecord[]
}

interface ModelMetric {
  model: string
  Mean_MAE: number
  Mean_RMSE: number
  Mean_R2: number
  Mean_R2_os: number
}

interface DetailData {
  model_text: string
  plot_image: string
  plot_data: Array<{ Feature: string, Importance: number }>
}

const props = defineProps<{
  data: QueryResultData | null
}>()

const showDetailModal = ref(false)
const showMetricsModal = ref(false)
const selectedModel = ref<ModelResult | null>(null)
const detailLoading = ref(false)
const detailData = ref<DetailData | null>(null)
const detailBtnLoadingModelName = ref<string | null>(null)
const detailCache = ref(new Map<string, DetailData>())

const trendImage = ref<string | null>(null)
const trendLoading = ref(false)

const identifierFields = computed(() => {
  if (!props.data)
    return []
  const d = props.data.identifier_data
  return [
    { label: '系统识别类型', value: props.data.detected_type || props.data.bond_type || '未知' },
    ...Object.entries(d).map(([label, value]) => ({ label, value })),
  ]
})

const historyColumns = computed(() => {
  if (!props.data?.df_history?.length)
    return []

  const keys = Object.keys(props.data.df_history[0])
  return keys.map(key => ({ title: key, key }))
})

const metricsColumns = [
  { title: '模型', key: 'model' },
  { title: 'Mean MAE', key: 'Mean_MAE' },
  { title: 'Mean RMSE', key: 'Mean_RMSE' },
  { title: 'Mean R²', key: 'Mean_R2' },
  { title: 'Mean R² OS', key: 'Mean_R2_os' },
]

const hasModelMetrics = computed(() => {
  return !!props.data?.model_metrics?.length
})

watch(() => props.data, async (newData) => {
  trendImage.value = null
  detailCache.value.clear()
  // 查询返回后自动请求近 9 个月评级趋势图（rating_trend_9m.png 同款）
  if (newData && newData.df_history && newData.df_history.length > 0) {
    await fetchTrendImage(newData)
  }
}, { immediate: true })

async function fetchTrendImage(data: QueryResultData) {
  trendLoading.value = true
  try {
    const response = await request.post('/ketiyi/trend', {
      df_history: data.df_history,
      bond_name: data.identifier_data.债券名称 || data.identifier_data.代码 || '',
      detected_type: data.detected_type || data.bond_type || '',
      months: 9,
    }, {
      headers: { 'Content-Type': 'application/json' },
    })
    if (response.data.status === 'success') {
      trendImage.value = response.data.data.trend_image
    }
  }
  catch (err: any) {
    console.error('Trend image request error:', err)
  }
  finally {
    trendLoading.value = false
  }
}

async function handleViewDetail(model: ModelResult) {
  selectedModel.value = model
  detailData.value = null

  if (detailCache.value.has(model.模型名称)) {
    detailData.value = detailCache.value.get(model.模型名称)!
    showDetailModal.value = true
    return
  }

  if (!model.importance || model.importance.length === 0) {
    detailData.value = null
    showDetailModal.value = true
    return
  }

  detailBtnLoadingModelName.value = model.模型名称
  try {
    await fetchDetailData(model)
  }
  finally {
    if (detailBtnLoadingModelName.value === model.模型名称)
      detailBtnLoadingModelName.value = null
  }
  showDetailModal.value = true
}

async function fetchDetailData(model: ModelResult) {
  if (!model.importance)
    return

  detailLoading.value = true

  try {
    const response = await request.post('/ketiyi/detail', {
      importance: model.importance,
      bond_type: props.data?.detected_type || props.data?.bond_type || '城投债',
    }, {
      headers: { 'Content-Type': 'application/json' },
    })

    if (response.data.status === 'success') {
      const data = response.data.data as DetailData
      detailData.value = data
      detailCache.value.set(model.模型名称, data)
    }
    else {
      console.error('Detail request failed:', response.data.message)
    }
  }
  catch (err: any) {
    console.error('Detail request error:', err)
  }
  finally {
    detailLoading.value = false
  }
}

function closeDetailModal() {
  showDetailModal.value = false
  selectedModel.value = null
  detailData.value = null
}

const columns = computed(() => [
  {
    title: '模型名称',
    key: '模型名称',
  },
  {
    title: '模型评级',
    key: '模型评级',
    render(row: ModelResult) {
      return h('n-tag', {
        type: getRatingColor(row.模型评级),
        size: 'small',
      }, {
        default: () => row.模型评级,
      })
    },
  },
  {
    title: '操作',
    key: 'actions',
    render(row: ModelResult) {
      const hasImportance = !!row.importance?.length

      return h(NButton, {
        size: 'small',
        type: 'primary',
        secondary: true,
        loading: detailBtnLoadingModelName.value === row.模型名称,
        disabled: !hasImportance || detailBtnLoadingModelName.value === row.模型名称,
        onClick: () => handleViewDetail(row),
      }, {
        default: () => hasImportance ? '查看详情' : '无详情',
      })
    },
  },
])

function getRatingColor(rating: string) {
  const ratingMap: Record<string, string> = {
    'AAA': 'success',
    'AA+': 'success',
    'AA': 'success',
    'AA-': 'success',
    'A+': 'info',
    'A': 'info',
    'A-': 'info',
    'BBB': 'warning',
    'BB': 'warning',
    'B': 'error',
    'CCC': 'error',
    'CC': 'error',
    'C': 'error',
    'D': 'error',
  }
  return ratingMap[rating] || 'default'
}
</script>

<template>
  <div v-if="data" class="space-y-6">
    <!-- 债券信息卡片 -->
    <n-card title="债券基本信息" :bordered="false" class="mb-6">
      <div class="gap-4 grid grid-cols-2 lg:grid-cols-4 md:grid-cols-3">
        <div v-for="field in identifierFields" :key="field.label" class="space-y-1">
          <div class="text-sm text-gray-500 dark:text-gray-400">
            {{ field.label }}
          </div>
          <div class="text-gray-800 font-medium dark:text-gray-200">
            {{ field.value }}
          </div>
        </div>
      </div>
    </n-card>

    <!-- 模型评级结果表格 -->
    <n-card title="模型评级结果" :bordered="false">
      <template #header-extra>
        <NButton
          v-if="hasModelMetrics"
          size="small"
          type="primary"
          secondary
          @click="showMetricsModal = true"
        >
          查看模型结果
        </NButton>
      </template>

      <n-data-table
        :columns="columns"
        :data="data.df_results"
        :bordered="false"
        size="medium"
        class="rounded-lg"
      />
    </n-card>

    <n-modal v-model:show="showMetricsModal">
      <n-card
        style="width: 720px; max-width: 90vw"
        title="模型结果"
        :bordered="false"
        size="huge"
        role="dialog"
        aria-modal="true"
      >
        <n-data-table
          :columns="metricsColumns"
          :data="data.model_metrics || []"
          :bordered="false"
          size="small"
        />
      </n-card>
    </n-modal>

    <!-- 历史评级记录：近 9 个月评级趋势图 + 历史评级表 -->
    <n-card v-if="data.df_history && data.df_history.length > 0" title="历史评级记录" :bordered="false">
      <template #header-extra>
        <n-tag size="small" type="info">
          近 9 个月走势
        </n-tag>
      </template>

      <NSpin :show="trendLoading">
        <div v-if="trendImage" class="p-4 mb-4 flex justify-center rounded-lg bg-white dark:bg-gray-900">
          <n-image
            :src="trendImage"
            alt="评级趋势图"
            class="rounded h-auto max-w-full shadow-sm"
          />
        </div>
        <div v-else-if="!trendLoading" class="py-4 mb-4 text-center text-sm text-gray-500">
          暂无趋势图数据
        </div>
      </NSpin>

      <n-data-table
        :columns="historyColumns"
        :data="data.df_history"
        :bordered="false"
        size="medium"
        :max-height="400"
        class="rounded-lg"
      />
    </n-card>

    <!-- 详情弹窗 -->
    <n-modal v-model:show="showDetailModal">
      <n-card
        style="width: 80vw; max-height: 80vh"
        :title="`${selectedModel?.模型名称} 详情分析`"
        :bordered="false"
        size="huge"
        role="dialog"
        aria-modal="true"
        class="overflow-hidden"
      >
        <div class="overflow-y-auto" style="max-height: 60vh">
          <NSpin :show="detailLoading">
            <div v-if="detailData" class="w-full">
              <div class="flex flex-col gap-6 w-full md:flex-row">
                <div class="flex-1 space-y-3 md:w-1/2">
                  <h3 class="text-lg text-gray-800 font-semibold dark:text-gray-200">
                    特征重要性可视化
                  </h3>
                  <div class="p-4 rounded-lg bg-white flex justify-center dark:bg-gray-900">
                    <NImage
                      v-if="detailData.plot_image"
                      :src="detailData.plot_image"
                      alt="特征重要性图表"
                      class="rounded h-auto max-w-full shadow-sm"
                    />
                  </div>
                </div>

                <div class="flex-1 space-y-3 md:w-1/2">
                  <h3 class="text-lg text-gray-800 font-semibold dark:text-gray-200">
                    模型分析报告
                  </h3>
                  <div class="leading-relaxed py-4 rounded-lg">
                    <div
                      class="prose prose-sm text-gray-700 max-w-none dark:text-gray-300"
                      v-html="marked.parse(detailData.model_text)"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div v-else-if="!detailLoading" class="py-8 text-center">
              <div class="i-carbon-information text-4xl text-gray-400 mb-4" />
              <p class="text-gray-600 dark:text-gray-400">
                {{ selectedModel?.importance ? '暂无详情数据' : '该模型暂无特征重要性数据' }}
              </p>
              <p class="text-sm text-gray-500 mt-2 dark:text-gray-500">
                模型: {{ selectedModel?.模型名称 }} | 评级: {{ selectedModel?.模型评级 }}
              </p>
            </div>

            <div v-else class="py-8 text-center">
              <p class="text-gray-600 dark:text-gray-400">
                正在加载详情数据...
              </p>
            </div>
          </NSpin>
        </div>

        <template #footer>
          <div class="flex justify-end space-x-2">
            <NButton @click="closeDetailModal">
              关闭
            </NButton>
          </div>
        </template>
      </n-card>
    </n-modal>
  </div>
</template>
