<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useGameTimer } from '../../composables/useGameTimer.js';
import { useGameCountdown } from '../../composables/useGameCountdown.js';
import GameCountdown from '../../components/game/GameCountdown.vue';
import GameHeader from '../../components/game/GameHeader.vue';
import GameProgress from '../../components/game/GameProgress.vue';
import { connectSocket, disconnectSocket } from '../../services/socket.js';
import IntroOverlay from '../../components/game/IntroOverlay.vue';

const router = useRouter();
const currentRound = ref(1);
const totalRounds = ref(5);
const speler1Naam = ref('Speler 1');
const speler2Naam = ref('Speler 2');
const speler1Kleur = ref('');
const speler2Kleur = ref('');
const speler1Uitkomst = ref('');
const speler2Uitkomst = ref('');

const kleurenMap = {
  blauw: '#2979ff',
  rood: '#f91818',
  geel: '#ffc400',
  groen: '#00b709',
};

function resolveKleur(value) {
  if (!value) return '';
  const key = String(value).toLowerCase();
  return kleurenMap[key] || value;
}

function normalizeUitkomst(value) {
  const key = String(value || '').toLowerCase();
  if (['juist', 'correct', 'goed', 'win', 'winner'].includes(key)) return 'juist';
  if (['te laat', 'telaat', 'too late'].includes(key)) return 'te-laat';
  if (['fout', 'incorrect', 'verkeerd', 'lose', 'loser'].includes(key)) return '';
  return '';
}

function resultClass(value) {
  return value === 'te-laat' ? 'fout' : value;
}

function resultLabel(value) {
  if (value === 'juist') return 'GOED';
  if (value === 'te-laat') return 'TE LAAT';
  return 'FOUT';
}

const speler1PanelBg = computed(() => speler1Kleur.value || 'rgba(255, 255, 255, 0.08)');
const speler2PanelBg = computed(() => speler2Kleur.value || 'rgba(255, 255, 255, 0.08)');

let _socket = null;

let detectedGameId = 1;
try {
  const raw = sessionStorage.getItem('lastGamePayload');
  if (raw) {
    const parsed = JSON.parse(raw || '{}');
    detectedGameId = parsed.gameId || parsed.game_id || parsed.spelId || parsed.spel_id || parsed.id || parsed.game || detectedGameId;
  }
} catch (e) {}

const { formattedTime, startTimer, stopTimer } = useGameTimer();
const { countdown, showCountdown, countdownText, startCountdown } = useGameCountdown({
  gameId: detectedGameId,
  onComplete: () => {
    startTimer();
  },
});

const showIntro = ref(true);

function beginGame() {
  // overlay done
}

function onOverlayExiting() {
  try {
    startCountdown();
  } catch (e) {}
}

function goBack() {
  stopTimer();
  router.push({ name: 'games' });
}

