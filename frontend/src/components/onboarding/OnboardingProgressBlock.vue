<script setup>
const props = defineProps({
  active: Boolean,
});
</script>

<template>
  <div class="c-progress-block" :class="{ 'c-progress-block--active': props.active }"></div>
</template>

<style scoped>
.c-progress-block {
  width: 1.5625rem;
  height: 0.625rem;
  border-radius: var(--radius-40);

  background-color: var(--blue-30);
}

.c-progress-block--active {
  background-color: var(--blue-100);
}
</style>
