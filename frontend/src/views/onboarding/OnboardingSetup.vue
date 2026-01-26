<script setup>
import { computed, onMounted, ref } from 'vue';
import CardPotjes from '../../components/cards/CardPotjes.vue';
import OnboardingProgressBlock from '../../components/onboarding/OnboardingProgressBlock.vue';
import ButtonsNext from '../../components/buttons/ButtonsNext.vue';
import { TriangleAlert } from 'lucide-vue-next';

import { useDeviceStatus } from '../../composables/useDeviceStatus.js';

const isLoaded = ref(false);

const { allDevicesConnected, connectedDevices, fetchDeviceStatus } = useDeviceStatus();

const isDeviceConnected = (kleur) => {
  return connectedDevices.value.some((device) => device.kleur === kleur);
};

const allPotsConnected = computed(() => {
  return isDeviceConnected('rood') && isDeviceConnected('blauw') && isDeviceConnected('groen') && isDeviceConnected('geel');
});

onMounted(() => {
  fetchDeviceStatus();
  requestAnimationFrame(() => {
    isLoaded.value = true;
  });
});
</script>

<template>
  <div class="o-container-desktop">
    <div class="c-setup" :class="{ 'is-loaded': isLoaded }">
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
        <ButtonsNext :progress="50" to="/warning" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.c-setup {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: start;
  height: calc(100dvh - 2.5rem);
  overflow: hidden;
  gap: 2rem;
  opacity: 0;
  transform: translateY(10px);
  transition:
    opacity 0.4s ease-out,
    transform 0.4s ease-out;
  will-change: opacity, transform;

  &.is-loaded {
    opacity: 1;
    transform: translateY(0);
  }

  @media (width >= 768px) {
    align-items: start;
    gap: 3rem;
  }
}

.c-setup__potjes {
  display: grid;
  grid-template-columns: repeat(2, minmax(auto, 1fr));
  gap: 1.25rem;
  width: 100%;
  box-sizing: border-box;
  justify-items: center;

  @media (width >= 768px) {
    display: flex;
  }
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
  position: absolute;
  bottom: 2rem;
  visibility: visible;
  opacity: 1;

  @media (width >= 768px) {
    left: 50%;
    transform: translateX(-50%);
  }
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

  @media (width >= 768px) {
    width: 60%;
  }
}

.c-setup__warning {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0.5rem;
  justify-content: center;
  font-weight: 500;
  text-align: center;
  margin: 0;
  padding: 0.5rem 1rem;
  border-radius: var(--radius-10, 0.5rem);
  width: 100%;
  box-sizing: border-box;
}
</style>
