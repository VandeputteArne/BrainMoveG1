<script setup>
import InputGebruikersnaam from '../../components/inputs/InputGebruikersnaam.vue';
import FiltersDifficulty from '../../components/filters/FiltersDifficulty.vue';
import FiltersRounds from '../../components/filters/FiltersRounds.vue';
import FiltersColor from '../../components/filters/FiltersColor.vue';
import ButtonsPrimary from '../../components/buttons/ButtonsPrimary.vue';
import LeaderboardSmall from '../../components/leaderboard/LeaderboardSmall.vue';

import { Play } from 'lucide-vue-next';

import { ref, onMounted } from 'vue';

const difficulties = ref([
  { id: '1', snelheid: 1 },
  { id: '2', snelheid: 2 },
  { id: '3', snelheid: 3 },
]);

const selectedDifficulty = ref('2');

const roundsOptions = ref([
  { id: '1', rondes: 3 },
  { id: '2', rondes: 5 },
  { id: '3', rondes: 10 },
]);

const smallLeaderboardData = ref([
  { name: 'Jonathan', time: 45 },
  { name: 'Anna', time: 50 },
  { name: 'Sophie', time: 60 },
]);

const selectedRounds = ref('1');
const selectedColor = ref([]);
const backendColors = ref(['1', '2', '3', '4']);
const excludedColor = ref('4');

onMounted(async () => {
  // voorbeeld: haal difficulties vanuit API en map naar { id, snelheid }
  // const res = await fetch('/api/games/123/difficulties');
  // const data = await res.json();
  // difficulties.value = data.map(d => ({ id: d.id, snelheid: d.snelheid }));
  // Initialize default selected colors when backendColors are present and selectedColor is empty
  if (Array.isArray(backendColors.value) && backendColors.value.length && selectedColor.value.length === 0) {
    selectedColor.value = backendColors.value.filter((id) => id !== excludedColor.value);
  }
});
</script>

<template>
  <div class="c-game-detail">
    <InputGebruikersnaam />

    <div class="c-game-detail__options">
      <h3>Instellingen</h3>
      <div class="c-game-detail__dif">
        <p>Moeilijkheidsgraad</p>
        <div class="c-game-detail__row">
          <FiltersDifficulty v-for="opt in difficulties" :key="opt.id" :id="opt.id" :snelheid="opt.snelheid" v-model="selectedDifficulty" name="difficulty" />
        </div>
      </div>

      <div class="c-game-detail__rounds">
        <p>Aantal rondes</p>
        <div class="c-game-detail__row"><FiltersRounds v-for="r in roundsOptions" :key="r.id" :id="r.id" :rondes="r.rondes" v-model="selectedRounds" name="rounds" /></div>
      </div>

      <div class="c-game-detail__colors">
        <p>Kleuren</p>
        <div class="c-game-detail__color-row">
          <FiltersColor v-for="id in backendColors" :key="id" :id="id" v-model="selectedColor" name="colors" />
        </div>
      </div>
    </div>

    <ButtonsPrimary url="/game/id" title="Start het spel" :icon="Play" />

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
