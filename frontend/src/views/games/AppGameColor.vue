<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';

import { connectSocket, disconnectSocket } from '../../services/socket.js';
import { useGameTimer } from '../../composables/useGameTimer.js';
import { useGameCountdown } from '../../composables/useGameCountdown.js';
import { useGameDeviceGuard } from '../../composables/useGameDeviceGuard.js';
import GameCountdown from '../../components/game/GameCountdown.vue';
import GameHeader from '../../components/game/GameHeader.vue';
import GameProgress from '../../components/game/GameProgress.vue';
import IntroOverlay from '../../components/game/IntroOverlay.vue';

const bgColor = ref('');
const currentRound = ref(1);
const totalRounds = ref(5);

const { formattedTime, startTimer, stopTimer } = useGameTimer();

const { countdown, showCountdown, countdownText, startCountdown } = useGameCountdown({
  gameId: 1,
  onComplete: () => {
    startTimer();
  },
});

useGameDeviceGuard(1);

const showIntro = ref(true);

function beginGame() {
  // overlay done
}

function onOverlayExiting() {
  try {
    startCountdown();
  } catch (e) {}
}

const isAnimating = ref(false);
const prevColor = ref('');

const kleuren = {
  blauw: '#2979ff', // blauw
  rood: '#f91818', // rood
  geel: '#ffc400', // geel
  groen: '#00b709', // groen
};

let _socket = null;
let chosenColors = [];
try {
  const raw = sessionStorage.getItem('lastGamePayload');
  if (raw) {
    const parsed = JSON.parse(raw || '{}');
    if (Array.isArray(parsed.kleuren)) {
      chosenColors = parsed.kleuren.map((c) => String(c).toLowerCase());
    }
  }
} catch (e) {
  chosenColors = [];
}

onMounted(async () => {
  try {
    _socket = connectSocket();
    _socket.on('connect', () => {
      console.log('[socket] connected', _socket && _socket.id);
    });

    _socket.on('gekozen_kleur', (payload) => {
      console.log('[socket] gekozen_kleur received:', payload);
      let color = null;
      let round = null;
      let total = null;
      if (typeof payload === 'string') color = payload;
      else if (payload && typeof payload === 'object') {
        color = payload.gekozen_kleur || payload.kleur || payload.color || null;
        round = payload.rondenummer || payload.ronde || payload.round || null;
        total = payload.maxronden || payload.totaal || payload.total || null;
      }
      if (!color || typeof color !== 'string') return;
      const norm = color.toLowerCase();
      if (chosenColors.length === 0 || chosenColors.includes(norm)) {
        const newColor = kleuren[norm] || color;
        prevColor.value = bgColor.value;
        isAnimating.value = true;
        setTimeout(() => {
          bgColor.value = newColor;
          setTimeout(() => {
            isAnimating.value = false;
          }, 60);
        }, 60);
      }
      if (round !== null && typeof round === 'number') currentRound.value = round;
      if (total !== null && typeof total === 'number') totalRounds.value = total;
    });

    _socket.on('game_einde', () => {
      console.log('[socket] game_einde received');
      stopTimer();
      router.push('/resultaten/proficiat');
    });
  } catch (e) {
    // socket connect may fail (CORS, network) — ignore here
  }

  // countdown starts when intro overlay exits
});

onUnmounted(() => {
  try {
    if (_socket) {
      _socket.off('gekozen_kleur');
      _socket.off('game_einde');
    }
  } finally {
    stopTimer();
  }
});

const router = useRouter();

function goBack() {
  if (window.history.length > 1) router.back();
  else router.push('/games');
}
</script>

<template>
  <div class="c-game-root">
    <GameCountdown v-if="showCountdown" :countdown="countdown" :text="countdownText" />

    <IntroOverlay v-model="showIntro" @exiting="onOverlayExiting" :durationMs="4000" title="Color Sprint" text="Wacht op het startsignaal en reageer zo snel mogelijk." overlayClass="c-game__intro" contentClass="c-game__intro-content" @done="beginGame" />

    <div v-if="!showIntro" class="c-game">
      <GameHeader :formatted-time="formattedTime" @stop="goBack" />

      <div class="c-game__content">
        <div class="c-game__background"></div>
        <div class="c-game__color" :class="{ 'is-animating': isAnimating }" :style="{ backgroundColor: bgColor }"></div>

        <GameProgress :current-round="currentRound" :total-rounds="totalRounds" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.c-game {
  display: flex;
  flex-direction: column;
  height: var(--app-height, 100vh);
  width: 100vw;
}

.c-game__content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.c-game__background {
  position: absolute;
  inset: 0;
  background: var(--gray-80);
  z-index: 0;
}

.c-game__color {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  transition:
    border-radius 0.2s ease-out,
    transform 0.2s ease-out;
  border-radius: 0;
  z-index: 1;
}

.c-game__color.is-animating {
  border-radius: 50%;
  transform: scale(0);
}
</style>
