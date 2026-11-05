<script setup lang="ts">
import type { DataTableColumn } from 'naive-ui'
import { NDataTable, NTooltip } from 'naive-ui'
import { computed, h, ref } from 'vue'

// Define props
interface Props {
  csvFile: File | null
}

const props = defineProps<Props>()

// State
const csvContent = ref('')
const loading = ref(false)

// Parse the CSV file when the component loads
function parseCsvFile() {
  if (!props.csvFile)
    return

  loading.value = true
  const reader = new FileReader()

  reader.onload = (e) => {
    const content = e.target?.result as string
    if (content) {
      csvContent.value = content
    }
    loading.value = false
  }

  reader.onerror = () => {
    loading.value = false
  }

  reader.readAsText(props.csvFile)
}

// Parse CSV content into an array of objects for the table
const parsedData = computed(() => {
  if (!csvContent.value)
    return []

  // Split CSV into rows and parse
  const rows = csvContent.value.trim().split('\n')
  if (rows.length === 0)
    return []

  // Get headers from first row
  const headers = rows[0].split(',')

  // Parse the rest of the rows
  return rows.slice(1).map((row) => {
    const values = row.split(',')
    const rowData: Record<string, string> = {}

    headers.forEach((header, index) => {
      rowData[header] = values[index] || ''
    })

    return rowData
  })
})

const financialMetrics = {
  name: {
    name: '名称',
    definition: '',
  },
  stkcd: {
    name: '股票代码',
    definition: '',
  },
  date: {
    name: '日期',
    definition: '',
  },
  returnAN: {
    name: '年化收益率（%）',
    definition: '（年度收益率）/（天数/365）×100%',
  },
  rawdownMax: {
    name: '最大回撤（%）',
    definition: '（最大峰值-最低值）/最大峰值 ×100%',
  },
  sharpAN: {
    name: '年化夏普比率',
    definition: '夏普比率 = (组合年化收益率 - 无风险利率) / 年化波动率',
  },
  varianceAN: {
    name: '收益率的波动率',
    definition: '上一年度日度收益率的方差',
  },
  pe: {
    name: '市盈率',
    definition: '股价/每股收益',
  },
  pb: {
    name: '市净率',
    definition: '股价/每股净资产',
  },
  floating_market_val: {
    name: '流动市值',
    definition: '流动市值的自然对数',
  },
  var95: {
    name: '在险价值5%分位',
    definition: '95%置信水平的在险价值（Value at Risk），252日滚动窗口',
  },
  var99: {
    name: '在险价值1%分位',
    definition: '99%置信水平的在险价值（Value at Risk），252日滚动窗口',
  },
  volatility: {
    name: '波动率',
    definition: '日度收益率的方差，252滚动窗口',
  },
  mVaR: {
    name: '边际VaR',
    definition: '通过求解投资组合（全市场股票等权）对每个资产权重的偏导数计算',
  },
  es95: {
    name: '股票ES95',
    definition: '95%置信水平下的期望损失，历史数据法，252日滚动窗口',
  },
  es99: {
    name: '股票ES99',
    definition: '99%置信水平下的期望损失，历史数据法，252日滚动窗口',
  },
}

// 注意：部分字段根据上下文进行了格式修正和内容补全（如夏普比率公式、t_Val字段处理等）
// 原始数据中"oatingmarke"疑似拼写错误，建议确认应为"floatingMarket"或类似表达

// Create a custom column header with tooltip
function createColumnHeader(name: string, definition?: string) {
  if (!definition) {
    return name
  }

  return h(
    'div',
    { class: 'column-header-with-tooltip' },
    [
      h(NTooltip, {
        placement: 'top',
        trigger: 'hover',
      }, {
        trigger: () => h('span', { class: 'header-with-info' }, [
          name,
          h('div', { class: 'info-icon ml-1' }, '?'),
        ]),
        default: () => definition,
      }),
    ],
  )
}

// Compute table columns from the CSV headers
const columns = computed(() => {
  if (!csvContent.value)
    return []

  // Get headers from first row of CSV
  const headers = csvContent.value.trim().split('\n')[0].split(',')

  return headers.map((header) => {
    const trimHeader = header.trim()
    if (!trimHeader) {
      return {
        title: '序号',
        key: '',
      } as DataTableColumn
    }

    const metricKey = trimHeader as keyof typeof financialMetrics
    if (Object.keys(financialMetrics).includes(trimHeader)) {
      const metric = financialMetrics[metricKey]

      return {
        title: createColumnHeader(metric.name || trimHeader, metric.definition),
        key: header,
      } as DataTableColumn
    }
    else {
      return {
        title: trimHeader,
        key: header,
      } as DataTableColumn
    }
  })
})

// Call the parse function when the component is mounted
if (props.csvFile) {
  parseCsvFile()
}
</script>

<template>
  <div class="special-result-container">
    <n-card title="预测结果" class="mt-4">
      <div class="csv-table">
        <n-spin :show="loading">
          <NDataTable
            v-if="parsedData.length > 0"
            :columns="columns"
            :data="parsedData"
            :bordered="false"
            :single-line="false"
            size="small"
            :pagination="{
              pageSize: 10,
            }"
          />
          <n-empty v-else description="无数据或正在加载..." />
        </n-spin>
      </div>
    </n-card>
  </div>
</template>

<style scoped>
.special-result-container {
  margin-top: 20px;
}

.csv-table {
  margin-top: 16px;
}

.column-header-with-tooltip {
  display: flex;
  align-items: center;
}

.header-with-info {
  display: inline-flex;
  align-items: center;
  cursor: help;
}

.info-icon {
  font-size: 12px;
  color: #2080f0;
  margin-left: 4px;
  opacity: 0.8;
  display: inline-flex;
  justify-content: center;
  align-items: center;
  min-width: 14px;
  height: 14px;
  border-radius: 50%;
  background-color: #e8f4ff;
  border: 1px solid #2080f0;
}

/* This styling will apply to the content inside the tooltip */
:deep(.n-tooltip) {
  max-width: 300px;
  font-size: 13px;
  line-height: 1.5;
}
</style>
