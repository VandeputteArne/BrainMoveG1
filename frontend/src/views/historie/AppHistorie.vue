<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';
import FilterGame from '../../components/filters/FilterGame.vue';
import InputGebruikersnaam from '../../components/inputs/InputGebruikersnaam.vue';
import FilterDatum from '../../components/filters/FilterDatum.vue';
import CardHistorie from '../../components/cards/CardHistorie.vue';
import { SlidersHorizontal, X } from 'lucide-vue-next';
import { getApiUrl } from '../../config/api.js';

const selectedGame = ref(null);
const gebruikersnaam = ref('');
const selectedDatum = ref('');
const historieData = ref([]);
const gameName = ref('');
const filtersRef = ref(null);
const showPopup = ref(false);
const isFiltersVisible = ref(true);
let observer = null;

async function fetchHistorie() {
  if (!selectedGame.value) {
    historieData.value = [];
    return;
  }

  const gameId = selectedGame.value;

  const params = new URLSearchParams();

  if (gebruikersnaam.value) {
    params.append('gebruikersnaam', gebruikersnaam.value);
  }

  if (selectedDatum.value) {
    const dateObj = new Date(selectedDatum.value);
    const day = String(dateObj.getDate()).padStart(2, '0');
    const month = String(dateObj.getMonth() + 1).padStart(2, '0');
    const year = dateObj.getFullYear();
    params.append('datum', `${day}-${month}-${year}`);
  }

  const queryString = params.toString();
  const url = getApiUrl(`trainingen/historie/${gameId}${queryString ? '?' + queryString : ''}`);

  console.log('Fetching historie from:', url);

  try {
    const res = await fetch(url);

    console.log('Response status:', res.status);

    if (res.ok) {
      const data = await res.json();
      console.log('Data received:', data);
      historieData.value = data.map((item) => ({
        id: item.training_id,
        gebruiker: item.gebruikersnaam,
        datumtijd: formatDateTime(item.start_tijd),
        score: item.waarde,
        eenheid: item.eenheid,
        url: `/resultaten/overzicht/${item.training_id}`,
      }));
    }
  } catch (error) {
    console.error('Failed to fetch historie:', error);
  }
}

function formatDateTime(isoString) {
  if (!isoString) return '';
  const date = new Date(isoString);
  const day = String(date.getDate()).padStart(2, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const year = date.getFullYear();
  return `${day}-${month}-${year}`;
}

watch([selectedGame, gebruikersnaam, selectedDatum], async () => {
  await fetchHistorie();
  // Setup observer for new cards after data loads
  nextTick(() => {
    setupIntersectionObserver();
  });
});

function setupIntersectionObserver() {
  // Clean up existing observer
  if (observer) {
    observer.disconnect();
  }

  // Create new observer
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    },
    {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px',
    }
  );

  // Observe all cards
  const cards = document.querySelectorAll('.c-historie__card');
  cards.forEach((card) => {
    observer.observe(card);
  });
}

function handleScroll() {
  if (!filtersRef.value) return;

  const rect = filtersRef.value.getBoundingClientRect();
  isFiltersVisible.value = rect.bottom > 0;
}

function togglePopup() {
  showPopup.value = !showPopup.value;
}

function closePopup() {
  showPopup.value = false;
}

onMounted(() => {
  fetchHistorie();

  window.addEventListener('scroll', handleScroll);
  handleScroll();
});

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll);
});
</script>

<template>
  <div class="c-historie">
    <div class="c-historie__container">
      <div ref="filtersRef" class="c-historie__filters">
        <h1>Historie</h1>
        <FilterGame v-model="selectedGame" @update:gameName="gameName = $event" />
        <InputGebruikersnaam v-model="gebruikersnaam" label="Zoek op gebruikersnaam" placeholder="Voer een gebruikersnaam in" />
        <FilterDatum v-model="selectedDatum" />
      </div>

      <div class="c-historie__content">
        <button v-if="!isFiltersVisible" class="c-historie__filter-button" @click="togglePopup">
          <SlidersHorizontal :size="20" />
          Filters
        </button>

        <div v-if="showPopup" class="c-historie__popup-overlay" @click="closePopup">
          <div class="c-historie__popup" @click.stop>
            <div class="c-historie__popup-header">
              <h2>Filters</h2>
              <button class="c-historie__popup-close" @click="closePopup">
                <X :size="24" />
              </button>
            </div>
            <div class="c-historie__popup-filters">
              <FilterGame v-model="selectedGame" @update:gameName="gameName = $event" />
              <InputGebruikersnaam v-model="gebruikersnaam" label="Zoek op gebruikersnaam" placeholder="Voer een gebruikersnaam in" />
              <FilterDatum v-model="selectedDatum" />
            </div>
          </div>
        </div>

        <div class="c-historie__overzicht">
          <div>
            <h3>{{ gameName || 'Selecteer een game' }}</h3>
            <p>{{ historieData.length }} Resultaten</p>
          </div>
          <div class="c-historie__resultaten">
            <CardHistorie v-for="item in historieData" :key="item.id" :gebruiker="item.gebruiker" :datumtijd="item.datumtijd" :score="item.score" :eenheid="item.eenheid" :url="item.url" />
            <p v-if="historieData.length === 0" class="c-historie__empty">Geen resultaten gevonden</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.c-historie {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-title);

  .c-historie__container {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-title);

    @media (width >= 768px) {
      flex-direction: row;
      gap: 3rem;
      align-items: flex-start;
    }
  }

  .c-historie__filters {
    display: flex;
    flex-direction: column;
    gap: 1rem;

    @media (width >= 768px) {
      flex: 0 0 300px;
      position: sticky;
      top: 6.5rem;
    }
  }

  .c-historie__content {
    @media (width >= 768px) {
      flex: 1;
    }
  }

  .c-historie__filter-button {
    position: fixed;
    bottom: 5rem;
    left: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    background: var(--blue-100);
    color: white;
    border: none;
    border-radius: var(--radius-40);
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    transition: all 0.3s;
    z-index: 100;

    &:hover {
      background: var(--blue-80);
      transform: translateY(-2px);
      box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
    }

    &:active {
      transform: translateY(0);
    }
  }

  .c-historie__popup-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    animation: fadeIn 0.2s;
  }

  .c-historie__popup {
    background: white;
    border-radius: var(--radius-20);
    padding: 2rem;
    max-width: 90%;
    width: 500px;
    max-height: 90vh;
    overflow-y: auto;
    animation: slideUp 0.3s;
  }

  .c-historie__popup-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;

    h2 {
      margin: 0;
      font-size: 1.5rem;
    }
  }

  .c-historie__popup-close {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0.25rem;
    color: var(--gray-60);
    transition: color 0.2s;

    &:hover {
      color: var(--gray-100);
    }
  }

  .c-historie__popup-filters {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  @keyframes slideUp {
    from {
      transform: translateY(20px);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }

  .c-historie__overzicht {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-blocks);

    .c-historie__resultaten {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }
  }
}
</style>
