<script setup lang="ts">
const props = defineProps<{ initial: number }>()

const count = ref(props.initial)

function inc() {
  count.value++
}

function dec() {
  count.value--
}
</script>

<template>
  <div>{{ count }} <button class="inc" @click="inc"> + </button><button class="dec" @click="dec"> - </button></div>
</template>
