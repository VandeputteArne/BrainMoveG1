<script setup>
import { defineProps } from 'vue';

const props = defineProps({
  counts: {
    type: Number,
  },
  type: {
    type: String,
  },
  label: {
    type: String,
  },
});
</script>

<template>
  <div :class="`c-overzicht__count-item c-overzicht__count-item--${props.type}`">
    <h2 class="c-overzicht__count-num">{{ props.counts }}</h2>
    <p class="small">{{ props.label }}</p>
  </div>
</template>

<style scoped>
.c-overzicht__count-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  padding: 1rem;
  border-radius: var(--radius-20);

  .c-overzicht__count-label {
    color: var(--gray-70);
  }
}

.c-overzicht__count-item--correct {
  background-color: #83d087;
}

.c-overzicht__count-item--fout {
  background-color: #ff7b7b;
}

.c-overzicht__count-item--telaat {
  background-color: #ffb961;
}
</style>
