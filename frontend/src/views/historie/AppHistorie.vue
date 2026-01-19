<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import FilterGame from '../../components/filters/FilterGame.vue';
import InputGebruikersnaam from '../../components/inputs/InputGebruikersnaam.vue';
import FilterDatum from '../../components/filters/FilterDatum.vue';
import CardHistorie from '../../components/cards/CardHistorie.vue';

const scrollContainer = ref(null);
const scrollThumb = ref(null);
const scrollTrack = ref(null);

const isDragging = ref(false);
const startY = ref(0);
const startScrollTop = ref(0);

function updateScrollbar() {
  if (!scrollContainer.value || !scrollThumb.value || !scrollTrack.value) return;

  const { scrollTop, scrollHeight, clientHeight } = scrollContainer.value;
  const trackHeight = scrollTrack.value.clientHeight;

  const thumbHeight = Math.max((clientHeight / scrollHeight) * trackHeight, 30);
  const thumbTop = (scrollTop / scrollHeight) * trackHeight;

  scrollThumb.value.style.height = `${thumbHeight}px`;
  scrollThumb.value.style.top = `${thumbTop}px`;
}

function onThumbMouseDown(e) {
  isDragging.value = true;
  startY.value = e.clientY;
  startScrollTop.value = scrollContainer.value.scrollTop;
  e.preventDefault();
}

function onMouseMove(e) {
  if (!isDragging.value || !scrollContainer.value || !scrollTrack.value) return;

  const deltaY = e.clientY - startY.value;
  const trackHeight = scrollTrack.value.clientHeight;
  const scrollHeight = scrollContainer.value.scrollHeight;
  const clientHeight = scrollContainer.value.clientHeight;

  const scrollRatio = scrollHeight / trackHeight;
  scrollContainer.value.scrollTop = startScrollTop.value + deltaY * scrollRatio;
}

function onMouseUp() {
  isDragging.value = false;
}

function onTrackClick(e) {
  if (!scrollContainer.value || !scrollTrack.value || !scrollThumb.value) return;
  if (e.target === scrollThumb.value) return;

  const trackRect = scrollTrack.value.getBoundingClientRect();
  const clickY = e.clientY - trackRect.top;
  const trackHeight = scrollTrack.value.clientHeight;
  const scrollHeight = scrollContainer.value.scrollHeight;

  scrollContainer.value.scrollTop = (clickY / trackHeight) * scrollHeight;
}

onMounted(() => {
  if (scrollContainer.value) {
    scrollContainer.value.addEventListener('scroll', updateScrollbar);
    updateScrollbar();
  }
  document.addEventListener('mousemove', onMouseMove);
  document.addEventListener('mouseup', onMouseUp);
});

onUnmounted(() => {
  if (scrollContainer.value) {
    scrollContainer.value.removeEventListener('scroll', updateScrollbar);
  }
  document.removeEventListener('mousemove', onMouseMove);
  document.removeEventListener('mouseup', onMouseUp);
});
</script>

<template>
  <div class="c-historie">
    <h1>Historie</h1>
    <div class="c-historie__filters">
      <FilterGame />
      <InputGebruikersnaam label="Zoek op gebruikersnaam" placeholder="Voer een gebruikersnaam in" />
      <FilterDatum />
    </div>

    <div class="c-historie__overzicht">
      <div>
        <h3>Color Sprint</h3>
        <p>Alle Resultaten</p>
      </div>
      <div class="c-historie__scroll-wrapper">
        <div ref="scrollContainer" class="c-historie__resultaten">
          <CardHistorie gebruiker="Jan" datumtijd="12-03-2024 14:30" gemtijd="00:45" score="1500" url="/resultaten/1/proficiat" />
          <CardHistorie gebruiker="Piet" datumtijd="10-03-2024 16:00" gemtijd="00:50" score="1400" url="/resultaten/2/proficiat" />
          <CardHistorie gebruiker="Klaas" datumtijd="08-03-2024 10:15" gemtijd="00:55" score="1300" url="/resultaten/3/proficiat" />
          <CardHistorie gebruiker="Marie" datumtijd="05-03-2024 09:45" gemtijd="00:48" score="1450" url="/resultaten/4/proficiat" />
          <CardHistorie gebruiker="Sophie" datumtijd="03-03-2024 11:20" gemtijd="00:52" score="1350" url="/resultaten/overzicht/5" />
        </div>
        <div ref="scrollTrack" class="c-historie__scrollbar" @click="onTrackClick">
          <div ref="scrollThumb" class="c-historie__scrollbar-thumb" @mousedown="onThumbMouseDown"></div>
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

  .c-historie__filters {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .c-historie__overzicht {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-blocks);

    .c-historie__scroll-wrapper {
      position: relative;
      display: flex;
      gap: 0.5rem;
    }

    .c-historie__resultaten {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      height: 18.75rem;
      overflow-y: scroll;
      flex: 1;
      padding-right: 0.25rem;

      /* Hide native scrollbar */
      &::-webkit-scrollbar {
        display: none;
      }
      -ms-overflow-style: none;
      scrollbar-width: none;
    }

    .c-historie__scrollbar {
      width: 0.5rem;
      height: 18.75rem;
      background: var(--gray-20);
      border-radius: var(--radius-40);
      position: relative;
      cursor: pointer;
      flex-shrink: 0;
    }

    .c-historie__scrollbar-thumb {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      background: var(--blue-100);
      border-radius: var(--radius-40);
      cursor: grab;
      transition: background 0.2s;

      &:hover {
        background: var(--blue-80);
      }

      &:active {
        cursor: grabbing;
      }
    }
  }
}

.c-historie__resultaten::-webkit-scrollbar-track {
  visibility: visible !important;
}

.c-historie__resultaten::-webkit-scrollbar-thumb {
  visibility: visible !important;
}
</style>
