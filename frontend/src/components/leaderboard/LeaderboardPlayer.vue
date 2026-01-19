<script setup>
import { computed } from 'vue';

const props = defineProps({
  name: { type: String, required: true },
  rank: { type: Number, default: 0 },
});

const firstLetter = computed(() => {
  return props.name ? props.name.charAt(0).toUpperCase() : '';
});

const backgroundClass = computed(() => {
  if (props.rank === 1) return 'is-gold';
  if (props.rank === 2) return 'is-silver';
  if (props.rank === 3) return 'is-bronze';
  return '';
});
</script>

<template>
  <div class="c-player">
    <div class="c-player__img" :class="backgroundClass">{{ firstLetter }}</div>
    <p class="c-player__name">{{ props.name }}</p>
  </div>
</template>

<style scoped>
.c-player {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  width: fit-content;

  .c-player__img {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 2.3rem;
    height: 2.3rem;
    border-radius: 100%;
    color: var(--color-white);

    &.is-gold {
      background-color: #d4af37;
    }

    &.is-silver {
      background-color: #c0c0c0;
    }

    &.is-bronze {
      background-color: #cd7f32;
    }
  }
}
</style>
