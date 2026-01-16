<script setup>
import FilterGame from '../../components/filters/FilterGame.vue';
import InputGebruikersnaam from '../../components/inputs/InputGebruikersnaam.vue';
import FilterDatum from '../../components/filters/FilterDatum.vue';
import CardHistorie from '../../components/cards/CardHistorie.vue';
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
      <div class="c-historie__resultaten">
        <CardHistorie gebruiker="Jan Jansen" datumtijd="12-03-2024 14:30" gemtijd="00:45" score="1500" url="/resultaten/1/proficiat" />
        <CardHistorie gebruiker="Piet Pietersen" datumtijd="10-03-2024 16:00" gemtijd="00:50" score="1400" url="/resultaten/2/proficiat" />
        <CardHistorie gebruiker="Klaas Klaassen" datumtijd="08-03-2024 10:15" gemtijd="00:55" score="1300" url="/resultaten/3/proficiat" />
        <CardHistorie gebruiker="Marie de Vries" datumtijd="05-03-2024 09:45" gemtijd="00:48" score="1450" url="/resultaten/4/proficiat" />
        <CardHistorie gebruiker="Sophie van den Berg" datumtijd="03-03-2024 11:20" gemtijd="00:52" score="1350" url="/resultaten/overzicht/5" />
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
}
</style>