onMounted(async () => {
  try {
    _socket = connectSocket();
    _socket.on('connect', () => {
      console.log('[socket] connected', _socket && _socket.id);
    });
    _socket.on('colorbattle_start', (payload) => {
      console.log('[socket] colorbattle_start received:', payload);
      if (payload?.speler1_naam) speler1Naam.value = payload.speler1_naam;
      if (payload?.speler2_naam) speler2Naam.value = payload.speler2_naam;
      const rounds = payload?.aantal_rondes ?? payload?.rondes ?? null;
      if (rounds !== null && !isNaN(Number(rounds))) totalRounds.value = Number(rounds);
    });
    _socket.on('colorbattle_ronde', (payload) => {
      console.log('[socket] colorbattle_ronde received:', payload);
      const round = payload?.rondenummer ?? payload?.ronde ?? payload?.round ?? null;
      const total = payload?.maxronden ?? payload?.aantal_rondes ?? payload?.total ?? null;
      if (round !== null && !isNaN(Number(round))) currentRound.value = Number(round);
      if (total !== null && !isNaN(Number(total))) totalRounds.value = Number(total);
      speler1Uitkomst.value = '';
      speler2Uitkomst.value = '';
      if (payload?.speler1_kleur) speler1Kleur.value = resolveKleur(payload.speler1_kleur);
      if (payload?.speler2_kleur) speler2Kleur.value = resolveKleur(payload.speler2_kleur);
    });
    _socket.on('colorbattle_ronde_einde', (payload) => {
      console.log('[socket] colorbattle_ronde_einde received:', payload);
      if (payload?.speler1_uitkomst) {
        const norm = normalizeUitkomst(payload.speler1_uitkomst);
        if (norm) {
          speler1Uitkomst.value = norm;
        }
      }
      if (payload?.speler2_uitkomst) {
        const norm = normalizeUitkomst(payload.speler2_uitkomst);
        if (norm) {
          speler2Uitkomst.value = norm;
        }
      }
    });
    _socket.on('colorbattle_einde', (payload) => {
      console.log('[socket] colorbattle_einde received:', payload);
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
      _socket.off('colorbattle_start');
      _socket.off('colorbattle_ronde');
      _socket.off('colorbattle_ronde_einde');
      _socket.off('colorbattle_einde');
    }
  } finally {
    disconnectSocket();
  }
  stopTimer();
});
</script>

<template>
  <div class="c-game-root">
    <GameCountdown v-if="showCountdown" :countdown="countdown" :text="countdownText" />

    <IntroOverlay v-model="showIntro" @exiting="onOverlayExiting" :durationMs="2000" title="Color Battle" text="Twee spelers, één strijd. Wacht op het startsignaal." overlayClass="c-game__intro" contentClass="c-game__intro-content" @done="beginGame" />

    <div v-if="!showIntro" class="c-game">
      <GameHeader :formatted-time="formattedTime" @stop="goBack" />

      <div class="c-game__content">
        <div class="c-game__background"></div>

        <div class="c-game__arena">
          <div class="c-game__panel c-game__panel--left" :style="{ backgroundColor: speler1PanelBg }">
            <h2>{{ speler1Naam }}</h2>
          </div>
          <div class="c-game__vs">VS</div>
          <div class="c-game__panel c-game__panel--right" :style="{ backgroundColor: speler2PanelBg }">
            <h2>{{ speler2Naam }}</h2>
          </div>
        </div>

        <transition name="result-overlay">
          <div v-if="speler1Uitkomst || speler2Uitkomst" class="c-game__result-overlay">
            <div :class="['c-game__result-block', `c-game__result--${resultClass(speler1Uitkomst)}`]">
              <div class="c-game__result-name">{{ speler1Naam }}</div>
              <div class="c-game__result-label">{{ resultLabel(speler1Uitkomst) }}</div>
            </div>
            <div :class="['c-game__result-block', `c-game__result--${resultClass(speler2Uitkomst)}`]">
              <div class="c-game__result-name">{{ speler2Naam }}</div>
              <div class="c-game__result-label">{{ resultLabel(speler2Uitkomst) }}</div>
            </div>
          </div>
        </transition>

        <GameProgress :current-round="currentRound" :total-rounds="totalRounds" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.c-game-root {
  height: 100vh;
  width: 100vw;
}

.c-game {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
}

.c-game__content {
  flex: 1;
  display: flex;
  align-items: start;
  justify-content: flex-start;
  position: relative;
  overflow: hidden;
}

.c-game__background {
  position: absolute;
  inset: 0;
  background: var(--gray-90);
  z-index: 0;
}

.c-game__arena {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
}

.c-game__panel {
  background: var(--gray-90);
  padding: 2.5rem 1.5rem;
  text-align: center;
  color: var(--color-white);
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 0.75rem;
  backdrop-filter: blur(6px);
  transition: none;
}

.c-game__panel h2 {
  font-size: 1.5rem;
}

.c-game__vs {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  z-index: 2;
  font-weight: 800;
  color: var(--color-white);
  font-size: 1.5rem;
  letter-spacing: 0.2rem;
  background: rgba(15, 23, 42, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 999px;
  padding: 0.4rem 1.2rem;
  box-shadow: 0 10px 26px rgba(0, 0, 0, 0.35);
}

.c-game__result-overlay {
  position: fixed;
  inset: 0;
  z-index: 3000;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 0;
  background: var(--gray-90);
  pointer-events: all;
}

.c-game__result-block {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--color-white);
  text-align: center;
  gap: 0.5rem;
  position: relative;
  overflow: hidden;
}

.c-game__result-block + .c-game__result-block {
  border-top: 1px solid rgba(255, 255, 255, 0.12);
}

.c-game__result-name {
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  opacity: 0.8;
}

.c-game__result-label {
  font-size: clamp(2.2rem, 5vw, 3rem);
  font-weight: 900;
  letter-spacing: 0.08em;
  padding: 0.5rem 1.6rem;
  border-radius: 999px;
}

.c-game__result--juist {
  background: var(--gray-90);
  color: var(--color-green);
}

.c-game__result--fout {
  background: var(--gray-90);
  color: var(--color-red);
}

/* Overlay enter/leave */
.result-overlay-enter-active,
.result-overlay-leave-active {
  transition:
    opacity 200ms ease,
    transform 240ms ease;
}

.result-overlay-enter-from,
.result-overlay-leave-to {
  opacity: 0;
  transform: scale(0.98);
}

.result-overlay-enter-to,
.result-overlay-leave-from {
  opacity: 1;
  transform: scale(1);
}

@keyframes result-pop {
  0% {
    transform: scale(0.85);
    opacity: 0;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

@media (width < 768px) {
  .c-game__vs {
    text-align: center;
  }
}
</style>
