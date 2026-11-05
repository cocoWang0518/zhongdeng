<script setup lang="ts">
import { NButton, NTooltip } from 'naive-ui'
import { computed, h, ref } from 'vue'

import RiskTabPane from './tabs/RiskTabPane.vue'
import TableTabPane from './tabs/TableTabPane.vue'

interface QinghuaItem {
  name: string
  definition: string
}

interface QinghuaExplainType {
  [key: string]: QinghuaItem
}

interface RiskExplainItem {
  '中文名称': string
  '含义说明': string
  '理想范围/判断标准': string
}

interface RiskExplainType {
  [key: string]: RiskExplainItem
}

interface Props {
  downloadResult?: string
  tableData?: string
  riskText?: Record<string, string | number | any[]>
  testInfo?: Record<string, string | number>
  datasetUrl?: string
}

const props = defineProps<Props>()

const { state: typedQinghuaExplain } = useAsyncState<QinghuaExplainType>(() => {
  return fetch('/const/qinghua.json').then(res => res.json())
}, {})

const { state: typedRiskExplain } = useAsyncState<RiskExplainType>(() => {
  return fetch('/const/risk_explain.json').then(res => res.json())
}, {})

const current = ref(1)
const activeTab = ref('table')

const hasResults = computed(() => {
  return props.downloadResult || (props.tableData && props.tableData.length > 0)
})

const testInfoEntries = computed(() => {
  return Object.entries(props.testInfo || {}).map(([label, value]) => ({ label, value }))
})

const hasTestInfo = computed(() => testInfoEntries.value.length > 0)

const parsedData = computed(() => {
  if (!props.tableData)
    return []

  const rows = props.tableData.trim().split('\n')
  if (rows.length === 0)
    return []

  const headers = rows[0].split(',')

  return rows.slice(1).map((row) => {
    const values = row.split(',')
    const rowData: Record<string, string> = {}

    headers.forEach((header, index) => {
      rowData[header] = values[index] || ''
    })

    return rowData
  })
})

const columns = computed(() => {
  if (!props.tableData)
    return []

  const headers = props.tableData.trim().split('\n')[0].split(',')
  return headers.map<any>((header) => {
    const qinghuaItem = typedQinghuaExplain.value?.[header.trim()]

    if (qinghuaItem && qinghuaItem.name) {
      return {
        title: () => {
          if (qinghuaItem.definition) {
            return h(
              'div',
              {
                class: 'cursor-help',
                style: 'border-bottom: 1px dashed #ccc;',
              },
              [
                h(
                  NTooltip,
                  { trigger: 'hover' },
                  {
                    default: () => qinghuaItem.definition,
                    trigger: () => qinghuaItem.name,
                  },
                ),
              ],
            )
          }

          return h('span', qinghuaItem.name)
        },
        key: header,
      }
    }

    return {
      title: header,
      key: header,
    }
  })
})

const industryRiskAnalysisColumns = computed(() => [
  {
    title: '行业',
    key: '行业',
  },
  {
    title: '样本数',
    key: '样本数',
  },
  {
    title: '行业R²',
    key: '行业R²',
  },
  {
    title: '行业最大误差',
    key: '行业最大误差',
  },
  {
    title: '行业风险溢价',
    key: '行业风险溢价',
  },
])

const tableRows = computed(() => parsedData.value)

function handlePageChange(page: number) {
  current.value = page
}
</script>

<template>
  <div class="w-full">
    <n-card v-if="hasResults" title="预测结果" class="mt-4">
      <template #header-extra>
        <div class="flex gap-2">
          <NButton
            v-if="downloadResult"
            tag="a"
            :href="downloadResult"
            target="_blank"
            download
            size="small"
            type="primary"
          >
            下载结果
          </NButton>
          <NButton
            v-if="datasetUrl"
            tag="a"
            :href="datasetUrl"
            target="_blank"
            download
            size="small"
            type="primary"
          >
            下载原数据集
          </NButton>
        </div>
      </template>

      <n-tabs v-model:value="activeTab" animated>
        <n-tab-pane v-if="hasTestInfo" name="test-info" tab="测试信息">
          <div class="gap-4 grid grid-cols-2 lg:grid-cols-4 md:grid-cols-3">
            <div v-for="item in testInfoEntries" :key="item.label" class="space-y-1">
              <div class="text-sm text-gray-500 dark:text-gray-400">
                {{ item.label }}
              </div>
              <div class="text-gray-800 font-medium dark:text-gray-200">
                {{ item.value }}
              </div>
            </div>
          </div>
        </n-tab-pane>

        <n-tab-pane name="table" tab="数据表格">
          <TableTabPane
            :parsed-data="tableRows"
            :columns="columns"
            :loading="false"
            :current="current"
            :on-page-change="handlePageChange"
          />
        </n-tab-pane>

        <n-tab-pane name="risk" tab="模型评估">
          <RiskTabPane
            :risk-text="riskText"
            :risk-explain="typedRiskExplain"
            :industry-risk-analysis-columns="industryRiskAnalysisColumns"
          />
        </n-tab-pane>
      </n-tabs>
    </n-card>

    <n-empty v-else description="请提交预测请求获取结果" />
  </div>
</template>
