<script setup>
import InputGebruikersnaam from '../../components/inputs/InputGebruikersnaam.vue';
import FiltersDifficulty from '../../components/filters/FiltersDifficulty.vue';
import FiltersRounds from '../../components/filters/FiltersRounds.vue';
import FiltersColor from '../../components/filters/FiltersColor.vue';
import LeaderboardSmall from '../../components/leaderboard/LeaderboardSmall.vue';

import { Play } from 'lucide-vue-next';

import { ref, onMounted, onUnmounted, computed, nextTick, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useDeviceStatus } from '../../composables/useDeviceStatus';
import { getApiUrl } from '../../config/api.js';
import { enableAudio } from '../../services/sound.js';
import DetailPopup from '../../components/DetailPopup.vue';

const router = useRouter();
const route = useRoute();

const gameId = computed(() => route.params.id);

const username = ref('');
const usernameError = ref(false);
const usernameInput = ref(null);

const isUsernameValid = computed(() => (username.value || '').toString().trim().length > 0);

const kleurenError = ref(false);

watch(username, (v) => {
  if ((v || '').toString().trim().length > 0) usernameError.value = false;
});

const difficulties = ref([]);
const selectedDifficulty = ref('Gemiddeld');

watch(selectedDifficulty, async (newDifficulty) => {
  if (newDifficulty && gameId.value) {
    await fetchLeaderboard();
  }
});

const roundsOptions = ref([]);
const selectedRounds = ref('');

const smallLeaderboardData = ref([]);

const selectedColor = ref([]);
const backendColors = ref(['blauw', 'rood', 'groen', 'geel']);
const availableColors = ref([]);
const excludedColor = ref('');

const { connectedDevices, disconnectedDevices } = useDeviceStatus();

function updateAvailableFromRefs() {
  try {
    const online = (connectedDevices.value || []).filter((d) => d && (d.status === 'online' || d.status === true));
    const set = new Set(online.map((d) => (d && d.kleur ? d.kleur : null)).filter(Boolean));
    availableColors.value = Array.from(set);
  } catch (e) {
    availableColors.value = [];
  }
}

watch(
  [connectedDevices, disconnectedDevices],
  () => {
    updateAvailableFromRefs();
  },
  { immediate: true, deep: true },
);

watch(
  availableColors,
  (avail) => {
    if (!Array.isArray(avail)) return;
    selectedColor.value = (selectedColor.value || []).filter((c) => avail.includes(c));
  },
  { immediate: true },
);

const gameName = ref('');
const gameDescription = ref('');
const gameImage = ref('');
const showDetailPopup = ref(false);
const detailPopupTitle = ref('');
const detailPopupMessage = ref('');

onMounted(async () => {
  try {
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
  } catch (e) {}
  const cachedDetails = sessionStorage.getItem(`gameDetails_${gameId.value}`);

  if (cachedDetails) {
    const data = JSON.parse(cachedDetails);
    loadGameData(data);
  } else {
    try {
      const res = await fetch(getApiUrl(`games/details/${gameId.value}`));
      const data = await res.json();

      const { leaderboard, ...gameSettings } = data;
      sessionStorage.setItem(`gameDetails_${gameId.value}`, JSON.stringify(gameSettings));

      loadGameData(data);
    } catch (error) {
      console.error('Failed to fetch game details:', error);
    }
  }

  await fetchLeaderboard();

  try {
    const raw = sessionStorage.getItem('last_global_popup');
    if (raw) {
      const parsed = JSON.parse(raw);
      detailPopupTitle.value = parsed.title || '';
      detailPopupMessage.value = parsed.message || '';
      showDetailPopup.value = true;
      sessionStorage.removeItem('last_global_popup');
    }
  } catch (e) {}
});

async function fetchLeaderboard() {
  if (!gameId.value || !selectedDifficulty.value) return;

  try {
    const leaderboardRes = await fetch(getApiUrl(`leaderboard/overview/${gameId.value}/${selectedDifficulty.value}`));
    const leaderboardData = await leaderboardRes.json();

    smallLeaderboardData.value = leaderboardData.slice(0, 3).map((entry) => ({
      name: entry.gebruikersnaam,
      time: entry.waarde,
      unit: entry.eenheid,
    }));
  } catch (error) {
    console.error('Failed to fetch leaderboard:', error);
  }
}

