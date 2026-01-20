<script setup>
import ButtonsPrimary from '../../components/buttons/ButtonsPrimary.vue';
</script>

<template>
  <div class="o-container-desktop">
    <div class="c-proficiat">
      <div class="c-proficiat__text">
        <h1>Proficiat!</h1>
        <h3>Goed gedaan! Je hebt de training afgerond</h3>
      </div>

      <img class="c-proficiat__img" src="/images/training-afgerond.png" alt="Proficiat" />

      <ButtonsPrimary url="/resultaten/overzicht" title="Bekijk je resultaten"></ButtonsPrimary>
    </div>
  </div>
</template>

<style scoped>
.c-proficiat {
  min-height: 100vh;
  display: grid;
  align-items: center;
  justify-items: center;
  gap: 1.5rem;
  padding: 2rem;
  box-sizing: border-box;
  text-align: center;
}

.c-proficiat__text {
  width: 100%;
  max-width: 60ch;
}

.c-proficiat__img {
  width: auto;
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  display: block;
}

@media (max-width: 576px) {
  .c-proficiat {
    padding: 1rem;
    gap: 1rem;
  }
  .c-proficiat__text {
    max-width: 90%;
  }
}
</style>
