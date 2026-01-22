<script setup>
import { watch } from 'vue';
import { playFlute, isAudioEnabled } from '../../services/sound.js';

const props = defineProps({
  countdown: {
    type: [String, Number],
    required: true,
  },
  text: {
    type: String,
    default: '',
  },
});

watch(
  () => props.countdown,
  (val) => {
    if (!val) return;
    try {
      if (!isAudioEnabled()) return;

      if (String(val).toUpperCase().includes('GO')) {
        playFlute(0.45, 523.25);
      } else {
        const n = Number(val);
        const freq = n === 3 ? 261.63 : n === 2 ? 329.63 : 392.0;
        playFlute(0.14, freq);
      }
    } catch (e) {
      // ignore audio playback errors
    }
  },
);
</script>

<template>
  <div class="c-game-countdown">
    <div class="c-game-countdown__number">{{ countdown }}</div>
    <p v-if="text" class="c-game-countdown__text">{{ text }}</p>
    <!-- audio is handled globally; no button here -->
  </div>
</template>

<style scoped>
.c-game-countdown {
  position: fixed;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  inset: 0;
  background: var(--gray-90);
  z-index: 1200;
}

.c-game-countdown__number {
  color: white;
  font-weight: 700;
  font-size: 4rem;
  padding: 0rem 1rem;
  border-radius: 0.5rem;
  animation: pop 0.45s ease forwards;
  user-select: none;
}

.c-game-countdown__text {
  margin-top: 1rem;
  color: var(--color-white);
  font-size: 1.5rem;
  user-select: none;
}

.c-game-countdown__enable {
  margin-top: 1.25rem;
  background: transparent;
  color: var(--color-white);
  border: 1px solid rgba(255, 255, 255, 0.18);
  padding: 0.5rem 0.75rem;
  border-radius: 0.375rem;
  cursor: pointer;
  font-weight: 600;
}

@keyframes pop {
  from {
    transform: scale(0.35);
    opacity: 0;
    filter: blur(2px);
  }
  60% {
    transform: scale(1.08);
    opacity: 1;
    filter: blur(0);
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
