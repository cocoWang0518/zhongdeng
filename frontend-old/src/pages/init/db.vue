<script setup lang="ts">
import type { DataTableColumns, DataTableRowKey } from 'naive-ui'
import { NButton, NTag } from 'naive-ui'
import { computed, h, onBeforeUnmount, onMounted, ref } from 'vue'
import request from '~/utils/request'

interface SqlScript {
  index: number
  name: string
  size: number
  modified_at: string
  is_empty: boolean
}

interface DbJob {
  id: string
  action: 'run_sql' | 'clear_db'
  filename: string | null
  filenames: string[]
  completed_filenames: string[]
  database: string
  status: 'running' | 'success' | 'error' | 'canceled'
  message: string
  started_at: string
  finished_at: string | null
  cancel_requested: boolean
  pid: number | null
  return_code: number | null
  log_tail: string
}

const loading = ref(false)
const actionLoading = ref(false)
const error = ref('')
const database = ref('')
const scripts = ref<SqlScript[]>([])
const selectedScriptNames = ref<DataTableRowKey[]>([])
const currentJob = ref<DbJob | null>(null)
let pollTimer: ReturnType<typeof setInterval> | undefined

const isJobRunning = computed(() => currentJob.value?.status === 'running')
const currentJobId = computed(() => currentJob.value?.id)
const selectedFilenameSet = computed(() => new Set(selectedScriptNames.value.map(String)))
const selectedFilenames = computed(() => {
  return scripts.value
    .filter(script => selectedFilenameSet.value.has(script.name))
    .map(script => script.name)
})
const selectedFilenameCount = computed(() => selectedFilenames.value.length)

