<script setup>
import CardPotjes from '../../components/cards/CardPotjes.vue';
import OnboardingProgressBlock from '../../components/onboarding/OnboardingProgressBlock.vue';
import ButtonsNext from '../../components/buttons/ButtonsNext.vue';
</script>

<template>
  <div class="c-setup">
    <div class="c-setup__text">
      <h1>Potjes aanzetten</h1>
      <p>Tik op het fysieke knopje onder een potje om het aan te zetten. Op het scherm en via geluid hoor je of het gelukt is.</p>
    </div>
    <div class="c-setup__potjes">
      <CardPotjes kleur="rood" :status="true" />
      <CardPotjes kleur="blauw" :status="false" />
      <CardPotjes kleur="groen" :status="true" />
      <CardPotjes kleur="geel" :status="false" />
    </div>

    <div class="c-setup__progress">
      <div class="c-setup__progess-blocks">
        <OnboardingProgressBlock :active="false" />
        <OnboardingProgressBlock :active="true" />
        <OnboardingProgressBlock :active="false" />
      </div>
      <ButtonsNext :progress="50" to="/warning" />
    </div>
  </div>
</template>

<style scoped>
.c-setup {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: start;
  height: 100dvh;
  gap: 2rem;
}

.c-setup__potjes {
  display: grid;
  grid-template-columns: repeat(2, minmax(auto, 1fr));
  gap: 1.25rem;
  width: 100%;
  box-sizing: border-box;
  justify-items: center;
}

.c-setup__progress {
}

.c-setup__circle {
  border-radius: 100%;
  z-index: -1;
}

.c-setup__circle--1 {
  position: absolute;
  width: 11rem;
  height: 11rem;
  top: -5rem;
  left: -5rem;

  background-color: var(--blue-40);
}

.c-setup__circle--2 {
  position: absolute;
  width: 11rem;
  height: 11rem;
  bottom: -5rem;
  right: -5rem;

  background-color: var(--blue-10);
}

.c-setup__progress {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
}

.c-setup__progess-blocks {
  display: flex;
  gap: 0.5rem;
}

.c-setup__text {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  width: 100%;
  padding-right: 2rem;
}
</style>
