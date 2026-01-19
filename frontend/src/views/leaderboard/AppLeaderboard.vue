<script setup>
import { ref } from 'vue';
import FilterGame from '../../components/filters/FilterGame.vue';
import FiltersDifficulty from '../../components/filters/FiltersDifficulty.vue';
import LeaderboardSmall from '../../components/leaderboard/LeaderboardSmall.vue';

const selectedDifficulty = ref('2');

const difficulties = ref([
  { id: '1', snelheid: 10, stars: 1 },
  { id: '2', snelheid: 5, stars: 2 },
  { id: '3', snelheid: 3, stars: 3 },
]);

const leaderboardData = ref([
  { name: 'Jonathan', time: 1.22 },
  { name: 'Maarten', time: 1.79 },
  { name: 'Anna', time: 2.06 },
  { name: 'Sophie', time: 2.34 },
  { name: 'Piet', time: 2.89 },
  { name: 'Klaas', time: 3.12 },
  { name: 'Marie', time: 3.45 },
  { name: 'Jan', time: 3.78 },
]);
</script>

<template>
  <div class="c-leaderboard">
    <h1>Leaderboard</h1>
    <div class="c-leaderboard__filters">
      <FilterGame />
      <div class="c-leaderboard__dif">
        <p>Moeilijkheidsgraad</p>
        <div class="c-leaderboard__row">
          <FiltersDifficulty v-for="opt in difficulties" :key="opt.id" :id="String(opt.id)" :snelheid="opt.snelheid" :stars="opt.stars" v-model="selectedDifficulty" name="difficulty" />
        </div>
      </div>
    </div>

    <div class="c-leaderboard__board">
      <div class="c-leaderboard__header"></div>
      <div class="c-leaderboard__body">
        <LeaderboardSmall v-for="(entry, index) in leaderboardData" :key="entry.name" :name="entry.name" :time="entry.time" :count="index + 1" :full="true" :borderDark="true" :total="leaderboardData.length" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.c-leaderboard {
  .c-leaderboard__body {
    background-color: var(--blue-10);
    padding: 0.5rem 1rem;
    border-radius: var(--radius-20);
  }

  .c-leaderboard__row {
    display: flex;
    flex-direction: row;
    gap: 1rem;
    justify-content: space-between;
  }

  .c-leaderboard__filters {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-blocks);
    margin-bottom: var(--spacing-title);
  }
}
</style>
