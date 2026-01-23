<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
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

const { formattedTime, startTimer, stopTimer } = useGameTimer();

const chosenColors = ref([]);
let detectedGameId = 1;
try {
  const raw = sessionStorage.getItem('lastGamePayload');
  if (raw) {
    const parsed = JSON.parse(raw || '{}');
    if (Array.isArray(parsed.kleuren)) {
      chosenColors.value = parsed.kleuren.map((c) => String(c).toLowerCase());
    }
    detectedGameId = parsed.gameId || parsed.game_id || parsed.spelId || parsed.spel_id || parsed.id || parsed.game || detectedGameId;
  }
} catch (e) {
  chosenColors.value = [];
}

const showMapping = ref(false);
const mappingData = ref([]);
const rawMappingPayload = ref(null);

const showIntro = ref(true);
const introDurationMs = 2000; // change this number to set seconds
let introTimer = null;

function beginGame() {
  console.debug('[NumberMatch] beginGame');
  showIntro.value = false;
  try {
    enableAudio().catch(() => {});
  } catch (e) {}
  // Start countdown; use slight delay as a fallback to avoid blocking UI
  setTimeout(() => {
    try {
      startCountdown();
    } catch (e) {
      console.error('[NumberMatch] startCountdown error', e);
    }
  }, 50);
}

const { countdown, showCountdown, countdownText, startCountdown } = useGameCountdown({
  gameId: detectedGameId,
  onComplete: () => {
    showMapping.value = true;
  },
});

const isAnimating = ref(false);
const currentNumber = ref(null);

const kleuren = {
  blauw: '#2979ff', // blauw
  rood: '#f91818', // rood
  geel: '#ffc400', // geel
  groen: '#00b709', // groen
};

let _socket = null;

const mappingItems = computed(() => {
  if (mappingData.value && mappingData.value.length) return mappingData.value;
  const base = chosenColors.value && chosenColors.value.length ? chosenColors.value : Object.keys(kleuren);
  if (!base || !base.length) return [];
  return base.map((k, i) => ({ kleur: String(k).toLowerCase(), nummer: i + 1 }));
});

const mappingLayoutClass = computed(() => {
  const n = Math.min(4, Math.max(1, mappingItems.value.length || 1));
  return `mapping-layout-${n}`;
});

onMounted(async () => {
  try {
    _socket = connectSocket();
    _socket.on('connect', () => {
      console.log('[socket] connected', _socket && _socket.id);
    });

    if (typeof _socket.onAny === 'function') {
      _socket.onAny((event, ...args) => {
        try {
          console.debug(`[socket:onAny] event=`, event, 'args=', args);
        } catch (e) {
          console.debug('[socket:onAny] event=', event);
        }
      });
    } else {
      console.debug('[socket] onAny not available on this socket instance');
    }

    _socket.on('nummer_mapping', (payload) => {
      console.log('[socket] nummer_mapping received:', payload);
      rawMappingPayload.value = payload;
      if (payload && typeof payload === 'object' && payload.mapping) {
        payload = payload.mapping;
        console.log('[socket] nummer_mapping normalized payload.mapping ->', payload);
      }

      let items = [];
      if (Array.isArray(payload)) {
        if (payload.length && typeof payload[0] === 'object') {
          items = payload.map((p) => ({ kleur: (p.kleur || p.color || '').toString().toLowerCase(), nummer: p.nummer ?? p.number ?? p.value }));
        } else {
          items = payload.map((k, i) => ({ kleur: String(k).toLowerCase(), nummer: i + 1 }));
        }
      } else if (payload && typeof payload === 'object') {
        Object.keys(payload).forEach((k) => {
          items.push({ kleur: String(k).toLowerCase(), nummer: payload[k] });
        });
      }

      items = items.map((it) => ({ kleur: String(it.kleur).toLowerCase(), nummer: Number(it.nummer) })).filter((it) => it.kleur && !isNaN(it.nummer));

      items.sort((a, b) => a.nummer - b.nummer);

      console.debug('[socket] nummer_mapping processed items:', items);
      console.table(items);

      mappingData.value = items;
    });

    _socket.on('gekozen_nummer', (payload) => {
      console.log('[socket] gekozen_nummer received:', payload);
      if (Array.isArray(payload) && payload.length) payload = payload[0];

      let nummer = null;
      let round = null;
      let total = null;
      if (typeof payload === 'number') nummer = payload;
      else if (typeof payload === 'string' && !isNaN(Number(payload))) nummer = Number(payload);
      else if (payload && typeof payload === 'object') {
        nummer = payload.nummer ?? payload.number ?? payload.value ?? null;
        if ((nummer === null || nummer === undefined) && payload.kleur) {
          const norm = String(payload.kleur).toLowerCase();
          const fromMapping = (mappingData.value || []).find((it) => String(it.kleur).toLowerCase() === norm);
          if (fromMapping) nummer = fromMapping.nummer;
          else {
            const idx = (chosenColors.value || []).indexOf(norm);
            if (idx >= 0) nummer = idx + 1;
          }
        }

        round = payload.rondenummer || payload.ronde || payload.round || null;
        total = payload.maxronden || payload.totaal || payload.total || null;
      }

      if (nummer !== null && (typeof nummer === 'number' || !isNaN(Number(nummer)))) {
        currentNumber.value = Number(nummer);
        try {
          const mapped = (mappingData.value || []).find((it) => Number(it.nummer) === Number(nummer));
          console.debug('[socket] gekozen_nummer resolved mapping ->', mapped);
        } catch (e) {}
        isAnimating.value = true;
        setTimeout(() => {
          isAnimating.value = false;
        }, 150);
        if (showMapping.value) {
          showMapping.value = false;
          startTimer();
        }
      }

      if (round !== null && !isNaN(Number(round))) currentRound.value = Number(round);
      if (total !== null && !isNaN(Number(total))) totalRounds.value = Number(total);
    });

    _socket.on('game_einde', () => {
      console.log('[socket] game_einde received');
      stopTimer();
      router.push('/resultaten/proficiat');
    });
  } catch (e) {
    // socket connect may fail (CORS, network) — ignore here
  }

  if (showIntro.value) {
    introTimer = setTimeout(async () => {
      try {
        await tryResumeIfExists();
      } catch (e) {}
      beginGame();
    }, introDurationMs);
  }
});

