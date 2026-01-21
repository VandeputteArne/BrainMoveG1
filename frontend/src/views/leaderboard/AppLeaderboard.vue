<script setup>
import { ref, watch, onMounted } from 'vue';
import FilterGame from '../../components/filters/FilterGame.vue';
import FiltersDifficulty from '../../components/filters/FiltersDifficulty.vue';
import LeaderboardSmall from '../../components/leaderboard/LeaderboardSmall.vue';
import LeaderboardPlayer from '../../components/leaderboard/LeaderboardPlayer.vue';

const selectedGame = ref(null);
const selectedDifficulty = ref('2');

const difficulties = ref([]);

const leaderboardData = ref([]);

async function fetchDifficulties() {
  if (!selectedGame.value) {
    difficulties.value = [];
    return;
  }

  try {
    const res = await fetch(`http://10.42.0.1:8000/leaderboard/filters/${selectedGame.value}`);
    if (!res.ok) throw new Error(`Request failed: ${res.status}`);
    const data = await res.json();

    difficulties.value = data.map((diff, index) => ({
      id: String(diff.moeilijkheid_id),
      stars: index + 1,
    }));

    if (difficulties.value.length > 0) {
      const exists = difficulties.value.some((d) => d.id === selectedDifficulty.value);
      if (!exists) {
        selectedDifficulty.value = difficulties.value[0].id;
      }
    }
  } catch (error) {
    console.error('Failed to fetch difficulties:', error);
    difficulties.value = [];
  }
}

async function fetchLeaderboard() {
  if (!selectedGame.value || !selectedDifficulty.value) {
    leaderboardData.value = [];
    return;
  }

  try {
    const res = await fetch(`http://10.42.0.1:8000/leaderboard/overview/${selectedGame.value}/${selectedDifficulty.value}`);
    if (!res.ok) throw new Error(`Request failed: ${res.status}`);
    const data = await res.json();

    leaderboardData.value = data.map((entry) => ({
      name: entry.gebruikersnaam,
      time: entry.waarde,
      rank: entry.plaats,
      unit: entry.eenheid,
    }));
  } catch (error) {
    console.error('Failed to fetch leaderboard:', error);
    leaderboardData.value = [];
  }
}

watch(selectedGame, () => {
  fetchDifficulties();
});

watch([selectedGame, selectedDifficulty], () => {
  fetchLeaderboard();
});

onMounted(() => {
  fetchLeaderboard();
});
</script>

<template>
  <div class="c-leaderboard">
    <div class="c-leaderboard__container">
      <div class="c-leaderboard__filters">
        <h1>Leaderboard</h1>
        <FilterGame v-model="selectedGame" />
        <div class="c-leaderboard__dif">
          <p>Moeilijkheidsgraad</p>
          <div class="c-leaderboard__row">
            <FiltersDifficulty v-for="opt in difficulties" :key="opt.id" :id="String(opt.id)" :stars="opt.stars" v-model="selectedDifficulty" name="difficulty" />
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
          <LeaderboardSmall v-for="(entry, index) in leaderboardData" :key="`${entry.rank}-${entry.name}-${index}`" :name="entry.name" :time="entry.time" :count="entry.rank" :full="true" :borderDark="true" :total="leaderboardData.length" :unit="entry.unit" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.c-leaderboard {
  .c-leaderboard__container {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-title);

    @media (width >= 768px) {
      flex-direction: row;
      gap: 3rem;
      align-items: flex-start;
    }
  }

  .c-leaderboard__filters {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-blocks);
    margin-bottom: var(--spacing-title);

    @media (width >= 768px) {
      flex: 0 0 300px;
      position: sticky;
      top: 6.5rem;
    }
  }

  .c-leaderboard__board {
    margin-top: 3.2rem;

    @media (width >= 768px) {
      flex: 1;
      margin-top: 6rem;
    }
  }

  .c-leaderboard__body {
    background-color: var(--blue-10);
    padding: 0.5rem 1rem;
    border-radius: var(--radius-20);
    position: relative;
    max-width: 90%;
    margin-left: auto;
    margin-right: auto;
    margin-top: -2.5rem;
    z-index: 2;

    @media (width < 576px) {
      max-width: 100%;
    }
  }

  .c-leaderboard__row {
    display: flex;
    flex-direction: row;
    gap: 1rem;
    justify-content: space-between;
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
    z-index: 1;
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
      left: 11%;
    }
  }

  .c-leaderboard__player--third {
    position: absolute;
    bottom: 75%;
    right: 16%;
    transform: scale(clamp(0.8, 1vw, 1.2));

    @media (width < 576px) {
      right: 11%;
    }
  }
}
</style>
