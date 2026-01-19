<script setup>
import { computed, onMounted } from 'vue';
import CardPotjes from '../../components/cards/CardPotjes.vue';
import OnboardingProgressBlock from '../../components/onboarding/OnboardingProgressBlock.vue';
import ButtonsNext from '../../components/buttons/ButtonsNext.vue';
import { TriangleAlert } from 'lucide-vue-next';

import { useDeviceStatus } from '../../composables/useDeviceStatus.js';

const { allDevicesConnected, connectedDevices, fetchDeviceStatus } = useDeviceStatus();

const isDeviceConnected = (kleur) => {
  return connectedDevices.value.some((device) => device.kleur === kleur);
};

const allPotsConnected = computed(() => {
  return isDeviceConnected('rood') && isDeviceConnected('blauw') && isDeviceConnected('groen') && isDeviceConnected('geel');
});

const buttonProgress = computed(() => (allPotsConnected.value ? 100 : 50));

onMounted(() => {
  fetchDeviceStatus();
});
</script>

<template>
  <div class="c-setup">
    <div class="c-setup__text">
      <h1>Potjes aanzetten</h1>
      <p>Tik op het fysieke knopje onder een potje om het aan te zetten. Op het scherm en via geluid hoor je of het gelukt is.</p>
    </div>
    <div class="c-setup__potjes">
      <CardPotjes kleur="rood" :status="isDeviceConnected('rood')" />
      <CardPotjes kleur="blauw" :status="isDeviceConnected('blauw')" />
      <CardPotjes kleur="groen" :status="isDeviceConnected('groen')" />
      <CardPotjes kleur="geel" :status="isDeviceConnected('geel')" />
    </div>

    <p v-if="!allPotsConnected" class="c-setup__warning"><TriangleAlert /> Niet alle potjes zijn verbonden</p>

    <div class="c-setup__progress">
      <div class="c-setup__progess-blocks">
        <OnboardingProgressBlock :active="false" />
        <OnboardingProgressBlock :active="true" />
        <OnboardingProgressBlock :active="false" />
      </div>
      <ButtonsNext :progress="buttonProgress" :disabled="!allPotsConnected" to="/warning" />
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

.c-setup__warning {
  color: var(--red-50, #f44336);
  font-weight: 500;
  text-align: center;
  margin: 0;
  padding: 0.5rem 1rem;
  background-color: rgba(244, 67, 54, 0.1);
  border-radius: var(--radius-10, 0.5rem);
  width: 100%;
  box-sizing: border-box;
}
</style>
