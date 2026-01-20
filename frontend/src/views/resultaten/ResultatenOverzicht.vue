<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import { Download, ChartNoAxesCombined } from 'lucide-vue-next';

import ButtonsPrimary from '../../components/buttons/ButtonsPrimary.vue';
import OverzichtCountItem from '../../components/overzicht/OverzichtCountItem.vue';
import OverzichtCard from '../../components/overzicht/OverzichtCard.vue';
import OverzichtGraph from '../../components/overzicht/OverzichtGraph.vue';

const route = useRoute();

const backUrl = computed(() => (route.params.id ? '/historie' : '/games'));
const backText = computed(() => (route.params.id ? 'Terug naar historie' : 'Terug naar games'));

const gameId = ref(null);

const stats = ref([
  { waarde: 0, label: 'Gemiddelde' },
  { waarde: 0, label: 'Beste' },
  { waarde: 0, label: 'Ranking' },
  { waarde: 0, label: 'Exactheid' },
]);

const rounds = ref([]);

const counts = ref([
  { type: 'correct', label: 'Correct', value: 0 },
  { type: 'telaat', label: 'Te laat', value: 0 },
  { type: 'fout', label: 'Fout', value: 0 },
]);

function applyData(data) {
  if (!data || typeof data !== 'object') return;

  // Store game_id if available
  if (data.game_id) {
    gameId.value = data.game_id;
  }

  // Check if this is memory game (game_id: 2)
  const isMemoryGame = data.game_id === 2;

  // Update stats - support both old (correcte_rondewaarden) and new (lijst_voor_grafiek) API
  stats.value = [
    { waarde: data.gemmidelde_waarde ?? data.gemiddelde_waarde ?? 0, label: 'Gemiddelde' },
    { waarde: isMemoryGame ? (data.aantal_kleuren ?? 0) : (data.beste_waarde ?? 0), label: isMemoryGame ? 'Aantal kleuren' : 'Beste' },
    { waarde: data.ranking ?? 0, label: 'Ranking' },
    { waarde: data.exactheid ?? 0, label: 'Exactheid' },
  ];

  // Update counts
  counts.value = [
    { type: 'correct', label: 'Correct', value: data.aantal_correct ?? 0 },
    { type: 'telaat', label: isMemoryGame ? 'Niet gespeeld' : 'Te laat', value: isMemoryGame ? (data.aantal_rondes_niet_gespeeld ?? 0) : (data.aantal_telaat ?? 0) },
    { type: 'fout', label: 'Fout', value: data.aantal_fout ?? 0 },
  ];

  // Update rounds - support both old and new field names
  const rondeData = data.lijst_voor_grafiek ?? data.correcte_rondewaarden;
  if (Array.isArray(rondeData)) {
    rounds.value = rondeData.map((r) => ({
      round: r.ronde_nummer,
      time: r.waarde,
    }));
  } else {
    rounds.value = [];
  }
}

async function loadResults() {
  const id = route.params.id;

  if (id) {
    // Load from API with id
    const cacheKey = `training_result_${id}`;
    const cached = sessionStorage.getItem(cacheKey);

    if (cached) {
      try {
        applyData(JSON.parse(cached));
        return;
      } catch (err) {
        console.warn('Failed to parse cached data:', err);
      }
    }

    try {
      const res = await fetch(`http://10.42.0.1:8000/trainingen/${id}/details`);
      if (!res.ok) throw new Error(`Request failed: ${res.status}`);
      const data = await res.json();
      sessionStorage.setItem(cacheKey, JSON.stringify(data));
      applyData(data);
    } catch (err) {
      console.error('Failed to fetch training result:', err);
    }
  } else {
    // Fetch latest round values from API (after game completion)
    try {
      const response = await fetch('http://10.42.0.1:8000/laatste_rondewaarden');

      if (response.ok) {
        const data = await response.json();
        sessionStorage.setItem('laatste_rondewaarden', JSON.stringify(data));
        applyData(data);
      } else {
        console.error('Failed to fetch round values:', response.statusText);
      }
    } catch (error) {
      console.error('Error fetching round values:', error);
    }
  }
}

