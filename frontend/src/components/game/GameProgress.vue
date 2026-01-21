<script setup>
const props = defineProps({
  currentRound: {
    type: Number,
    required: true,
  },
  totalRounds: {
    type: Number,
    required: true,
  },
});
</script>

<template>
  <div class="c-game-progress">
    <h3>Ronde {{ currentRound }} / {{ totalRounds }}</h3>
    <div class="c-game-progress__bar">
      <div class="c-game-progress__fill" :style="{ width: (currentRound / totalRounds) * 100 + '%' }"></div>
    </div>
  </div>
</template>

<style scoped>
.c-game-progress {
  position: absolute;
  bottom: 2rem;
  max-width: 12.5rem;
  left: 50%;
  transform: translateX(-50%);
  width: 90%;
  color: var(--color-white);
  text-align: center;
  z-index: 30;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.c-game-progress__bar {
  width: 100%;
  height: 1.5625rem;
  background: var(--color-white);
  border-radius: var(--radius-40);
  margin-top: 0.5rem;
  overflow: hidden;
  padding: 0.1875rem;
}

.c-game-progress__fill {
  height: 100%;
  background: var(--blue-100);
  border-radius: var(--radius-40);
  transition: width 0.3s ease;
}
</style>