function loadGameData(data) {
  gameName.value = data.game_naam || '';
  gameDescription.value = data.game_beschrijving || '';
  gameImage.value = `/images/cards/${data.game_naam?.toLowerCase().replace(/\s+/g, '')}.png` || '';

  difficulties.value = data.list_moeilijkheden.map((item, index) => ({
    id: String(item.moeilijkheid_id),
    moeilijkheid: item.moeilijkheid,
    snelheid: item.snelheid,
    stars: index + 1,
  }));
  selectedDifficulty.value = difficulties.value.length >= 2 ? difficulties.value[1].id : difficulties.value.length > 0 ? difficulties.value[0].id : '';

  roundsOptions.value = data.aantal_rondes.map((item) => ({
    id: String(item.ronde_id),
    rondes: item.nummer,
  }));
  selectedRounds.value = roundsOptions.value.length > 0 ? roundsOptions.value[0].id : '';

  if (Array.isArray(backendColors.value) && backendColors.value.length && selectedColor.value.length === 0) {
    const init = availableColors.value.length ? backendColors.value.filter((id) => availableColors.value.includes(id) && id !== excludedColor.value) : backendColors.value.filter((id) => id !== excludedColor.value);
    selectedColor.value = init;
  }
}

function updateAvailableColorsFromSession(parsed) {
  try {
    const connected = Array.isArray(parsed.connectedDevices) ? parsed.connectedDevices : [];
    let online = connected.filter((d) => d && (d.status === 'online' || d.status === true));
    if (online.length === 0 && Array.isArray(parsed.apparaten)) {
      online = parsed.apparaten.filter((d) => d && d.status === 'online');
    }
    const set = new Set(online.map((d) => (d && d.kleur ? d.kleur : null)).filter(Boolean));
    availableColors.value = Array.from(set);
  } catch (e) {
    availableColors.value = [];
  }
}

function readAvailableColors() {
  try {
    const raw = sessionStorage.getItem('device_status');
    if (raw) {
      const parsed = JSON.parse(raw);
      updateAvailableColorsFromSession(parsed);
    } else {
      availableColors.value = [];
    }
  } catch (e) {
    availableColors.value = [];
  }
}

function onDeviceStatusChanged(e) {
  if (e?.detail) updateAvailableColorsFromSession(e.detail);
  else readAvailableColors();
}

onMounted(() => {
  readAvailableColors();
  window.addEventListener('device_status_changed', onDeviceStatusChanged);
  window.addEventListener('storage', (ev) => {
    if (ev.key === 'device_status') readAvailableColors();
  });
  const onGlobalPopup = (ev) => {
    const detail = ev?.detail || {};
    if (detail && (detail.title || detail.message)) {
      detailPopupTitle.value = detail.title || '';
      detailPopupMessage.value = detail.message || '';
      showDetailPopup.value = true;
    }
  };
  window.addEventListener('show_global_popup', onGlobalPopup);
  onUnmounted(() => {
    window.removeEventListener('show_global_popup', onGlobalPopup);
  });
});

onUnmounted(() => {
  window.removeEventListener('device_status_changed', onDeviceStatusChanged);
  window.removeEventListener('storage', (ev) => {
    if (ev.key === 'device_status') readAvailableColors();
  });
});

watch(selectedColor, (v) => {
  if (Array.isArray(v) && v.length >= 2) kleurenError.value = false;
});

function buildPayload() {
  const diff = difficulties.value.find((d) => String(d.id) === String(selectedDifficulty.value));
  const rnd = roundsOptions.value.find((r) => String(r.id) === String(selectedRounds.value));

  const diffId = diff?.id ? parseInt(diff.id) : null;
  const rndId = rnd?.id ? parseInt(rnd.id) : null;

  if (!diffId || !rndId) {
    console.error('Missing difficulty or round selection', { diffId, rndId, selectedDifficulty: selectedDifficulty.value, selectedRounds: selectedRounds.value });
  }

  return {
    game_id: parseInt(gameId.value),
    gebruikersnaam: username.value || null,
    moeilijkheids_id: diffId,
    snelheid: diff?.snelheid ?? null,
    ronde_id: rndId,
    rondes: rnd?.rondes ?? null,
    kleuren: selectedColor.value.map(String),
  };
}

