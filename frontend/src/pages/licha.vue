<script setup lang="ts">
import type { DataTableColumns } from 'naive-ui'
import request from '~/utils/request'

/** 数据集分类枚举（与后端 VALID_LICHA_DATASETS 一致） */
const DATASET_OPTIONS = [
  '券商债项',
  '银行债项',
  '信用债项',
  '券商主体',
  '银行主体',
  '信用债主体',
  '城投债项',
  '城投主体',
  'ABS专项',
]

/** 生成 2022-01 ~ 2025-07 月份列表 */
const MONTH_OPTIONS: string[] = []
const monthCursor = new Date(2022, 0, 1)
const monthEnd = new Date(2025, 6, 1)
for (let d = monthCursor; d <= monthEnd; d.setMonth(d.getMonth() + 1)) {
  MONTH_OPTIONS.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`)
}

interface LichaResult {
  meta_info: Record<string, string | number>
  metrics: {
    'MAE'?: number
    'RMSE'?: number
    'R²'?: number
    '各评级数量统计'?: Record<string, number>
    [key: string]: any
  }
  bond_list: Array<Record<string, any>>
}

const selectedDataset = ref(DATASET_OPTIONS[6]) // 默认：城投债项
const targetMonth = ref('2023-10')
const loading = ref(false)
const error = ref('')
const result = ref<LichaResult | null>(null)

const ratingStatColumns: DataTableColumns<{ 评级: string, 数量: number }> = [
  { title: '评级', key: '评级', width: 100 },
  {
    title: '数量',
    key: '数量',
    render(row) {
      return h(
        'div',
        { class: 'flex items-center gap-2' },
        [
          h('span', row.数量),
          h('div', { class: 'flex-1 bg-gray-100 rounded-full h-2 dark:bg-dark-700 overflow-hidden' }, [
            h('div', {
              class: 'bg-blue-500 rounded-full h-2 transition-all',
              style: { width: `${Math.min(100, (row.数量 / maxRatingCount.value) * 100)}%` },
            }),
          ]),
        ],
      )
    },
  },
]

const maxRatingCount = computed(() => {
  const counts = result.value?.metrics?.['各评级数量统计']
  if (!counts)
    return 1
  return Math.max(1, ...Object.values(counts))
})

const ratingStatData = computed(() => {
  const counts = result.value?.metrics?.['各评级数量统计'] || {}
  return Object.entries(counts).map(([评级, 数量]) => ({ 评级, 数量 }))
})

/** 代码搜索关键字 */
const searchKeyword = ref('')

/** 按代码搜索过滤后的债券列表 */
const filteredBondList = computed(() => {
  const list = result.value?.bond_list || []
  const kw = searchKeyword.value.trim().toLowerCase()
  if (!kw)
    return list
  return list.filter(row =>
    String(row['代码'] ?? '').toLowerCase().includes(kw),
  )
})

/** CSV 导出 */
function exportCsv() {
  const list = filteredBondList.value
  if (!list.length)
    return

  const cols = ['数据类型', '预测月份', '代码', '预测利差', '评级结果']
  const header = cols.join(',')
  const rows = list.map(row =>
    cols.map(col =>
      row[col] !== undefined && row[col] !== null ? `"${String(row[col]).replace(/"/g, '""')}"` : '',
    ).join(','),
  )
  const csv = [header, ...rows].join('\n')
  const bom = '﻿'
  const blob = new Blob([bom + csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `利差预测_${selectedDataset.value}_${targetMonth.value}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

/** bond_list 固定列：数据类型 → 预测月份 → 代码 → 预测利差 → 评级结果 */
const bondColumns = computed<DataTableColumns<Record<string, any>>>(() => {
  const list = result.value?.bond_list || []
  if (!list.length)
    return []
  const keys = Object.keys(list[0])
  const columnDefs: Array<{ key: string, title: string, width?: number }> = [
    { key: '数据类型', title: '数据类型', width: 110 },
    { key: '预测月份', title: '预测月份', width: 110 },
    { key: '代码', title: '代码', width: 140 },
    { key: '预测利差', title: '预测利差', width: 110 },
    { key: '评级结果', title: '评级结果', width: 100 },
  ]
  return columnDefs
    .filter(col => keys.includes(col.key))
    .map(col => ({
      key: col.key,
      title: col.title,
      width: col.width,
      render(row: Record<string, any>) {
        const value = row[col.key]
        if (col.key === '评级结果') {
          return h('n-tag', { type: getRatingColor(String(value)), size: 'small' }, { default: () => value })
        }
        if (col.key === '预测利差' && typeof value === 'number') {
          return h('span', value.toFixed(4))
        }
        return h('span', value ?? '-')
      },
    }))
})

function getRatingColor(rating: string) {
  const ratingMap: Record<string, string> = {
    'AAA级': 'success',
    'AA+级': 'success',
    'AA级': 'info',
    'A+级': 'info',
    'A级': 'info',
    'BBB级': 'warning',
    'BB级': 'warning',
    'B级': 'error',
    'CCC级': 'error',
    'CC级': 'error',
    'C级': 'error',
  }
  return ratingMap[rating] || 'default'
}

const bondPagination = { pageSize: 10, showSizePicker: true, pageSizes: [10, 20, 50, 100] }

async function handlePredict() {
  loading.value = true
  error.value = ''
  result.value = null
  searchKeyword.value = ''

  try {
    const response = await request.post('/ketiyi/licha', {
      SELECTED_DATASET: selectedDataset.value,
      TARGET_MONTH: targetMonth.value,
    }, {
      headers: { 'Content-Type': 'application/json' },
    })

    if (response.data.status === 'success') {
      result.value = response.data.data
    }
    else {
      error.value = response.data.message || '预测失败，请稍后重试'
    }
  }
  catch (err: any) {
    console.error('Licha prediction error:', err)
    error.value = err.response?.data?.message || err.message || '预测失败，请稍后重试'
  }
  finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="mx-auto px-4 py-6 max-w-7xl w-full">
    <n-card title="利差预测" :bordered="false" class="mb-6">
      <p class="text-gray-700 mb-4 dark:text-gray-300">
        选择数据集分类与预测月份，基于历史数据训练 GBDT 模型预测信用利差，并推演中文评级分布。
      </p>

      <div class="gap-4 grid grid-cols-1 items-end md:grid-cols-[240px_180px_auto]">
        <div class="space-y-1">
          <div class="text-sm text-gray-500 dark:text-gray-400">
            数据集分类
          </div>
          <n-select v-model:value="selectedDataset" :options="DATASET_OPTIONS.map(v => ({ label: v, value: v }))" />
        </div>
        <div class="space-y-1">
          <div class="text-sm text-gray-500 dark:text-gray-400">
            预测月份
          </div>
          <n-select v-model:value="targetMonth" :options="MONTH_OPTIONS.map(v => ({ label: v, value: v }))" />
        </div>
        <n-button type="primary" :loading="loading" @click="handlePredict">
          <template #icon>
            <div class="i-carbon-predictive-analysis" />
          </template>
          开始预测
        </n-button>
      </div>

      <n-alert v-if="error" type="error" class="mt-4" closable>
        {{ error }}
      </n-alert>
    </n-card>

    <n-spin :show="loading">
      <div v-if="result" class="space-y-6">
        <!-- 1. 预测信息 -->
        <n-card title="预测信息" :bordered="false">
          <n-descriptions :column="3" bordered size="small">
            <n-descriptions-item v-for="(value, key) in result.meta_info" :key="key" :label="key">
              {{ value }}
            </n-descriptions-item>
          </n-descriptions>
        </n-card>

        <!-- 2. 预测效果 -->
        <n-card title="预测效果" :bordered="false">
          <div class="gap-4 grid grid-cols-1 sm:grid-cols-3">
            <n-statistic v-if="result.metrics.MAE !== undefined" label="MAE 平均绝对误差" :value="result.metrics.MAE" />
            <n-statistic v-if="result.metrics.RMSE !== undefined" label="RMSE 均方根误差" :value="result.metrics.RMSE" />
            <n-statistic v-if="result.metrics['R²'] !== undefined" label="R² 决定系数" :value="result.metrics['R²']" />
          </div>

          <n-divider v-if="ratingStatData.length" />
          <div v-if="ratingStatData.length">
            <div class="text-sm text-gray-500 mb-3 dark:text-gray-400">
              各评级数量统计
            </div>
            <n-data-table
              :columns="ratingStatColumns"
              :data="ratingStatData"
              :bordered="false"
              size="small"
              :max-height="300"
            />
          </div>
        </n-card>

        <!-- 3. 预测结果（债券明细） -->
        <n-card title="预测结果" :bordered="false">
          <template #header-extra>
            <div class="flex gap-2 items-center">
              <n-input
                v-model:value="searchKeyword"
                clearable
                placeholder="搜索代码..."
                size="small"
                class="w-45"
              >
                <template #prefix>
                  <div class="i-carbon-search text-gray-500" />
                </template>
              </n-input>
              <n-button
                size="small"
                type="primary"
                secondary
                :disabled="!filteredBondList.length"
                @click="exportCsv"
              >
                <template #icon>
                  <div class="i-carbon-download" />
                </template>
                CSV
              </n-button>
              <n-tag size="small" type="info">
                共 {{ filteredBondList.length }} / {{ result.bond_list.length }} 只
              </n-tag>
            </div>
          </template>
          <n-data-table
            :columns="bondColumns"
            :data="filteredBondList"
            :bordered="false"
            :single-line="false"
            :pagination="bondPagination"
            size="small"
          >
            <template #empty>
              <n-empty description="暂无预测数据" />
            </template>
          </n-data-table>
        </n-card>
      </div>

      <n-empty v-else-if="!error" description="选择参数后点击「开始预测」" class="py-12" />
    </n-spin>
  </div>
</template>
