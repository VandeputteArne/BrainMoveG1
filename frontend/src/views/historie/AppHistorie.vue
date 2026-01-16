<script setup>
import FilterGame from '../../components/filters/FilterGame.vue';
import InputGebruikersnaam from '../../components/inputs/InputGebruikersnaam.vue';
import FilterDatum from '../../components/filters/FilterDatum.vue';
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
      <h3>Color Sprint</h3>
      <p>Alle Resultaten</p>
      <div class="c-historie__resultaten"></div>
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
}
</style>
