<script setup lang="ts">
import { marked } from 'marked'
import { computed } from 'vue'

// 定义props
interface Props {
  modelText?: string
}

const props = defineProps<Props>()

// Process Markdown text by removing code block wrappers
function processMarkdown(content?: string) {
  if (!content)
    return ''

  // Remove code block delimiters if present
  let processedContent = ''
  if (content.startsWith('```')) {
    // Extract text between first and last triple backticks
    const firstDelimiter = content.indexOf('\n')
    const lastDelimiter = content.lastIndexOf('```')
    if (firstDelimiter !== -1 && lastDelimiter !== -1) {
      processedContent = content.substring(firstDelimiter + 1, lastDelimiter).trim()
    }
  }
  else {
    processedContent = content
  }
  return processedContent
}

// Computed properties for the processed Markdown content
const processedModelText = computed(() => {
  return marked.parse(processMarkdown(props.modelText))
})
</script>

<template>
  <div>
    <div v-if="props.modelText" class="text-content markdown-content">
      <div v-html="processedModelText" />
    </div>
    <n-empty v-else description="暂无模型解释" />
  </div>
</template>

<style scoped>
.markdown-content :deep(h1) {
  font-size: 1.75rem;
  font-weight: 700;
  margin-top: 1rem;
  margin-bottom: 0.75rem;
}

.markdown-content :deep(h2) {
  font-size: 1.5rem;
  font-weight: 600;
  margin-top: 0.75rem;
  margin-bottom: 0.5rem;
}

.markdown-content :deep(h3) {
  font-size: 1.25rem;
  font-weight: 600;
  margin-top: 0.5rem;
  margin-bottom: 0.25rem;
}

.markdown-content :deep(p) {
  margin-bottom: 0.75rem;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  padding-left: 1.5rem;
  margin-bottom: 0.75rem;
}

.markdown-content :deep(li) {
  margin-bottom: 0.25rem;
}

.markdown-content :deep(strong) {
  font-weight: 700;
}

.markdown-content :deep(blockquote) {
  border-left: 4px solid #e5e7eb;
  padding-left: 1rem;
  margin-left: 0;
  margin-right: 0;
  font-style: italic;
  color: #4b5563;
}

.markdown-content :deep(code) {
  background-color: #f3f4f6;
  padding: 0.2rem 0.4rem;
  border-radius: 0.25rem;
  font-family: monospace;
}

.markdown-content :deep(pre) {
  background-color: #f3f4f6;
  padding: 1rem;
  border-radius: 0.25rem;
  overflow-x: auto;
  margin-bottom: 0.75rem;
}
</style>
