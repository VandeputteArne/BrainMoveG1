<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import { Download, ChartNoAxesCombined, TrophyIcon } from 'lucide-vue-next';
import { exportToExcel } from '../../composables/useExcelExport.js';

import ButtonsPrimary from '../../components/buttons/ButtonsPrimary.vue';
import OverzichtCountItem from '../../components/overzicht/OverzichtCountItem.vue';
import OverzichtCard from '../../components/overzicht/OverzichtCard.vue';
import OverzichtGraph from '../../components/overzicht/OverzichtGraph.vue';
import { getApiUrl } from '../../config/api.js';

const route = useRoute();

const backUrl = computed(() => (route.params.id ? '/historie' : '/games'));
const backText = computed(() => (route.params.id ? 'Terug naar historie' : 'Terug naar games'));

const gameId = ref(null);
const username = ref('');
const isColorBattle = ref(false);
const colorBattle = ref({
  speler1_naam: '',
  speler2_naam: '',
  speler1_correct: 0,
  speler2_correct: 0,
  speler1_fout: 0,
  speler2_fout: 0,
  winnaar: '',
  lijst_voor_grafiek: [],
});
const battleActive = ref('speler1');

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

  // Store game_id and username if available
  if (data.game_id) {
    gameId.value = data.game_id;
  }
  if (data.gebruikersnaam) {
    username.value = data.gebruikersnaam;
  }

  isColorBattle.value = !!(data.speler1_naam && data.speler2_naam);
  if (isColorBattle.value) {
    colorBattle.value = {
      speler1_naam: data.speler1_naam || '',
      speler2_naam: data.speler2_naam || '',
      speler1_correct: Number(data.speler1_correct ?? 0),
      speler2_correct: Number(data.speler2_correct ?? 0),
      speler1_fout: Number(data.speler1_fout ?? 0),
      speler2_fout: Number(data.speler2_fout ?? 0),
      winnaar: data.winnaar || '',
      lijst_voor_grafiek: Array.isArray(data.lijst_voor_grafiek) ? data.lijst_voor_grafiek : [],
    };
    return;
  }

  const isMemoryGame = data.game_id === 2;

  stats.value = [
    { waarde: data.gemmidelde_waarde ?? data.gemiddelde_waarde ?? 0, label: 'Gemiddelde' },
    { waarde: isMemoryGame ? (data.aantal_kleuren ?? 0) : (data.beste_waarde ?? 0), label: isMemoryGame ? 'Onthouden' : 'Beste' },
    { waarde: data.ranking ?? 0, label: 'Ranking' },
    { waarde: data.exactheid ?? 0, label: 'Exactheid' },
  ];

  counts.value = [
    { type: 'correct', label: 'Correct', value: data.aantal_correct ?? 0 },
    { type: 'telaat', label: isMemoryGame ? 'Ongespeeld' : 'Te laat', value: isMemoryGame ? (data.aantal_rondes_niet_gespeeld ?? 0) : (data.aantal_telaat ?? 0) },
    { type: 'fout', label: 'Fout', value: data.aantal_fout ?? 0 },
  ];

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

const battleRounds1 = computed(() => (colorBattle.value.lijst_voor_grafiek || []).filter((r) => r?.speler_naam === colorBattle.value.speler1_naam).map((r) => ({ round: r.ronde_nummer, time: r.waarde })));
const battleRounds2 = computed(() => (colorBattle.value.lijst_voor_grafiek || []).filter((r) => r?.speler_naam === colorBattle.value.speler2_naam).map((r) => ({ round: r.ronde_nummer, time: r.waarde })));
const battleAverage1 = computed(() => {
  if (!battleRounds1.value.length) return 0;
  const sum = battleRounds1.value.reduce((s, r) => s + r.time, 0);
  return +(sum / battleRounds1.value.length).toFixed(2);
});
const battleAverage2 = computed(() => {
  if (!battleRounds2.value.length) return 0;
  const sum = battleRounds2.value.reduce((s, r) => s + r.time, 0);
  return +(sum / battleRounds2.value.length).toFixed(2);
});
const battleAccuracy1 = computed(() => {
  const total = colorBattle.value.speler1_correct + colorBattle.value.speler1_fout;
  if (!total) return 0;
  return Math.round((colorBattle.value.speler1_correct / total) * 100);
});
const battleAccuracy2 = computed(() => {
  const total = colorBattle.value.speler2_correct + colorBattle.value.speler2_fout;
  if (!total) return 0;
  return Math.round((colorBattle.value.speler2_correct / total) * 100);
});

