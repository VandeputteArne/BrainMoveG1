<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';

import { useGameTimer } from '../../composables/useGameTimer.js';
import { useGameCountdown } from '../../composables/useGameCountdown.js';
import GameCountdown from '../../components/game/GameCountdown.vue';
import GameHeader from '../../components/game/GameHeader.vue';
import GameProgress from '../../components/game/GameProgress.vue';

const currentRound = ref(1);
const totalRounds = ref(5);

// Use the timer composable
const { formattedTime, startTimer, stopTimer } = useGameTimer();

// Use the countdown composable
const { countdown, showCountdown, countdownText, startCountdown } = useGameCountdown({
  gameId: 2, // Memory game ID
  onComplete: () => {
    startTimer();
  },
});

const router = useRouter();

onMounted(async () => {
  // Start countdown
  await startCountdown();
});

onUnmounted(() => {
  // Stop timer when component unmounts
  stopTimer();
});

function goBack() {
  if (window.history.length > 1) router.back();
  else router.push('/games');
}
</script>

<template>
  <GameCountdown v-if="showCountdown" :countdown="countdown" :text="countdownText" />

  <div v-else class="c-game-memory">
    <GameHeader :formatted-time="formattedTime" @stop="goBack" />

    <div class="c-game-memory__content">
      <h2>Memory Game</h2>
      <p>Game content coming soon...</p>

      <GameProgress :current-round="currentRound" :total-rounds="totalRounds" />
    </div>
  </div>
</template>

<style scoped>
.c-game-memory {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.c-game-memory__content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  position: relative;
}
</style>
