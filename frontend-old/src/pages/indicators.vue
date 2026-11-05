<script setup lang="ts">
import type { DataTableColumns, SelectOption } from 'naive-ui'
import { computed, h, ref, watch } from 'vue'
import request from '~/utils/request'

interface ModelCount {
  label: string
  value: string
  count: number
}

interface FeatureItem {
  id: number
  index: number
  feature_name: string
  actual_meaning: string
  data_source: string
  feature_category: string | null
  calculation_method: string | null
  used_model: string
}

const DEFAULT_MODEL = '信用债模型'
const fallbackModels = ['信用债模型', '债项主体模型', 'ABS模型', '城投债模型', '城投主体模型', '基金主体模型']

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const error = ref('')
const keyword = ref('')
const selectedModel = ref(DEFAULT_MODEL)
const total = ref(0)
const models = ref<ModelCount[]>(fallbackModels.map(model => ({ label: model, value: model, count: 0 })))
const items = ref<FeatureItem[]>([])

const modelOptions = computed<SelectOption[]>(() =>
  models.value.map(model => ({
    label: `${model.label}（${model.count}）`,
    value: model.value,
  })),
)

const filteredItems = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  if (!text)
    return items.value

  return items.value.filter(item =>
    [
      item.index,
      item.feature_name,
      item.actual_meaning,
      item.feature_category,
      item.calculation_method,
      item.data_source,
    ].some(value => String(value ?? '').toLowerCase().includes(text)),
  )
})

const columns: DataTableColumns<FeatureItem> = [
  {
    title: '序号',
    key: 'index',
    width: 80,
    sorter: 'default',
  },
  {
    title: '特征名',
    key: 'feature_name',
    width: 160,
  },
  {
    title: '实际含义',
    key: 'actual_meaning',
    minWidth: 260,
    render(row) {
      return h('span', row.actual_meaning || '-')
    },
  },
  {
    title: '特征类型',
    key: 'feature_category',
    width: 160,
    render(row) {
      return h('span', row.feature_category || '-')
    },
  },
  {
    title: '计算方式',
    key: 'calculation_method',
    minWidth: 260,
    render(row) {
      return h('span', row.calculation_method || '-')
    },
  },
  {
    title: '数据来源',
    key: 'data_source',
    width: 180,
    render(row) {
      return h('span', row.data_source || '-')
    },
  },
]

const pagination = {
  pageSize: 15,
  showSizePicker: true,
  pageSizes: [10, 15, 30, 50],
}

function getQueryModel(value: unknown) {
  return typeof value === 'string' && value ? value : DEFAULT_MODEL
}

async function fetchFeatures(model: string) {
  loading.value = true
  error.value = ''

  try {
    const response = await request.get('/metadata/features', {
      params: { model },
    })

    if (response.data.status === 'success') {
      models.value = response.data.models
      selectedModel.value = response.data.selected_model
      total.value = response.data.total
      items.value = response.data.items
    }
    else {
      error.value = response.data.message || '指标加载失败'
      items.value = []
      total.value = 0
    }
  }
  catch (err: any) {
    error.value = err.response?.data?.message || err.message || '指标加载失败'
    items.value = []
    total.value = 0
  }
  finally {
    loading.value = false
  }
}

function handleModelUpdate(model: string) {
  if (model === selectedModel.value)
    return

  keyword.value = ''
  router.replace({
    path: '/indicators',
    query: { model },
  })
}

watch(
  () => route.query.model,
  async (queryModel) => {
    const model = getQueryModel(queryModel)
    selectedModel.value = model

    if (queryModel !== model) {
      await router.replace({
        path: '/indicators',
        query: { model },
      })
      return
    }

    await fetchFeatures(model)
  },
  { immediate: true },
)
</script>

<template>
  <div class="mx-auto px-4 py-6 max-w-7xl w-full">
    <n-card title="指标查看" :bordered="false" class="mb-6">
      <div class="gap-4 grid grid-cols-1 lg:grid-cols-[280px_1fr_160px] md:grid-cols-[260px_1fr]">
        <n-select
          :value="selectedModel"
          :options="modelOptions"
          @update:value="handleModelUpdate"
        />
        <n-input
          v-model:value="keyword"
          clearable
          placeholder="搜索特征名、实际含义、特征类型、计算方式或数据来源"
        >
          <template #prefix>
            <div class="i-carbon-search text-gray-500" />
          </template>
        </n-input>
        <div class="text-sm text-gray-700 px-3 rounded bg-gray-50 flex h-9 items-center justify-start dark:text-gray-200 dark:bg-dark-700">
          共 {{ total }} 个指标
        </div>
      </div>
    </n-card>

    <n-card :bordered="false">
      <template #header>
        <div class="flex gap-2 items-center">
          <span>{{ selectedModel }}</span>
          <n-tag size="small" type="info">
            显示 {{ filteredItems.length }} 条
          </n-tag>
        </div>
      </template>

      <n-spin :show="loading">
        <n-alert v-if="error" type="error" class="mb-4" closable>
          {{ error }}
        </n-alert>
        <n-data-table
          :columns="columns"
          :data="filteredItems"
          :bordered="false"
          :single-line="false"
          :pagination="pagination"
          size="small"
          :scroll-x="1100"
        >
          <template #empty>
            <n-empty :description="keyword ? '没有匹配的指标' : '暂无指标数据'" />
          </template>
        </n-data-table>
      </n-spin>
    </n-card>
  </div>
</template>
