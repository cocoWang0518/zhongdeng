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
  task_type: '信用债项评级',
  data_type: '',
  industry_type: '',
  file: null,
})

const industryTypeOptions = [
  '券商',
  '银行',
  '非银行金融',
  '房地产',
  '电力及公用事业',
  '基础化工',
  '石油石化',
  '基础设施与地产产业',
  '周期产业',
  '工业设备制造',
  '科技产业',
].map(value => ({ label: value, value }))

const dataTypeOptions = computed(() => {
  if (!model.industry_type)
    return []
  const types = ['财务+非财务']
  if (!['工业设备制造', '科技产业'].includes(model.industry_type))
    types.push('仅财务')
  return types.map(value => ({ label: value, value }))
})

watch(() => props.data, (newVal) => {
  model.task_type = '信用债项评级'
  model.industry_type = industryTypeOptions.some(option => option.value === newVal.industry_type)
    ? newVal.industry_type
    : ''
  model.data_type = dataTypeOptions.value.some(option => option.value === newVal.data_type)
    ? newVal.data_type
    : ''
}, { immediate: true })

watch(() => model.industry_type, () => {
  if (!dataTypeOptions.value.some(option => option.value === model.data_type))
    model.data_type = ''
})

const rules: FormRules = {
  data_type: [
    {
      trigger: 'change',
      validator() {
        return dataTypeOptions.value.some(option => option.value === model.data_type)
          || new Error('请选择当前行业支持的数据类型')
      },
    },
  ],
  industry_type: [
    {
      trigger: 'change',
      validator() {
        return industryTypeOptions.some(option => option.value === model.industry_type)
          || new Error('请选择行业类型')
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
    formData.append('data_type', model.data_type)
    formData.append('industry_type', model.industry_type)

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
    task_type: '信用债项评级',
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
        <n-form-item path="industry_type" label="行业类型">
          <n-select
            v-model:value="model.industry_type"
            :options="industryTypeOptions"
            placeholder="请选择行业类型"
            clearable
          />
        </n-form-item>

        <n-form-item path="data_type" label="数据类型">
          <n-select
            v-model:value="model.data_type"
            :options="dataTypeOptions"
            :disabled="!model.industry_type"
            placeholder="请选择数据类型"
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
