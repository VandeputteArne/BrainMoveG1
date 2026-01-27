<script setup>
import { ref, onMounted } from 'vue';
import ButtonsNext from '../../components/buttons/ButtonsNext.vue';
import OnboardingProgressBlock from '../../components/onboarding/OnboardingProgressBlock.vue';

const isLoaded = ref(false);

onMounted(() => {
  requestAnimationFrame(() => {
    isLoaded.value = true;
  });
});
</script>

<template>
  <div class="c-onboarding">
    <div class="c-onboarding__inhoud" :class="{ 'is-loaded': isLoaded }">
      <img class="c-onboarding__image" src="/images/BrainMove-Logo.png" alt="BrainMove Logo" loading="eager" decoding="async" fetchpriority="high" />
      <div class="c-onboarding__text">
        <h1>BrainMove</h1>
        <h3 class="c-onboarding__h2">Beweeg slimmer, denk scherper</h3>
      </div>
    </div>
    <div class="c-onboarding__progress" :class="{ 'is-loaded': isLoaded }">
      <div class="c-onboarding__progess-blocks">
        <OnboardingProgressBlock :active="true" />
        <OnboardingProgressBlock :active="false" />
        <OnboardingProgressBlock :active="false" />
        <OnboardingProgressBlock :active="false" />
      </div>
      <ButtonsNext :progress="25" to="/setup" />
    </div>

    <div class="c-onboarding__circle c-onboarding__circle--1"></div>
    <div class="c-onboarding__circle c-onboarding__circle--2"></div>
  </div>
</template>

<style scoped>
.c-onboarding {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: var(--app-height, 100vh);
  padding: 0rem 1.25rem;

  position: relative;
  overflow: hidden;

  .c-onboarding__inhoud {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    width: 100%;
    gap: 2rem;
    margin-bottom: 4rem;
    opacity: 0;
    transform: translateY(20px);
    transition:
      opacity 0.6s ease-out,
      transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
    will-change: opacity, transform;

    &.is-loaded {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .c-onboarding__image {
    width: 60%;
    max-width: 20rem;
    height: auto;
    transform: scale(0.9);
    transition: transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) 0.1s;
    will-change: transform;

    .is-loaded & {
      transform: scale(1);
    }
  }

  .c-onboarding__text {
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .c-onboarding__progress {
    position: absolute;
    bottom: 2rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2rem;
    opacity: 0;
    transform: translateY(20px);
    transition:
      opacity 0.6s ease-out 0.3s,
      transform 0.6s ease-out 0.3s;
    will-change: opacity, transform;

    &.is-loaded {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .c-onboarding__circle {
    border-radius: 100%;
    z-index: -1;
    animation: float 6s ease-in-out infinite;
  }

  .c-onboarding__circle--1 {
    position: absolute;
    width: 11rem;
    height: 11rem;
    top: -5rem;
    left: -5rem;

    background-color: var(--blue-40);
  }

  .c-onboarding__circle--2 {
    position: absolute;
    width: 11rem;
    height: 11rem;
    bottom: -5rem;
    right: -5rem;

    background-color: var(--blue-10);
    animation-delay: 3s;
  }

  .c-onboarding__progess-blocks {
    display: flex;
    gap: 0.5rem;
  }

  .c-onboarding__h2 {
    text-align: center;
  }

  @keyframes float {
    0%,
    100% {
      transform: translateY(0) scale(1);
    }
    50% {
      transform: translateY(-15px) scale(1.05);
    }
  }

  @media (max-height: 700px) {
    justify-content: flex-start;
    height: auto;
    min-height: var(--app-height, 100vh);
    overflow: auto;
    padding-bottom: 2rem;

    .c-onboarding__progress {
      position: static;
      margin-top: 2rem;
    }
  }
}
</style>
