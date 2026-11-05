<script setup lang="ts">
// 定义props
interface Props {
  allPlotImage?: string
}

const props = defineProps<Props>()
</script>

<template>
  <div>
    <div v-if="props.allPlotImage" class="text-content">
      <n-image
        class="h-auto w-full"
        :src="props.allPlotImage"
      />
    </div>
    <n-empty v-else description="暂无结果图" />
  </div>
</template>
