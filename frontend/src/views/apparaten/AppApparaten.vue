<script setup>
import CardPotjes from '../../components/cards/CardPotjes.vue';
import ButtonsPrimary from '../../components/buttons/ButtonsPrimary.vue';

import { Power } from 'lucide-vue-next';
</script>

<template>
  <div class="c-apparaten">
    <h1>Apparaten</h1>
    <div class="c-apparaten__grid">
      <CardPotjes kleur="rood" :status="true" label="Potje 1" :batterij="75" />
      <CardPotjes kleur="blauw" :status="false" label="Potje 2" :batterij="50" />
      <CardPotjes kleur="groen" :status="true" label="Potje 3" :batterij="90" />
      <CardPotjes kleur="geel" :status="false" label="Potje 4" :batterij="20" />
    </div>

    <button class="c-button c-apparaten__button">
      <span class="c-button__icon"><Power /></span>
      <h3>Alles uitschakelen</h3>
    </button>
  </div>
</template>

<style scoped>
.c-apparaten {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-title);
  max-width: 75rem;
  margin: 0 auto;
}

.c-apparaten__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(auto, 1fr));
  gap: 1.25rem;
  width: 100%;
  box-sizing: border-box;
  justify-items: center;

  @media (width >= 768px) {
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
  }

  @media (width >= 1024px) {
    grid-template-columns: repeat(4, 1fr);
    gap: 2rem;
  }
}

.c-apparaten__button {
  margin-top: 1rem;
  max-width: 400px;
  align-self: center;
}
</style>