const activePlayerName = computed(() => (battleActive.value === 'speler1' ? colorBattle.value.speler1_naam : colorBattle.value.speler2_naam));
const activeRounds = computed(() => (battleActive.value === 'speler1' ? battleRounds1.value : battleRounds2.value));
const activeAverage = computed(() => (battleActive.value === 'speler1' ? battleAverage1.value : battleAverage2.value));
const activeCorrect = computed(() => (battleActive.value === 'speler1' ? colorBattle.value.speler1_correct : colorBattle.value.speler2_correct));
const activeFout = computed(() => (battleActive.value === 'speler1' ? colorBattle.value.speler1_fout : colorBattle.value.speler2_fout));
const activeAccuracy = computed(() => (battleActive.value === 'speler1' ? battleAccuracy1.value : battleAccuracy2.value));
const isWinnerActive = computed(() => !!colorBattle.value.winnaar && colorBattle.value.winnaar === activePlayerName.value);
const isWinnerSpeler1 = computed(() => !!colorBattle.value.winnaar && colorBattle.value.winnaar === colorBattle.value.speler1_naam);
const isWinnerSpeler2 = computed(() => !!colorBattle.value.winnaar && colorBattle.value.winnaar === colorBattle.value.speler2_naam);

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
      const res = await fetch(getApiUrl(`trainingen/${id}/details`));
      if (!res.ok) throw new Error(`Request failed: ${res.status}`);
      const data = await res.json();
      sessionStorage.setItem(cacheKey, JSON.stringify(data));
      applyData(data);
    } catch (err) {
      console.error('Failed to fetch training result:', err);
    }
  } else {
    try {
      const response = await fetch(getApiUrl('trainingen/laatste_rondewaarden'));

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

// Excel export
async function exportCsv() {
  if (isColorBattle.value) {
    await exportToExcel({
      stats: [
        { waarde: activeAverage.value, label: 'Gemiddelde' },
        { waarde: `${activeAccuracy.value}%`, label: 'Exactheid' },
      ],
      counts: [
        { type: 'correct', label: 'Correct', value: activeCorrect.value },
        { type: 'fout', label: 'Fout', value: activeFout.value },
      ],
      rounds: activeRounds.value,
      username: activePlayerName.value,
    });
    return;
  }
  await exportToExcel({
    stats: stats.value,
    counts: counts.value,
    rounds: rounds.value,
    username: username.value,
  });
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

    <template v-if="isColorBattle">
      <div class="c-overzicht__battle">
        <div class="c-overzicht__battle-header">
          <div class="c-overzicht__battle-winner">
            <span class="c-overzicht__battle-winner-icon"><TrophyIcon /></span>
            <div class="c-overzicht__battle-winner-text">
              <span class="c-overzicht__battle-winner-label">Winnaar</span>
              <strong class="c-overzicht__battle-winner-name">{{ colorBattle.winnaar || '—' }}</strong>
            </div>
          </div>
          <div class="c-overzicht__battle-tabs" role="tablist" aria-label="Speler resultaten">
            <button type="button" :class="['c-overzicht__battle-tab', battleActive === 'speler1' ? 'is-active' : '']" @click="battleActive = 'speler1'">
              {{ colorBattle.speler1_naam || 'Speler 1' }}
            </button>
            <button type="button" :class="['c-overzicht__battle-tab', battleActive === 'speler2' ? 'is-active' : '']" @click="battleActive = 'speler2'">
              {{ colorBattle.speler2_naam || 'Speler 2' }}
            </button>
          </div>
        </div>

        <div class="c-overzicht__battle-stats">
          <OverzichtCard :waarde="activeAverage" :label="'Gemiddelde'" />
          <OverzichtCard :waarde="activeAccuracy" :label="'Exactheid'" />
        </div>

        <div class="c-overzicht__rounds">
          <div class="c-overzicht__rounds-header">
            <ChartNoAxesCombined />
            <h3>Reactietijden per Ronde</h3>
          </div>
          <OverzichtGraph v-if="activeRounds.length" :key="battleActive" :results="activeRounds" :average-time="activeAverage" />
        </div>

        <div class="c-overzicht__counts">
          <h3>Totale uitslag</h3>
          <div class="c-overzicht__counts-inner">
            <OverzichtCountItem :counts="activeCorrect" label="Correct" type="correct" />
            <OverzichtCountItem :counts="activeFout" label="Fout" type="fout" />
          </div>
        </div>
      </div>
    </template>

    <template v-else>
      <div class="c-overzicht__stats">
        <OverzichtCard v-for="stat in stats" :key="stat.label" :waarde="stat.waarde" :label="stat.label" />
      </div>

      <div class="c-overzicht__rounds">
        <div class="c-overzicht__rounds-header">
          <ChartNoAxesCombined />
          <h3>Reactietijden per Ronde</h3>
        </div>

        <OverzichtGraph v-if="rounds.length" :results="rounds" :average-time="computedAverage" />
      </div>

      <div class="c-overzicht__counts">
        <h3>Totale uitslag</h3>
        <div class="c-overzicht__counts-inner">
          <OverzichtCountItem v-for="count of counts" :counts="count.value" :label="count.label" :type="count.type" />
        </div>
      </div>
    </template>

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

  .c-overzicht__battle {
    margin-top: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .c-overzicht__battle-header {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  .c-overzicht__battle-winner {
    min-width: 150px;
    margin: auto;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    padding: 0.5rem 1rem;
    border-radius: 999px;
    background: var(--blue-10);
    border: 1px solid var(--gray-20);
  }

  .c-overzicht__battle-winner-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 2rem;
    height: 2rem;
    border-radius: 50%;
    background: var(--blue-10);
    color: var(--blue-100);
  }

  .c-overzicht__battle-winner-text {
    display: flex;
    flex-direction: column;
    line-height: 1.1;
  }

  .c-overzicht__battle-winner-label {
    font-size: 0.75rem;
    color: var(--gray-60);
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .c-overzicht__battle-winner-name {
    font-size: 1.05rem;
    color: var(--gray-80);
    font-weight: 700;
  }

  .c-overzicht__battle-tabs {
    display: flex;
    justify-content: center;
    border-bottom: 1px solid var(--gray-20);
    padding-bottom: 0.5rem;
  }

  .c-overzicht__battle-tab {
    border: none;
    background: transparent;
    padding: 0.25rem 0.2rem 0.4rem;
    font-size: 1rem;
    flex: 1;
    font-weight: 700;
    color: var(--gray-60);
    cursor: pointer;
    position: relative;
  }

  .c-overzicht__battle-tab.is-active {
    color: var(--blue-100);
  }

  .c-overzicht__battle-tab.is-active::after {
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    bottom: -0.55rem;
    height: 3px;
    background: var(--blue-100);
    border-radius: 999px;
  }

  .c-overzicht__battle-stats {
    display: grid;
    gap: 1.25rem;
    grid-template-columns: repeat(2, minmax(0, 1fr));

    @media (width >= 768px) {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
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
