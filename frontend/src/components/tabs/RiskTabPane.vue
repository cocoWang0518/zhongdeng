<!-- eslint-disable vue/no-use-v-if-with-v-for -->
<script setup lang="ts">
// 定义风险指标解释的类型
interface RiskExplainItem {
  '中文名称': string
  '含义说明': string
  '理想范围/判断标准': string
}

interface RiskExplainType {
  [key: string]: RiskExplainItem
}

// 定义props
interface Props {
  riskText?: Record<string, string | number | any[]>
  riskExplain: RiskExplainType
  industryRiskAnalysisColumns: any[]
}

const props = defineProps<Props>()

const metricEntries = computed(() => {
  if (!props.riskText)
    return []

  return Object.entries(props.riskText).filter(([key]) => {
    return key !== '行业风险分析' && key !== '分类报告'
  })
})

const classificationReportRows = computed(() => {
  const report = props.riskText?.分类报告
  if (Array.isArray(report))
    return report

  return []
})

const classificationReportColumns = [
  {
    title: '类别',
    key: '类别',
  },
  {
    title: '精确率',
    key: '精确率',
  },
  {
    title: '召回率',
    key: '召回率',
  },
  {
    title: 'F1 得分',
    key: 'F1 得分',
  },
  {
    title: '样本数',
    key: '样本数',
  },
]
</script>

<template>
  <div>
    <div v-if="riskText" class="whitespace-pre-wrap">
      <n-descriptions label-placement="left" title="模型评估" :column="2" bordered>
        <template v-for="[key, value] in metricEntries" :key="key">
          <n-descriptions-item>
            <template #label>
              <n-tooltip v-if="riskExplain[key]?.含义说明" trigger="hover">
                <template #trigger>
                  <span class="cursor-help">{{ riskExplain[key]?.中文名称 ? `${riskExplain[key]?.中文名称}(${key})` : key }}</span>
                </template>
                {{ riskExplain[key]?.含义说明 }}
              </n-tooltip>
              <span v-else>{{ riskExplain[key]?.中文名称 ? `${riskExplain[key]?.中文名称}(${key})` : key }}</span>
            </template>
            <div class="risk-value-container">
              <div class="risk-actual-value">
                {{ value }}
              </div>
              <div v-if="riskExplain[key]?.['理想范围/判断标准']" class="risk-standard text-xs text-gray-500 mt-1">
                {{ riskExplain[key]['理想范围/判断标准'] }}
              </div>
            </div>
          </n-descriptions-item>
        </template>
      </n-descriptions>

      <p v-if="classificationReportRows.length > 0" class="text-sm text-gray-500 mt-3">
        指标取值为0～1；精确率、召回率和F1按样本数加权，逐评级结果见下方分类报告。
      </p>

      <n-card v-if="classificationReportRows.length > 0" title="分类报告" class="mt-4" :bordered="false">
        <n-data-table
          :data="classificationReportRows"
          :columns="classificationReportColumns"
          :bordered="false"
          :single-line="false"
          size="small"
        />
      </n-card>

      <n-card v-if="riskText['行业风险分析']" title="行业风险分析" class="mt-4" :bordered="false">
        <n-data-table :data="riskText['行业风险分析'] as any" :columns="industryRiskAnalysisColumns" />
      </n-card>
    </div>
    <n-empty v-else description="暂无模型评估" />
  </div>
</template>

<style scoped>
.risk-value-container {
  display: flex;
  flex-direction: column;
}

.risk-actual-value {
  font-weight: 500;
}

.cursor-help {
  cursor: help;
  border-bottom: 1px dashed #ccc;
}
</style>
