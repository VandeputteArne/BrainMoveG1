<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { connectSocket, disconnectSocket } from '../../services/socket.js';
import { enableAudio, tryResumeIfExists } from '../../services/sound.js';
import { useGameTimer } from '../../composables/useGameTimer.js';
import { useGameCountdown } from '../../composables/useGameCountdown.js';
import { useGameDeviceGuard } from '../../composables/useGameDeviceGuard.js';
import GameCountdown from '../../components/game/GameCountdown.vue';
import GameHeader from '../../components/game/GameHeader.vue';
import GameProgress from '../../components/game/GameProgress.vue';
import IntroOverlay from '../../components/game/IntroOverlay.vue';

const router = useRouter();

const currentRound = ref(1);
const totalRounds = ref(5);
const showIntro = ref(true);
const { formattedTime, startTimer, stopTimer } = useGameTimer();

let detectedGameId = 1;
try {
  const raw = sessionStorage.getItem('lastGamePayload');
  if (raw) {
    const parsed = JSON.parse(raw || '{}');
    detectedGameId = parsed.gameId || parsed.game_id || parsed.spelId || parsed.spel_id || parsed.id || parsed.game || detectedGameId;
  }
} catch (e) {}

const { countdown, showCountdown, countdownText, startCountdown } = useGameCountdown({
  gameId: detectedGameId,
  onComplete: () => {
    startTimer();
  },
});

useGameDeviceGuard(detectedGameId);
const kleuren = {
  blauw: '#2979ff',
  rood: '#f91818',
  geel: '#ffc400',
  groen: '#00b709',
};

const currentColor = ref('');
const fallPercentage = ref(0); // 0..100
const fallTimeMs = ref(2000);
const isFalling = ref(false);
const landed = ref(false);
const showWaiting = ref(false);
const particles = ref([]);
const showExplosion = ref(false);
const horizontalBias = ref(0); // px offset: negative = left, positive = right
const horizontalAmp = ref(15); // amplitude for sine curve in px
const wrapperRef = ref(null);
const wrapperWidth = ref(0);

function updateWrapperWidth() {
  try {
    if (wrapperRef.value && wrapperRef.value.clientWidth) wrapperWidth.value = wrapperRef.value.clientWidth;
    else wrapperWidth.value = window.innerWidth;
  } catch (e) {
    wrapperWidth.value = window.innerWidth;
  }
}

let _socket = null;
function beginGame() {
  try {
    enableAudio().catch(() => {});
  } catch (e) {}
}

async function onOverlayExiting() {
  try {
    await tryResumeIfExists();
  } catch (e) {}
  try {
    startCountdown();
  } catch (e) {
    console.error('[Falling] startCountdown error', e);
  }
}

function goBack() {
  stopTimer();
  router.push({ name: 'games' });
}

