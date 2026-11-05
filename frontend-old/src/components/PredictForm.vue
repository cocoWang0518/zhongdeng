<script setup lang="ts">
import type { FormInst, FormItemRule, FormRules, UploadFileInfo } from 'naive-ui'
import { computed, reactive, ref, watch } from 'vue'

interface FormModel {
  task_type: string
  data_type: string
  industry_type: string
  file: File | null
}

const props = defineProps<{
  data: Pick<FormModel, 'task_type' | 'data_type' | 'industry_type'>
}>()

const emit = defineEmits<{
  submitSuccess: [data: FormData]
}>()

const formRef = ref<FormInst | null>(null)
const fileListRef = ref<UploadFileInfo[]>([])
const uploading = ref(false)

const model = reactive<FormModel>({
  task_type: '',
  data_type: '',
  industry_type: '',
  file: null,
})

const taskTypeOptions = [
  { label: '信用债项评级', value: '信用债项评级' },
  { label: '城投债项评级', value: '城投债项评级' },
  { label: 'ABS债项评级', value: 'ABS债项评级' },
]

const isAbsTask = computed(() => model.task_type === 'ABS债项评级')
const requiresDetailedParams = computed(() => !!model.task_type && !isAbsTask.value)

const dataTypeOptions = computed(() => {
  if (model.task_type === '信用债项评级' || model.task_type === '城投债项评级') {
    return [
      { label: '仅财务', value: '仅财务' },
      { label: '财务+非财务', value: '财务+非财务' },
    ]
  }

  return []
})

const secondaryTypeLabel = computed(() => {
  if (model.task_type === '城投债项评级')
    return '地区类型'

  return '行业类型'
})

const industryTypeOptions = computed(() => {
  if (model.task_type === '信用债项评级') {
    return [
      { label: '基础设施与地产产业', value: '基础设施与地产产业' },
      { label: '消费产业', value: '消费产业' },
      { label: '周期产业', value: '周期产业' },
      { label: '制造产业', value: '制造产业' },
      { label: '医疗健康产业', value: '医疗健康产业' },
      { label: '科技产业', value: '科技产业' },
      { label: '金融产业', value: '金融产业' },
      { label: '电力及公用事业', value: '电力及公用事业' },
      { label: '房地产', value: '房地产' },
      { label: '建筑', value: '建筑' },
      { label: '全产业', value: '全产业' },
    ]
  }

  if (model.task_type === '城投债项评级') {
    return [
      { label: '全地区', value: '全地区' },
      { label: '东部地区', value: '东部地区' },
      { label: '中部地区', value: '中部地区' },
      { label: '西部地区', value: '西部地区' },
      { label: '东南沿海', value: '东南沿海' },
      { label: '东北地区', value: '东北地区' },
      { label: 'TabM', value: 'TabM' },
    ]
  }

  return []
})

watch(() => props.data, (newVal) => {
  model.task_type = newVal.task_type || ''
  model.data_type = newVal.data_type || ''
  model.industry_type = newVal.industry_type || ''
}, { immediate: true })

watch(() => model.task_type, (taskType) => {
  const allowedDataTypes = dataTypeOptions.value.map(option => option.value)
  const allowedIndustries = industryTypeOptions.value.map(option => option.value)

  if (!allowedDataTypes.includes(model.data_type))
    model.data_type = ''

  if (!allowedIndustries.includes(model.industry_type))
    model.industry_type = ''

  if (!taskType) {
    model.data_type = ''
    model.industry_type = ''
  }
})

const rules: FormRules = {
  task_type: [
    {
      required: true,
      message: '请选择任务类型',
      trigger: 'change',
    },
  ],
  data_type: [
    {
      message: '请选择数据类型',
      trigger: 'change',
      validator() {
        if (requiresDetailedParams.value && !model.data_type)
          return new Error('请选择数据类型')

        return true
      },
    },
  ],
  industry_type: [
    {
      trigger: 'change',
      validator() {
        if (requiresDetailedParams.value && !model.industry_type)
          return new Error(`请选择${secondaryTypeLabel.value}`)

        return true
      },
    },
  ],
  file: [
    {
      required: true,
      trigger: 'change',
      validator(rule: FormItemRule, value: File | null) {
        if (!value)
          return new Error('请上传文件')

        return true
      },
    },
  ],
}

function handleFileUpload(options: { file: UploadFileInfo, fileList: UploadFileInfo[] }) {
  fileListRef.value = options.fileList
  model.file = options.fileList[0]?.file || null
}

async function handleSubmit() {
  await formRef.value?.validate()

  uploading.value = true

  try {
    const formData = new FormData()
    formData.append('task_type', model.task_type)
    formData.append('data_type', isAbsTask.value ? '财务+非财务' : model.data_type)
    formData.append('industry_type', isAbsTask.value ? '整体' : model.industry_type)

    if (model.file)
      formData.append('file', model.file)

    emit('submitSuccess', formData)
  }
  catch (error) {
    console.error('Form submission error:', error)
  }
  finally {
    uploading.value = false
  }
}

function resetForm() {
  formRef.value?.restoreValidation()
  fileListRef.value = []
  Object.assign(model, {
    task_type: '',
    data_type: '',
    industry_type: '',
    file: null,
  })
}
</script>

<template>
  <div class="w-full">
    <n-card title="预测表单" class="mb-4">
      <n-form
        ref="formRef"
        :model="model"
        :rules="rules"
        label-placement="left"
        label-width="auto"
        require-mark-placement="right-hanging"
      >
        <n-form-item path="task_type">
          <n-tabs
            v-model:value="model.task_type"
            type="segment"
            animated
            class="w-full"
          >
            <n-tab-pane
              v-for="option in taskTypeOptions"
              :key="option.value"
              :name="option.value"
              :tab="option.label"
            />
          </n-tabs>
        </n-form-item>

        <n-form-item v-if="requiresDetailedParams" path="data_type" label="数据类型">
          <n-select
            v-model:value="model.data_type"
            :options="dataTypeOptions"
            placeholder="请选择数据类型"
            clearable
          />
        </n-form-item>

        <n-form-item v-if="requiresDetailedParams" path="industry_type" :label="secondaryTypeLabel">
          <n-select
            v-model:value="model.industry_type"
            :options="industryTypeOptions"
            :placeholder="`请选择${secondaryTypeLabel}`"
            clearable
          />
        </n-form-item>

        <n-form-item path="file" label="上传文件">
          <n-upload
            v-model:file-list="fileListRef"
            :max="1"
            :default-upload="false"
            accept=".csv,.parquet"
            @change="handleFileUpload"
          >
            <n-button>选择文件</n-button>
          </n-upload>
        </n-form-item>

        <div class="mt-6 flex gap-4 justify-end">
          <n-button @click="resetForm">
            重置
          </n-button>
          <n-button type="primary" :loading="uploading" @click="handleSubmit">
            提交预测
          </n-button>
        </div>
      </n-form>
    </n-card>
  </div>
</template>
