<script setup>
import { defineProps } from 'vue';

const props = defineProps({
  counts: {
    type: Number,
  },
  type: {
    type: String,
  },
});
</script>

<template>
  <div :class="`c-overzicht__count-item c-overzicht__count-item--${props.type}`">
    <h2 class="c-overzicht__count-num">{{ props.counts }}</h2>
    <p class="small">{{ props.type }}</p>
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

.c-overzicht__count-item--wrong {
  background-color: #ffb961;
}

.c-overzicht__count-item--late {
  background-color: #ff7b7b;
}
</style>
