<script setup>
import { ref } from 'vue';
import FilterGame from '../../components/filters/FilterGame.vue';
import FiltersDifficulty from '../../components/filters/FiltersDifficulty.vue';
import LeaderboardSmall from '../../components/leaderboard/LeaderboardSmall.vue';
import LeaderboardPlayer from '../../components/leaderboard/LeaderboardPlayer.vue';

const selectedDifficulty = ref('2');

const difficulties = ref([
  { id: '1', snelheid: 10, stars: 1 },
  { id: '2', snelheid: 5, stars: 2 },
  { id: '3', snelheid: 3, stars: 3 },
]);

const leaderboardData = ref([
  { name: 'Jonathan', time: 1.22, rank: 1 },
  { name: 'Maarten', time: 1.79, rank: 2 },
  { name: 'Anna', time: 2.06, rank: 3 },
  { name: 'Sophie', time: 2.34, rank: 4 },
  { name: 'Piet', time: 2.89, rank: 5 },
  { name: 'Klaas', time: 3.12, rank: 6 },
  { name: 'Marie', time: 3.45, rank: 7 },
  { name: 'Jan', time: 3.78, rank: 8 },
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
      <div class="c-leaderboard__header">
        <div class="c-leaderboard__podium">
          <LeaderboardPlayer v-if="leaderboardData[1]" :name="leaderboardData[1].name" :rank="2" class="c-leaderboard__player c-leaderboard__player--second" />
          <LeaderboardPlayer v-if="leaderboardData[0]" :name="leaderboardData[0].name" :rank="1" class="c-leaderboard__player c-leaderboard__player--first" />
          <LeaderboardPlayer v-if="leaderboardData[2]" :name="leaderboardData[2].name" :rank="3" class="c-leaderboard__player c-leaderboard__player--third" />
        </div>
        <img src="/images/podium.png" alt="Podium" class="c-leaderboard__image" />
      </div>
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

  .c-leaderboard__board {
    margin-top: 7rem;
  }

  .c-leaderboard__image {
    width: 100%;
    height: auto;
    position: relative;
    display: block;
  }

  .c-leaderboard__header {
    position: relative;
    margin-bottom: 1rem;
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
  }

  .c-leaderboard__podium {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
  }

  .c-leaderboard__player--first {
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
  }

  .c-leaderboard__player--second {
    position: absolute;
    bottom: 78%;
    left: 16%;
    transform: scale(clamp(0.8, 1vw, 1.2));

    @media (width < 576px) {
      left: 12%;
    }
  }

  .c-leaderboard__player--third {
    position: absolute;
    bottom: 75%;
    right: 16%;
    transform: scale(clamp(0.8, 1vw, 1.2));

    @media (width < 576px) {
      right: 14%;
    }
  }
}
</style>
