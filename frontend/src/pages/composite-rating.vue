<script setup lang="ts">
import type { DataTableColumns } from 'naive-ui'
import request from '~/utils/request'

interface RatedBond {
  code: string | number | null
  spread: number
  rating: string
}

interface RatingResult {
  dataset: string
  month: string
  training_window: string
  distribution: Array<{ rating: string, count: number }>
  bonds: RatedBond[]
}

const endpoint = '/ketiyi/composite-rating'
const dataset = ref<string | null>(null)
const month = ref<string | null>(null)
const datasets = ref<string[]>([])
const months = ref<string[]>([])
const result = ref<RatingResult | null>(null)
const loadingOptions = ref(true)
const rating = ref(false)
const error = ref('')

const columns: DataTableColumns<RatedBond> = [
  { title: '代码', key: 'code' },
  { title: '预测利差', key: 'spread', render: row => row.spread.toFixed(4) },
  { title: '综合评级', key: 'rating' },
]
const pagination = { pageSize: 10, showSizePicker: true, pageSizes: [10, 20, 50] }
const chartStep = computed(() => {
  const max = Math.max(1, ...(result.value?.distribution.map(item => item.count) ?? []))
  return Math.ceil(max / 4)
})

function formatMonth(value: string) {
  const [year, monthNumber] = value.split('-')
  return `${year}年${Number(monthNumber)}月`
}

async function loadOptions() {
  loadingOptions.value = true
  error.value = ''
  try {
    const { data } = await request.get(`${endpoint}/options`, {
      params: { dataset: dataset.value },
    })
    if (dataset.value) {
      months.value = data.months
    }
    else {
      datasets.value = data.datasets
    }
  }
  catch {
    error.value = '读取评级选项失败，请重试。'
  }
  finally {
    loadingOptions.value = false
  }
}

function changeDataset(value: string) {
  dataset.value = value
  month.value = null
  months.value = []
  result.value = null
  void loadOptions()
}

async function loadRating(value: string) {
  month.value = value
  rating.value = true
  error.value = ''
  result.value = null
  try {
    const { data } = await request.get<RatingResult>(endpoint, {
      params: { dataset: dataset.value, month: value },
    })
    result.value = data
  }
  catch (err: any) {
    error.value = err.response?.data?.message || '生成综合评级失败，请重试。'
  }
  finally {
    rating.value = false
  }
}

function retry() {
  if (month.value)
    void loadRating(month.value)
  else
    void loadOptions()
}

onMounted(loadOptions)
</script>

<template>
  <div class="mx-auto px-4 py-6 max-w-7xl w-full space-y-6">
    <n-card title="综合评级" :bordered="false">
      <p class="mb-4">
        综合评级以利差预测为依据，分类模型结果可在「信用评级」中作为辅助参考。
      </p>
      <div class="gap-4 grid sm:grid-cols-[240px_240px]">
        <div>
          <div class="text-sm mb-1">
            债券类型
          </div>
          <n-select
            :value="dataset"
            :options="datasets.map(value => ({ label: value, value }))"
            :disabled="loadingOptions || rating"
            placeholder="请选择债券类型"
            @update:value="changeDataset"
          />
        </div>
        <div>
          <div class="text-sm mb-1">
            评级月份
          </div>
          <n-select
            :value="month"
            :options="months.map(value => ({ label: formatMonth(value), value }))"
            :loading="loadingOptions && !!dataset"
            :disabled="!months.length || loadingOptions || rating"
            :placeholder="dataset && !loadingOptions && !months.length && !error ? '暂无可评级月份' : '请选择年份和月份'"
            @update:value="loadRating"
          />
        </div>
      </div>
      <n-alert v-if="error" type="error" class="mt-4">
        {{ error }}
        <n-button size="small" class="ml-2" @click="retry">
          重试
        </n-button>
      </n-alert>
    </n-card>

    <n-card v-if="rating" :bordered="false">
      <n-spin size="small" />
      <span class="ml-2">正在生成 {{ dataset }} {{ formatMonth(month!) }}的综合评级…</span>
    </n-card>

    <template v-if="result">
      <n-card title="月度评级分布" :bordered="false">
        <p class="text-sm mb-2">
          {{ result.dataset }} · {{ formatMonth(result.month) }} · 共 {{ result.bonds.length }} 条样本
        </p>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          按该类型当月预测利差的百分位划分等级。各柱显示实际样本数量。
        </p>
        <div class="overflow-x-auto">
          <svg
            viewBox="0 0 800 275"
            class="w-full min-w-150 max-w-230"
            role="img"
            :aria-label="result.distribution.map(item => `${item.rating} ${item.count} 条`).join('，')"
          >
            <text x="14" y="20" fill="currentColor" font-size="12">样本数</text>
            <g v-for="tick in 5" :key="tick">
              <line x1="60" x2="786" :y1="235 - (tick - 1) * 47" :y2="235 - (tick - 1) * 47" stroke="currentColor" opacity="0.18" />
              <text x="52" :y="239 - (tick - 1) * 47" text-anchor="end" fill="currentColor" font-size="12">
                {{ (tick - 1) * chartStep }}
              </text>
            </g>
            <g v-for="(item, index) in result.distribution" :key="item.rating" :transform="`translate(${93 + index * 66} 0)`">
              <title>{{ item.rating }} · {{ item.count }} 条</title>
              <rect x="-19" :y="235 - item.count / chartStep * 47" width="38" :height="item.count / chartStep * 47" rx="3" fill="#3478da" />
              <text :y="227 - item.count / chartStep * 47" text-anchor="middle" fill="currentColor" font-size="12">
                {{ item.count }}
              </text>
              <text y="257" text-anchor="middle" fill="currentColor" font-size="12">
                {{ item.rating }}
              </text>
            </g>
          </svg>
        </div>
      </n-card>
      <n-card title="综合评级明细" :bordered="false">
        <p class="text-sm text-gray-500 mb-3 dark:text-gray-400">
          利差模型训练窗口 {{ result.training_window }}
        </p>
        <n-data-table :columns="columns" :data="result.bonds" :pagination="pagination" size="small" />
      </n-card>
    </template>
    <n-empty v-else-if="!rating && !error" description="选择债券类型和月份后查看评级分布" class="py-12" />
  </div>
</template>