async function startGame() {
  const name = (username.value || '').toString().trim();
  const colorsValid = Array.isArray(selectedColor.value) && selectedColor.value.length >= 2;

  usernameError.value = !name;
  kleurenError.value = !colorsValid;

  if (usernameError.value) {
    await nextTick();
    usernameInput.value?.focus?.();
  }

  if (usernameError.value || kleurenError.value) return;

  const payload = buildPayload();

  try {
    try {
      sessionStorage.removeItem('last_global_popup');
    } catch (e) {}
    sessionStorage.setItem('lastGamePayload', JSON.stringify(payload));
  } catch (e) {
    // opslag niet beschikbaar, ga verder zonder opslaan
  }

  try {
    const res = await fetch(getApiUrl(`games/${gameId.value}/instellingen`), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (res.ok) {
      try {
        await enableAudio();
      } catch (e) {}
      router.push(`/games/${gameId.value}/play`);
      return;
    } else {
      const data = await res.json().catch(() => ({}));
      if (res.status === 409) {
        detailPopupTitle.value = 'Spel al bezig';
        detailPopupMessage.value = data?.message || 'Er loopt al een spel. Probeer het later opnieuw.';
      } else if (res.status === 400) {
        detailPopupTitle.value = 'Instellingen missen';
        detailPopupMessage.value = data?.message || 'Controleer de spelinstellingen.';
      } else {
        detailPopupTitle.value = 'Fout bij starten';
        detailPopupMessage.value = data?.message || 'Kon het spel niet starten. Probeer het opnieuw.';
      }
      showDetailPopup.value = true;
      return;
    }
  } catch (e) {
    // netwerk/backend niet beschikbaar -> show error
    console.error('Network error:', e);
    detailPopupTitle.value = 'Netwerkfout';
    detailPopupMessage.value = 'Kan verbinding met de server niet maken. Controleer uw netwerk.';
    showDetailPopup.value = true;
    return;
  }
}
</script>

<template>
  <div class="c-game-detail">
    <DetailPopup :show="showDetailPopup" :title="detailPopupTitle" :message="detailPopupMessage" @close="showDetailPopup = false" />
    <div class="c-game-detail__left">
      <div>
        <InputGebruikersnaam ref="usernameInput" v-model="username" bold />
        <p v-if="usernameError" class="error">Gebruikersnaam is verplicht</p>
      </div>

      <div class="c-game-detail__options">
        <h3>Instellingen</h3>
        <div class="c-game-detail__dif">
          <p>Moeilijkheidsgraad</p>
          <div class="c-game-detail__row">
            <FiltersDifficulty v-for="opt in difficulties" :key="opt.id" :id="String(opt.id)" :snelheid="opt.snelheid" :stars="opt.stars" v-model="selectedDifficulty" name="difficulty" />
          </div>
        </div>

        <div class="c-game-detail__rounds">
          <p>Aantal rondes</p>
          <div class="c-game-detail__row"><FiltersRounds v-for="r in roundsOptions" :key="r.id" :id="String(r.id)" :rondes="r.rondes" v-model="selectedRounds" name="rounds" /></div>
        </div>

        <div class="c-game-detail__colors">
          <p>Kleuren</p>
          <div class="c-game-detail__color-col">
            <div class="c-game-detail__color-row">
              <template v-if="availableColors.length">
                <FiltersColor v-for="id in backendColors.filter((c) => availableColors.includes(c))" :key="id" :id="id" v-model="selectedColor" name="colors" />
              </template>
              <template v-else>
                <p>Geen potjes aan.</p>
              </template>
            </div>
            <p v-if="kleurenError" class="error">Selecteer minstens 2 kleuren</p>
          </div>
        </div>
      </div>

      <button :class="'c-button' + (availableColors.length < 2 ? ' c-button--disabled' : '')" type="button" @click="startGame" aria-label="Start het spel" :disabled="availableColors.length < 2">
        <span class="c-button__icon" aria-hidden="true"><component :is="Play" /></span>
        <h3>Start het spel</h3>
      </button>
    </div>

    <div class="c-game-detail__right">
      <img class="c-game-detail__img" :src="gameImage" :alt="`${gameName} illustration`" />
      <div class="c-game-detail__info">
        <h1>{{ gameName }}</h1>
        <p>{{ gameDescription }}</p>
      </div>

      <div class="c-game-detail__leader">
        <h2>Leaderboard</h2>
        <LeaderboardSmall v-for="(entry, index) in smallLeaderboardData" :key="entry.name" :name="entry.name" :time="entry.time" :count="index + 1" :full="false" :borderDark="false" :total="smallLeaderboardData.length" :unit="entry.unit" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.c-game-detail {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-title);

  @media (min-width: 768px) {
    flex-direction: row;
    gap: 3rem;
    align-items: flex-start;
  }

  .c-game-detail__left {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-title);

    @media (min-width: 768px) {
      flex: 1;
    }
  }

  .c-game-detail__right {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-title);

    @media (min-width: 768px) {
      flex: 1;
    }
  }

  .c-game-detail__row {
    display: flex;
    flex-direction: row;
    gap: 1rem;
    justify-content: space-between;
  }

  .c-game-detail__color-row {
    display: flex;
    flex-direction: row;
    gap: 0.75rem;
  }

  .c-game-detail__color-col {
    display: flex;
    flex-direction: column;
  }

  .c-game-detail__options {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-blocks);
  }

  .c-game-detail__img {
    display: block;
    width: 100vw;
    max-width: 100vw;
    height: 6.25rem;
    object-fit: cover;
    margin-left: calc(50% - 50vw);
    margin-right: calc(50% - 50vw);

    @media (min-width: 768px) {
      width: 100%;
      max-width: 100%;
      height: 12rem;
      margin-left: 0;
      margin-right: 0;
      border-radius: var(--radius-20);
    }
  }

  .c-game-detail__info {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
}
</style>
