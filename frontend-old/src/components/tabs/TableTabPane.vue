<script setup lang="ts">
// 定义props
interface Props {
  parsedData: any[]
  columns: any[]
  loading: boolean
  current: number
  onPageChange: (page: number) => void
}

defineProps<Props>()
</script>

<template>
  <div>
    <n-data-table
      v-if="parsedData.length > 0"
      :page="current"
      :columns="columns"
      :data="parsedData"
      :loading="loading"
      :bordered="false"
      :single-line="false"
      size="small"
      :pagination="{
        pageSize: 10,
        onUpdatePage: onPageChange,
      }"
    />
    <n-empty v-else description="暂无表格数据" />
  </div>
</template>
