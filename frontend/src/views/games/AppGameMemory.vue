<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import IntroOverlay from '../../components/game/IntroOverlay.vue';
import { useRouter } from 'vue-router';

import { connectSocket, disconnectSocket } from '../../services/socket.js';
import { enableAudio, tryResumeIfExists } from '../../services/sound.js';
import { useGameTimer } from '../../composables/useGameTimer.js';
import { useGameCountdown } from '../../composables/useGameCountdown.js';
import GameCountdown from '../../components/game/GameCountdown.vue';
import GameHeader from '../../components/game/GameHeader.vue';
import GameProgress from '../../components/game/GameProgress.vue';

const currentRound = ref(1);
const totalRounds = ref(5);
const bgColor = ref('#313335');
const isAnimating = ref(false);
const showWaitingScreen = ref(false);
const showRoundScreen = ref(false);

const kleuren = {
  blauw: '#2979ff',
  rood: '#f91818',
  geel: '#ffc400',
  groen: '#00b709',
};

const { formattedTime, startTimer, stopTimer } = useGameTimer();

const { countdown, showCountdown, countdownText, startCountdown } = useGameCountdown({
  gameId: 2,
  onComplete: () => {
    startTimer();
  },
});

const showIntro = ref(true);

function beginGame() {
  console.debug('[Memory] beginGame (overlay done)');
  try {
    enableAudio().catch(() => {});
  } catch (e) {}
}

async function onOverlayExiting() {
  // overlay starting to hide: resume audio and start countdown underneath
  try {
    await tryResumeIfExists();
  } catch (e) {}
  try {
    startCountdown();
  } catch (e) {
    console.error('[Memory] startCountdown error', e);
  }
}

const router = useRouter();

const goBack = () => {
  stopTimer();
  router.push({ name: 'games' });
};

let _socket = null;

onMounted(async () => {
  try {
    _socket = connectSocket();
    _socket.on('connect', () => {
      console.log('[socket] connected', _socket && _socket.id);
    });

    _socket.on('ronde_start', (payload) => {
      console.log('[socket] ronde_start received:', payload);

      bgColor.value = '#313335';
      isAnimating.value = false;

      showWaitingScreen.value = false;

      showRoundScreen.value = true;

      if (payload && typeof payload === 'object') {
        const round = payload.rondenummer || payload.ronde || payload.round || null;
        const total = payload.maxronden || payload.totaal || payload.total || null;

        if (round !== null && typeof round === 'number') {
          currentRound.value = round;
        }
        if (total !== null && typeof total === 'number') {
          totalRounds.value = total;
        }
      }
    });

    _socket.on('wacht_even', (payload) => {
      console.log('[socket] wacht_even received:', payload);

      let message = null;
      if (typeof payload === 'string') {
        message = payload;
      } else if (payload && typeof payload === 'object') {
        message = payload.bericht || payload.message || null;
      }

      if (message === 'start') {
        showRoundScreen.value = false;
      }
    });

    _socket.on('kleuren_getoond', (payload) => {
      console.log('[socket] kleuren_getoond received:', payload);

      showWaitingScreen.value = true;
    });

    _socket.on('toon_kleur', (payload) => {
      console.log('[socket] toon_kleur received:', payload);

      let color = null;
      if (typeof payload === 'string') {
        color = payload;
      } else if (payload && typeof payload === 'object') {
        color = payload.kleur || payload.color || null;
      }

      if (!color || typeof color !== 'string') return;

      const norm = color.toLowerCase();
      const newColor = kleuren[norm] || color;

      isAnimating.value = true;
      setTimeout(() => {
        bgColor.value = newColor;
        setTimeout(() => {
          isAnimating.value = false;
        }, 60);
      }, 60);
    });

    _socket.on('game_einde', (payload) => {
      console.log('[socket] game_einde received', payload);

      let status = null;
      if (typeof payload === 'string') {
        status = payload;
      } else if (payload && typeof payload === 'object') {
        status = payload.status || null;
      }

      if (status === 'game gedaan') {
        stopTimer();
        router.push('/resultaten/proficiat');
      }
    });
  } catch (err) {
    console.error('[socket] error:', err);
  }

  // Intro overlay is handled by IntroOverlay component (auto-advances and resumes audio)
});

