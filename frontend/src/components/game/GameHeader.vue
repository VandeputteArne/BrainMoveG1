<script setup>
import { Timer, OctagonX } from 'lucide-vue-next';

const props = defineProps({
  formattedTime: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(['stop']);

function handleStop() {
  emit('stop');
}
</script>

<template>
  <div class="c-game-header">
    <button class="c-game-header__stop" @click="handleStop">
      <span class="c-game-header__icon"><OctagonX /></span>
      <span class="c-game-header__text">stop</span>
    </button>
    <p class="c-game-header__timer">
      <span class="c-game-header__icon"><Timer /></span>
      <span>{{ formattedTime }}</span>
    </p>
  </div>
</template>

<style scoped>
.c-game-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 0.75rem;
}

.c-game-header__stop {
  display: flex;
  align-items: center;
  gap: 0.3125rem;
  text-decoration: none;
  color: var(--gray-80);
  background-color: transparent;
  border: none;
  cursor: pointer;
  font-size: 1rem;
}

.c-game-header__timer {
  display: flex;
  align-items: center;
  gap: 0.3125rem;
  color: var(--gray-80);
  font-size: 1rem;
  margin: 0;
}

.c-game-header__icon {
  display: flex;
  align-items: center;
  width: 1.5rem;
  height: 1.5rem;
}

.c-game-header__text {
  line-height: 1;
}
</style>