onMounted(async () => {
  // measure wrapper width and update on resize
  updateWrapperWidth();
  window.addEventListener('resize', updateWrapperWidth);
  try {
    _socket = connectSocket();
    _socket.on('connect', () => {
      console.log('[socket] connected', _socket && _socket.id);
    });

    _socket.on('vallende_kleur_start', (payload) => {
      console.log('[socket] vallende_kleur_start received:', payload);
      showWaiting.value = false;
      isFalling.value = true;

      const kleur = payload && (payload.kleur || payload.color) ? String(payload.kleur || payload.color).toLowerCase() : '';
      const ronde = payload && (payload.rondenummer || payload.ronde || payload.round) ? Number(payload.rondenummer || payload.ronde || payload.round) : null;
      const max = payload && (payload.maxronden || payload.totaal || payload.total) ? Number(payload.maxronden || payload.totaal || payload.total) : null;
      const valTijd = payload && (payload.val_tijd || payload.val_tijd_ms || payload.valtijd) ? Number(payload.val_tijd || payload.val_tijd_ms || payload.valtijd) : null;

      currentColor.value = kleur || '';
      if (ronde !== null && !isNaN(ronde)) currentRound.value = ronde;
      if (max !== null && !isNaN(max)) totalRounds.value = max;
      if (valTijd && !isNaN(valTijd)) fallTimeMs.value = valTijd;

      // decide horizontal bias for this falling color: sometimes center, sometimes left/right
      // compute max available bias based on wrapper width and orb size
      const orbEl = wrapperRef.value ? wrapperRef.value.querySelector('.c-falling-orb') : null;
      const orbSize = orbEl ? orbEl.offsetWidth : 136; // fallback ~8.5rem
      const maxBias = Math.max(0, Math.floor(wrapperWidth.value / 2 - orbSize / 2 - 8));

      const r = Math.random();
      if (r < 0.33) {
        horizontalBias.value = 0; // center
      } else if (r < 0.66) {
        horizontalBias.value = -Math.round(Math.random() * maxBias);
      } else {
        horizontalBias.value = Math.round(Math.random() * maxBias);
      }
      horizontalAmp.value = 10 + Math.random() * Math.min(60, Math.max(8, maxBias / 6)); // curve amplitude scales with available width

      fallPercentage.value = 0;
      // Fallback animatie
      const start = Date.now();
      const duration = fallTimeMs.value || 2000;
      const raf = () => {
        const elapsed = Date.now() - start;
        const pct = Math.min(100, Math.round((elapsed / duration) * 100));
        fallPercentage.value = pct;
        if (pct < 100 && isFalling.value) requestAnimationFrame(raf);
      };
      requestAnimationFrame(raf);
    });

    _socket.on('vallende_kleur_percentage', (payload) => {
      if (!payload) return;
      const pct = payload.percentage ?? payload.percentage_value ?? payload.percentagePct ?? null;
      if (pct !== null && !isNaN(Number(pct))) {
        const normalized = Math.max(0, Math.min(100, Number(pct)));
        fallPercentage.value = normalized;

        if (normalized >= 100) {
          landed.value = true;
          showExplosion.value = true;

          // Genereer explosie deeltjes
          particles.value = Array.from({ length: 20 }, (_, i) => ({
            id: i,
            angle: i * 18 + Math.random() * 10,
            speed: 0.8 + Math.random() * 0.6,
            size: 6 + Math.random() * 8,
          }));

          setTimeout(() => {
            landed.value = false;
            isFalling.value = false;
            showExplosion.value = false;
            particles.value = [];
            horizontalBias.value = 0;
            horizontalAmp.value = 15;
          }, 1200);
        }
      }
      const ronde = payload.rondenummer || payload.ronde || payload.round || null;
      if (ronde !== null && !isNaN(Number(ronde))) currentRound.value = Number(ronde);
    });
    _socket.on('wacht_even', (payload) => {
      console.log('[socket] wacht_even received:', payload);
      showWaiting.value = true;
      isFalling.value = false;
    });
    _socket.on('game_einde', (payload) => {
      console.log('[socket] game_einde received:', payload);
      stopTimer();
      router.push('/resultaten/proficiat');
    });
  } catch (e) {
    console.error('[socket] error:', e);
  }
});
onUnmounted(() => {
  try {
    if (_socket) {
      _socket.off('vallende_kleur_start');
      _socket.off('vallende_kleur_percentage');
      _socket.off('wacht_even');
      _socket.off('game_einde');
    }
  } finally {
    stopTimer();
    window.removeEventListener('resize', updateWrapperWidth);
  }
});
</script>

