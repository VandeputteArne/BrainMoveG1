// ...existing code...
<script setup>
import { ref, computed } from 'vue';
import { Download, ChartNoAxesCombined } from 'lucide-vue-next';

import ButtonsPrimary from '../../components/buttons/ButtonsPrimary.vue';
import OverzichtCountItem from '../../components/overzicht/OverzichtCountItem.vue';
import OverzichtCard from '../../components/overzicht/OverzichtCard.vue';
import OverzichtGraph from '../../components/overzicht/OverzichtGraph.vue';

// Hardcoded data (later vervang door API)
const stats = ref([
  { waarde: 0.24, label: 'Gemiddelde' },
  { waarde: 0.13, label: 'Beste' },
  { waarde: 10, label: 'Ranking' },
  { waarde: 70, label: 'Exactheid' },
]);
// Hardcoded per-round reactietijden
const rounds = ref([
  { round: 1, time: 0.24 },
  { round: 2, time: 0.3 },
  { round: 3, time: 0.18 },
  { round: 4, time: 0.13 },
  { round: 5, time: 0.28 },
]);

// Hardcoded counts (correct / wrong / late)
const counts = ref([
  { type: 'correct', value: 12 },
  { type: 'wrong', value: 2 },
  { type: 'late', value: 1 },
]);

// derive values from arrays (keeps UI consistent if you later replace with API data)
const computedAverage = computed(() => {
  if (!rounds.value.length) return 0;
  const sum = rounds.value.reduce((s, r) => s + r.time, 0);
  return +(sum / rounds.value.length).toFixed(2);
});
const computedBest = computed(() => {
  if (!rounds.value.length) return 0;
  return Math.min(...rounds.value.map((r) => r.time));
});

// CSV export (simple)
function exportCsv() {
  const rows = [['Stat', 'Value'], ['Average', stats.value.average], ['Best', stats.value.best], ['Ranking', stats.value.ranking], ['Accuracy (%)', stats.value.accuracyPct], [], ['Round', 'Time (s)'], ...rounds.value.map((r) => [r.round, r.time]), [], ['Correct', counts.value.correct], ['Wrong', counts.value.wrong], ['Late', counts.value.late]];

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
        <OverzichtCountItem v-for="count of counts" :counts="count.value" :type="count.type" />
      </div>
    </div>

    <div class="c-overzicht__buttons">
      <ButtonsPrimary url="/games" title="Speel opnieuw"></ButtonsPrimary>
      <router-link to="/games" class="c-overzicht__back">Terug naar home</router-link>
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
