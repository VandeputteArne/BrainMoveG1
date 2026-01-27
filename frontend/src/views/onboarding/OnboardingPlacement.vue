<script setup>
import { ref, onMounted } from 'vue';
import OnboardingProgressBlock from '../../components/onboarding/OnboardingProgressBlock.vue';
import ButtonsNext from '../../components/buttons/ButtonsNext.vue';

const isLoaded = ref(false);

onMounted(() => {
  requestAnimationFrame(() => {
    isLoaded.value = true;
  });
});
</script>

<template>
  <div class="o-container-desktop">
    <div class="c-opstelling" :class="{ 'is-loaded': isLoaded }">
      <div class="c-opstelling__text">
        <h1>Opstelling potjes</h1>
      </div>

      <img class="c-opstelling__image" src="/images/opstelling.png" alt="Opstelling potjes in een 2x2 meter speelveld" loading="lazy" decoding="async" />

      <p class="c-opstelling__description">Zet de potjes in een speelveld van 2x2 meter. Laat genoeg ruimte zodat spelers vrij kunnen bewegen.</p>

      <div class="c-opstelling__progress">
        <div class="c-opstelling__progess-blocks">
          <OnboardingProgressBlock :active="false" />
          <OnboardingProgressBlock :active="false" />
          <OnboardingProgressBlock :active="true" />
          <OnboardingProgressBlock :active="false" />
        </div>
        <ButtonsNext :progress="75" to="/warning" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.c-opstelling {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: start;
  height: calc(var(--app-height, 100vh) - 5.5rem);
  overflow: hidden;
  gap: 3rem;
  margin-top: 3rem;
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

  @media (max-height: 700px) {
    height: auto;
    min-height: var(--app-height, 100vh);
    overflow: auto;
    padding-bottom: 2rem;
  }
}

.c-opstelling__text {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 0 1rem;
  max-width: 26rem;
}

.c-opstelling__image {
  width: 90%;
  max-width: 15rem;
  height: auto;
}

.c-opstelling__progress {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
  position: absolute;
  bottom: 2rem;
  visibility: visible;
  opacity: 1;
  width: 100%;
  padding: 0 1.25rem;

  @media (width >= 768px) {
    max-width: 30rem;
  }

  @media (max-height: 700px) {
    position: static;
    margin-top: 2rem;
  }
}

.c-opstelling__progess-blocks {
  display: flex;
  gap: 0.5rem;
}

.c-opstelling__description {
  text-align: center;
  padding: 0 1rem;
  max-width: 26rem;
}
</style>
