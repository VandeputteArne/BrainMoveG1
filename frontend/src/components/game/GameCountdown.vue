<script setup>
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
</script>

<template>
  <div class="c-game-countdown">
    <div class="c-game-countdown__number">{{ countdown }}</div>
    <p v-if="text" class="c-game-countdown__text">{{ text }}</p>
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
