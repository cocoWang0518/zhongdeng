<script setup lang="ts">
import QueryForm from '~/components/QueryForm.vue'
import QueryResult from '~/components/QueryResult.vue'
import { useSidebarStore } from '~/stores/sidebar'
import request from '~/utils/request'

useSidebarStore().chatSessions.forEach((chat) => {
  chat.selected = false
})

const loading = ref(false)
const error = ref('')
const queryResult = ref(null)

const formData = {
  bond_type: '',
  keyword: '',
}

async function handleFormSubmit(queryData: any) {
  loading.value = true
  error.value = ''
  queryResult.value = null

  try {
    const response = await request.post('/ketiyi/query', queryData, {
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (response.data.status === 'success') {
      queryResult.value = response.data.data
    }
    else {
      error.value = response.data.message || '查询失败，请稍后重试'
    }
  }
  catch (err: any) {
    console.error('Query submission error:', err)
    error.value = err.response?.data?.message || err.message || '查询失败，请稍后重试'
  }
  finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="mx-auto px-4 py-6 max-w-7xl w-full">
    <n-card title="新建查询" :bordered="false" class="mb-6">
      <p class="text-gray-700 mb-4 dark:text-gray-300">
        输入债券代码或名称进行模糊搜索，系统将返回评级结果与历史趋势。
      </p>

      <n-spin :show="loading">
        <n-alert v-if="error" type="error" class="mb-4" closable>
          {{ error }}
        </n-alert>

        <QueryForm
          :data="formData"
          @submit-success="handleFormSubmit"
        />
      </n-spin>
    </n-card>

    <QueryResult v-if="queryResult" :data="queryResult" />
  </div>
</template>