onUnmounted(() => {
  try {
    if (_socket) {
      _socket.off('ronde_start');
      _socket.off('wacht_even');
      _socket.off('kleuren_getoond');
      _socket.off('toon_kleur');
      _socket.off('game_einde');
    }
  } finally {
    stopTimer();
    // IntroOverlay clears its own timer
  }
});
</script>

<template>
  <div class="c-game-root">
    <GameCountdown v-if="showCountdown" :countdown="countdown" :text="countdownText" />

    <IntroOverlay v-model="showIntro" @exiting="onOverlayExiting" :durationMs="2000" title="Memory" text="Wacht tot de kleuren getoond zijn. Kijk goed en probeer ze te onthouden." overlayClass="c-game-memory__intro" contentClass="c-game-memory__intro-content" @done="beginGame" />

    <div v-if="!showIntro" class="c-game-memory">
      <GameHeader :formatted-time="formattedTime" @stop="goBack" />

      <div class="c-game-memory__content">
        <div class="c-game-memory__background"></div>
        <div class="c-game-memory__color" :class="{ 'is-animating': isAnimating }" :style="{ backgroundColor: bgColor }"></div>

        <!-- Round screen overlay -->
        <div v-if="showRoundScreen" class="c-game-memory__round-screen">
          <div class="c-game-memory__round-content">
            <h2>Ronde {{ currentRound }}</h2>
          </div>
        </div>

        <!-- Waiting screen overlay -->
        <div v-if="showWaitingScreen" class="c-game-memory__waiting">
          <div class="c-game-memory__waiting-content">
            <h2>Doe maar!</h2>
            <p>Wachten op volgende ronde...</p>
          </div>
        </div>

        <GameProgress :current-round="currentRound" :total-rounds="totalRounds" />
      </div>
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

.c-game-memory__background {
  position: absolute;
  inset: 0;
  background: var(--gray-80);
  z-index: 0;
}

.c-game-memory__color {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  transition:
    border-radius 0.2s ease-out,
    transform 0.2s ease-out;
}

.c-game-memory__color.is-animating {
  border-radius: 50%;
  transform: scale(0);
}

.c-game-memory__round-screen {
  position: absolute;
  inset: 0;
  background: var(--gray-90);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 15;
  animation: fadeIn 0.3s ease;
}

.c-game-memory__round-content {
  text-align: center;
  color: white;
}

.c-game-memory__round-content h2 {
  font-size: 2.5rem;
  margin: 0 0 1.5rem 0;
  font-weight: bold;
}

.c-game-memory__round-countdown {
  font-size: 4rem;
  margin: 0;
  font-weight: bold;
  color: #2979ff;
}

.c-game-memory__waiting {
  position: absolute;
  inset: 0;
  background: var(--gray-90);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  animation: fadeIn 0.3s ease;
}

.c-game-memory__waiting-content {
  text-align: center;
  color: white;
}

.c-game-memory__waiting-content h2 {
  font-size: 2rem;
  margin: 0 0 1rem 0;
}

.c-game-memory__waiting-content p {
  font-size: 1.25rem;
  margin: 0;
  opacity: 0.8;
}

.c-game-memory__intro {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 30;
}
.c-game-memory__intro-content {
  text-align: center;
  color: white;
  padding: 2rem;
}
.c-game-memory__intro-content p {
  margin: 1rem 0 2rem 0;
}
.btn {
  padding: 0.6rem 1.2rem;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
}
.btn-primary {
  background: var(--blue-500);
  color: white;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
