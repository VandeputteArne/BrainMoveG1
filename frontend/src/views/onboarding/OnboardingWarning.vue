<script setup>
import { ref, onMounted } from 'vue';
import ButtonsPrimary from '../../components/buttons/ButtonsPrimary.vue';
import OnboardingProgressBlock from '../../components/onboarding/OnboardingProgressBlock.vue';

const isLoaded = ref(false);

onMounted(() => {
  requestAnimationFrame(() => {
    isLoaded.value = true;
  });
});
</script>

<template>
  <div class="o-container-desktop">
    <div class="c-warning" :class="{ 'is-loaded': isLoaded }">
      <h1>Waarschuwing</h1>
      <img src="/images/waarschuwing.png" alt="Waarschuwing" class="c-warning__img" loading="lazy" decoding="async" />
      <p class="c-warning__text">Schakel het systeem altijd uit via de pagina Apparaten. Trek nooit de stekker uit het stopcontact, dit kan het systeem beschadigen.</p>
      <div class="c-warning__progress">
        <div class="c-warning__progess-blocks">
          <OnboardingProgressBlock :active="false" />
          <OnboardingProgressBlock :active="false" />
          <OnboardingProgressBlock :active="false" />
          <OnboardingProgressBlock :active="true" />
        </div>
        <buttons-primary url="/games" title="Begin met trainen" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.c-warning {
  display: flex;
  flex-direction: column;
  align-items: center;
  height: calc(var(--app-height, 100vh) - 5.5rem);
  gap: 3rem;
  margin-top: 3rem;
  opacity: 0;
  transition:
    opacity 0.4s ease-out,
    transform 0.4s ease-out;
  will-change: opacity, transform;
  transform: translateY(10px);

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

  .c-warning__text {
    text-align: center;
    padding: 0 1rem;
    max-width: 20rem;
  }

  .c-warning__progess-blocks {
    display: flex;
    gap: 0.5rem;
  }

  .c-warning__progress {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.5rem;
    margin-top: 2rem;
    width: 100%;
    padding: 0rem 1.25rem;
    position: absolute;
    bottom: 2rem;
    visibility: visible;
    opacity: 1;

    @media (width >= 768px) {
      max-width: 30rem;
    }

    @media (max-height: 700px) {
      position: static;
      margin-top: 2rem;
    }
  }

  .c-warning__img {
    width: 90%;
    max-width: 20rem;
    height: auto;
  }
}
</style>
