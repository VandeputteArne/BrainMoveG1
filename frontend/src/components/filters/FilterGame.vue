<script setup>
import { Gamepad2, ChevronDown } from 'lucide-vue-next';
import { ref, onMounted } from 'vue';

const gameoptions = ref([]);
const selectRef = ref(null);

onMounted(async () => {
  const cachedGames = sessionStorage.getItem('gameFilters');
  if (cachedGames) {
    gameoptions.value = JSON.parse(cachedGames);
    return;
  }

  try {
    const res = await fetch('http://10.42.0.1:8000/games/filters');
    const data = await res.json();

    gameoptions.value = data.map((game) => ({
      id: String(game.game_id),
      gametype: game.game_naam,
    }));

    sessionStorage.setItem('gameFilters', JSON.stringify(gameoptions.value));
  } catch (error) {
    console.error('Failed to fetch game filters:', error);
  }
});

function openSelect(event) {
  if (event.target !== selectRef.value && selectRef.value) {
    selectRef.value.showPicker?.() || selectRef.value.focus();
  }
}
</script>

<template>
  <div class="c-filter-game">
    <p>Gametype</p>
    <div class="c-filter-game__filter" @click="openSelect">
      <Gamepad2 class="c-filter-game__icon" />
      <select ref="selectRef" id="gametype-select" class="c-filter-game__select" @click.stop>
        <option v-for="option in gameoptions" :key="option.id" :data-id="option.id" :value="option.gametype">{{ option.gametype }}</option>
      </select>
      <ChevronDown class="c-filter-game__icon" />
    </div>
  </div>
</template>

<style scoped>
.c-filter-game {
  display: flex;
  flex-direction: column;
  gap: 0.3125rem;
  font-size: 0.875rem;

  .c-filter-game__filter {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    border-radius: var(--radius-40);
    border: solid 1px var(--gray-40);
    padding: 0.5rem 0.625rem;
    cursor: pointer;
  }

  .c-filter-game__icon {
    width: 1.25rem;
    height: 1.25rem;
    color: var(--blue-100);
  }

  .c-filter-game__select {
    all: unset;
    flex-grow: 1;
    cursor: pointer;
    height: 100%;
  }
}
</style>
