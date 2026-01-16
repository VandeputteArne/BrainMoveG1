<script setup>
import { ref, onMounted } from 'vue';
import GameCard from '../../components/cards/CardsGame.vue';

const games = ref([]);

onMounted(async () => {
  try {
    const res = await fetch('http://10.42.0.1:8000/games/overview');
    const data = await res.json();

    games.value = data.map((game, index) => ({
      id: String(index + 1),
      title: game.game_naam,
      tag: game.tag,
      bestTime: game.highscore,
      unit: game.eenheid,
      image: `images/cards/${game.game_naam.toLowerCase().replace(/\s+/g, '-')}.png`,
    }));
  } catch (error) {
    console.error('Failed to fetch games:', error);
  }
});
</script>

<template>
  <h1 class="title">Alle games</h1>
  <div class="c-games">
    <GameCard v-for="g in games" :key="g.id" :id="g.id" :title="g.title" :tag="g.tag" :best-time="g.bestTime" :unit="g.unit" :image="g.image" />
  </div>
</template>

<style scoped></style>
