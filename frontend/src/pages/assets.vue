<script setup lang="ts">
import type { DataTableColumns, SelectOption } from 'naive-ui'
import { computed, h, ref, watch } from 'vue'
import request from '~/utils/request'

interface ModelCount {
  label: string
  value: string
  count: number
}

interface AssetItem {
  id: number
  index: number
  资产代码: string
  资产名称: string
  适用模型: string
}

const DEFAULT_MODEL = '信用债模型'
const fallbackModels = ['信用债模型', '债项主体模型', 'ABS模型', '城投债模型', '城投主体模型', '基金模型', '基金主体模型', '保险主体模型', '保险债项模型', '券商主体模型', '券商债项模型', '银行主体模型', '银行债项模型']

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const error = ref('')
const keyword = ref('')
const selectedModel = ref(DEFAULT_MODEL)
const total = ref(0)
const models = ref<ModelCount[]>(fallbackModels.map(model => ({ label: model, value: model, count: 0 })))
const items = ref<AssetItem[]>([])

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
      item.资产代码,
      item.资产名称,
      item.适用模型,
    ].some(value => String(value ?? '').toLowerCase().includes(text)),
  )
})

const columns: DataTableColumns<AssetItem> = [
  {
    title: '序号',
    key: 'index',
    width: 80,
    sorter: 'default',
  },
  {
    title: '资产代码',
    key: '资产代码',
    width: 180,
  },
  {
    title: '资产名称',
    key: '资产名称',
    minWidth: 260,
    render(row) {
      return h('span', row.资产名称 || '-')
    },
  },
  {
    title: '适用模型',
    key: '适用模型',
    width: 160,
  },
]

const pagination = {
  defaultPageSize: 15,
  showSizePicker: true,
  pageSizes: [10, 15, 30, 50],
}

function getQueryModel(value: unknown) {
  return typeof value === 'string' && value ? value : DEFAULT_MODEL
}

async function fetchAssets(model: string) {
  loading.value = true
  error.value = ''

  try {
    const response = await request.get('/metadata/assets', {
      params: { model },
    })

    if (response.data.status === 'success') {
      models.value = response.data.models
      selectedModel.value = response.data.selected_model
      total.value = response.data.total
      items.value = response.data.items
    }
    else {
      error.value = response.data.message || '资产加载失败'
      items.value = []
      total.value = 0
    }
  }
  catch (err: any) {
    error.value = err.response?.data?.message || err.message || '资产加载失败'
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
    path: '/assets',
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
        path: '/assets',
        query: { model },
      })
      return
    }

    await fetchAssets(model)
  },
  { immediate: true },
)
</script>

<template>
  <div class="mx-auto px-4 py-6 max-w-7xl w-full">
    <n-card title="资产查看" :bordered="false" class="mb-6">
      <div class="gap-4 grid grid-cols-1 lg:grid-cols-[280px_1fr_160px] md:grid-cols-[260px_1fr]">
        <n-select
          :value="selectedModel"
          :options="modelOptions"
          @update:value="handleModelUpdate"
        />
        <n-input
          v-model:value="keyword"
          clearable
          placeholder="搜索资产代码、资产名称或适用模型"
        >
          <template #prefix>
            <div class="i-carbon-search text-gray-500" />
          </template>
        </n-input>
        <div class="text-sm text-gray-700 px-3 rounded bg-gray-50 flex h-9 items-center justify-start dark:text-gray-200 dark:bg-dark-700">
          共 {{ total }} 个资产
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
          :scroll-x="760"
        >
          <template #empty>
            <n-empty :description="keyword ? '没有匹配的资产' : '暂无资产数据'" />
          </template>
        </n-data-table>
      </n-spin>
    </n-card>
  </div>
</template>