<template>
  <div class="c-game-root c-game-falling">
    <GameCountdown v-if="showCountdown" :countdown="countdown" :text="countdownText" />

    <IntroOverlay v-model="showIntro" :durationMs="2000" title="Falling Colors" text="Kijk goed welke kleur er naar beneden valt!" overlayClass="c-game__intro" contentClass="c-game__intro-content" @exiting="onOverlayExiting" @done="beginGame" />

    <div v-if="!showIntro" class="c-game">
      <GameHeader :formatted-time="formattedTime" @stop="goBack" />

      <div class="c-game__content">
        <div class="c-game__background">
          <div class="stars"></div>
        </div>

        <div class="c-falling-wrapper" ref="wrapperRef">
          <div
            class="c-falling-orb"
            :class="{ 'is-falling': isFalling, 'is-landed': landed }"
            :style="{
              transform: `translate(calc(-50% + ${horizontalBias}px + ${Math.sin(fallPercentage * 0.04) * horizontalAmp}px), ${Math.min(100, fallPercentage)}vh)`,
              transition: isFalling ? `transform ${fallTimeMs}ms cubic-bezier(0.45, 0.05, 0.55, 0.95)` : 'none',
              opacity: fallPercentage > 0 ? 1 : 0,
            }"
          >
            <div class="orb-glow" :style="{ color: kleuren[currentColor] || currentColor || '#999' }"></div>

            <div
              class="orb-core"
              :style="{
                backgroundColor: kleuren[currentColor] || currentColor || '#999',
                boxShadow: `inset -10px -10px 20px rgba(0,0,0,0.2), inset 10px 10px 20px rgba(255,255,255,0.4)`,
              }"
            >
              <div class="orb-face">
                <div class="eye left"></div>
                <div class="eye right"></div>
                <div class="mouth"></div>
              </div>
            </div>

            <div
              v-for="i in 15"
              :key="'trail-' + i"
              class="trail-particle"
              :style="{
                '--x-offset': Math.sin(i * 123) * 15 + 'px' /* Willekeurige verspreiding links/rechts */,
                '--delay': i * 0.1 + 's' /* Verspreide starttijd */,
                '--size-scale': 0.6 + Math.random() * 0.5 /* Verschil in grootte */,
                '--drop-color': kleuren[currentColor] || currentColor || '#999',
              }"
            >
              <span class="droplet-gloss"></span>
            </div>

            <div v-if="showExplosion" class="explosion-container">
              <div
                v-for="p in particles"
                :key="p.id"
                class="explosion-particle"
                :style="{
                  '--angle': p.angle + 'deg',
                  '--speed': p.speed,
                  '--size': p.size + 4 + 'px',
                  backgroundColor: p.id % 2 === 0 ? '#fff' : kleuren[currentColor] || currentColor || '#999',
                }"
              ></div>
            </div>
          </div>
        </div>

        <div v-if="showWaiting" class="c-game-waiting">
          <div class="c-game-waiting__content">
            <div class="loading-bounce">
              <div class="bounce-dot"></div>
              <div class="bounce-dot"></div>
              <div class="bounce-dot"></div>
            </div>
            <h2>Wacht even...</h2>
            <p>Het volgende spel komt zo!</p>
          </div>
        </div>

        <GameProgress :current-round="currentRound" :total-rounds="totalRounds" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.c-game {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  font-family: 'Varela Round', 'Comic Sans MS', sans-serif;
  overflow: hidden;
}

.c-game__content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  width: 100%;
}

.c-game__background {
  position: absolute;
  inset: 0;
  background-color: var(--gray-90);
  z-index: 0;
}

.stars {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(white 1px, transparent 1px), radial-gradient(rgba(255, 255, 255, 0.5) 2px, transparent 2px);
  background-size:
    100px 100px,
    200px 200px;
  background-position:
    0 0,
    40px 60px;
  opacity: 0.3;
}

.c-falling-wrapper {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 2;
  perspective: 1000px;
}

.c-falling-orb {
  position: absolute;
  top: 0;
  left: 50%;
  width: 8.5rem;
  height: 8.5rem;
  pointer-events: none;
  opacity: 0;
  z-index: 10;
}

.orb-glow {
  position: absolute;
  inset: -20px;
  border-radius: 50%;
  background: radial-gradient(circle, currentColor 0%, transparent 70%);
  opacity: 0.4;
  filter: blur(15px);
  transition: all 0.2s;
}

.orb-core {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 4px solid rgba(255, 255, 255, 0.2);
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2; /* Bovenop de druppels */
}

