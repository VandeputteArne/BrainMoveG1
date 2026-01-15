<script setup>
import { ref, onMounted } from 'vue';
import GameCard from '../../components/cards/CardsGame.vue';

const games = ref([{ id: '1', title: 'Color Sprint', tag: 'Reactiesnelheid', bestTime: 0.5, unit: 's', image: 'images/cards/color-sprint.png' }]);

onMounted(async () => {
  // als je data vanaf een API wilt laden, doe dat hier en zet games.value = fetchedData
  // const res = await fetch('/api/games'); games.value = await res.json();
});
</script>

<template>
  <h1 class="title">Alle games</h1>
  <div class="c-games">
    <GameCard v-for="g in games" :key="g.id" :id="g.id" :title="g.title" :tag="g.tag" :best-time="g.bestTime" :unit="g.unit" :image="g.image" />
  </div>
</template>

<style scoped></style>
