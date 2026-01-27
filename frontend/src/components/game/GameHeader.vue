<script setup>
import { Timer, OctagonX } from 'lucide-vue-next';
import { getApiUrl } from '../../config/api.js';

const props = defineProps({
  formattedTime: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(['stop']);

import { ref } from 'vue';

const isLoading = ref(false);

async function handleStop() {
  try {
    isLoading.value = true;
    await fetch(getApiUrl('games/stop'), { method: 'GET' });
  } catch (err) {
    console.error('Stop API call failed', err);
  } finally {
    isLoading.value = false;
  }

  emit('stop');
}
</script>

<template>
  <div class="c-game-header">
    <button class="c-game-header__stop" @click="handleStop" :disabled="isLoading" :aria-busy="isLoading">
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
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 0.75rem;
  background-color: var(--color-white);
  z-index: 1000;
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

.c-game-header__stop[disabled] {
  opacity: 0.5;
  cursor: not-allowed;
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
