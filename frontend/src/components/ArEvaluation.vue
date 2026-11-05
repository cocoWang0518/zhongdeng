<script setup lang="ts">
import type { UploadFileInfo } from 'naive-ui'
import { computed, ref, watch } from 'vue'
import request from '~/utils/request'

interface MonthlyAr {
  month: string
  N: number
  N_default_1y: number
  N_nondefault_1y: number
  default_rate_1y: number
  AR_CAP: number | null
  AUC: number | null
  valid_AR: boolean
  reason: string
}

interface ArResult {
  summary: {
    overall_ar: number | null
    overall_method: string
    valid_months: number
    total_months: number
    sample_count: number
    subject_count: number
    data_end: string
    mean_auc: number | null
  }
  monthly: MonthlyAr[]
  warnings: string[]
  cleaning: {
    input_rows: number
    missing_rows: number
    duplicate_rows: number
    already_defaulted_rows: number
    incomplete_window_rows: number
  }
}

const file = ref<File | null>(null)
const fileList = ref<UploadFileInfo[]>([])
const dataEnd = ref('2025-09-01')
const idCol = ref('stkcd')
const dateCol = ref('ym')
const ratingCol = ref('信用评级')
const defaultDateCol = ref('首次违约日期')
const loading = ref(false)
const error = ref('')
const result = ref<ArResult | null>(null)
const validOnly = ref(true)

watch([file, dataEnd, idCol, dateCol, ratingCol, defaultDateCol], () => {
  result.value = null
  error.value = ''
})

const visibleMonths = computed(() => result.value?.monthly.filter(row => !validOnly.value || row.valid_AR) || [])
function formatNumber(value: number | null) {
  return value === null ? '无法计算' : value.toFixed(6)
}
const columns = [
  { title: '评级月份', key: 'month', width: 110 },
  { title: '样本数', key: 'N', width: 90 },
  { title: '一年内违约数', key: 'N_default_1y', width: 120 },
  { title: '非违约数', key: 'N_nondefault_1y', width: 100 },
  { title: 'AR值', key: 'AR_CAP', width: 125, render: (row: MonthlyAr) => formatNumber(row.AR_CAP) },
  { title: 'AUC', key: 'AUC', width: 125, render: (row: MonthlyAr) => formatNumber(row.AUC) },
  { title: '说明', key: 'reason', width: 220, render: (row: MonthlyAr) => row.valid_AR ? '有效' : row.reason },
]

function handleUpload(options: { fileList: UploadFileInfo[] }) {
  fileList.value = options.fileList
  file.value = options.fileList[0]?.file || null
}

async function calculate() {
  error.value = ''
  result.value = null
  if (!file.value) {
    error.value = '请先上传评级结果文件'
    return
  }
  if (!dataEnd.value || !idCol.value.trim() || !dateCol.value.trim() || !ratingCol.value.trim() || !defaultDateCol.value.trim()) {
    error.value = '请填写截止日期和四个字段名称'
    return
  }
  const payload = new FormData()
  payload.append('file', file.value)
  payload.append('data_end', dataEnd.value)
  payload.append('id_col', idCol.value.trim())
  payload.append('date_col', dateCol.value.trim())
  payload.append('rating_col', ratingCol.value.trim())
  payload.append('default_date_col', defaultDateCol.value.trim())
  loading.value = true
  try {
    const response = await request.post('/ar/calculate', payload, { timeout: 120000 })
    if (response.data.status !== 'success')
      throw new Error(response.data.message || 'AR计算失败')
    result.value = response.data.data
  }
  catch (err: any) {
    error.value = err.response?.data?.message || err.message || 'AR计算失败，请稍后重试'
  }
  finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <n-alert type="info" :show-icon="false" class="mb-4">
      上传主体评级结果即可计算，无需上传模型。总体AR为有效月份AR的等权平均；各月按未来一年内是否首次违约计算。
      文件应包含主体代码、评级月份、信用评级、首次违约日期，未违约日期留空。Excel读取第一个工作表。
    </n-alert>
    <n-form label-placement="top">
      <n-form-item label="评级结果文件（.xlsx / .csv / .parquet，不超过50MB）">
        <n-upload
          :file-list="fileList" :default-upload="false" :max="1"
          accept=".xlsx,.csv,.parquet" :disabled="loading" @change="handleUpload"
        >
          <n-button :disabled="loading">
            选择评级结果文件
          </n-button>
        </n-upload>
      </n-form-item>
      <n-form-item label="违约数据截止日期">
        <input v-model="dataEnd" type="date" :disabled="loading" class="px-3 py-2 border rounded dark:bg-gray-800">
        <span class="text-sm text-gray-500 ml-3">只纳入具备完整未来一年观察窗口的评级记录。</span>
      </n-form-item>
      <n-collapse class="mb-4">
        <n-collapse-item title="字段设置（文件列名不同时修改）" name="columns">
          <div class="gap-3 grid grid-cols-1 sm:grid-cols-2">
            <n-form-item label="主体代码列">
              <n-input v-model:value="idCol" :disabled="loading" />
            </n-form-item>
            <n-form-item label="评级月份列">
              <n-input v-model:value="dateCol" :disabled="loading" />
            </n-form-item>
            <n-form-item label="信用评级列">
              <n-input v-model:value="ratingCol" :disabled="loading" />
            </n-form-item>
            <n-form-item label="首次违约日期列">
              <n-input v-model:value="defaultDateCol" :disabled="loading" />
            </n-form-item>
          </div>
        </n-collapse-item>
      </n-collapse>
      <n-button type="primary" :loading="loading" @click="calculate">
        计算AR值
      </n-button>
    </n-form>

    <n-alert v-if="error" type="error" class="mt-4">
      {{ error }}
    </n-alert>
    <div v-if="result" class="mt-5 space-y-4">
      <n-alert v-for="warning in result.warnings" :key="warning" type="warning">
        {{ warning }}
      </n-alert>
      <div class="gap-4 grid grid-cols-1 sm:grid-cols-3">
        <n-statistic label="总体AR值（有效月份等权平均）" :value="formatNumber(result.summary.overall_ar)" />
        <n-statistic label="有效AR月份数" :value="`${result.summary.valid_months} / ${result.summary.total_months}`" />
        <n-statistic label="有效月份平均AUC" :value="formatNumber(result.summary.mean_auc)" />
      </div>
      <p class="text-sm text-gray-500">
        截止日期：{{ result.summary.data_end }}；纳入{{ result.summary.subject_count }}个主体、{{ result.summary.sample_count }}条主体月度记录。
        AR按系数展示，取值范围为-1至1。
      </p>
      <p class="text-sm text-gray-500">
        原始{{ result.cleaning.input_rows }}条；缺失或无效主体/月/评级剔除{{ result.cleaning.missing_rows }}条；
        重复去除{{ result.cleaning.duplicate_rows }}条；评级时已违约剔除{{ result.cleaning.already_defaulted_rows }}条；
        观察窗口不足一年剔除{{ result.cleaning.incomplete_window_rows }}条。
      </p>
      <div class="flex gap-3 items-center">
        <span>各月AR值</span>
        <n-switch v-model:value="validOnly" />
        <span class="text-sm text-gray-500">仅显示有效月份</span>
      </div>
      <n-data-table :columns="columns" :data="visibleMonths" :pagination="{ pageSize: 12 }" :scroll-x="890" :max-height="420" />
    </div>
  </div>
</template>
