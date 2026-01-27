<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { LayoutGrid, Rows3 } from 'lucide-vue-next';
import GameCard from '../../components/cards/CardsGame.vue';
import { getApiUrl } from '../../config/api.js';

const games = ref([]);
const viewMode = ref('row');
const isMobile = ref(window.innerWidth < 768);

const updateIsMobile = () => {
  isMobile.value = window.innerWidth < 768;
};

const toggleView = () => {
  viewMode.value = viewMode.value === 'grid' ? 'row' : 'grid';
};

const showGridIcon = computed(() => {
  if (isMobile.value) {
    return viewMode.value === 'grid';
  }
  return viewMode.value === 'row';
});

onMounted(async () => {
  window.addEventListener('resize', updateIsMobile);

  try {
    const res = await fetch(getApiUrl('games/overview'));
    const data = await res.json();

    games.value = data.map((game, index) => ({
      id: String(index + 1),
      title: game.game_naam,
      tag: game.tag,
      bestTime: game.highscore,
      unit: game.eenheid,
      image: `images/cards/${game.game_naam.toLowerCase().replace(/\s+/g, '')}.png`,
    }));
  } catch (error) {
    console.error('Failed to fetch games:', error);
  }
});

onUnmounted(() => {
  window.removeEventListener('resize', updateIsMobile);
});
</script>

<template>
  <div class="c-games-page">
    <div class="c-games__header">
      <h1>Alle games</h1>
      <button @click="toggleView" class="c-games__view-toggle" :aria-label="viewMode === 'grid' ? 'Switch to row view' : 'Switch to grid view'">
        <LayoutGrid v-if="showGridIcon" :size="24" />
        <Rows3 v-else :size="24" />
      </button>
    </div>
    <div class="c-games" :class="`c-games--${viewMode}`">
      <div v-for="(g, index) in games" :key="g.id" class="c-games__item" :style="{ '--delay': `${Math.min(index * 80, 560)}ms` }">
        <GameCard :id="g.id" :title="g.title" :tag="g.tag" :best-time="g.bestTime" :unit="g.unit" :image="g.image" :view="viewMode" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.c-games-page {
  display: contents;
}

.c-games__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: var(--spacing-title);
}

.c-games__view-toggle {
  background: transparent;
  border: none;
  color: var(--color-text);
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition:
    background-color 0.2s ease,
    color 0.2s ease;
}

.c-games__view-toggle:hover {
  background-color: var(--blue-100, rgba(0, 0, 0, 0.05));
  color: var(--color-white);
}

.c-games__view-toggle:active {
  transform: scale(0.95);
}

.c-games--row {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  transition: all 0.3s ease;
  margin-bottom: 5rem;

  @media (width >= 768px) {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    width: 100%;
    gap: 2rem;
  }
}

.c-games--grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  transition: all 0.3s ease;
  margin-bottom: 5rem;

  @media (width >= 768px) {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }
}

.c-games__item {
  opacity: 0;
  transform: translateY(14px) scale(0.98);
  animation: games-reveal 520ms cubic-bezier(0.2, 0.7, 0.2, 1) forwards;
  animation-delay: var(--delay, 0ms);
  width: 100%;
}

@keyframes games-reveal {
  0% {
    opacity: 0;
    transform: translateY(14px) scale(0.98);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@media (prefers-reduced-motion: reduce) {
  .c-games__item {
    animation: none;
    opacity: 1;
    transform: none;
  }
}
</style>
