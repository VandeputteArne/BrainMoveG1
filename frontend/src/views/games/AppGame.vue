<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';

import { Timer, OctagonX } from 'lucide-vue-next';
import { connectSocket, disconnectSocket } from '../../services/socket.js';
import { getApiUrl } from '../../config/api.js';

const countdown = ref(3);
const showCountdown = ref(true);
const bgColor = ref('');
const currentRound = ref(1);
const totalRounds = ref(5);

const elapsedSeconds = ref(0);
let timerInterval = null;

const formattedTime = computed(() => {
  const total = elapsedSeconds.value;
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const seconds = total % 60;
  if (hours > 0) return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
});

function startTimer() {
  if (timerInterval) return;
  elapsedSeconds.value = 0;
  timerInterval = setInterval(() => {
    elapsedSeconds.value += 1;
  }, 1000);
}

function stopTimer() {
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
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
      // stop timer before navigating
      stopTimer();
      router.push('/resultaten/proficiat');
    });
  } catch (e) {
    // socket connect may fail (CORS, network) — ignore here
  }

  for (let i = 3; i >= 1; i--) {
    countdown.value = i;
    if (i === 1) {
      try {
        await fetch(getApiUrl('games/1/play'), { method: 'GET' });
      } catch (e) {
        // ignore network/CORS errors for this signal
      }
    }
    await new Promise((r) => setTimeout(r, 700));
  }
  showCountdown.value = false;
  // start local elapsed timer when countdown finished
  startTimer();
});

onUnmounted(() => {
  try {
    if (_socket) {
      _socket.off('gekozen_kleur');
      _socket.off('game_einde');
    }
  } finally {
    // stop timer and disconnect socket when component unmounts
    stopTimer();
    disconnectSocket();
  }
});

const router = useRouter();

function goBack() {
  if (window.history.length > 1) router.back();
  else router.push('/games');
}
</script>

<template>
  <div class="o-gamecontainer">
    <div v-if="showCountdown" class="c-countdown" aria-hidden="true">
      <div class="c-countdown__number">{{ countdown }}</div>
      <p class="c-countdown__text">Maak je klaar...</p>
    </div>

    <div v-else class="c-game">
      <div class="c-game__top">
        <button class="c-game__close" type="button" @click="goBack" aria-label="Sluit het spel">
          <span class="c-game__span"><OctagonX class="c-game__close-icon" /></span> stop
        </button>
        <p class="c-game__timer">
          <span class="c-game__span"><Timer class="c-game__timer-icon" /></span>{{ formattedTime }}
        </p>
      </div>

      <div class="c-game__bot">
        <div class="c-game__background"></div>
        <div class="c-game__color" :class="{ 'is-animating': isAnimating }" :style="{ backgroundColor: bgColor }"></div>

        <div class="c-game__round">
          <h3>Ronde {{ currentRound }} / {{ totalRounds }}</h3>
          <div class="c-game__progressbar">
            <div class="c-game__progressbar-fill" :style="{ width: (currentRound / totalRounds) * 100 + '%' }"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.c-gamecontainer {
  position: relative;
  width: 100%;
  height: 100dvh;
  overflow: hidden;
}

.c-countdown {
  position: fixed;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  inset: 0;
  background: var(--gray-90);
  z-index: 1200;

  .c-countdown__number {
    color: white;
    font-weight: 700;
    font-size: 4rem;
    padding: 0rem 1rem;
    border-radius: 0.5rem;
    animation: pop 0.45s ease forwards;
    user-select: none;
  }

  .c-countdown__text {
    margin-top: 1rem;
    color: var(--color-white);
    font-size: 1.5rem;
    user-select: none;
  }
}

.c-game {
  display: flex;
  flex-direction: column;
  height: 100dvh;
  width: 100vw;
  overflow: hidden;

  .c-game__top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem 0.75rem;
  }

  .c-game__close {
    display: flex;
    align-items: center;
    gap: 0.3125rem;
    text-decoration: none;
    color: var(--gray-80);
    background-color: transparent;
    border: none;
    cursor: pointer;

    .c-game__close-icon {
      width: 1.5rem;
      height: 1.5rem;
    }
  }

  .c-game__span {
    display: flex;
    align-items: end;
    width: 1.5rem;
    height: 1.5rem;
  }

  .c-game__timer {
    display: flex;
    align-items: end;
    gap: 0.3125rem;
    color: var(--gray-80);

    .c-game__timer-icon {
      width: 1.5rem;
      height: 1.5rem;
    }
  }

  .c-game__bot {
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

  .c-game__round {
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

  .c-game__progressbar {
    width: 100%;
    height: 1.5625rem;
    background: var(--color-white);
    border-radius: var(--radius-40);
    margin-top: 0.5rem;
    overflow: hidden;
    padding: 0.1875rem;
  }

  .c-game__progressbar-fill {
    height: 100%;
    background: var(--blue-100);
    border-radius: var(--radius-40);
    transition: width 0.3s ease;
  }
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
