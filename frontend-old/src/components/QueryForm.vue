<script setup lang="ts">
import type { FormInst, FormRules } from 'naive-ui'

interface QueryModel {
  bond_type: string
  keyword: string
}

const _props = defineProps<{
  data: QueryModel
}>()

const emit = defineEmits(['submitSuccess'])

const formRef = ref<FormInst | null>(null)
const submitting = ref(false)

const model = reactive<QueryModel>({
  bond_type: '',
  keyword: '',
})

watch(() => _props.data, (newVal) => {
  model.bond_type = newVal.bond_type
  model.keyword = newVal.keyword
}, { immediate: true })

const bondTypeOptions = [
  { label: '正常查询', value: '' },
  { label: '基金', value: '基金' },
]

const rules: FormRules = {
  keyword: [
    {
      required: true,
      message: '请输入债券代码或名称',
      trigger: 'blur',
    },
  ],
}

async function handleSubmit() {
  await formRef.value?.validate()

  submitting.value = true

  try {
    const queryData = {
      bond_type: model.bond_type,
      keyword: model.keyword,
    }
    emit('submitSuccess', queryData)
  }
  catch (error) {
    console.error('Form submission error:', error)
  }
  finally {
    submitting.value = false
  }
}

function resetForm() {
  formRef.value?.restoreValidation()
  Object.assign(model, {
    bond_type: '',
    keyword: '',
  })
}
</script>

<template>
  <div class="w-full">
    <n-card title="查询表单" class="mb-4">
      <n-form
        ref="formRef"
        :model="model"
        :rules="rules"
        label-placement="left"
        label-width="auto"
        require-mark-placement="right-hanging"
      >
        <!-- 查询类型选择 -->
        <n-form-item path="bond_type">
          <n-tabs
            v-model:value="model.bond_type"
            type="segment"
            animated
            class="w-full"
          >
            <n-tab-pane
              v-for="option in bondTypeOptions"
              :key="option.value"
              :name="option.value"
              :tab="option.label"
            />
          </n-tabs>
        </n-form-item>

        <!-- 关键词输入 -->
        <n-form-item path="keyword" label="关键词">
          <n-input
            v-model:value="model.keyword"
            placeholder="请输入代码或名称进行模糊搜索"
          />
        </n-form-item>

        <div class="mt-6 flex gap-4 justify-end">
          <n-button @click="resetForm">
            重置
          </n-button>
          <n-button type="primary" :loading="submitting" @click="handleSubmit">
            <template #icon>
              <div class="i-carbon-search" />
            </template>
            开始查询
          </n-button>
        </div>
      </n-form>
    </n-card>
  </div>
</template>
