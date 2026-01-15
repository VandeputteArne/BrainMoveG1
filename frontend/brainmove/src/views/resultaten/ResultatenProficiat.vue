<script setup>
import ButtonsPrimary from '../../components/buttons/ButtonsPrimary.vue';
import { onMounted } from 'vue';

onMounted(async () => {
  try {
    const response = await fetch('http://10.42.0.1:8000/laatste_rondewaarden');

    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('laatste_rondewaarden', JSON.stringify(data));
    } else {
      console.error('Failed to fetch round values:', response.statusText);
    }
  } catch (error) {
    console.error('Error fetching round values:', error);
  }
});
</script>

<template>
  <div class="c-proficiat">
    <div class="c-proficiat__text">
      <h1>Proficiat!</h1>
      <h3>Goed gedaan! Je hebt de training afgerond</h3>
    </div>

    <img class="c-proficiat__img" src="/images/training-afgerond.png" alt="Proficiat" />

    <ButtonsPrimary to="/resultaten/overzicht" title="Bekijk je resultaten"></ButtonsPrimary>
  </div>
</template>

<style scoped>
.c-proficiat {
  min-height: 100vh;
  display: grid;
  grid-template-rows: auto 1fr auto;
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
