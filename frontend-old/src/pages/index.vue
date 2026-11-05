<script setup lang="ts">
// Index page now just shows the main content area
// The sidebar is in App.vue as a layout
</script>

<template>
  <div class="p-5 flex flex-col h-full w-full">
    <div class="rounded-lg bg-white flex flex-1 items-center justify-center dark:bg-dark-800">
      <n-empty description="选择一个对话或创建新对话" />
    </div>
  </div>
</template>