onUnmounted(() => {
  try {
    if (_socket) {
      _socket.off('game_einde');
      _socket.off('nummer_mapping');
      _socket.off('gekozen_nummer');
    }
  } finally {
    stopTimer();
    disconnectSocket();
    if (introTimer) {
      clearTimeout(introTimer);
      introTimer = null;
    }
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

    <!-- Intro instruction overlay shown before countdown (click anywhere to start) -->
    <div v-if="showIntro" class="c-game__intro" @click.self="beginGame" role="button" aria-label="Start game">
      <div class="c-game__intro-content">
        <h2>Number Match</h2>
        <p>Onthoud welke kleur bij welk nummer hoort. Wacht op het startsignaal.</p>
      </div>
    </div>

    <div v-else class="c-game">
      <GameHeader :formatted-time="formattedTime" @stop="goBack" />

      <div class="c-game__content">
        <div class="c-game__background"></div>

        <div v-if="showMapping" class="c-game__mapping">
          <div :class="['c-game__mapping-grid', mappingLayoutClass]">
            <template v-for="(item, index) in mappingItems" :key="item.kleur + '-' + item.nummer">
              <div class="c-game__mapping-item" :style="{ backgroundColor: kleuren[item.kleur] || '#ccc' }">
                <div class="c-game__mapping-number">{{ item.nummer }}</div>
                <div class="c-game__mapping-label">{{ item.kleur }}</div>
              </div>
            </template>
          </div>
        </div>

        <div v-else class="c-game__number-area">
          <div class="c-game__number" :class="{ 'is-animating': isAnimating }">
            <span v-if="currentNumber !== null">{{ currentNumber }}</span>
            <span v-else class="c-game__waiting">Wachten...</span>
          </div>
        </div>

        <GameProgress v-if="!showMapping" :current-round="currentRound" :total-rounds="totalRounds" />
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

.c-game__mapping {
  position: absolute;
  z-index: 2;
  inset: 0;
  display: flex;
  align-items: stretch;
  justify-content: stretch;
}
.c-game__mapping-grid {
  width: 100%;
  height: 100%;
  display: grid;
  gap: 0.5rem;
  grid-auto-rows: 1fr;
  grid-auto-flow: dense;
  grid-template-columns: repeat(auto-fit, minmax(0, 1fr));
}
.c-game__mapping-grid.mapping-layout-1 {
  grid-template-columns: 1fr;
  grid-template-rows: 1fr;
}
.c-game__mapping-grid.mapping-layout-2 {
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: 1fr;
}
.c-game__mapping-grid.mapping-layout-3 {
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: 1fr 1fr;
}
.c-game__mapping-grid.mapping-layout-3 .c-game__mapping-item:nth-child(3) {
  grid-column: 1 / -1;
}
.c-game__mapping-grid.mapping-layout-4 {
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
}
.c-game__mapping-item {
  width: 100%;
  height: 100%;
  border-radius: 0.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
}
.c-game__mapping-number {
  font-size: 5rem;
}
.c-game__mapping-label {
  font-size: 1.2rem;
  margin-top: 0.5rem;
  text-transform: uppercase;
  opacity: 0.9;
}

.c-game__intro {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 30;
}
.c-game__intro-content {
  text-align: center;
  color: white;
  padding: 2rem;
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

.c-game__number-area {
  position: absolute;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  inset: 0;
}
.c-game__number {
  font-size: 6rem;
  color: white;
  font-weight: 800;
  text-shadow: 0 6px 18px rgba(0, 0, 0, 0.4);
}
.c-game__number.is-animating {
  transform: scale(1.08);
  transition: transform 120ms ease-out;
}
.c-game__waiting {
  font-size: 1.25rem;
  color: rgba(255, 255, 255, 0.85);
}
</style>

<style scoped>
.c-debug-panel {
  position: fixed;
  right: 0.5rem;
  top: 3.5rem;
  width: 280px;
  max-height: 60vh;
  overflow: auto;
  background: rgba(0, 0, 0, 0.7);
  color: #fff;
  padding: 0.5rem;
  font-size: 12px;
  z-index: 100;
  border-radius: 6px;
}
.c-debug-panel pre {
  white-space: pre-wrap;
  word-break: break-word;
  color: #dfe6ff;
}
</style>