.c-falling-orb.is-falling .orb-core {
  animation: jelly-fall 0.6s ease-in-out infinite alternate;
}

@keyframes jelly-fall {
  0% {
    transform: scale(1, 1);
  }
  100% {
    transform: scale(0.95, 1.05);
  }
}

.orb-face {
  position: relative;
  width: 60%;
  height: 40%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  top: -5px;
}

.eye {
  width: 18px;
  height: 24px;
  background: white;
  border-radius: 50%;
  position: relative;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.eye::after {
  content: '';
  position: absolute;
  top: 8px;
  right: 4px;
  width: 6px;
  height: 6px;
  background: #333;
  border-radius: 50%;
}

.mouth {
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 16px;
  height: 10px;
  background: #333;
  border-radius: 0 0 20px 20px;
  opacity: 0.8;
}

.c-falling-orb.is-landed .mouth {
  width: 20px;
  height: 6px;
  border-radius: 10px;
}

.trail-particle {
  position: absolute;
  top: 40%;
  left: 50%;
  width: 4rem;
  height: 4rem;

  border-radius: 50%;

  background: var(--drop-color, #999);
  box-shadow:
    inset -2px -4px 6px rgba(0, 0, 0, 0.2),
    /* Schaduw onderin */ inset 2px 2px 6px rgba(255, 255, 255, 0.4); /* Licht bovenin */

  margin-left: -8px; /* Centreren */
  z-index: 1; /* Achter de orb-core */

  animation: liquid-detach 0.8s linear infinite;
  animation-delay: var(--delay);
  opacity: 0; /* Onzichtbaar tot animatie start */
}

.trail-particle .droplet-gloss {
  position: absolute;
  top: 15%;
  left: 20%;
  width: 30%;
  height: 30%;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  filter: blur(0.5px);
}

@keyframes liquid-detach {
  0% {
    transform: translate(-50%, 0) scale(var(--size-scale));
    opacity: 1;
  }
  20% {
    transform: translate(calc(-50% + (var(--x-offset) * 0.3)), -20px) scaleX(0.8) scaleY(1.2) scale(var(--size-scale));
    opacity: 0.9;
  }
  100% {
    transform: translate(calc(-50% + var(--x-offset)), -180px) scale(0);
    opacity: 0;
  }
}

.explosion-container {
  position: absolute;
  inset: 0;
}

.explosion-particle {
  position: absolute;
  top: 50%;
  left: 50%;
  width: var(--size);
  height: var(--size);
  border-radius: 3px;
  margin-left: calc(var(--size) / -2);
  margin-top: calc(var(--size) / -2);
  animation: explode-confetti 1s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
}

@keyframes explode-confetti {
  0% {
    transform: translate(0, 0) rotate(0deg) scale(1);
    opacity: 1;
  }
  100% {
    transform: translate(calc(cos(var(--angle)) * 250px * var(--speed)), calc(sin(var(--angle)) * 250px * var(--speed))) rotate(720deg) scale(0.5);
    opacity: 0;
  }
}

.c-falling-orb.is-landed {
  animation: squash-land 0.4s cubic-bezier(0.2, 0.8, 0.25, 1);
}

@keyframes squash-land {
  0% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(1.4, 0.6) translateY(20px);
  }
  60% {
    transform: scale(0.8, 1.2) translateY(-10px);
  }
  100% {
    transform: scale(1, 1) translateY(0);
  }
}

.c-game-waiting {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 30;
}

.c-game-waiting__content {
  text-align: center;
  color: white;
}

.loading-bounce {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-bottom: 20px;
}
.bounce-dot {
  width: 15px;
  height: 15px;
  background: white;
  border-radius: 50%;
  animation: simple-bounce 0.6s infinite alternate;
}
.bounce-dot:nth-child(2) {
  animation-delay: 0.1s;
}
.bounce-dot:nth-child(3) {
  animation-delay: 0.2s;
}

@keyframes simple-bounce {
  from {
    transform: translateY(0);
  }
  to {
    transform: translateY(-15px);
  }
}
</style>