onMounted(loadResults);

watch(
  () => route.params.id,
  () => {
    loadResults();
  },
);

// derive values from arrays (keeps UI consistent if you later replace with API data)
const computedAverage = computed(() => {
  if (!rounds.value.length) return stats.value[0]?.waarde || 0;
  const sum = rounds.value.reduce((s, r) => s + r.time, 0);
  return +(sum / rounds.value.length).toFixed(2);
});
const computedBest = computed(() => {
  if (!rounds.value.length) return stats.value[1]?.waarde || 0;
  return Math.min(...rounds.value.map((r) => r.time));
});

// CSV export (simple)
function exportCsv() {
  const data = stats.value;
  const rows = [['Stat', 'Value'], ['Gemiddelde', data[0]?.waarde || 0], ['Beste', data[1]?.waarde || 0], ['Ranking', data[2]?.waarde || 0], ['Exactheid (%)', data[3]?.waarde || 0], [], ['Type', 'Count'], ['Correct', counts.value[0]?.value || 0], ['Wrong', counts.value[1]?.value || 0], ['Late', counts.value[2]?.value || 0]];

  if (rounds.value.length) {
    rows.push([], ['Round', 'Time (s)']);
    rounds.value.forEach((r) => rows.push([r.round, r.time]));
  }

  const csv = rows.map((r) => r.join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `results_${Date.now()}.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
</script>

<template>
  <div class="c-overzicht">
    <div class="c-overzicht__title">
      <h1>Resultaten</h1>
      <button class="c-overzicht__export" type="button" @click="exportCsv" aria-label="Exporteren">
        <span class="c-overzicht__export-icon"><Download class="c-overzicht__export-svg" /></span>
        <h3>Exporteren</h3>
      </button>
    </div>

    <div class="c-overzicht__stats">
      <OverzichtCard v-for="stat in stats" :key="stat.label" :waarde="stat.waarde" :label="stat.label" />
    </div>

    <div class="c-overzicht__rounds">
      <div class="c-overzicht__rounds-header">
        <ChartNoAxesCombined />
        <h3>Reactietijden per Ronde</h3>
      </div>

      <OverzichtGraph :results="rounds" :average-time="computedAverage" />
    </div>

    <div class="c-overzicht__counts">
      <h3>Totale uitslag</h3>
      <div class="c-overzicht__counts-inner">
        <OverzichtCountItem v-for="count of counts" :counts="count.value" :label="count.label" :type="count.type" />
      </div>
    </div>

    <div class="c-overzicht__buttons">
      <ButtonsPrimary :url="`/games/${gameId || route.params.id || ''}`" title="Speel opnieuw"></ButtonsPrimary>
      <router-link :to="backUrl" class="c-overzicht__back">{{ backText }}</router-link>
    </div>
  </div>
</template>

<style scoped>
.c-overzicht {
  .c-overzicht__title {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
  }

  .c-overzicht__export {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: transparent;
    border: none;
    color: var(--blue-100);
    font-weight: 600;
    cursor: pointer;
    height: fit-content;

    .c-overzicht__export-icon {
      display: flex;
      align-items: center;
      width: 1.25rem;
      height: 1.25rem;
    }

    .c-overzicht__export-svg {
      width: 100%;
      height: 100%;
      stroke-width: 0.175rem;
    }
  }

  .c-overzicht__stats {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
    margin-top: 1.5rem;
  }

  .c-overzicht__rounds {
    margin-top: 2rem;

    .c-overzicht__rounds-header {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-bottom: 1rem;
    }
  }

  .c-overzicht__counts {
    margin-top: 2rem;

    .c-overzicht__counts-inner {
      display: flex;
      justify-content: space-between;
      margin-top: 0.3125rem;
      gap: 0.625rem;
    }
  }

  .c-overzicht__buttons {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    margin-top: 2.5rem;
  }

  .c-overzicht__back {
    color: var(--blue-100);
    font-weight: 600;
    text-decoration: none;
    cursor: pointer;
  }
}
</style>
