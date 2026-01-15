<script setup>
import InputGebruikersnaam from '../../components/inputs/InputGebruikersnaam.vue';
import FiltersDifficulty from '../../components/filters/FiltersDifficulty.vue';
import FiltersRounds from '../../components/filters/FiltersRounds.vue';
import FiltersColor from '../../components/filters/FiltersColor.vue';
import LeaderboardSmall from '../../components/leaderboard/LeaderboardSmall.vue';

import { Play } from 'lucide-vue-next';

import { ref, onMounted, computed, nextTick, watch } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const username = ref('');
const usernameError = ref(false);
const usernameInput = ref(null);

const isUsernameValid = computed(() => (username.value || '').toString().trim().length > 0);

watch(username, (v) => {
  if ((v || '').toString().trim().length > 0) usernameError.value = false;
});

const difficulties = ref([
  { id: 1, snelheid: 5 },
  { id: 2, snelheid: 10 },
  { id: 3, snelheid: 15 },
]);

const selectedDifficulty = ref('2');

const roundsOptions = ref([
  { id: 1, rondes: 3 },
  { id: 2, rondes: 5 },
  { id: 3, rondes: 10 },
]);

const smallLeaderboardData = ref([
  { name: 'Jonathan', time: 45 },
  { name: 'Anna', time: 50 },
  { name: 'Sophie', time: 60 },
]);

const selectedRounds = ref('1');
const selectedColor = ref([]);
const backendColors = ref(['blauw', 'rood', 'groen', 'geel']);
const excludedColor = ref('geel');

onMounted(async () => {
  if (Array.isArray(backendColors.value) && backendColors.value.length && selectedColor.value.length === 0) {
    selectedColor.value = backendColors.value.filter((id) => id !== excludedColor.value);
  }
});

function buildPayload() {
  const diff = difficulties.value.find((d) => String(d.id) === String(selectedDifficulty.value)) || { id: selectedDifficulty.value };
  const rnd = roundsOptions.value.find((r) => String(r.id) === String(selectedRounds.value)) || { id: selectedRounds.value };

  return {
    game_id: 1,
    gebruikersnaam: username.value || null,
    moeilijkheids_id: diff.id,
    snelheid: diff.snelheid ?? null,
    ronde_id: rnd.id,
    rondes: rnd.rondes ?? null,
    kleuren: selectedColor.value.map(String),
  };
}

async function startGame() {
  const name = (username.value || '').toString().trim();
  if (!name) {
    usernameError.value = true;
    await nextTick();
    usernameInput.value?.focus?.();
    return;
  }

  usernameError.value = false;

  const payload = buildPayload();

  try {
    localStorage.setItem('lastGamePayload', JSON.stringify(payload));
  } catch (e) {
    // opslag niet beschikbaar, ga verder zonder opslaan
  }

  try {
    const res = await fetch('http://10.42.0.1:8000/games/1/instellingen', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (res.ok) {
      const data = await res.json();
      const gameId = data?.id || data?.gameId;
      if (gameId) {
        router.push(`/game/${gameId}`);
        return;
      }
      router.push(`/games/${gameId}/play`);
      return;
    }
  } catch (e) {
    // netwerk/backend niet beschikbaar -> fallback
  }

  router.push('/games/1/play');
}
</script>

<template>
  <div class="c-game-detail">
    <div>
      <InputGebruikersnaam ref="usernameInput" v-model="username" />
      <p v-if="usernameError" class="error">Gebruikersnaam is verplicht</p>
    </div>

    <div class="c-game-detail__options">
      <h3>Instellingen</h3>
      <div class="c-game-detail__dif">
        <p>Moeilijkheidsgraad</p>
        <div class="c-game-detail__row">
          <FiltersDifficulty v-for="opt in difficulties" :key="opt.id" :id="String(opt.id)" :snelheid="opt.snelheid" v-model="selectedDifficulty" name="difficulty" />
        </div>
      </div>

      <div class="c-game-detail__rounds">
        <p>Aantal rondes</p>
        <div class="c-game-detail__row"><FiltersRounds v-for="r in roundsOptions" :key="r.id" :id="String(r.id)" :rondes="r.rondes" v-model="selectedRounds" name="rounds" /></div>
      </div>

      <div class="c-game-detail__colors">
        <p>Kleuren</p>
        <div class="c-game-detail__color-row">
          <FiltersColor v-for="id in backendColors" :key="id" :id="id" v-model="selectedColor" name="colors" />
        </div>
      </div>
    </div>

    <button class="c-button" type="button" @click="startGame" aria-label="Start het spel">
      <span class="c-button__icon" aria-hidden="true"><component :is="Play" /></span>
      <h3>Start het spel</h3>
    </button>

    <img class="c-game-detail__img" src="/cards/color-sprint.png" alt="Game illustration" />
    <div class="c-game-detail__info">
      <h1>Color Sprint</h1>
      <p>Blijf scherp! Zodra een kleur op het scherm verschijnt, moet je onmiddellijk in actie komen en naar de bijpassende kleur bewegen. Elke seconde telt. Verbeter je reactietijd, versla je eigen records en word steeds sneller.</p>
    </div>

    <div class="c-game-detail__leader">
      <h2>Leaderboard</h2>
      <LeaderboardSmall v-for="(entry, index) in smallLeaderboardData" :key="entry.name" :name="entry.name" :time="entry.time" :count="index + 1" />
    </div>
  </div>
</template>

<style scoped>
.c-game-detail {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-title);

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
  }

  .c-game-detail__info {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
}
</style>