const columns: DataTableColumns<SqlScript> = [
  {
    type: 'selection',
    disabled: () => isJobRunning.value,
  },
  {
    title: '序号',
    key: 'index',
    width: 80,
    sorter: 'default',
  },
  {
    title: 'SQL 文件',
    key: 'name',
    minWidth: 260,
  },
  {
    title: '大小',
    key: 'size',
    width: 140,
    render(row) {
      return formatBytes(row.size)
    },
  },
  {
    title: '修改时间',
    key: 'modified_at',
    width: 210,
    render(row) {
      return formatDate(row.modified_at)
    },
  },
  {
    title: '状态',
    key: 'status',
    width: 120,
    render(row) {
      const status = getScriptStatus(row)
      return h(
        NTag,
        {
          size: 'small',
          type: status.type,
          bordered: false,
        },
        { default: () => status.label },
      )
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    fixed: 'right',
    render(row) {
      const isRunningThisFile = currentJob.value?.action === 'run_sql'
        && currentJob.value.filename === row.name
        && currentJob.value.status === 'running'

      return h(
        NButton,
        {
          size: 'small',
          type: 'primary',
          secondary: true,
          disabled: isJobRunning.value,
          loading: isRunningThisFile,
          onClick: () => runSql(row),
        },
        { default: () => '运行' },
      )
    },
  },
]

const pagination = {
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
}

function formatBytes(bytes: number) {
  if (bytes < 1024)
    return `${bytes} B`
  if (bytes < 1024 * 1024)
    return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function formatDate(value: string | null) {
  if (!value)
    return '-'

  const date = new Date(value)
  if (Number.isNaN(date.getTime()))
    return value

  return date.toLocaleString('zh-CN', { hour12: false })
}

function getJobStatusLabel(status: DbJob['status']) {
  const labels = {
    running: '运行中',
    success: '成功',
    error: '失败',
    canceled: '已取消',
  }
  return labels[status]
}

function getJobStatusType(status: DbJob['status']) {
  const types = {
    running: 'info',
    success: 'success',
    error: 'error',
    canceled: 'warning',
  } as const
  return types[status]
}

function getActionLabel(action: DbJob['action']) {
  return action === 'clear_db' ? '清空数据库' : '运行 SQL'
}

function getJobFilenames(job: DbJob | null) {
  if (!job)
    return []
  if (job.filenames?.length)
    return job.filenames
  return job.filename ? [job.filename] : []
}

function getJobFilenameTagType(job: DbJob, filename: string) {
  if (job.completed_filenames?.includes(filename))
    return 'success'
  if (job.status === 'running' && job.filename === filename)
    return 'info'
  if (job.status === 'error' && job.filename === filename)
    return 'error'
  if (job.status === 'canceled' && job.filename === filename)
    return 'warning'
  return 'default'
}

function getScriptStatus(row: SqlScript) {
  const job = currentJob.value
  if (job?.action === 'run_sql') {
    const jobFilenames = getJobFilenames(job)
    if (jobFilenames.includes(row.name)) {
      if (job.completed_filenames?.includes(row.name)) {
        return {
          label: '已完成',
          type: 'success' as const,
        }
      }

      if (job.status === 'running' && job.filename === row.name) {
        return {
          label: getJobStatusLabel(job.status),
          type: getJobStatusType(job.status),
        }
      }

      if (job.status === 'running') {
        return {
          label: '队列中',
          type: 'info' as const,
        }
      }

      return {
        label: getJobStatusLabel(job.status),
        type: getJobStatusType(job.status),
      }
    }
  }

  if (row.is_empty) {
    return {
      label: '空文件',
      type: 'warning' as const,
    }
  }

  return {
    label: '待运行',
    type: 'default' as const,
  }
}

function setJob(job: DbJob | null) {
  currentJob.value = job
  if (job?.status === 'running')
    startPolling()
  else
    stopPolling()
}

function startPolling() {
  if (pollTimer)
    return

  pollTimer = setInterval(() => {
    pollJob()
  }, 2000)
}

function stopPolling() {
  if (!pollTimer)
    return

  clearInterval(pollTimer)
  pollTimer = undefined
}

async function fetchScripts(options: { syncCurrentJob?: boolean } = {}) {
  const { syncCurrentJob = true } = options
  loading.value = true
  error.value = ''

  try {
    const response = await request.get('/init/db/api/scripts')
    if (response.data.status === 'success') {
      database.value = response.data.database
      scripts.value = response.data.scripts
      pruneSelectedScripts()
      if (syncCurrentJob && response.data.current_job)
        setJob(response.data.current_job)
    }
    else {
      error.value = response.data.message || 'SQL 文件列表加载失败'
    }
  }
  catch (err: any) {
    error.value = err.response?.data?.message || err.message || 'SQL 文件列表加载失败'
  }
  finally {
    loading.value = false
  }
}

async function createJob(payload: { action: DbJob['action'], filename?: string, filenames?: string[] }) {
  actionLoading.value = true
  error.value = ''

  try {
    const response = await request.post('/init/db/api/jobs', payload)
    if (response.data.status === 'success')
      setJob(response.data.job)
    else
      error.value = response.data.message || '任务创建失败'
  }
  catch (err: any) {
    const data = err.response?.data
    if (data?.current_job)
      setJob(data.current_job)
    error.value = data?.message || err.message || '任务创建失败'
  }
  finally {
    actionLoading.value = false
  }
}

function runSql(row: SqlScript) {
  createJob({
    action: 'run_sql',
    filename: row.name,
  })
}

function runSelectedSql() {
  if (!selectedFilenameCount.value)
    return

  createJob({
    action: 'run_sql',
    filenames: selectedFilenames.value,
  })
}

function clearDatabase() {
  createJob({ action: 'clear_db' })
}

function rowKey(row: SqlScript) {
  return row.name
}

function clearSelectedScripts() {
  selectedScriptNames.value = []
}

function updateSelectedScriptNames(keys: DataTableRowKey[]) {
  selectedScriptNames.value = keys
}

function pruneSelectedScripts() {
  const scriptNames = new Set(scripts.value.map(script => script.name))
  selectedScriptNames.value = selectedScriptNames.value.filter(name => scriptNames.has(String(name)))
}

async function pollJob() {
  if (!currentJobId.value)
    return

  try {
    const response = await request.get(`/init/db/api/jobs/${currentJobId.value}`)
    if (response.data.status === 'success') {
      setJob(response.data.job)
      if (response.data.job.status !== 'running')
        await fetchScripts({ syncCurrentJob: false })
    }
  }
  catch (err: any) {
    error.value = err.response?.data?.message || err.message || '任务状态加载失败'
    stopPolling()
  }
}

async function cancelJob() {
  if (!currentJobId.value)
    return

  actionLoading.value = true
  error.value = ''

  try {
    const response = await request.post(`/init/db/api/jobs/${currentJobId.value}/cancel`)
    if (response.data.status === 'success')
      setJob(response.data.job)
    else
      error.value = response.data.message || '取消任务失败'
  }
  catch (err: any) {
    error.value = err.response?.data?.message || err.message || '取消任务失败'
  }
  finally {
    actionLoading.value = false
  }
}

onMounted(() => {
  fetchScripts()
})

onBeforeUnmount(() => {
  stopPolling()
})
</script>

<template>
  <div class="mx-auto px-4 py-6 max-w-7xl w-full">
    <n-card title="数据库初始化" :bordered="false" class="mb-6">
      <div class="gap-4 flex flex-col">
        <div class="gap-3 flex flex-wrap items-center justify-between">
          <div class="gap-2 flex flex-wrap items-center">
            <n-tag type="info" :bordered="false">
              当前数据库：{{ database || '-' }}
            </n-tag>
            <n-tag :bordered="false">
              SQL 文件：{{ scripts.length }}
            </n-tag>
          </div>

          <div class="gap-2 flex flex-wrap items-center">
            <n-button
              secondary
              :disabled="loading || isJobRunning"
              @click="fetchScripts()"
            >
              <template #icon>
                <div class="i-carbon-renew" />
              </template>
              刷新
            </n-button>

            <n-popconfirm @positive-click="clearDatabase">
              <template #trigger>
                <n-button
                  type="error"
                  secondary
                  :disabled="isJobRunning"
                  :loading="actionLoading && currentJob?.action === 'clear_db'"
                >
                  <template #icon>
                    <div class="i-carbon-trash-can" />
                  </template>
                  清空数据库
                </n-button>
              </template>
              确认清空并重建当前数据库？
            </n-popconfirm>

            <n-button
              v-if="isJobRunning"
              type="warning"
              secondary
              :loading="actionLoading"
              @click="cancelJob"
            >
              <template #icon>
                <div class="i-carbon-stop" />
              </template>
              取消运行
            </n-button>
          </div>
        </div>

        <n-alert type="warning" :bordered="false">
          清空数据库会删除当前库并重建空库；取消 SQL 运行只能终止客户端进程，已执行成功的语句不会回滚。
        </n-alert>

        <n-alert v-if="error" type="error" closable>
          {{ error }}
        </n-alert>
      </div>
    </n-card>

    <n-card :bordered="false">
      <template #header>
        <div class="gap-3 flex flex-wrap items-center justify-between">
          <div class="gap-2 flex flex-wrap items-center">
            <span>SQL 脚本</span>
            <n-tag v-if="isJobRunning" size="small" type="info" :bordered="false">
              后台运行中
            </n-tag>
            <n-tag v-if="selectedFilenameCount" size="small" :bordered="false">
              已选择 {{ selectedFilenameCount }}
            </n-tag>
          </div>

          <div class="gap-2 flex flex-wrap items-center">
            <n-button
              type="primary"
              secondary
              :disabled="!selectedFilenameCount || isJobRunning"
              :loading="actionLoading && !isJobRunning"
              @click="runSelectedSql"
            >
              <template #icon>
                <div class="i-carbon-play" />
              </template>
              批量运行
            </n-button>

            <n-button
              v-if="selectedFilenameCount"
              secondary
              :disabled="isJobRunning"
              @click="clearSelectedScripts"
            >
              清空选择
            </n-button>
          </div>
        </div>
      </template>

      <n-spin :show="loading">
        <n-data-table
          :columns="columns"
          :data="scripts"
          :bordered="false"
          :single-line="false"
          :pagination="pagination"
          :row-key="rowKey"
          :checked-row-keys="selectedScriptNames"
          size="small"
          :scroll-x="980"
          @update:checked-row-keys="updateSelectedScriptNames"
        >
          <template #empty>
            <n-empty description="sql 文件夹中暂无 SQL 脚本" />
          </template>
        </n-data-table>
      </n-spin>
    </n-card>

    <n-card v-if="currentJob" title="任务状态" :bordered="false" class="mt-6">
      <div class="gap-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
        <div class="text-sm text-gray-600 dark:text-gray-300">
          类型
          <div class="text-base text-gray-900 font-medium mt-1 dark:text-gray-100">
            {{ getActionLabel(currentJob.action) }}
          </div>
        </div>
        <div class="text-sm text-gray-600 dark:text-gray-300">
          状态
          <div class="mt-1">
            <n-tag :type="getJobStatusType(currentJob.status)" :bordered="false">
              {{ getJobStatusLabel(currentJob.status) }}
            </n-tag>
          </div>
        </div>
        <div class="text-sm text-gray-600 dark:text-gray-300">
          开始时间
          <div class="text-base text-gray-900 font-medium mt-1 dark:text-gray-100">
            {{ formatDate(currentJob.started_at) }}
          </div>
        </div>
        <div class="text-sm text-gray-600 dark:text-gray-300">
          结束时间
          <div class="text-base text-gray-900 font-medium mt-1 dark:text-gray-100">
            {{ formatDate(currentJob.finished_at) }}
          </div>
        </div>
      </div>

      <n-descriptions :column="1" label-placement="left" class="mt-5">
        <n-descriptions-item v-if="getJobFilenames(currentJob).length" label="SQL 文件">
          <div class="gap-2 flex flex-wrap">
            <n-tag
              v-for="filename in getJobFilenames(currentJob)"
              :key="filename"
              size="small"
              :type="getJobFilenameTagType(currentJob, filename)"
              :bordered="false"
            >
              {{ filename }}
            </n-tag>
          </div>
        </n-descriptions-item>
        <n-descriptions-item label="任务 ID">
          {{ currentJob.id }}
        </n-descriptions-item>
        <n-descriptions-item label="消息">
          {{ currentJob.message || '-' }}
        </n-descriptions-item>
        <n-descriptions-item v-if="currentJob.return_code !== null" label="退出码">
          {{ currentJob.return_code }}
        </n-descriptions-item>
      </n-descriptions>

      <n-code
        v-if="currentJob.log_tail"
        :code="currentJob.log_tail"
        language="text"
        show-line-numbers
        class="mt-5"
      />
    </n-card>
  </div>
</template>
